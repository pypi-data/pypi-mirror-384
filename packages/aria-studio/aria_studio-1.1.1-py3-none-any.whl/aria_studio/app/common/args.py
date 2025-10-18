# Copyright (c) Meta Platforms, Inc. and affiliates.
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

import argparse
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Args:
    """
    Class to hold the arguments passed in from command line
    """

    _args: Optional[argparse.Namespace] = None

    @classmethod
    def get_args(cls):
        """Get the arguments passed in from command line"""
        if cls._args is None:
            cls._args = _parse_arguments()
            logger.debug(f"args: {cls._args}")
        return cls._args


def _parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--use-system-adb",
        action="store_true",
        help="Use adb binary that is already installed on the system. The default is to use the adb binary that comes with Aria Studio.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on",
    )
    parser.add_argument(
        "--no-browser",
        action="store_false",
        dest="browser",
        help="Do not open a browser window",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload of the app",
    )
    return parser.parse_args()
