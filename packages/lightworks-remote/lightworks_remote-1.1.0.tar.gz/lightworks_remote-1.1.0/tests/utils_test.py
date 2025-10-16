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

import json
import os

import numpy as np
import pytest
from lightworks import (
    PhotonicCircuit,
    Sampler,
    State,
    random_unitary,
)

from lightworks_remote.payloads import Payload
from lightworks_remote.remote.sampler_compiler import SamplerCompiler
from lightworks_remote.utils.file_management import (
    get_data_from_json,
    validate_json_filename,
    write_data_to_json,
)
from lightworks_remote.utils.serialization import serialize


class TestSerialize:
    """
    Unit tests for the serialization functionality of the remote module.
    """

    def test_payload(self):
        """
        Checks that a generated payload can be serialized.
        """
        task = Sampler(PhotonicCircuit(4), State([1, 0, 1, 0]), 10000)
        compiler = SamplerCompiler(task._generate_task())
        payload = Payload(**compiler._generate_payload())

        serialize(payload)

    def test_payload_to_json(self):
        """
        Checks that a generated payload can be serialized and then saved to a
        json file.
        """
        task = Sampler(PhotonicCircuit(4), State([1, 0, 1, 0]), 10000)
        compiler = SamplerCompiler(task._generate_task())
        payload = Payload(**compiler._generate_payload())
        payload = serialize(payload)
        with open("test_payload_dump.json", "w") as f:  # noqa: PLW1514
            json.dump(payload, f)
        os.remove("test_payload_dump.json")

    @pytest.mark.parametrize("value", [1, 1.1, "Test", True, [1, 2.4]])
    def test_serialize_unmodified(self, value):
        """
        Checks serialization does nothing for certain types.
        """
        assert serialize(value) == value

    def test_serialize_complex(self):
        """
        Checks serialization of complex number converts it to a string.
        """
        number = 1.9 + 0.5j
        converted = serialize(number)
        assert isinstance(converted, str)
        assert str(number.real) in converted
        assert str(number.imag) in converted

    def test_serialize_state(self):
        """
        Checks that a provided state is converted to a list by the serialize
        method.
        """
        state = serialize(State([1, 0, 1, 0]))
        assert isinstance(state, list)

    def test_serialize_list(self):
        """
        Checks serialization on a list of values will serialize all of the
        values.
        """
        converted = serialize([1.1, State([1, 2, 3, 4]), 1 + 0.5j])
        assert converted == [1.1, [1, 2, 3, 4], serialize(1 + 0.5j)]

    def test_serialize_array(self):
        """
        Checks serialization converts a numpy array into a list.
        """
        array = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        converted = serialize(array)
        assert isinstance(converted, list)
        assert converted == array.tolist()

    def test_serialize_complex_array(self):
        """
        Checks serialization of complex array converts it into a list with
        string values.
        """
        array = random_unitary(3)
        converted = serialize(array)
        assert isinstance(converted, list)
        assert isinstance(converted[0][0], str)
        assert converted == array.astype(str).tolist()

    def test_serialize_dict(self):
        """
        Checks serialization of dictionary operates on the keys/values.
        """
        d = {State([1, 0, 1, 0]): 1 + 0.5j, "test": random_unitary(3)}
        converted = serialize(d)
        assert "[1, 0, 1, 0]" in converted
        assert converted["[1, 0, 1, 0]"] == serialize(1 + 0.5j)
        assert "test" in converted
        assert isinstance(converted["test"], list)

    def test_serialize_dict_nested(self):
        """
        Checks serialization of dictionary operates on the keys/values when
        a dictionary is one of the values..
        """
        d = {
            State([1, 0, 1, 0]): 1 + 0.5j,
            "test": {State([1, 0, 1, 0]): 1 + 0.5j, "test": random_unitary(3)},
        }
        converted = serialize(d)
        assert "[1, 0, 1, 0]" in converted
        assert converted["[1, 0, 1, 0]"] == serialize(1 + 0.5j)
        assert "[1, 0, 1, 0]" in converted["test"]
        assert isinstance(converted["test"]["test"], list)


class TestFileManagement:
    """
    Unit tests for file_management.py section of utils.
    """

    @pytest.mark.parametrize("value", [["test"], True, 1])
    def test_validate_file_name(self, value):
        """
        Checks that validate file name raises an exception if a non-string value
        is provided.
        """
        with pytest.raises(TypeError):
            validate_json_filename(value)

    def test_validate_file_name_adds_json(self):
        """
        Checks that validate file name adds the json extension if this is not
        included.
        """
        filename = str(validate_json_filename("test"))
        assert filename.endswith(".json")

    def test_validate_file_name_json_included(self):
        """
        Checks that validate file name doesn't add the json extension if this is
        already included.
        """
        filename = str(validate_json_filename("test.json"))
        assert filename.endswith(".json")
        assert not filename.endswith(".json.json")

    def test_write_data(self):
        """
        Checks that write data is able to write a dictionary to a json file.
        """
        data = {"test": [1, 2, 3], "test2": [4, 5, 6]}
        write_data_to_json(data, "_test_data.json")
        assert os.path.isfile("_test_data.json")
        os.remove("_test_data.json")

    def test_write_data_no_json(self):
        """
        Checks that write data is able to write a dictionary to a json file when
        the extension is not provided.
        """
        data = {"test": [1, 2, 3], "test2": [4, 5, 6]}
        write_data_to_json(data, "_test_data")
        assert os.path.isfile("_test_data.json")
        os.remove("_test_data.json")

    def test_write_data_path(self):
        """
        Checks that write data is able to write a dictionary to a json file
        when a path is included.
        """
        data = {"test": [1, 2, 3], "test2": [4, 5, 6]}
        write_data_to_json(data, ".pytest_cache/_test_data.json")
        assert os.path.isfile(".pytest_cache/_test_data.json")
        os.remove(".pytest_cache/_test_data.json")

    def test_write_data_non_serialized(self):
        """
        Checks that write data is able to serialize a dictionary and save to a
        json file.
        """
        data = {"test": State([1, 2, 3]), "array": random_unitary(6)}
        write_data_to_json(data, "_test_data.json")
        assert os.path.isfile("_test_data.json")
        os.remove("_test_data.json")

    def test_get_data(self):
        """
        Checks that get data is able to recover a dictionary from a created json
        file.
        """
        data = {"test3": [1, 2, 3], "test4": [4, 5, 6]}
        with open("_test_data.json", "w", encoding="locale") as f:
            json.dump(data, f, indent=4)
        recovered = get_data_from_json("_test_data.json")
        assert recovered == data
        os.remove("_test_data.json")

    def test_get_data_no_json(self):
        """
        Checks that get data is able to recover a dictionary from a created json
        file when the file extension is not provided
        """
        data = {"test3": [1, 2, 3], "test4": [4, 5, 6]}
        with open("_test_data.json", "w", encoding="locale") as f:
            json.dump(data, f, indent=4)
        recovered = get_data_from_json("_test_data")
        assert recovered == data
        os.remove("_test_data.json")

    def test_get_data_path(self):
        """
        Checks that get data is able to recover a dictionary from a created json
        file within a sub-directory.
        """
        data = {"test3": [1, 2, 3], "test4": [4, 5, 6]}
        with open(".pytest_cache/_test_data.json", "w", encoding="locale") as f:
            json.dump(data, f, indent=4)
        recovered = get_data_from_json(".pytest_cache/_test_data.json")
        assert recovered == data
        os.remove(".pytest_cache/_test_data.json")
