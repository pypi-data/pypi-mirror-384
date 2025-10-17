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
Configures a test certificate and api url so that unit tests can be run
successfully.
"""

from lightworks_remote import install_certificate, set_api_url

with open("test_cert.pem", "w", encoding="utf-8") as file:
    file.write("This is a certificate.")

install_certificate("test_cert.pem")

set_api_url("https://test/")
