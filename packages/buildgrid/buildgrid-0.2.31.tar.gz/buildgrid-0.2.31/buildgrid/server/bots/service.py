# Copyright (C) 2018 Bloomberg LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  <http://www.apache.org/licenses/LICENSE-2.0>
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
BotsService
=================

"""

import uuid
from threading import Event

import grpc
from google.protobuf import empty_pb2

from buildgrid._protos.build.bazel.remote.execution.v2.remote_execution_pb2 import ExecutedActionMetadata
from buildgrid._protos.google.devtools.remoteworkers.v1test2.bots_pb2 import DESCRIPTOR as BOTS_DESCRIPTOR
from buildgrid._protos.google.devtools.remoteworkers.v1test2.bots_pb2 import (
    BotSession,
    CreateBotSessionRequest,
    PostBotEventTempRequest,
    UpdateBotSessionRequest,
)
from buildgrid._protos.google.devtools.remoteworkers.v1test2.bots_pb2_grpc import (
    BotsServicer,
    add_BotsServicer_to_server,
)
from buildgrid.server.bots.instance import BotsInterface
from buildgrid.server.decorators import rpc
from buildgrid.server.enums import BotStatus
from buildgrid.server.exceptions import InvalidArgumentError
from buildgrid.server.logging import buildgrid_logger
from buildgrid.server.scheduler.impl import BotMetrics, Scheduler
from buildgrid.server.scheduler.properties import hash_from_dict
from buildgrid.server.servicer import InstancedServicer
from buildgrid.server.settings import MAX_WORKER_TTL, NETWORK_TIMEOUT
from buildgrid.server.utils.bots import bot_log_tags, get_bot_capacity
from buildgrid.server.utils.cancellation import CancellationContext


def _get_bot_name_parent_part(name: str) -> str:
    names = name.split("/")
    return "/".join(names[:-1])


LOGGER = buildgrid_logger(__name__)


class BotsService(BotsServicer, InstancedServicer[BotsInterface]):
    SERVICE_NAME = "Bots"
    REGISTER_METHOD = add_BotsServicer_to_server
    FULL_NAME = BOTS_DESCRIPTOR.services_by_name[SERVICE_NAME].full_name

    @rpc(instance_getter=lambda r: r.parent)
    def CreateBotSession(self, request: CreateBotSessionRequest, context: grpc.ServicerContext) -> BotSession:
        if not request.bot_session.bot_id:
            raise InvalidArgumentError("Bots's id must be set by client.")

        scheduler = self.current_instance.scheduler
        capacity = get_bot_capacity(request.bot_session)
        labels = scheduler.property_set.bot_property_labels(request.bot_session)
        capabilities = list(map(hash_from_dict, scheduler.property_set.worker_properties(request.bot_session)))

        request.bot_session.name = f"{request.parent}/{uuid.uuid4()}"
        with scheduler.bot_notifier.subscription(request.bot_session.name) as event:
            scheduler.add_bot_entry(
                bot_name=request.bot_session.name,
                bot_session_id=request.bot_session.bot_id,
                bot_session_status=request.bot_session.status,
                bot_property_labels=labels,
                bot_capability_hashes=capabilities,
                bot_capacity=capacity,
                instance_name=request.parent,
            )

            LOGGER.info("Created new BotSession. Requesting leases.", tags=bot_log_tags(request.bot_session))
            self._request_leases(
                request.bot_session,
                CancellationContext(context),
                event,
                scheduler,
                deadline=context.time_remaining(),
                capacity=capacity,
            )
        self._assign_deadline_for_botsession(request.bot_session, scheduler)

        LOGGER.debug("Completed CreateBotSession.", tags=bot_log_tags(request.bot_session))
        return request.bot_session

    @rpc(instance_getter=lambda r: _get_bot_name_parent_part(r.name))
    def UpdateBotSession(self, request: UpdateBotSessionRequest, context: grpc.ServicerContext) -> BotSession:
        if request.name != request.bot_session.name:
            raise InvalidArgumentError(
                "Name in UpdateBotSessionRequest does not match BotSession. "
                f" UpdateBotSessionRequest.name=[{request.name}] BotSession.name=[{request.bot_session.name}]"
            )

        # Strip out the Partial Execution Metadata and format into a dict of [leaseID, partialExecutionMetadata]
        # The metadata header should be in the format "partial-execution-metadata-<lease_id>-bin"
        all_metadata_entries = context.invocation_metadata()
        lease_id_to_partial_execution_metadata: dict[str, ExecutedActionMetadata] = {}
        for entry in all_metadata_entries:
            if entry.key.startswith("partial-execution-metadata-"):  # type: ignore [attr-defined]
                execution_metadata = ExecutedActionMetadata()
                execution_metadata.ParseFromString(entry.value)  # type: ignore [attr-defined]
                lease_id = entry.key[len("partial-execution-metadata-") : -len("-bin")]  # type: ignore
                lease_id_to_partial_execution_metadata[lease_id] = execution_metadata

        LOGGER.debug("Beginning initial lease synchronization.", tags=bot_log_tags(request.bot_session))

        orig_leases_count = len(request.bot_session.leases)
        scheduler = self.current_instance.scheduler
        with scheduler.bot_notifier.subscription(request.bot_session.name) as event:
            capacity = get_bot_capacity(request.bot_session)
            leases = scheduler.synchronize_bot_leases(
                request.bot_session.name,
                request.bot_session.bot_id,
                request.bot_session.status,
                request.bot_session.leases,
                lease_id_to_partial_execution_metadata,
                max_capacity=capacity,
            )
            del request.bot_session.leases[:]
            request.bot_session.leases.extend(leases)

            LOGGER.debug("Completed initial lease synchronization.", tags=bot_log_tags(request.bot_session))

            capabilities = list(map(hash_from_dict, scheduler.property_set.worker_properties(request.bot_session)))
            scheduler.maybe_update_bot_platforms(request.bot_session.name, capabilities)

            # Only block on lease assignment if we aren't currently working on anything, to avoid
            # the client needing to deal with interrupting this wait when a current job is
            # completed. Any extra assignments can be picked up when we next synchronize.
            #
            # This should also be skipped if we've removed a lease from the session, to mitigate
            # situations where the scheduler is updated with the new state of a lease, but a fault
            # thereafter causes the worker to retry the old UpdateBotSession call.
            if not leases and not orig_leases_count:
                self._request_leases(
                    request.bot_session,
                    CancellationContext(context),
                    event,
                    scheduler,
                    deadline=context.time_remaining(),
                    capacity=capacity,
                )

        metadata = scheduler.get_metadata_for_leases(
            request.bot_session.leases, only_current_instance=_get_bot_name_parent_part(request.name) != "*"
        )
        self._assign_deadline_for_botsession(request.bot_session, scheduler)

        LOGGER.debug("Completed UpdateBotSession.", tags=bot_log_tags(request.bot_session))
        context.set_trailing_metadata(metadata)  # type: ignore[arg-type]  # tricky covariance issue.

        return request.bot_session

    @rpc(instance_getter=lambda r: _get_bot_name_parent_part(r.name))
    def PostBotEventTemp(self, request: PostBotEventTempRequest, context: grpc.ServicerContext) -> empty_pb2.Empty:
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        return empty_pb2.Empty()

    def query_connected_bots_for_instance(self, instance_name: str) -> int:
        if instance := self.instances.get(instance_name):
            return instance.scheduler.bot_notifier.listener_count_for_instance(instance_name)
        return 0

    def get_bot_status_metrics(self, instance_name: str) -> BotMetrics:
        if instance := self.instances.get(instance_name):
            return instance.scheduler.get_bot_status_metrics()
        return {
            "bots_total": {},
            "bots_per_property_label": {},
            "available_capacity_total": {},
            "available_capacity_per_property_label": {},
        }

    def _assign_deadline_for_botsession(self, bot_session: BotSession, scheduler: Scheduler) -> None:
        bot_session.expire_time.FromDatetime(scheduler.refresh_bot_expiry_time(bot_session.name, bot_session.bot_id))

    def _request_leases(
        self,
        bot_session: BotSession,
        context: CancellationContext,
        event: Event,
        scheduler: Scheduler,
        deadline: float | None = None,
        capacity: int = 1,
    ) -> None:
        # We do not assign new leases if we are not in the OK state.
        if bot_session.status != BotStatus.OK.value:
            LOGGER.debug("BotSession not healthy. Skipping lease request.", tags=bot_log_tags(bot_session))
            return

        # Skip waiting for new leases if we're at capacity
        if len(bot_session.leases) == capacity:
            LOGGER.debug(
                "BotSession already assigned to capacity. Skipping lease request.",
                tags=bot_log_tags(bot_session),
            )
            return

        # If no deadline is set default to the max we allow workers to long-poll for work
        if deadline is None:
            deadline = MAX_WORKER_TTL

        # If the specified bot session keepalive timeout is greater than the
        # deadline it can result in active bot sessions being reaped
        deadline = min(deadline, scheduler.bot_session_keepalive_timeout)

        # Use 80% of the given deadline to give time to respond but no less than NETWORK_TIMEOUT
        ttl = deadline * 0.8
        if ttl < NETWORK_TIMEOUT:
            LOGGER.info(
                "BotSession expires in less time than timeout. No leases will be assigned.",
                tags={**bot_log_tags(bot_session), "network_timeout": NETWORK_TIMEOUT},
            )
            return

        # refresh the bot session expiry time as `_request_leases` may wait for a while
        self._assign_deadline_for_botsession(bot_session, scheduler)

        # Wait for an update to the bot session and then resynchronize the lease.
        LOGGER.debug("Waiting for job assignment.", tags={**bot_log_tags(bot_session), "deadline": deadline})
        context.on_cancel(event.set)
        event.wait(ttl)

        # This is a best-effort check the see if the original request is still alive. Depending on
        # network and proxy configurations, this status may not accurately reflect the state of the
        # client connection. If we know for certain that the request is no longer being monitored,
        # we can exit now to avoid state changes not being acked by the bot.
        if context.is_cancelled():
            LOGGER.debug("Bot request cancelled. Skipping lease synchronization.", tags=bot_log_tags(bot_session))
            return

        # In the case that we had a timeout, we can return without post lease synchronization. This
        # helps deal with the case of uncommunicated cancellations from the bot request. If the bot
        # is actually still waiting on work, this will be immediately followed up by a new request
        # from the worker, where the initial synchronization will begin a bot ack for the pending
        # job. In the case that the request has been abandoned, it avoids competing updates to the
        # database records in the corresponding bots session.
        if not event.is_set():
            LOGGER.debug("Bot assignment timeout. Skipping lease synchronization.", tags=bot_log_tags(bot_session))
            return

        # Synchronize the lease again to pick up db changes.
        LOGGER.debug("Synchronizing leases after job assignment wait.", tags=bot_log_tags(bot_session))
        if leases := scheduler.synchronize_bot_leases(
            bot_session.name, bot_session.bot_id, bot_session.status, bot_session.leases, max_capacity=capacity
        ):
            del bot_session.leases[:]
            bot_session.leases.extend(leases)
