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

from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

import requests

from lightworks_remote.utils import AuthenticationError
from lightworks_remote.utils.configuration import APIURL


def catch_error_codes(
    func: Callable[..., requests.Response],
) -> requests.Response:
    """
    Check for generic errors and raise an exception for these.
    """

    @wraps(func)
    def run_and_catch(
        self: "HTTPInterface", *args: Any, **kwargs: Any
    ) -> requests.Response:
        response = func(self, *args, **kwargs)
        if response.status_code == 401:
            raise AuthenticationError(
                "Unable to authenticate with job submission service, this may "
                "result from an invalid or expired access token being provided."
            )
        if response.status_code == 403:
            raise AuthenticationError(
                "Not authenticated to access the requested resource."
            )
        return response

    return run_and_catch


TIMEOUT = 10  # Set timeout for requests


class HTTPInterface:
    """
    Generic http interface to automatically include base url and certificate
    data into http requests.

    Args:

        url (APIURL) : The APIURl object which details the base url.

        certificate (str) : A file path to provide a certificate for
            authentication with the http endpoint.

    """

    def __init__(self, url: APIURL, certificate: str | Path) -> None:
        self._url = url
        self._certificate = str(certificate)

    @catch_error_codes
    def _get(self, loc: str, **kwargs: Any) -> requests.Response:
        return self._get_no_catch(loc, **kwargs)

    @catch_error_codes
    def _post(self, loc: str, **kwargs: Any) -> requests.Response:
        return self._post_no_catch(loc, **kwargs)

    @catch_error_codes
    def _put(self, loc: str, **kwargs: Any) -> requests.Response:
        return self._put_no_catch(loc, **kwargs)

    def _get_no_catch(self, loc: str, **kwargs: Any) -> requests.Response:
        return requests.get(
            self._url.url + loc,
            verify=self._certificate,
            timeout=TIMEOUT,
            **kwargs,
        )

    def _post_no_catch(self, loc: str, **kwargs: Any) -> requests.Response:
        return requests.post(
            self._url.url + loc,
            verify=self._certificate,
            timeout=TIMEOUT,
            **kwargs,
        )

    def _put_no_catch(self, loc: str, **kwargs: Any) -> requests.Response:
        return requests.put(
            self._url.url + loc,
            verify=self._certificate,
            timeout=TIMEOUT,
            **kwargs,
        )
