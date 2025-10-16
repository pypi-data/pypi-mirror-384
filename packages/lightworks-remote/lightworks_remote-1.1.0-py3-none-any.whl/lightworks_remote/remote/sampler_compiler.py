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

from types import NoneType
from typing import Any

from lightworks import PostSelection, State
from lightworks.sdk.tasks import SamplerTask
from lightworks.sdk.utils.heralding import add_heralds_to_state
from lightworks.sdk.utils.post_selection import DefaultPostSelection


class SamplerCompiler:
    """
    Creates and verifies a payload for performing sampling experiments on a
    remote QPU.

    Args:

        data (SamplerTask) : The sampler data to run on the QPU.

    """

    def __init__(self, data: SamplerTask) -> None:
        self.data = self._validate(data)

    def _validate(self, data: SamplerTask) -> SamplerTask:
        # Circuit
        if data.circuit.loss_modes != 0:
            raise ValueError(
                "Circuits to be executed on remote QPU cannot have any loss "
                "elements."
            )
        heralds = data.circuit.heralds
        for d in [heralds.input, heralds.output]:
            if d and max(d.values()) > 1:
                raise ValueError(
                    "Circuit to sampler from cannot have more than 1 heralded "
                    "photons per mode."
                )
        # Input
        for i in data.input_state:
            if i > 1:
                raise ValueError(
                    "Inputs must have a max of 1 photons per mode."
                )
        if sum(data.input_state) < 1:
            raise ValueError("Input state should contain at least one photon.")
        # Min photon detection
        if data.min_detection is not None:
            if data.min_detection < 1:
                raise ValueError(
                    "Minimum photon detection should be at least 1."
                )
            if data.min_detection > sum(data.input_state):
                raise ValueError(
                    "Minimum photon detection cannot be larger than input "
                    "photon number."
                )
        # Post-selection
        if not isinstance(
            data.post_selection, PostSelection | NoneType | DefaultPostSelection
        ):
            raise TypeError(
                "post_selection should be PostSelection object or None. "
                "Post-selection functions are not supported on remote QPUs."
            )
        # Source
        if data.source is not None:
            raise TypeError(
                "Custom source properties are not supported on remote QPUs."
            )
        # Detector
        if data.detector is not None:
            raise TypeError(
                "Custom detector properties are not supported on remote QPUs."
            )
        return data

    @property
    def full_input_state(self) -> State:
        """Returns the full input state including heralded modes."""
        return State(
            add_heralds_to_state(
                self.data.input_state, self.data.circuit.heralds.input
            )
        )

    def _generate_payload(
        self, direct_encoding: bool = False
    ) -> dict[str, Any]:
        """Used to create the payload for submission."""
        # Generate min detection number based on provided value and heralds
        min_detection = (
            sum(self.data.input_state)
            if self.data.min_detection is None
            else self.data.min_detection
        ) + sum(self.data.circuit.heralds.input.values())
        # Get post-selection data
        post_selection = self._get_post_selection()
        # Create dictionary and then return
        payload = {
            "n_modes": self.data.circuit.n_modes,
            "input": self.full_input_state,
            "n_samples": self.data.n_samples,
            "min_detection": min_detection,
            "direct_implementation": direct_encoding,
            "unitary": self.data.circuit.U_full,
        }
        if direct_encoding:
            payload["circuit_spec"] = self.data.circuit._circuit_spec
        # Only add post_selection if it is required
        if post_selection["post_select"] or post_selection["herald"]:
            payload["job_data"] = dict(post_selection)
        return payload

    def _get_post_selection(
        self,
    ) -> dict[str, list[tuple[tuple[int, ...], tuple[int, ...]]]]:
        """Generates required post-selection data for a particular payload"""
        post_selection = []
        # Get data from manually set post-selection
        if self.data.post_selection is not None and not isinstance(
            self.data.post_selection, DefaultPostSelection
        ):
            if not isinstance(self.data.post_selection, PostSelection):
                raise TypeError(
                    "Post-selection cannot be a function when executing "
                    "remotely, must be a lightworks PostSelection object."
                )
            herald_modes = list(self.data.circuit.heralds.output.keys())
            for rule in self.data.post_selection.rules:
                mapped_modes = [_map_mode(m, herald_modes) for m in rule.modes]
                if max(mapped_modes) >= self.data.circuit.n_modes:
                    raise ValueError(
                        "Provided post-selection rules detected to exceed size "
                        "of circuit."
                    )
                post_selection.append((tuple(mapped_modes), rule.n_photons))
        # And from heralds at the output
        herald: list[tuple[tuple[int, ...], tuple[int, ...]]] = []
        for m, n in self.data.circuit.heralds.output.items():
            herald.append(((m,), (n,)))
        return {"post_select": post_selection, "herald": herald}


def _map_mode(mode: int, herald_modes: list[int]) -> int:
    """
    Remaps a provided mode around the heralded modes of a circuit.
    """
    for i in sorted(herald_modes):
        if mode >= i:
            mode += 1
    return mode
