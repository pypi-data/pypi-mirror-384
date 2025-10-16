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

import contextlib
import os
from random import randint

import pytest
import requests

from lightworks_remote import AuthenticationError, token
from lightworks_remote.remote import BatchJob, Job


class TestJob:
    """
    Unit tests for Job object, which handles submission of payload and
    communication with the system.
    """

    def setup_method(self):
        """
        Creates an example payload which can be used for testing.
        """
        self.test_payload = {
            "qpu": "Test",
            "input": [randint(1, 10) for _ in range(4)],
            "unitary": [[randint(1, 10) for _ in range(4)] for _ in range(4)],
            "post_selection": None,
        }

    def test_creation(self):
        """
        Checks a job can be created.
        """
        Job()

    def test_creation_payload(self):
        """
        Checks a job can be created with a provided test payload.
        """
        Job(self.test_payload)

    def test_payload_assignement(self):
        """
        Checks payload returned by property is the assigned payload on job
        creation.
        """
        j = Job(self.test_payload)
        assert j.payload == self.test_payload

    def test_job_id_before_submission(self):
        """
        Checks job id returns None if this is requested before submission.
        """
        j = Job(self.test_payload)
        assert j.job_id is None

    def test_job_submission(self):
        """
        Checks that the submission code is working up to the point at which it
        fails because of a connection or authentication error.
        """
        j = Job(self.test_payload)
        token.set("1234")
        with contextlib.suppress(requests.ConnectionError, AuthenticationError):
            j._submit()

    def test_job_save(self):
        """
        Checks that a job can be saved to a file when values are null.
        """
        j = Job()
        j.save_to_file("_test_data")
        assert os.path.isfile("_test_data.json")
        os.remove("_test_data.json")

    def test_job_save_overwrite(self):
        """
        Checks that a job is protected from being overwritten unless this is
        allowed.
        """
        j = Job()
        j.save_to_file("_test_data")
        assert os.path.isfile("_test_data.json")
        # Check with overwrite off
        with pytest.raises(ValueError):
            j.save_to_file("_test_data")
        # And then allow this
        j.save_to_file("_test_data", allow_overwrite=True)
        os.remove("_test_data.json")

    def test_job_save_with_data(self):
        """
        Checks that a job can be saved to a file when there is a job id and
        payload.
        """
        j = Job(self.test_payload)
        j._job_id = randint(1, 100)
        j.save_to_file("_test_data")
        assert os.path.isfile("_test_data.json")
        os.remove("_test_data.json")

    def test_job_load(self):
        """
        Checks that a job can be loaded from a file and the data is preserved.
        """
        j = Job()
        j.save_to_file("_test_data")
        new_j = Job()
        new_j.load_from_file("_test_data")
        assert new_j.job_id == j.job_id
        assert new_j.payload == j.payload
        os.remove("_test_data.json")

    def test_job_load_with_data(self):
        """
        Checks that a job can be loaded from a file and the data is preserved
        when a payload and job id are assigned.
        """
        j = Job(self.test_payload)
        j._job_id = randint(1, 100)
        j.save_to_file("_test_data")
        new_j = Job()
        new_j.load_from_file("_test_data")
        assert new_j.job_id == j.job_id
        assert new_j.payload.payload == j.payload
        os.remove("_test_data.json")

    def teardown_class(self):
        """
        Deletes _test_data in case this is missed.
        """
        with contextlib.suppress(FileNotFoundError):
            os.remove("_test_data.json")


class TestBatchJob:
    """
    Unit tests for BatchJob object.
    """

    def setup_method(self):
        """
        Creates an example payload and job which can be used for testing.
        """
        self.test_payload = {
            "qpu": "Test",
            "input": [randint(1, 10) for _ in range(4)],
            "unitary": [[randint(1, 10) for _ in range(4)] for _ in range(4)],
            "post_selection": None,
        }
        self.test_job = Job(self.test_payload)

    def test_batch_job_creation(self):
        """
        Checks BatchJob can be created.
        """
        BatchJob()

    def test_batch_job_addition(self):
        """
        Checks that a job can be added to a BatchJob
        """
        BatchJob()._add(self.test_job, "test")

    def test_job_iteration(self):
        """
        Checks that batch job can be iterated through.
        """
        job = BatchJob()
        job._add(self.test_job, "test1")
        job._add(self.test_job, "test2")
        for i, name in enumerate(job):
            assert name == f"test{i + 1}"

    def test_batch_job_jobs_property(self):
        """
        Adds multiple jobs to a BatchJob and confirms the names and job data
        is correctly stored.
        """
        job = BatchJob()
        job._add(self.test_job, "test1")
        job._add(self.test_job, "test2")
        assert len(job.jobs) == 2
        assert "test1" in job
        assert "test2" in job
        assert job["test1"] is self.test_job

    def test_batch_job_save(self):
        """
        Checks that a BatchJob can be saved from a file.
        """
        job = BatchJob()
        job._add(self.test_job, "test1")
        job._add(self.test_job, "test2")
        job.save_to_file("_test_batch_data")
        assert os.path.isfile("_test_batch_data.json")
        os.remove("_test_batch_data.json")

    def test_batch_job_save_overwrite(self):
        """
        Checks that a job is protected from being overwritten unless this is
        allowed.
        """
        job = BatchJob()
        job._add(self.test_job, "test1")
        job._add(self.test_job, "test2")
        job.save_to_file("_test_data")
        assert os.path.isfile("_test_data.json")
        # Check with overwrite off
        with pytest.raises(ValueError):
            job.save_to_file("_test_data")
        # And then allow this
        job.save_to_file("_test_data", allow_overwrite=True)
        os.remove("_test_data.json")

    def test_batch_job_load(self):
        """
        Checks that a BatchJob can be loaded from a file.
        """
        job = BatchJob()
        job._add(self.test_job, "test1")
        job._add(self.test_job, "test2")
        job.save_to_file("_test_batch_data")
        new_job = BatchJob()
        new_job.load_from_file("_test_batch_data")
        assert new_job.keys() == job.keys()
        assert new_job["test1"].payload["input"] == self.test_payload["input"]
        os.remove("_test_batch_data.json")

    def teardown_class(self):
        """
        Deletes _test_batch_data in case this is missed.
        """
        with contextlib.suppress(FileNotFoundError):
            os.remove("_test_batch_data.json")
