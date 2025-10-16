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

from dataclasses import dataclass

from .qpu_details import QPUDetails

ARTEMIS_QPU_DETAILS_MAP = {
    "id": "id",
    "name": "name",
    "numberOfModes": "n_modes",
    "maxPhotonInputNumber": "max_photon_input",
    "maxDetectionFilter": "max_detection_filter",
    "defaultMaxSamples": "default_max_samples",
    "maxSamples": "max_samples",
    "isAvailable": "available",
    "lastUpdated": "last_updated",
}


@dataclass(kw_only=True)
class ArtemisQPU(QPUDetails):
    """
    Dataclass for storing all details of an artemis QPU.
    """

    name: str
    id: str
    n_modes: int
    max_photon_input: int
    max_detection_filter: int
    default_max_samples: int
    max_samples: dict[int, int]
    available: bool
    last_updated: str
