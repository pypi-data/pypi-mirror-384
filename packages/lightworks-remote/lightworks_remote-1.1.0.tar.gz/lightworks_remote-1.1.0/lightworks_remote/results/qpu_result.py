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
from collections.abc import Callable
from copy import copy
from types import FunctionType, MethodType
from typing import Any

import matplotlib.figure
import matplotlib.pyplot as plt
from lightworks import State
from lightworks.sdk.results import Result
from lightworks.sdk.utils import PostSelectionFunction
from lightworks.sdk.utils.heralding import remove_heralds_from_state
from lightworks.sdk.utils.post_selection import PostSelectionType

from lightworks_remote.utils import write_data_to_json


class QPUSamplingResult(Result[State, int]):
    """
    Stores the results from a job, handling the application of post-selection
    rules if this is included as a "post_select" or "herald" field in the data
    dictionary.

    Args:

        data (dict) : The data to process and store in the Result object.

    """

    def __init__(self, data: dict[str, Any]) -> None:
        if data["results"] is None:
            super().__init__({})
            self.__outputs = None
            self.__raw_data = data
            self._post_selection = data.get("job_data")
            warnings.warn(
                "No results were returned by the system.", stacklevel=1
            )
            return
        # Copy data to avoid modification issues
        data = copy(data)
        # Extract post-selection from data if included
        job_data = data.get("job_data")
        # Apply post_selection to get data processed data
        if job_data is not None:
            post_select = job_data.pop("post_select", [])
            herald = job_data.pop("herald", [])
            post_select = [] if post_select is None else post_select
            herald = [] if herald is None else herald
            herald_modes = [h[0][0] for h in herald]
            rules = list(post_select) + list(herald)
            try:
                data_r = apply_post_selection(
                    data["results"], rules, herald_modes
                )
            except IndexError:
                warnings.warn(
                    "Raw data returned: An index error was raised while trying "
                    "to apply post-selection and/or heralding to the results. "
                    "This likely results from one of the criteria being "
                    "outside of the allowed range.",
                    stacklevel=2,
                )
                data_r = data["results"]
            except Exception as e:  # noqa: BLE001
                warnings.warn(
                    "Raw data returned: An unknown error occurred while trying "
                    "to apply post-selection and/or heralding to the results. "
                    f"Returning raw data instead. Exception: {e}.",
                    stacklevel=2,
                )
                data_r = data["results"]
        else:
            data_r = data["results"]
        super().__init__(data_r)
        # Also save raw data and post-selection
        self.__raw_data = data["results"]
        self._post_selection = (
            {"post_select": post_select, "herald": herald}
            if job_data is not None
            else None
        )
        self._job_data = job_data
        # And calculate outputs from data
        self.__outputs = list(self.keys())

    def __getitem__(self, item: State) -> int:
        """Custom get item behaviour - used when object accessed with []."""
        if not self:
            raise ValueError("Result contains no data.")
        if not isinstance(item, State):
            raise TypeError("Get item value must be a State.")
        if item not in self:
            raise KeyError("Provided output state not in data.")
        return super().__getitem__(item)

    @property
    def raw_data(self) -> dict[str, Any]:
        """
        Stores raw data from a job.
        """
        return self.__raw_data

    @property
    def outputs(self) -> list[State] | None:
        """
        All outputs measured in the result.
        """
        return self.__outputs

    @property
    def post_selection(
        self,
    ) -> list[tuple[tuple[int, ...], tuple[int, ...]]] | None:
        """
        Returns any post-selection criteria included with a result.
        """
        return self._post_selection

    def plot(
        self, show: bool = True
    ) -> tuple[matplotlib.figure.Figure, plt.Axes] | None:
        """
        Creates a bar chart plot of the data contained within the result.
        """
        if not len(self):
            raise ValueError("Result contains no data.")
        fig, ax = plt.subplots(figsize=(7, 6))
        x_data = range(len(self))
        ax.bar(x_data, list(self.values()))
        ax.set_xticks(x_data)
        labels = [str(s) for s in self]
        ax.set_xticklabels(labels, rotation=90)
        ax.set_xlabel("State")
        ax.set_ylabel("Counts")

        # Optionally use show on plot if specified
        if show:
            plt.show()
            return None
        return (fig, ax)

    def save(self, filename: str, raw_data: bool = False) -> None:
        """
        Saves the stored data to a json file.

        Args:

            filename (str) : The name to use for saving the results data,
                this can also contain a path to save it within a specific
                directory.

            raw_data (bool, optional) : Controls whether the post-processed or
                raw data should be saved.

        """
        # Select correct data and save
        if not raw_data:
            if not len(self):
                raise ValueError("Result contains no data.")
            data = {str(k.s)[1:-1]: v for k, v in self.items()}
        else:
            data = self.raw_data

        write_data_to_json(data, filename)

    def map(
        self,
        mapping: Callable[[State, Any], State],
        *args: Any,
        **kwargs: Any,
    ) -> "QPUSamplingResult":
        """
        Performs a generic remapping of states based on a provided function.
        """
        if not isinstance(mapping, FunctionType | MethodType):
            raise TypeError(
                "Provided mapping should be a callable function which accepts "
                "and returns a State object."
            )
        mapped_result: dict[State, int] = {}
        for out_state, val in self.items():
            new_s = mapping(out_state, *args, **kwargs)
            if new_s in mapped_result:
                mapped_result[new_s] += val
            else:
                mapped_result[new_s] = val
        return self._recombine_mapped_result(mapped_result)

    def apply_post_selection(
        self, post_selection: PostSelectionType | Callable[[State], bool]
    ) -> "QPUSamplingResult":
        """
        Applies an additional post-selection criteria to the stored result and
        returns this as a new object.
        """
        if isinstance(post_selection, FunctionType | MethodType):
            post_selection = PostSelectionFunction(post_selection)
        if not isinstance(post_selection, PostSelectionType):
            raise TypeError(
                "Provided post_selection should either be a PostSelection "
                "object or a callable function which accepts a state and "
                "returns a boolean to indicate whether the state is valid."
            )
        return self._recombine_mapped_result(
            {
                state: val
                for state, val in self.items()
                if post_selection.validate(state)
            }
        )

    def _recombine_mapped_result(
        self, mapped_result: dict[State, int]
    ) -> "QPUSamplingResult":
        """Creates a new Result object from mapped data."""
        return QPUSamplingResult({"results": mapped_result})


def apply_post_selection(
    data: dict[State, int],
    rules: list[tuple[tuple[int, ...], tuple[int, ...]]],
    herald_modes: list[int],
) -> dict[State, int]:
    """
    Applies the post-selection criteria to a set of data in a dictionary.

    Args:

        data (dict) : The unprocessed data dictionary.

        rules (list) : The post-selection rules to be applied.

        herald_modes (list) : The modes used for heralding, which will be
            removed from the state.

    Returns:

        dict : The processed dictionary of data.

    """
    return {
        State(remove_heralds_from_state(k, herald_modes)): v
        for k, v in data.items()
        if meets_post_selection(k, rules)
    }


def meets_post_selection(
    state: State, post_selection: list[tuple[tuple[int, ...], tuple[int, ...]]]
) -> bool:
    """
    Validates whether a provided State meets the set post-selection criteria.

    Args:

        state (State) : The state which is to be checked.

        post_selection (int) : The post-selection rules to be applied.

    Returns:

        bool : Indicates whether the provided State meets the post-selection
            criteria.

    """
    for rule in post_selection:
        total = 0
        for mode in rule[0]:
            total += state[mode]
        if total not in rule[1]:
            return False
    return True
