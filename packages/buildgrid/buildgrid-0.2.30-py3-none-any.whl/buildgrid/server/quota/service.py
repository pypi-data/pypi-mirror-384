# Copyright (C) 2025 Bloomberg LP
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


from grpc import ServicerContext

from buildgrid._protos.build.buildgrid.quota_pb2 import DESCRIPTOR as QUOTA_DESCRIPTOR
from buildgrid._protos.build.buildgrid.quota_pb2 import (
    DeleteInstanceQuotaRequest,
    DeleteInstanceQuotaResponse,
    GetInstanceQuotaRequest,
    GetInstanceQuotaResponse,
    PutInstanceQuotaRequest,
    PutInstanceQuotaResponse,
)
from buildgrid._protos.build.buildgrid.quota_pb2_grpc import QuotaServicer, add_QuotaServicer_to_server
from buildgrid.server.decorators import rpc
from buildgrid.server.exceptions import NotFoundError
from buildgrid.server.logging import buildgrid_logger
from buildgrid.server.scheduler.impl import Scheduler
from buildgrid.server.servicer import UninstancedServicer

LOGGER = buildgrid_logger(__name__)


class QuotaService(QuotaServicer, UninstancedServicer):
    SERVICE_NAME = "Quota"
    REGISTER_METHOD = add_QuotaServicer_to_server
    FULL_NAME = QUOTA_DESCRIPTOR.services_by_name[SERVICE_NAME].full_name

    def __init__(self, scheduler: Scheduler):
        super().__init__()
        self._scheduler = scheduler

    def start(self) -> None:
        self._stack.enter_context(self._scheduler)

    @rpc(instance_getter=lambda r: r.instance_name)
    def GetInstanceQuota(self, request: GetInstanceQuotaRequest, context: ServicerContext) -> GetInstanceQuotaResponse:
        quota = self._scheduler.get_instance_quota(instance_name=request.instance_name, bot_cohort=request.bot_cohort)
        if quota is None:
            raise NotFoundError(
                f"Instance quota not found. instance={request.instance_name} bot_cohort={request.bot_cohort}"
            )
        LOGGER.debug(
            "Got instance quota.",
            tags={
                "instance": request.instance_name,
                "bot_cohort": request.bot_cohort,
                "quota": str(quota),
            },
        )

        return GetInstanceQuotaResponse(instance_quota=quota)

    @rpc(instance_getter=lambda r: r.instance_name)
    def PutInstanceQuota(self, request: PutInstanceQuotaRequest, context: ServicerContext) -> PutInstanceQuotaResponse:
        self._scheduler.put_instance_quota(
            instance_name=request.instance_name,
            bot_cohort=request.bot_cohort,
            min_quota=request.min_quota,
            max_quota=request.max_quota,
        )
        LOGGER.info(
            "Put instance quota.",
            tags={
                "instance": request.instance_name,
                "bot_cohort": request.bot_cohort,
                "min_quota": request.min_quota,
                "max_quota": request.max_quota,
            },
        )
        return PutInstanceQuotaResponse()

    @rpc(instance_getter=lambda r: r.instance_name)
    def DeleteInstanceQuota(
        self, request: DeleteInstanceQuotaRequest, context: ServicerContext
    ) -> DeleteInstanceQuotaResponse:
        if self._scheduler.delete_instance_quota(instance_name=request.instance_name, bot_cohort=request.bot_cohort):
            LOGGER.info(
                "Deleted instance quota.", tags={"instance": request.instance_name, "bot_cohort": request.bot_cohort}
            )
            return DeleteInstanceQuotaResponse()
        else:
            raise NotFoundError(
                f"Instance quota not found. instance={request.instance_name} bot_cohort={request.bot_cohort}"
            )
