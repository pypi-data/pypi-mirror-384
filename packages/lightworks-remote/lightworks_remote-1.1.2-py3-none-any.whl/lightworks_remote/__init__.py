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
Lightworks Remote
=================

Extension to lightworks to support compilation and submission of jobs to a
remote backend, either for emulation or hardware execution.
"""

import warnings

from .__version import __version__
from .remote import (
    QPU,
    cancel_job,
    check_job_complete,
    get_job_details,
    get_job_status,
    get_qpu_details,
    get_results,
    list_all_jobs,
    list_qpus,
    list_scheduled_jobs,
    load_job_from_file,
    show_scheduled,
)
from .token import token
from .utils import (
    install_certificate,
    saved_job_exists,
    set_api_url,
)
from .utils.exceptions import *

__all__ = [
    "QPU",
    "cancel_job",
    "check_job_complete",
    "get_job_details",
    "get_job_status",
    "get_qpu_details",
    "get_results",
    "install_certificate",
    "list_all_jobs",
    "list_qpus",
    "list_scheduled_jobs",
    "load_job_from_file",
    "saved_job_exists",
    "set_api_url",
    "show_scheduled",
    "token",
]


def warning_on_one_line(
    message: Warning | str,
    category: type[Warning],
    filename: str,  # noqa: ARG001
    lineno: int,  # noqa: ARG001
    line: str | None = None,  # noqa: ARG001
) -> str:
    """
    Customs warnings message which overwrites some of the noise in the default
    message.
    """
    return f"{category.__name__}: {message}\n"


warnings.formatwarning = warning_on_one_line
