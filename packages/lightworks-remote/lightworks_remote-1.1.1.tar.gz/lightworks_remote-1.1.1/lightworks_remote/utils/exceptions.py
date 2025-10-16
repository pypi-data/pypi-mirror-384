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

from requests import Response


class LightworksRemoteError(Exception):
    """General exception for lightworks remote module."""


class JobSubmissionError(LightworksRemoteError):
    """For errors arising during submission procedure."""


class AuthenticationError(LightworksRemoteError):
    """For errors relating to authentication of system."""


class ValidationError(LightworksRemoteError):
    """For errors arising from invalid values provided as part of a job."""


class TokenError(LightworksRemoteError):
    """For errors relating to getting/setting of authentication token."""


class ResultsError(LightworksRemoteError):
    """For errors relating to retrieval of results from the remote platform."""


class JobError(LightworksRemoteError):
    """General errors relating to a job."""


class JobNotFoundError(LightworksRemoteError):
    """For errors when a job with matching id is not found."""


class HTTPError(LightworksRemoteError):
    """For other errors relating to HTTP communication with platform."""

    def __init__(self, message: str, response: Response | None = None) -> None:
        if not isinstance(response, Response | NoneType):
            raise TypeError(
                "response should be a requests Response object or None."
            )
        if response is not None:
            message += f" (Code: {response.status_code} {response.reason})"
        super().__init__(message)
