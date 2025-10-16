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

from collections.abc import Sequence
from typing import Any, overload

from lightworks import Batch, Sampler
from lightworks import __version__ as LIGHTWORKS_VERSION  # noqa: N812
from lightworks.sdk.tasks import Task
from multimethod import multimethod
from numpy import inf

from lightworks_remote.http.qpu_details import QPUDetails
from lightworks_remote.payloads import ArtemisPayload, Payload
from lightworks_remote.utils import ValidationError

from .batch_job import BatchJob
from .job import Job
from .sampler_compiler import SamplerCompiler
from .system_management import get_qpu_details


class QPU:
    """
    Defines the target QPU and facilitates execution of a task on that
    particular piece of hardware.

    Args:

        name (str) : The id of the QPU which is to be used.

    """

    def __init__(self, name: str) -> None:
        # Assign name to attribute
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"lightworks_remote.QPU('{self.name}')"

    @property
    def name(self) -> str:
        """Returns the name of the QPU"""
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("QPU name should be a string.")
        self.__name = value

    @property
    def details(self) -> QPUDetails:
        """Returns all details about the selected QPU"""
        return get_qpu_details(self.name)

    @overload
    def __call__(
        self,
        task: Task,
        direct_encoding: bool = ...,
        job_name: str = ...,
        options: dict[str, Any] | None = None,
    ) -> Job: ...

    @overload
    def __call__(
        self,
        task: Batch,
        direct_encoding: bool = ...,
        job_name: str | list[str] = ...,
        options: dict[str, Any] | None = None,
    ) -> BatchJob: ...

    def __call__(
        self,
        task: Task | Batch,
        direct_encoding: bool = False,
        job_name: str | list[str] = "Job",
        options: dict[str, Any] | None = None,
    ) -> Job | BatchJob:
        """Prepare and submit a task to a target QPU backend."""
        return self.run(task, direct_encoding, job_name, options)  # type: ignore[arg-type]

    @overload
    def run(
        self,
        task: Task,
        direct_encoding: bool = ...,
        job_name: str = ...,
        options: dict[str, Any] | None = None,
    ) -> Job: ...

    @overload
    def run(
        self,
        task: Batch,
        direct_encoding: bool = ...,
        job_name: str | list[str] = ...,
        options: dict[str, Any] | None = None,
    ) -> BatchJob: ...

    def run(
        self,
        task: Task | Batch,
        direct_encoding: bool = False,
        job_name: str | list[str] = "Job",
        options: dict[str, Any] | None = None,
    ) -> Job | BatchJob:
        """
        Prepare and submit a task to a target QPU backend.

        Args:

            task (Task | Batch) : The target task to run on the chosen QPU.

            direct_encoding (bool, optional) : Controls whether a circuit is
                compiled into a unitary to be executed or the circuit spec is
                used to better preserve the structure of the circuit.

            job_name (str | list, optional) : Set a name to use as a reference
                for the job. If a batch then this can be a list of names,
                otherwise a number will be appended to the base name for each
                job in the batch. Defaults to job.

            options (dict | None, optional) : Allows additional options to be
                provided within job data. Should only be used by advanced users
                who have been told which options are available.

        Returns:

            Job : Job object which can be used for interacting with the created
                job.

        """
        # Perform initial submission
        job = self.run_async(
            task,  # type: ignore[arg-type]
            direct_encoding=direct_encoding,
            job_name=job_name,  # type: ignore[arg-type]
            options=options,
        )
        # Wait until compilation is complete
        # For single jobs
        if isinstance(job, Job):
            job._check_successful_compilation()
        # For multiple
        else:
            for j in job.jobs:
                j._check_successful_compilation()

        # Then return created job object
        return job

    @overload
    def run_async(
        self,
        task: Task,
        direct_encoding: bool = ...,
        job_name: str = ...,
        options: dict[str, Any] | None = None,
    ) -> Job: ...

    @overload
    def run_async(
        self,
        task: Batch,
        direct_encoding: bool = ...,
        job_name: str | list[str] = ...,
        options: dict[str, Any] | None = None,
    ) -> BatchJob: ...

    def run_async(
        self,
        task: Task | Batch,
        direct_encoding: bool = False,
        job_name: str | list[str] = "Job",
        options: dict[str, Any] | None = None,
    ) -> Job | BatchJob:
        """
        Prepare and submit a task to a target QPU backend without waiting for
        compilation to complete.

        Args:

            task (Task | Batch) : The target task to run on the chosen QPU.

            direct_encoding (bool, optional) : Controls whether a circuit is
                compiled into a unitary to be executed or the circuit spec is
                used to better preserve the structure of the circuit.

            job_name (str | list, optional) : Set a name to use as a reference
                for the job. If a batch then this can be a list of names,
                otherwise a number will be appended to the base name for each
                job in the batch. Defaults to job.

            options (dict | None, optional) : Allows additional options to be
                provided within job data. Should only be used by advanced users
                who have been told which options are available.

        Returns:

            Job : Job object which can be used for interacting with the created
                job.

        """
        # Check task
        if not isinstance(task, Task | Batch):
            raise TypeError("Provided task should be a Task or Batch object.")
        # Check direct encoding is boolean
        if not isinstance(direct_encoding, bool):
            raise TypeError(
                "direct_encoding should be set to either True or False."
            )
        # Download QPU data to be used for validation
        self._qpu_data = get_qpu_details(self.name)
        # Then run task
        return self._run(task, direct_encoding, job_name, options)

    @multimethod
    def _run(
        self,
        task: Task,
        direct_encoding: bool,
        job_name: str,
        options: dict[str, Any] | None = None,
    ) -> Job:
        """
        Generates payload from a single task and submits.
        """
        # Process job name
        job_name = get_job_name(task, job_name)
        # Get payload and add QPU + job name
        payload = self._get_payload(task, direct_encoding, job_name, options)

        # And finally submit job and return
        job = Job(payload)
        job._submit()
        return job

    @_run.register
    def _run_batch(
        self,
        task: Batch,
        direct_encoding: bool,
        job_name: str | list[str],
        options: dict[str, Any] | None = None,
    ) -> BatchJob:
        """
        Generates the payload from a batch of tasks and submits these.
        """
        # Process job name
        job_name = get_job_name(task, job_name)
        # Create batch job and add individuals
        batch_job = BatchJob()
        for i, c in enumerate(task):
            # Get payload and add required additions
            payload = self._get_payload(
                c, direct_encoding, job_name[i], options
            )

            # Store job in batch jobs
            batch_job[payload.job_name] = Job(payload)  # type: ignore[attr-defined]
        # Then submit all
        batch_job._submit_all()
        return batch_job

    def _get_payload(
        self,
        task: Task,
        direct_encoding: bool,
        job_name: str,
        options: dict[str, Any] | None = None,
    ) -> Payload:
        """
        Generates a verifies a payload from a task and then returns this.
        """
        payload = self._build_payload_from_task(
            task, direct_encoding, job_name, options
        )
        # Check payload before returning
        self._verify_payload(payload)
        return payload

    def _build_payload_from_task(
        self,
        task: Task,
        direct_encoding: bool,
        job_name: str,
        options: dict[str, Any] | None = None,
    ) -> ArtemisPayload:
        """
        Creates a payload using data from the provided task.
        """
        if not isinstance(task, Sampler):
            raise ValidationError(
                "Remote QPU only supports execution of Sampler tasks."
            )
        data = task._generate_task()
        compiler = SamplerCompiler(data)
        payload = ArtemisPayload(
            qpu=self.name,
            job_name=job_name,
            lightworks_version=LIGHTWORKS_VERSION,
            **compiler._generate_payload(direct_encoding=direct_encoding),
        )
        # Add additional job data from kwargs
        if options is not None:
            for k, v in options.items():
                if payload.job_data is None:
                    payload.job_data = {}
                payload.job_data[k] = v
        return payload

    def _verify_payload(self, payload: ArtemisPayload) -> None:
        """
        Checks the payload against data from the QPU using a set of validation
        rules.
        """
        # Number of modes
        if payload.n_modes > self._qpu_data.n_modes:
            msg = (
                f"Number of modes required for circuit ({payload.n_modes}) is "
                "larger the number the target QPU "
                f"({self._qpu_data.n_modes})."
            )
            raise ValidationError(msg)
        # Input state
        if sum(payload.input) > self._qpu_data.max_photon_input:
            msg = (
                f"Number of input photons ({sum(payload.input)}) is larger "
                "than the maximum available for the system "
                f"({self._qpu_data.max_photon_input})."
            )
            raise ValidationError(msg)
        # Min photon detection number
        if payload.min_detection > self._qpu_data.max_detection_filter:
            msg = (
                f"Minimum photon detection filter ({payload.min_detection}) is "
                "larger than the max value allowed for the system "
                f"({self._qpu_data.max_detection_filter})."
            )
            raise ValidationError(msg)
        # Number of samples
        allowed_samples = min(
            self._qpu_data.default_max_samples,
            self._qpu_data.max_samples.get(payload.min_detection, inf),
        )
        if payload.n_samples > allowed_samples:
            msg = (
                f"Number of samples ({payload.n_samples:,}) is larger "
                "than the maximum allowed for the set minimum photon detection "
                f"filter ({allowed_samples:,})."
            )
            raise ValidationError(msg)


@overload
def get_job_name(task: Task, name: str) -> str: ...


@overload
def get_job_name(task: Batch, name: str | list[str]) -> list[str]: ...


def get_job_name(task: Task | Batch, name: str | list[str]) -> str | list[str]:
    """
    Processes a provided job names, checking it is of the correct format, and
    returns the value.
    """
    if not isinstance(name, str):
        if isinstance(task, Batch) and isinstance(name, Sequence):
            if len(name) == task.num:
                return list(name)
            msg = (
                "Number of job names should be equal to the number of "
                f"tasks ({task.num})."
            )
            raise ValueError(msg)
        if isinstance(task, Batch):
            raise TypeError("Job name should be a string or list of strings.")
        raise TypeError("Job name should be a string.")
    if isinstance(task, Batch):
        return [name + f"_{i + 1}" for i in range(task.num)]
    return name
