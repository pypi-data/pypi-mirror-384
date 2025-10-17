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

import webbrowser
from argparse import ArgumentParser


def open_docs() -> None:
    """
    Open docs in a web browsers.
    """
    webbrowser.open("https://aegiq.gitlab.io/general/artemis/artemis-manual/")
    print("Documentation opened in browser.")  # noqa: T201


def main() -> None:
    """
    Processes provided arguments and performs corresponding commands.
    """
    parser = ArgumentParser(prog="lightworks_remote")
    _, uargs = parser.parse_known_args()
    for a in uargs:
        if a == "docs":
            open_docs()
        else:
            msg = f"Unrecognised argument '{a}' passed."
            raise ValueError(msg)


if __name__ == "__main__":
    main()
