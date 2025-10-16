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

import time
from pathlib import Path
from typing import Any

from lightworks import State

from lightworks_remote.results import QPUSamplingResult
from lightworks_remote.token import token
from lightworks_remote.utils import (
    HTTPError,
    JobError,
    JobNotFoundError,
    JobSubmissionError,
    ResultsError,
    get_persistent_file_data_location,
)
from lightworks_remote.utils.configuration import URL

from .artemis_job_details import (
    ARTEMIS_JOB_DETAILS_MAP,
    ArtemisJobDetails,
    get_no_results_reason,
)
from .artemis_qpu_details import ARTEMIS_QPU_DETAILS_MAP, ArtemisQPU
from .interface import HTTPInterface
from .status import Status


class ArtemisHTTPInterface(HTTPInterface):
    """
    Handles all communication with Artemis cloud interface.
    """

    def __init__(self) -> None:
        certificate = self._get_certificate()
        super().__init__(URL, certificate)

    def submit_job(self, payload: dict[str, Any]) -> int:
        """
        Submits the provided payload dictionary to the configured url and
        returns the job id if accepted.

        Args:

            payload (dict) : Serializable dictionary for submission to the url.

        Returns:

            int : The created job id.

        """
        response = self._post(
            "jobs", headers={"x-access-token": token.get()}, json=payload
        )

        if response.status_code == 202:
            return response.headers["X-Job-Id"]
        if response.status_code == 400:
            r = response.json()
            error_msg = "The following fields failed validation: \n"
            for e in r["errors"]:
                error_msg += f"\t{e['name']} : {e['reason']}. \n"
            raise JobSubmissionError(error_msg)
        raise HTTPError(
            "Something unexpected went wrong while attempting to submit "
            "the job.",
            response=response,
        )

    def get_job_status(self, job_id: int | str) -> Status:
        """
        Returns status of job with the requested id.
        """
        return self.get_job_details(job_id).job_status

    def get_job_queue_position(self, job_id: int | str) -> int | None:
        """
        Returns queue position of the requested job if it has been scheduled,
        otherwise will return None.
        """
        details = self.get_job_details(job_id)
        return details.queue_position

    def get_job_details(self, job_id: int | str) -> ArtemisJobDetails:
        """Gets full set of details for the job with the requested id."""
        response = self._get(
            f"jobs/{job_id}", headers={"x-access-token": token.get()}
        )

        if response.status_code == 200:
            details = ArtemisJobDetails(
                **{
                    ARTEMIS_JOB_DETAILS_MAP[k]: v
                    for k, v in response.json().items()
                }
            )
            # Remove queue position if job not in queue
            if details.job_status != Status.SCHEDULED:
                details.queue_position = None
            return details
        if response.status_code == 404:
            raise JobNotFoundError("Job with requested ID not found.")
        raise HTTPError(
            "Something unexpected went wrong while attempting to retrieve "
            "job details.",
            response=response,
        )

    def check_for_compilation_errors(
        self, job_id: int | str
    ) -> tuple[bool, list[tuple[int, str]]]:
        """
        Checks if any errors may have occurred during the compilation process.
        Note: This doesn't check if compilation has actually taken place so
        should only be called after the compilation.
        """
        details = self.get_job_details(job_id)
        if details.job_status != Status.FAILED:
            return (False, [])
        for log in details.logs:
            if "CompilationErrors" in log["meta"]:
                errors = [
                    (e["Code"], e["Message"])
                    for e in log["meta"]["CompilationErrors"]
                ]
                return (True, errors)
        return (False, [])

    def cancel_job(self, job_id: int | str) -> None:
        """
        Cancels job with matching id, raising an error if a matching job is not
        found.
        """
        # First check if job exists and if it can be cancelled.
        details = self.get_job_details(job_id)
        if details.job_status == Status.CANCELLED:
            msg = (
                f"Job with requested ID ({job_id}) has already been cancelled."
            )
            raise JobError(msg)
        if not details.job_status.is_cancellable:
            msg = (
                f"Job with requested ID ({job_id}) is not in a cancellable "
                "state."
            )
            raise JobError(msg)
        # If passes these checks then try to cancel
        response = self._put(
            f"jobs/{job_id}/cancel", headers={"x-access-token": token.get()}
        )
        if response.status_code == 204:
            return
        raise HTTPError(
            "Something unexpected went wrong while attempting to cancel "
            "the job.",
            response=response,
        )

    def get_results(
        self, job_id: int | str, max_retry: int = 10
    ) -> QPUSamplingResult:
        """
        Retrieves the results for the job with the supplied id.
        """
        # First check job status shows job is complete
        details = self.get_job_details(job_id)
        if not details.job_status.is_complete:
            msg = f"Job with requested ID ({job_id}) is not yet complete."
            raise ResultsError(msg)
        if not details.job_status.has_results:
            reason = get_no_results_reason(details)
            msg = (
                f"Job with requested ID ({job_id}) did not generate any "
                f"results {reason}"
            )
            raise ResultsError(msg)
        # Then attempt to get results
        response = self._get(
            f"jobs/{job_id}/results", headers={"x-access-token": token.get()}
        )
        if response.status_code == 200:
            results = response.json()
            processed_result = {
                key: val
                if key != "results" or val is None
                else {
                    State([int(i) for i in state[1:-1].split(", ")]): counts
                    for state, counts in val.items()
                }
                for key, val in results.items()
            }
            return QPUSamplingResult(processed_result)
        if response.status_code == 400:
            reason = get_no_results_reason(details)
            msg = (
                f"Job with requested ID ({job_id}) did not generate any "
                f"results {reason}"
            )
            raise ResultsError(msg)
        # Sometimes 404 is returned when results are requested too quickly, in
        # this case sleep and retry
        if response.status_code == 404:
            time.sleep(0.5)
            if max_retry > 0:
                return self.get_results(job_id, max_retry=max_retry - 1)
            msg = (
                f"Unable to retrieve results for Job with ID {job_id}, these "
                "may not be available yet."
            )
            raise ResultsError(msg)
        raise HTTPError(
            "Something unexpected went wrong while attempting to get results "
            "for the job.",
            response=response,
        )

    def list_all_job_ids(self) -> list[int]:
        """
        List all jobs submitted to the system.
        """
        response = self._get(
            "jobs",
            headers={"x-access-token": token.get()},
            params={"pageSize": 2**31 - 1},
        )
        return sorted(
            [data["id"] for data in response.json()["items"]], reverse=True
        )

    def list_scheduled_job_ids(self) -> list[int]:
        """
        Lists all jobs awaiting execution on the system.
        """
        response = self._get(
            "jobs",
            headers={"x-access-token": token.get()},
            params={
                "pageSize": 2**31 - 1,
                "statuses": ["Accepted", "Scheduled"],
            },
        )
        return sorted([data["id"] for data in response.json()["items"]])

    def list_all_job_details(self) -> list[dict[str, Any]]:
        """
        Returns details of all jobs submitted to system.
        """
        response = self._get(
            "jobs",
            headers={"x-access-token": token.get()},
            params={"pageSize": 2**31 - 1},
        )
        return response.json()["items"]

    def get_all_qpus(self) -> dict[str, dict[str, Any]]:
        """
        Returns details of all QPUs, such as names, ids and status.
        """
        response = self._get("qpus", headers={"x-access-token": token.get()})
        data = response.json()
        all_qpus = {}
        for qpu in data:
            name = qpu["name"]
            del qpu["name"]
            all_qpus[name] = qpu
        return all_qpus

    def list_qpus(self) -> list[str]:
        """
        Returns a list of all accessible QPUs.
        """
        return list(self.get_all_qpus().keys())

    def get_qpu_details(self, name: str) -> ArtemisQPU:
        """
        Returns all details for a particular QPU>
        """
        all_qpus = self.get_all_qpus()
        if name not in all_qpus:
            raise ValueError("QPU with provided name not found.")
        id_ = all_qpus[name]["id"]
        response = self._get(
            f"Qpus/{id_}", headers={"x-access-token": token.get()}
        )
        details = response.json()
        details["maxSamples"] = {
            items["item1"]: items["item2"] for items in details["maxSamples"]
        }
        return ArtemisQPU(
            **{ARTEMIS_QPU_DETAILS_MAP[k]: v for k, v in details.items()}
        )

    def _test_connection(self) -> None:
        """Checks that a connection can be established with the API."""
        self._get_no_catch("jobs")

    def _get_certificate(self) -> Path:
        """
        Used for recovering the certificate required to communicate with the
        remote client. If not found it instructs the user where this should be
        placed.
        """
        # Get persistent data path
        path = get_persistent_file_data_location()
        # Then try to find certificate
        full_path = path / "certificate.pem"
        if not full_path.exists():
            msg = (
                "certificate.pem file not found, this can be added with the "
                "install_certificate method or manually placed in "
                f"the following directory: '{path}'."
            )
            raise FileNotFoundError(msg)
        return full_path
