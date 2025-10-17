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
import string
from random import choice

import pytest

from lightworks_remote import TokenError, token

options = list(string.ascii_letters) + [str(i) for i in range(9)]
TOKEN = "".join([choice(options) for _ in range(1000)])
TOKEN_SAVE_NAME = "pytest_test_token"  # noqa: S105


class TestToken:
    """
    Checks the correct functioning of the token module.
    """

    def setup_method(self):
        """Perform setup before each test in which the token value is reset."""
        token.set(TOKEN)

    def test_set(self):
        """Confirms token can be set to a provided value."""
        assert token._Token__token == TOKEN

    @pytest.mark.parametrize("value", [None, 1234, ["test"]])
    def test_invalid_set(self, value):
        """
        Checks TypeError raised if an invalid type is set for the token.
        """
        with pytest.raises(TypeError):
            token.set(value)

    def test_get(self):
        """Confirms token value can be retrieved using get."""
        assert token.get() == TOKEN

    def test_str(self):
        """Checks that str returns token value."""
        assert str(token) == TOKEN

    def test_repr(self):
        """Checks token value is in repr return."""
        assert TOKEN in repr(token)

    def test_save(self):
        """Checks that token is able to be saved successfully."""
        token.save(TOKEN_SAVE_NAME, overwrite=True)

    def test_save_no_overwrite(self):
        """
        Confirms an error is raised if a token is saved with the same name twice
        with the overwrite option being enabled.
        """
        token.save(TOKEN_SAVE_NAME, overwrite=True)
        with pytest.raises(TokenError):
            token.save(TOKEN_SAVE_NAME, overwrite=False)

    def test_save_default_no_overwrite(self):
        """
        Confirms that default value for the overwrite option if False by
        checking an exception is raised if token is saved with same name twice.
        """
        token.save(TOKEN_SAVE_NAME, overwrite=True)
        with pytest.raises(TokenError):
            token.save(TOKEN_SAVE_NAME)

    def test_load(self):
        """
        Checks that token is able to be overwritten and then retrieved using the
        load method.
        """
        token.save(TOKEN_SAVE_NAME, overwrite=True)
        token.set("None")
        token.load(TOKEN_SAVE_NAME)
        assert token.get() == TOKEN

    def teardown_class(self):
        """Perform tear down by deleting saved token."""
        with contextlib.suppress(TokenError):
            token.delete_saved(TOKEN_SAVE_NAME)
