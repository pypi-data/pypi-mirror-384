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

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any

import numpy as np
from lightworks import State
from numpy.typing import NDArray


class Payload:
    """Generic Payload which allows for any fields to be specified as kwargs."""

    def __init__(self, **kwargs: Any) -> None:
        self.__all_attrs = []
        for k, v in kwargs.items():
            setattr(self, k, v)
            self.__all_attrs.append(k)

    def __str__(self) -> str:
        """String representation of payload."""
        data = [
            f"{k}={getattr(self, k)}"
            if not isinstance(k, str)
            else f"{k}='{getattr(self, k)}'"
            for k in self.__all_attrs
        ]
        joined_data = ", ".join(data)
        return f"Payload({joined_data})"

    def __repr__(self) -> str:
        """Representation of payload."""
        return str(self)

    @property
    def payload(self) -> dict[str, Any]:
        """Returns created payload for the Artemis system."""
        if is_dataclass(self):
            return asdict(self)
        return {k: getattr(self, k) for k in self.__all_attrs}


@dataclass(kw_only=True)
class ArtemisPayload(Payload):
    """
    Stores details of payload for Artemis.
    """

    qpu: str
    job_name: str
    lightworks_version: str
    n_modes: int
    input: State | list[int]
    n_samples: int
    min_detection: int
    direct_implementation: bool
    unitary: NDArray[np.complex128]
    circuit_spec: list[Any] | None = None
    job_data: dict[str, Any] | None = None
