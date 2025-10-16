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
Contains utilities for assisting with saving and loading data from files.
"""

import json
import platform
from pathlib import Path
from typing import Any

from lightworks_remote.payloads import Payload

from .serialization import serialize


def write_data_to_json(
    data: Payload | dict[str, Any], filename: str | Path
) -> None:
    """
    Writes the provided data to a json file.
    """
    data = serialize(data)
    full_path = validate_json_filename(filename)
    # Create directory if it doesn't exist
    full_path.parent.mkdir(parents=True, exist_ok=True)

    with open(full_path, "w", encoding="locale") as f:
        json.dump(data, f, indent=4)


def get_data_from_json(filename: str | Path) -> dict[str, Any]:
    """
    Gets data from a json file.
    """
    full_path = validate_json_filename(filename)
    if not saved_job_exists(full_path):
        raise FileNotFoundError("File with provided name does not exist.")
    with open(full_path, encoding="locale") as f:
        return json.load(f)


def validate_json_filename(filename: str | Path) -> Path:
    """
    Checks that a provided file name is a string and adds .json at end if this
    is not included
    """
    if not isinstance(filename, str | Path):
        raise TypeError("Provided filename should be a string or Path.")
    return Path(filename).with_suffix(".json")


def saved_job_exists(filename: str | Path) -> bool:
    """
    Checks if a saved job with the provided filename exists.
    """
    full_path = validate_json_filename(filename)
    return full_path.exists()


def get_persistent_file_data_location() -> Path:
    """
    Gets OS-dependent location that any persistent data should be saved to.
    """
    if platform.system() == "Windows":
        path = Path.home() / ".aegiq/lightworks/"
    elif platform.system() == "Linux":
        path = Path.home() / ".local/share/Aegiq/lightworks/"
    elif platform.system() == "Darwin":
        path = Path.home() / "Library/Application Support/Aegiq/lightworks/"
    else:
        msg = (
            "Certificate save location not yet implemented for current "
            f"platform ({platform.system()})."
        )
        raise NotImplementedError(msg)
    path.mkdir(parents=True, exist_ok=True)
    return path
