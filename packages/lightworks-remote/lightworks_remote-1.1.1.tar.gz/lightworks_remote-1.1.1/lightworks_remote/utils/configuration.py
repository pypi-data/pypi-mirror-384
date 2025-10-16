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

"""
For management of certificates required to communicate with the API.
"""

import shutil
import warnings

from .exceptions import LightworksRemoteError
from .file_management import get_persistent_file_data_location


def set_api_url(url: str) -> None:
    """
    Saves the api url to a text file and then also assigns to the URL class.
    """
    URL._set(url)


def install_certificate(filename: str) -> None:
    """
    Installs the web certificate required for communication with the API to the
    correct location.
    """
    path = get_persistent_file_data_location()
    shutil.copy(filename, path / "certificate.pem")


class APIURL:
    """
    Stores and manages URL information, attempting to retrieve it on class
    initialisation.
    """

    def __init__(self) -> None:
        path = get_persistent_file_data_location()
        self._url: str | None
        try:
            with open(path / "api_url.txt", encoding="utf-8") as f:
                self._url = f.read()
        except Exception:  # noqa: BLE001
            warnings.warn(
                "Could not retrieve API URL, configure this with the "
                "'set_api_url' function.",
                stacklevel=1,
                category=UserWarning,
            )
            self._url = None

    @property
    def url(self) -> str:
        """Returns the currently set url."""
        if self._url is None:
            raise LightworksRemoteError(
                "API URL not set, this can be configured with the 'set_api_url'"
                "function."
            )
        return self._url

    def _set(self, url: str) -> None:
        path = get_persistent_file_data_location()
        with open(path / "api_url.txt", "w", encoding="utf-8") as f:
            f.write(url)
        self._url = url


# Configure URL class
URL = APIURL()
