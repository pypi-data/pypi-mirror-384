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

from typing import Any

import pandas as pd

from lightworks_remote.http import ArtemisHTTPInterface, JobDetails
from lightworks_remote.results import QPUSamplingResult
from lightworks_remote.utils import get_data_from_json

from .batch_job import BatchJob
from .job import Job


def cancel_job(job_id: int | str) -> None:
    """
    Cancels job with matching id, raising an error if a matching job is not
    found.
    """
    api = ArtemisHTTPInterface()
    return api.cancel_job(job_id)


def list_scheduled_jobs() -> list[int]:
    """
    List all jobs awaiting execution on hardware.
    """
    api = ArtemisHTTPInterface()
    return api.list_scheduled_job_ids()


def list_all_jobs() -> list[int]:
    """
    List all jobs submitted by a user.
    """
    api = ArtemisHTTPInterface()
    return api.list_all_job_ids()


def get_job_status(job_id: int | str) -> str:
    """
    Gets status of job with a matching id.
    """
    api = ArtemisHTTPInterface()
    return api.get_job_status(job_id).value


def get_job_details(job_id: int | str) -> JobDetails:
    """
    Returns all details about the requested job.
    """
    api = ArtemisHTTPInterface()
    return api.get_job_details(job_id)


def check_job_complete(job_id: int | str) -> bool:
    """
    Returns whether or not the requested job is completed.
    """
    api = ArtemisHTTPInterface()
    return api.get_job_status(job_id).is_complete


def get_results(job_id: int | str) -> QPUSamplingResult:
    """
    Retrieves results for the job with matching id.
    """
    api = ArtemisHTTPInterface()
    return api.get_results(job_id)


def show_scheduled() -> pd.DataFrame:
    """
    Creates and returns a dataframe detailing all scheduled jobs and their
    current status.
    """
    # NOTE: Maybe this should only show a maximum number of jobs
    api = ArtemisHTTPInterface()
    scheduled = list_scheduled_jobs()
    all_data = []
    for s in scheduled:
        job_data = api.get_job_details(s)
        # If not scheduled yet then set position to be largest possible value
        position = job_data.queue_position
        position = position if position is not None else 2**31 - 1
        all_data.append([job_data.job_id, job_data.job_status.value, position])
    # Create dataframe and sort
    sch = pd.DataFrame(all_data, columns=["Job ID", "Status", "Queue Position"])
    sch = sch.sort_values(["Queue Position", "Job ID"], ascending=[True, True])
    # Convert queue position into int then str and convert any original none
    # values to waiting
    sch = sch.astype({"Queue Position": int})
    sch = sch.astype({"Queue Position": str})

    return sch.replace({"Queue Position": {str(2**31 - 1): "Waiting"}})


def load_job_from_file(filename: str) -> Job | BatchJob:
    """
    Loads job data from the provided file path.

    Args:

        filename (str) : The name of the data file to load, this can also
            contain a path to load from within a specific directory.

    """
    data = get_data_from_json(filename)
    if "job_type" not in data:
        raise KeyError(
            "Unable to identify job type from file data. json file should "
            "contain the key 'type'."
        )
    job: Any
    if data["job_type"] == "job":
        job = Job()
    elif data["job_type"] == "batch_job":
        job = BatchJob()
    else:
        raise ValueError("Job type from data file not recognised.")
    job.load_from_file(filename)
    return job
