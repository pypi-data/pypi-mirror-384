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

import lightworks as lw
import pytest

from lightworks_remote import QPU
from lightworks_remote.payloads import Payload


class TestQPU:
    """
    Unit tests for QPU object.
    """

    def test_qpu_creation(self):
        """
        Checks that a QPU can be successfully created.
        """
        QPU("test")

    @pytest.mark.parametrize("value", [True, 1, ["Test"]])
    def test_invalid_qpu_name(self, value):
        """
        Checks that a QPU name must be a string.
        """
        with pytest.raises(TypeError):
            QPU(value)

    @pytest.mark.parametrize("value", [True, 1, ["Test"]])
    def test_invalid_qpu_name_property(self, value):
        """
        Checks that the QPU name property cannot be overwritten by a non-string
        value.
        """
        q = QPU("test")
        with pytest.raises(TypeError):
            q.name = value

    def test_qpu_name_in_str(self):
        """
        Checks that QPU name in return value when str used on the QPU.
        """
        q = QPU("test")
        assert "test" in str(q)

    def test_qpu_name_in_repr(self):
        """
        Checks that QPU name in return value when repr used on the QPU.
        """
        q = QPU("test")
        assert "test" in repr(q)

    def test_payload_type(self):
        """
        Checks that created payload is always of the correct type.
        """
        task = lw.Sampler(lw.PhotonicCircuit(4), lw.State([1, 0, 1, 0]), 1000)
        qpu = QPU("test")
        assert isinstance(
            qpu._build_payload_from_task(task, False, "test"), Payload
        )

    def test_job_name(self):
        """
        Checks that job name is correctly replicated in the Payload.
        """
        task = lw.Sampler(lw.PhotonicCircuit(4), lw.State([1, 0, 1, 0]), 1000)
        qpu = QPU("test")
        payload = qpu._build_payload_from_task(task, False, "test_1")
        assert payload.job_name == "test_1"

    def test_direct_encoding(self):
        """
        Checks that direct encoding is correctly replicated in the Payload and
        that a circuit spec is also introduced.
        """
        task = lw.Sampler(
            lw.Unitary(lw.random_unitary(4)), lw.State([1, 0, 1, 0]), 1000
        )
        qpu = QPU("test")
        payload = qpu._build_payload_from_task(task, True, "test_1")
        assert payload.direct_implementation
        assert payload.circuit_spec

    def test_job_options(self):
        """
        Checks that options are correctly replicated in the payload job_data.
        """
        task = lw.Sampler(lw.PhotonicCircuit(4), lw.State([1, 0, 1, 0]), 1000)
        qpu = QPU("test")
        options = {"1": "Test", "2": 3}
        payload = qpu._build_payload_from_task(task, False, "test_1", options)
        assert "1" in payload.job_data
        assert "2" in payload.job_data
        assert payload.job_data["1"] == "Test"
        assert payload.job_data["2"] == 3
