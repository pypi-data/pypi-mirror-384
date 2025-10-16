# Copyright 2025 - 2025 Aegiq Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from enum import Enum


class Status(Enum):
    """
    Enumerate all possible job statuses.
    """

    ACCEPTED = "Accepted"
    COMPILING = "Compiling"
    SCHEDULED = "Scheduled"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"
    TIMEDOUT = "Timed Out"

    def __str__(self) -> str:
        """Overwrites str to return value instead of key."""
        return self.value

    @property
    def is_complete(self) -> bool:
        """Returns whether current status can be considered complete."""
        return self in {  # type: ignore [comparison-overlap]
            self.COMPLETED,
            self.FAILED,
            self.CANCELLED,
            self.TIMEDOUT,
        }

    @property
    def is_cancellable(self) -> bool:
        """Returns whether job is cancellable in current status."""
        return self in {  # type: ignore [comparison-overlap]
            self.ACCEPTED,
            self.COMPILING,
            self.SCHEDULED,
            self.RUNNING,
        }

    @property
    def has_results(self) -> bool:
        """Returns if job was able to generate a set of results."""
        return self in {self.COMPLETED, self.TIMEDOUT}  # type: ignore [comparison-overlap]
