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

import os

import pytest
from lightworks import State

from lightworks_remote.results import QPUSamplingResult
from lightworks_remote.results.qpu_result import (
    apply_post_selection,
    meets_post_selection,
)


class TestResult:
    """
    Unit tests for the QPUSamplingResult object.
    """

    def setup_method(self):
        """
        Creates a set of test data that can be used with the result.
        """
        self.data = {
            "results": {
                State([1, 1, 1, 0, 0, 0]): 100,
                State([0, 0, 0, 1, 1, 1]): 200,
                State([1, 0, 1, 1, 0, 0]): 300,
                State([0, 1, 0, 0, 1, 1]): 400,
            }
        }

    def test_result_creation(self):
        """
        Checks QPUSamplingResult object can be created from a provided data
        dictionary.
        """
        QPUSamplingResult(self.data)

    def test_result_creation_post_selection(self):
        """
        Checks QPUSamplingResult object can be created from a provided data
        dictionary when post-selection is included.
        """
        self.data["post_selection"] = {"post_select": [((0, 1), (1,))]}
        QPUSamplingResult(self.data)

    def test_result_creation_post_selection_herald(self):
        """
        Checks QPUSamplingResult object can be created from a provided data
        dictionary when post-selection is included only through heralding.
        """
        self.data["post_selection"] = {"herald": [((0, 1), (1,))]}
        QPUSamplingResult(self.data)

    @pytest.mark.parametrize("value", [[], None])
    def test_result_creation_post_selection_empty_post_select(self, value):
        """
        Checks QPUSamplingResult object can be created from a provided data
        dictionary when post-selection is included.
        """
        self.data["post_selection"] = {"post_select": value}
        QPUSamplingResult(self.data)

    @pytest.mark.parametrize("value", [[], None])
    def test_result_creation_post_selection_empty_herald(self, value):
        """
        Checks QPUSamplingResult object can be created from a provided data
        dictionary when post-selection is included.
        """
        self.data["post_selection"] = {
            "post_select": [((0, 1), (1,))],
            "herald": value,
        }
        QPUSamplingResult(self.data)

    def test_post_selection_not_in_data(self):
        """
        Checks post-selection field is correctly removed from data and raw data.
        """
        self.data["job_data"] = {"post_select": [((0, 1), (1,))]}
        r = QPUSamplingResult(self.data)
        assert "post_selection" not in r
        assert "post_selection" not in r.raw_data

    def test_post_selection_applied(self):
        """
        Checks that post-selection is correctly applied to remove states which
        do not match.
        """
        self.data["job_data"] = {"post_select": [((0,), (1,))]}
        r = QPUSamplingResult(self.data)
        assert len(r) == 2
        assert State([1, 1, 1, 0, 0, 0]) in r
        assert State([1, 0, 1, 1, 0, 0]) in r
        assert State([0, 0, 0, 1, 1, 1]) not in r
        assert State([0, 1, 0, 0, 1, 1]) not in r

    def test_heralding_applied(self):
        """
        Checks that heralding is correctly applied to remove states which do not
        match.
        """
        self.data["job_data"] = {"herald": [((0,), (1,))]}
        r = QPUSamplingResult(self.data)
        assert len(r) == 2
        assert State([1, 1, 0, 0, 0]) in r
        assert State([0, 1, 1, 0, 0]) in r
        assert State([0, 0, 1, 1, 1]) not in r
        assert State([1, 0, 0, 1, 1]) not in r

    def test_result_does_not_modify_raw_data(self):
        """
        Checks result does not modify raw data when applying processing.
        """
        self.data["job_data"] = {
            "post_select": [((0, 1), (1,))],
            "herald": [((2,), (1,))],
        }
        QPUSamplingResult(self.data)
        assert "job_data" in self.data

    def test_result_raw_data_is_unprocessed(self):
        """
        Checks result does not modify raw data when applying post-selection and
        confirms data and raw data are different.
        """
        self.data["job_data"] = {"post_select": [((0, 1), (1,))]}
        r = QPUSamplingResult(self.data)
        assert r.raw_data == self.data["results"]
        assert r.raw_data != r

    def test_results_save(self):
        """
        Checks result data can be saved to a file.
        """
        r = QPUSamplingResult(self.data)
        r.save("_test_results")
        assert os.path.isfile("_test_results.json")
        os.remove("_test_results.json")

    def test_results_save_json(self):
        """
        Checks result data can be saved to a file when json file extension is
        included at the end.
        """
        r = QPUSamplingResult(self.data)
        r.save("_test_results.json")
        assert os.path.isfile("_test_results.json")
        os.remove("_test_results.json")

    def test_results_save_path(self):
        """
        Checks result data can be saved to a file with a relative path. The
        existing .pytest_cache directory is used.
        """
        r = QPUSamplingResult(self.data)
        r.save(".pytest_cache/_test_results")
        assert os.path.isfile(".pytest_cache/_test_results.json")
        os.remove(".pytest_cache/_test_results.json")

    def test_results_save_abs_path(self):
        """
        Checks result data can be saved to a file with an absolute path. The
        existing .pytest_cache directory is used.
        """
        r = QPUSamplingResult(self.data)
        r.save(os.getcwd() + "/.pytest_cache/_test_results")
        assert os.path.isfile(".pytest_cache/_test_results.json")
        os.remove(".pytest_cache/_test_results.json")

    def test_meets_post_selection(self):
        """
        Checks meets_post_selection returns True for a valid State.
        """
        assert meets_post_selection(State([1, 0, 1, 0]), [((1,), (0,))])
        assert meets_post_selection(State([1, 0, 1, 0]), [((0, 1), (1,))])
        assert meets_post_selection(State([1, 0, 1, 0]), [((0, 1, 2), (2,))])

    def test_meets_post_selection_false(self):
        """
        Checks meets_post_selection returns False for an invalid State.
        """
        assert not meets_post_selection(State([0, 1, 1, 0]), [((1,), (0,))])
        assert not meets_post_selection(State([1, 1, 0, 0]), [((0, 1), (1,))])
        assert not meets_post_selection(
            State([0, 0, 1, 1]), [((0, 1, 2), (2,))]
        )

    def test_meets_post_selection_multi_photons(self):
        """
        Checks meets_post_selection returns True for a valid State when multiple
        possible photon numbers are provided.
        """
        assert meets_post_selection(State([1, 0, 1, 0]), [((1,), (0, 1))])
        assert meets_post_selection(State([1, 1, 1, 0]), [((1,), (0, 1))])
        assert meets_post_selection(State([1, 1, 1, 0]), [((0, 1), (1, 2))])

    def test_meets_post_selection_multi_rules(self):
        """
        Checks meets_post_selection returns True for a valid State when multiple
        rules are all applied.
        """
        post_selection = [((1,), (0, 1)), ((2, 3), (1,))]
        assert meets_post_selection(State([1, 0, 1, 0]), post_selection)

    def test_meets_post_selection_multi_rules_false(self):
        """
        Checks meets_post_selection returns False for an invalid State when
        multiple rules are all applied.
        """
        post_selection = [((1,), (0, 1)), ((2, 3), (2,))]
        assert not meets_post_selection(State([1, 0, 1, 0]), post_selection)

    def test_meets_post_selection_empty_list(self):
        """
        Checks that meets_post_selection works with an empty list.
        """
        meets_post_selection(self.data, [])

    def test_apply_post_selection(self):
        """
        Checks apply_post_selection removes the correct States.
        """
        data = apply_post_selection(self.data["results"], [((0, 1), (1,))], [])
        for s in data:
            assert s[0] + s[1] == 1

    def test_apply_post_selection_multi_photon(self):
        """
        Checks apply_post_selection removes the correct States when multi photon
        numbers are valid.
        """
        data = apply_post_selection(
            self.data["results"], [((0, 1), (1, 2))], []
        )
        for s in data:
            assert s[0] + s[1] in {1, 2}

    def test_apply_post_selection_multi_rules(self):
        """
        Checks apply_post_selection removes the correct States when multi photon
        numbers are valid.
        """
        post_selection = [((0, 1), (1, 2)), ((2,), (1,))]
        data = apply_post_selection(self.data["results"], post_selection, [])
        for s in data:
            assert s[0] + s[1] in {1, 2}
            assert s[2] == 1

    def test_herald_modes_removed(self):
        """
        Checks that the herald modes are removed when this is used.
        """
        heralds = [0, 3]
        data = apply_post_selection(self.data["results"], [], heralds)
        for s in self.data["results"]:
            assert s[1:3] + s[4:] in data

    def test_apply_post_selection_empty_list(self):
        """
        Checks that apply_post_selection works with an empty list.
        """
        apply_post_selection(self.data, [], [])
