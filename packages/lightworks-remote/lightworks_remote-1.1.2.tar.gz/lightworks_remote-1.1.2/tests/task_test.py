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

import pytest
from lightworks import (
    PhotonicCircuit,
    PostSelection,
    Sampler,
    State,
    Unitary,
    random_unitary,
)

from lightworks_remote.remote.sampler_compiler import SamplerCompiler


class TestSamplerTask:
    """Contains all unit tests relating to the SamplerTask."""

    def setup_method(self):
        """
        Assigns some circuit attribute and resets before each test.
        """
        self.circuit = PhotonicCircuit(6)
        self.input_state = State([1, 0, 0, 1, 0, 0])
        self.n_samples = 10000
        self.min_detection_number = 2
        self.post_selection = None
        self.all_args = {
            "circuit": self.circuit,
            "input_state": self.input_state,
            "n_samples": self.n_samples,
            "min_detection": self.min_detection_number,
            "post_selection": self.post_selection,
        }

    def test_basic_setup(self):
        """
        Sets up a SamplerTask to confirm basic initialisation functionality.
        """
        Sampler(**self.all_args)

    def test_basic_setup_only_req_args(self):
        """
        Sets up a SamplerTask to confirm basic initialisation functionality,
        providing only the required args and allowing others to assume default
        values.
        """
        Sampler(self.circuit, self.input_state, self.n_samples)

    def test_payload_contents(self):
        """
        Checks payload contents does not change.
        """
        task = Sampler(**self.all_args)
        compiler = SamplerCompiler(task._generate_task())
        payload = compiler._generate_payload()

        expected_keys = [
            "n_modes",
            "input",
            "n_samples",
            "min_detection",
            "unitary",
            "direct_implementation",
            "circuit_spec",
        ]
        for k in payload:
            if k not in expected_keys:
                pytest.fail("Unexpected key present in payload.")

    def test_payload_values(self):
        """
        Checks that the values from the payload are the expected values for the
        provided job.
        """
        task = Sampler(**self.all_args)
        compiler = SamplerCompiler(task._generate_task())
        payload = compiler._generate_payload()

        expected_values = {
            "n_modes": 6,
            "input": State([1, 0, 0, 1, 0, 0]),
            "n_samples": 10000,
            "min_detection": 2,
        }
        for k, v in expected_values.items():
            if k not in payload:
                pytest.fail(f"Key {k} not found in payload.")
            else:
                assert payload[k] == v

    def test_heralded_circuit(self):
        """
        Confirms that the correct payload values are generated when heralds are
        included within a circuit.
        """
        sub_circ = PhotonicCircuit(6)
        sub_circ.herald(0, 1)
        sub_circ.herald(5, 1)
        circ = PhotonicCircuit(6)
        circ.add(sub_circ, 1)
        # Generate task and get payload
        task = Sampler(circ, self.input_state, self.n_samples)
        compiler = SamplerCompiler(task._generate_task())
        payload = compiler._generate_payload()
        # Then check against expected values
        expected_values = {
            "n_modes": 8,
            "input": State([1, 1, 0, 0, 1, 0, 1, 0]),
            "n_samples": 10000,
            "min_detection": 4,
        }
        for k, v in expected_values.items():
            if k not in payload:
                pytest.fail(f"Key {k} not found in payload.")
            else:
                assert payload[k] == v

    def test_lossy_circuit(self):
        """
        Checks that attempt to use a lossy circuit will raise an exception.
        """
        circuit = PhotonicCircuit(6)
        circuit.loss(0, 1)
        self.all_args["circuit"] = circuit
        task = Sampler(**self.all_args)
        with pytest.raises(ValueError):
            SamplerCompiler(task._generate_task())

    def test_no_min_detection(self):
        """
        Checks correct default value for min_detection is found in cases where
        this is not specified.
        """
        task = Sampler(self.circuit, self.input_state, self.n_samples)
        compiler = SamplerCompiler(task._generate_task())
        payload = compiler._generate_payload()
        assert payload["min_detection"] == 2

    def test_heralds(self):
        """
        Checks that input state is set correctly when
        """
        circ = Unitary(random_unitary(6))
        circ.herald(1, 1)
        circ.herald(4, 1)
        task = Sampler(circ, State([1, 0, 0, 0]), 10000)
        compiler = SamplerCompiler(task._generate_task())
        payload = compiler._generate_payload()
        assert payload["input"] == State([1, 1, 0, 0, 1, 0])

    def test_no_post_selection(self):
        """
        Checks that if no heralding/post-selection is set then the payload does
        not contain the post-selection field.
        """
        task = Sampler(**self.all_args)
        compiler = SamplerCompiler(task._generate_task())
        payload = compiler._generate_payload()
        assert "post_selection" not in payload

    def test_add_post_selection(self):
        """
        Checks that when post-selection is added with the add_post_selection
        option then this is set over the correct modes.
        """
        p = PostSelection()
        p.add([0, 2], 1)
        self.all_args["post_selection"] = p
        task = Sampler(**self.all_args)
        compiler = SamplerCompiler(task._generate_task())
        payload = compiler._generate_payload()

        assert payload["job_data"]["post_select"][0][0] == (0, 2)

    def test_add_post_selection_and_heralds(self):
        """
        Checks that when post-selection is added with the add_post_selection
        option then this is set over the correct modes.
        """
        circ = Unitary(random_unitary(6))
        circ.herald(1, 1)
        circ.herald(4, 1)

        p = PostSelection()
        p.add([0, 2], 1)

        task = Sampler(circ, State([1, 0, 0, 0]), 10000, post_selection=p)
        compiler = SamplerCompiler(task._generate_task())
        payload = compiler._generate_payload()

        assert payload["job_data"]["post_select"][0][0] == (0, 3)
        assert payload["job_data"]["herald"][0][0] == (1,)
        assert payload["job_data"]["herald"][1][0] == (4,)
