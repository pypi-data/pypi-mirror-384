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

import warnings
from collections import UserDict
from typing import Any

from lightworks_remote.http import Status
from lightworks_remote.results import QPUSamplingResult
from lightworks_remote.utils import (
    JobError,
    ResultsError,
    get_data_from_json,
    saved_job_exists,
    write_data_to_json,
)

from .job import Job


class BatchJob(UserDict[str, Job]):
    """
    Used for managing a batch of submitted jobs. It allows the status and
    results of all jobs contained to retrieved simultaneously.
    """

    def __init__(self) -> None:
        super().__init__()
        self.__results_cache: dict[str, QPUSamplingResult | str] = {}

    @property
    def names(self) -> list[str]:
        """Lists all names of jobs in the batch."""
        return list(self.keys())

    @property
    def jobs(self) -> list[Job]:
        """Returns a list of the created jobs."""
        return list(self.values())

    @property
    def job_id(self) -> dict[str, int]:
        """Returns a dictionary of job names and job ids."""
        return {name: job.job_id for name, job in self.items()}

    @property
    def status(self) -> dict[str, Status]:
        """Returns a dictionary of job names and job statuses."""
        return {name: job.status for name, job in self.items()}

    @property
    def queue_position(self) -> dict[str, int | None]:
        """Returns a dictionary of job names and queue positions."""
        return {name: job.queue_position for name, job in self.items()}

    @property
    def all_complete(self) -> bool:
        """Checks if all jobs are complete."""
        return all(job.complete for job in self.values())

    @property
    def all_success(self) -> bool:
        """Checks all jobs completed successfully."""
        return all(job.success for job in self.values())

    def __str__(self) -> str:
        return f"BatchJob(names = {self.names})"

    def __repr__(self) -> str:
        return "lightworks_remote." + str(self)

    def __getitem__(self, key: str) -> Any:
        if key not in self:
            raise KeyError("Job with matching name not found.")
        return super().__getitem__(key)

    def __setitem__(self, key: str, value: Job) -> None:
        if key in self:
            raise KeyError("Job with provided name already exists.")
        if not isinstance(value, Job):
            raise TypeError("job should be a Job object.")
        if not isinstance(key, str):
            raise TypeError("name should be a string.")
        super().__setitem__(key, value)

    def _add(self, job: Job, name: str) -> None:
        self[name] = job

    def _submit_all(self) -> None:
        """Submits all of the jobs contained within the batch."""
        for job in self.values():
            job._submit()

    def cancel_all(self) -> None:
        """
        Cancels all submitted jobs within a batch.
        """
        for job in self.values():
            if job.complete:
                continue  # Skip any jobs already completed
            try:
                job.cancel()
            except JobError as e:
                print(str(e))  # noqa: T201

    def wait_until_complete(self) -> None:
        """Pauses Python execution until all jobs are completed."""
        # Work through each job until all are finished.
        for job in self.values():
            job.wait_until_complete()

    def get_all_results(self) -> dict[str, QPUSamplingResult | str]:
        """
        Retrieve all results from jobs.
        """
        if not self.all_complete:
            raise ResultsError("Jobs are not all complete yet.")
        for name in self.names:
            self.get_result(name)

        return self.__results_cache

    def get_result(self, name: str) -> QPUSamplingResult | str:
        """
        Retrieve a singular result using the job name as a reference.
        """
        if name not in self.__results_cache or isinstance(
            self.__results_cache[name], str
        ):
            try:
                self.__results_cache[name] = self[name].get_result()
            # If an error is raised then use exception string as result and log
            # an error as well
            except ResultsError as e:
                self.__results_cache[name] = str(e)
                warnings.warn(
                    f"Job '{name}' (id = {self[name].job_id}) did not generate "
                    "any results.",
                    stacklevel=2,
                )

        return self.__results_cache[name]

    def retry_failed(self) -> bool:
        """
        Resubmits any jobs which may have failed.

        Returns:

            bool : Indicates whether any jobs were re-submitted or if all were
                successful.

        """
        job_failed = False
        for name, job in self.items():
            if not job.success:
                job_failed = True
                job.retry()
                self.__results_cache.pop(name, None)
        return job_failed

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
        data: dict[str, Any] = {
            name: job._get_job_data() for name, job in self.items()
        }
        data["job_type"] = "batch_job"

        write_data_to_json(data, filename)

    def load_from_file(self, filename: str) -> None:
        """
        Loads job data from the provided file path.

        Args:

            filename (str) : The name of the data file to load, this can also
                contain a path to load from within a specific directory.

        """
        data = get_data_from_json(filename)

        super().__init__()  # Clear jobs before saving
        try:
            for name, job_data in data.items():
                if name == "job_type":
                    continue
                self[name] = Job()
                self[name]._job_id = job_data["job_id"]
                self[name]._payload = job_data["payload"]
        except KeyError as e:
            raise JobError(
                "Unable to locate required job data within file."
            ) from e
