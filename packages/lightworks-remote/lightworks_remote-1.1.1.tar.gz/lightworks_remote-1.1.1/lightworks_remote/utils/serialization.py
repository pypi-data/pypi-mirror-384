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

import numpy as np
from lightworks import State
from multimethod import multimethod

from lightworks_remote.payloads import Payload


@multimethod
def serialize(value: Any) -> Any:
    """
    Defines the default serialization behaviour in which the value is just
    returned without modification.
    """
    return value


@serialize.register
def serialize_payload(payload: Payload) -> dict[str, Any]:
    """
    Performs serialization of a dictionary to ensure it is compatible with
    submission via HTTP protocol.
    """
    return serialize(payload.payload)


@serialize.register
def serialize_complex(value: complex) -> str:
    """
    Converts a complex number into a string.
    """
    return str(value)


@serialize.register
def serialize_state(state: State) -> list[int]:
    """
    Retrieves the list representation of a State.
    """
    return list(state.s)


@serialize.register
def serialize_numpy_array(array: np.ndarray[Any, Any]) -> list[Any]:
    """
    Converts a numpy array into a list, casting the values to strings if the
    data type is complex.
    """
    if "complex" in str(array.dtype):
        array = array.astype(str)
    return array.tolist()


@serialize.register
def serialize_list(value: list[Any]) -> list[Any]:
    """
    Performs serialization of all values within a list.
    """
    for i, v in enumerate(value):
        value[i] = serialize(v)
    return value


@serialize.register
def serialize_dict(value: dict[Any, Any]) -> dict[str, Any]:
    """
    Performs serialization of all values within a dictionary.
    """
    return {str(serialize(k)): serialize(v) for k, v in value.items()}
