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

"""
Will interact with Artemis system through HTTP protocol
"""

import time
from typing import Any

from lightworks_remote.http import ArtemisHTTPInterface, JobDetails, Status
from lightworks_remote.payloads import Payload
from lightworks_remote.results import QPUSamplingResult
from lightworks_remote.utils import (
    JobError,
    JobSubmissionError,
    get_data_from_json,
    saved_job_exists,
    write_data_to_json,
)
from lightworks_remote.utils.serialization import serialize


class Job:
    """
    Stores details of a submitted job, can be used to recover status info and
    then results once computation is complete.

    Args:

        payload (dict) : The payload which defines the required configuration
            for the job.

    """

    def __init__(self, payload: Payload | None = None) -> None:
        self._payload = payload
        self._interface = ArtemisHTTPInterface()

    def __str__(self) -> str:
        id_ = self._job_id if hasattr(self, "_job_id") else None
        return f"Job(id = {id_})"

    def __repr__(self) -> str:
        return "lightworks_remote." + str(self)

    @property
    def job_id(self) -> int:
        """Returns the id of the job."""
        if not hasattr(self, "_job_id"):
            return None  # type: ignore[return-value]
        return self._job_id

    @property
    def status(self) -> Status:
        """Returns the status of the job."""
        return self._interface.get_job_status(self.job_id)

    @property
    def complete(self) -> bool:
        """
        Returns whether or not a job has completed. This does not mean it was
        successful however, and could have failed or been cancelled.
        """
        return self.status.is_complete

    @property
    def success(self) -> bool:
        """
        Confirms a job was completed successfully.
        """
        return self.status == Status.COMPLETED

    @property
    def queue_position(self) -> int | None:
        """
        Returns the queue position of the job if it has one, otherwise returns
        None.
        """
        return self._interface.get_job_queue_position(self.job_id)

    @property
    def payload(self) -> Payload | None:
        """Returns the payload used to create the job."""
        return self._payload

    @property
    def details(self) -> JobDetails:
        """Returns the id of the job."""
        return self._interface.get_job_details(self.job_id)

    def _submit(self) -> None:
        """
        Submits the configured job to the web interface. This will re-submit
        the job and replace the id if this has already been submitted.
        """
        if self.payload is None:
            raise JobSubmissionError("No payload provided to job.")
        serialized = serialize(self.payload)
        self._job_id = self._interface.submit_job(serialized)

    def cancel(self) -> None:
        """Cancels the current job."""
        return self._interface.cancel_job(self.job_id)

    def retry(self) -> None:
        """Resubmits the job."""
        return self._submit()

    def wait_until_complete(self) -> None:
        """Pauses Python execution until the job is complete."""
        while not self.complete:
            time.sleep(0.5)

    def get_result(self) -> QPUSamplingResult:
        """
        Gets the result of a job..
        """
        return self._interface.get_results(self.job_id)

    def save_to_file(
        self, filename: str, allow_overwrite: bool = False
    ) -> None:
        """
        Saves the job id and payload to a file so that this can be restored at a
        later date.

        Args:

            filename (str) : The name to use for saving the job data, this can
                also contain a path to save it within a specific directory.

            allow_overwrite (bool) : Controls whether an exists saved job while
                be overwritten. Defaults to False.

        """
        if saved_job_exists(filename) and not allow_overwrite:
            raise ValueError(
                "A saved job with this name already exists. Either use a "
                "different name or set allow_overwrite to True to allow "
                "replacement."
            )
        write_data_to_json(self._get_job_data(), filename)

    def load_from_file(self, filename: str) -> None:
        """
        Loads job data from the provided file path.

        Args:

            filename (str) : The name of the data file to load, this can also
                contain a path to load from within a specific directory.

        """
        data = get_data_from_json(filename)

        try:
            self._job_id = data["job_id"]
            payload = data["payload"]
        except KeyError as e:
            raise JobError(
                "Unable to locate required job data within file."
            ) from e
        self._payload = Payload(**payload) if payload else None

    def _get_job_data(self) -> dict[str, Any]:
        """
        Returns a dictionary containing all data related to a job.
        """
        return {
            "job_type": "job",
            "job_id": self.job_id,
            "payload": self.payload,
        }

    def _check_successful_compilation(self) -> None:
        """
        Waits until compilation has completed and then checks for success.
        """
        # Wait until compiled
        while self.status in {Status.ACCEPTED, Status.COMPILING}:
            pass
        # Then check for any errors
        failed, errors = self._interface.check_for_compilation_errors(
            self.job_id
        )
        if failed:
            error_msg = (
                "The following errors occurred during the compilation process "
                f"for the job {self.job_id}: \n"
            )
            error_msg += "\tCode \tMessage \n"
            for e in errors:
                error_msg += f"\t{e[0]} \t{e[1]} \n"
            raise JobSubmissionError(error_msg)
