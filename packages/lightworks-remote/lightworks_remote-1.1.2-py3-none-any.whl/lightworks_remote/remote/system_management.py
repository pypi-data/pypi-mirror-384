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

from lightworks_remote.http import ArtemisHTTPInterface
from lightworks_remote.http.artemis_qpu_details import ArtemisQPU


def list_qpus() -> list[str]:
    """
    Gets and returns a list of all available QPUs on the Artemis platform.
    """
    api = ArtemisHTTPInterface()
    return api.list_qpus()


def get_qpu_details(name: str) -> ArtemisQPU:
    """
    Returns details of QPU with provided name.
    """
    api = ArtemisHTTPInterface()
    return api.get_qpu_details(name)
