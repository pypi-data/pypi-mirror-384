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


from pydantic import BaseModel, ConfigDict


class JobEventModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class JobCreated(JobEventModel):
    pass


class NewOperation(JobEventModel):
    operation_name: str
    total_operation_count: int


class JobAssigned(JobEventModel):
    worker_name: str
    assignment_strategy: str
    time_in_queue: int


class JobCompleted(JobEventModel):
    worker_name: str | None
    status: int
    duration: float | None


class JobOperationCancelled(JobEventModel):
    worker_name: str | None
    operation_name: str
    cancelled_operation_count: int
    total_operation_count: int


class JobCancelled(JobEventModel):
    worker_name: str | None


class JobRetried(JobEventModel):
    attempt_number: int
    max_attempts: int


class JobProgressUpdate(JobEventModel):
    timestamp_name: str
    worker_name: str
