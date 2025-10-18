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

import importlib
import logging
import re
import sys
from pathlib import Path
from typing import Final, Optional

from aria_studio.app.singleton_base import SingletonBase

logger = logging.getLogger(__name__)


class AppInfoManager(metaclass=SingletonBase):
    """
    The class to cache the Aria Studio executable data.
    """

    __SUFFIX_DEVELOPMENT: Final[str] = "-development"
    __SUFFIX_ELECTRON: Final[str] = "S"

    __ARIA_STUDIO_PACKAGE_NAME: Final[str] = "aria-studio"
    __PAT_PACKAGE_NAME: Final[str] = "projectaria_tools"
    __LOG_NTH_REQUEST: Final[int] = 100

    __suffix: str
    __cached_version: Optional[str] = None
    __cached_pat_version: Optional[str] = None

    __log_number: int

    def __init__(self):
        self.__suffix = (
            AppInfoManager.__SUFFIX_ELECTRON
            if self.__is_electron()
            else AppInfoManager.__SUFFIX_DEVELOPMENT
        )
        self.__log_number = AppInfoManager.__LOG_NTH_REQUEST - 1

    async def get_version(self) -> str:
        """
        Gets the Aria Studio version from the cache. If the cache is empty, it will be filled in.

        The application version cannot change during runtime, so it's fine to read once and cache it.
        """

        if self.__cached_version is None:
            try:
                # @manual
                from aria_studio.app.local.meta_app_info import get_version_file_path

                version_file: Path = get_version_file_path()
            except ImportError:
                version_file: Path = (
                    Path(sys._MEIPASS) / "aria_studio" / "VERSION.bzl"
                    if self.__is_electron()
                    else Path("VERSION.bzl")
                )

            if version_file.is_file():
                with open(version_file, "r") as fp:
                    content: str = fp.read().strip()
                    group: str = re.search(
                        r'versionName\s*=\s*"([0-9.]+)"', content
                    ).group()
                    self.__cached_version = (
                        f"{re.search(r'([0-9.]+)', group).group()}{self.__suffix}"
                    )
            else:
                self.__cached_version = importlib.metadata.version(
                    AppInfoManager.__ARIA_STUDIO_PACKAGE_NAME
                )

        self.__log_number += 1
        if self.__log_number % AppInfoManager.__LOG_NTH_REQUEST == 0:
            logger.info(
                f"Running Aria Studio {self.__cached_version}, Project Aria Tools {self.get_pat_version()}"
            )
            self.__log_number = 0

        return self.__cached_version

    def get_pat_version(self) -> str:
        """
        Gets the Project Aria Tools version from the cache. If the cache is empty, it will be filled in.

        The PAT version cannot change during runtime, so it's fine to read once and cache it.
        """

        if self.__cached_pat_version is None:
            try:
                # @manual
                from aria_studio.app.local.meta_app_info import (
                    get_pat_version_file_path,
                )

                version_file: Path = get_pat_version_file_path()
            except ImportError:
                version_file: Path = (
                    Path(sys._MEIPASS) / "aria_studio" / "PAT_VERSION"
                    if self.__is_electron()
                    else Path()
                )

            if version_file.is_file():
                with open(version_file, "r") as fp:
                    self.__cached_pat_version = fp.read().strip()
            else:
                try:
                    self.__cached_pat_version = importlib.metadata.version(
                        AppInfoManager.__PAT_PACKAGE_NAME
                    )
                except importlib.metadata.PackageNotFoundError:
                    # unknown as of writing execution path
                    self.__cached_pat_version = "Internal"

        return self.__cached_pat_version

    def __is_electron(self) -> bool:
        """
        Checks if the application is running as an Electron app.
        """

        return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")
