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

# ruff: noqa: PLW1514

import json
from pathlib import Path

from lightworks_remote.utils import (
    AuthenticationError,
    TokenError,
    get_persistent_file_data_location,
)


class Token:
    """
    Stores and provides token data, as well as utilities for saving and loading
    this data to a persistent location.
    """

    def __init__(self) -> None:
        self.__token: str | None = None

    def __str__(self) -> str:
        return str(self.__token)

    def __repr__(self) -> str:
        return f"lightworks_remote.token('{self.__token}')"

    def set(self, token: str) -> None:
        """
        Sets the current token. This should be provided as a string.
        """
        if not isinstance(token, str):
            raise TypeError("Token should be provided in string format.")
        self.__token = token

    def get(self) -> str:
        """
        Retrieves the currently set token value.
        """
        if self.__token is None:
            raise AuthenticationError(
                "Token has not been configured, this can be achieved with the "
                "set method (lightworks_remote.token.set('token'))."
            )
        return self.__token

    def save(self, name: str, overwrite: bool = False) -> None:
        """
        Save the token that is currently set, using a name to identify it which
        can be used in the load method later.

        Args:

            name (str) : The name which should be used to save the token.

            overwrite (bool, optional) : Dictates whether the token name can be
                used to overwrite an existing token. Defaults to False.

        Raises:

            TokenError : If an existing token if found with the set name and
                overwrite is set to False.

        """
        if not isinstance(name, str):
            raise TypeError("Save name should be a string")
        path = self._get_file_loc()
        # If file exists then load
        if path.exists():
            with open(path) as f:
                data = json.load(f)
        else:
            data = {}
        # Check for existing key if not allowed to overwrite
        if not overwrite and name in data:
            raise TokenError(
                "Existing token with chosen name found, select a different"
                " name or pass overwrite = True to method call."
            )
        # Then added to dictionary
        data[name] = self.get()
        # And update save file
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

    def load(self, name: str) -> None:
        """
        Loads a saved token with provided name.

        Args:

            name (str) : The name of the token to load.

        Raises:

            TokenError : When a token matching the provided name is not found.

        """
        # Check file and token name exists
        self._check_save_loc_exists()
        path = self._get_file_loc()
        with open(path) as f:
            data = json.load(f)
        if name not in data:
            raise TokenError("Token with requested name not found.")
        # Update set token value
        self.set(data[name])

    def delete_saved(self, name: str) -> None:
        """
        Delete saved token with provided name.

        Args:

            name (str) : The name of the token to delete.

        Raises:

            TokenError : When a token matching the provided name is not found.

        """
        # Check file and token name exists
        self._check_save_loc_exists()
        path = self._get_file_loc()
        with open(path) as f:
            data = json.load(f)
        if name not in data:
            raise TokenError("Token with requested name not found.")
        # Remove token
        del data[name]
        # Update save file
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

    def list_saved(self) -> None:
        """
        Prints a list of all currently saved tokens.
        """
        # Check file exists
        self._check_save_loc_exists()
        path = self._get_file_loc()
        # Get all token data and print
        with open(path) as f:
            data = json.load(f)
        print(list(data.keys()))  # noqa: T201

    def _check_save_loc_exists(self) -> None:
        """
        Checks if the token save location has been created.
        """
        path = self._get_file_loc()
        if not path.exists():
            raise TokenError("No tokens have been saved yet.")

    def _get_file_loc(self) -> Path:
        """
        Returns file file location for json used to store tokens.
        """
        # Set path according to platform
        path = get_persistent_file_data_location()
        return path / "tokens.json"
