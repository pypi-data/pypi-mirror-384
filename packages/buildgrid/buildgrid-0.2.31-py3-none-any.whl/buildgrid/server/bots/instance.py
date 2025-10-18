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

from contextlib import ExitStack

from buildgrid._protos.google.devtools.remoteworkers.v1test2.bots_pb2 import DESCRIPTOR as BOTS_DESCRIPTOR
from buildgrid.server.logging import buildgrid_logger
from buildgrid.server.scheduler import Scheduler
from buildgrid.server.servicer import Instance

LOGGER = buildgrid_logger(__name__)


class BotsInterface(Instance):
    SERVICE_NAME = BOTS_DESCRIPTOR.services_by_name["Bots"].full_name

    def __init__(self, scheduler: Scheduler) -> None:
        self._stack = ExitStack()
        self.scheduler = scheduler

    def start(self) -> None:
        self._stack.enter_context(self.scheduler)
        self._stack.enter_context(self.scheduler.bot_notifier)
        if self.scheduler.session_expiry_interval > 0:
            self._stack.enter_context(self.scheduler.session_expiry_timer)

    def stop(self) -> None:
        self._stack.close()
        LOGGER.info("Stopped Bots.")
