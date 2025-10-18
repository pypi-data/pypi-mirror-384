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

import asyncio
import logging
import platform
import shutil
import subprocess
import threading
import webbrowser

from configparser import ConfigParser, NoSectionError
from contextlib import asynccontextmanager
from functools import wraps
from pathlib import Path
from typing import Final, List, Optional

from aria_studio.app.common.args import Args
from aria_studio.app.constants import ARIA_STUDIO_DB, LOCALHOST
from aria_studio.app.device.device_manager import DeviceManager

from fastapi import FastAPI, HTTPException, status

from projectaria_tools.aria_mps_cli.cli_lib.authentication import Authenticator
from projectaria_tools.aria_mps_cli.cli_lib.common import log_exceptions
from projectaria_tools.aria_mps_cli.cli_lib.constants import CONFIG_DIR, CONFIG_FILE
from projectaria_tools.aria_mps_cli.cli_lib.http_helper import HttpHelper

logger = logging.getLogger(__name__)

VRS_FLAG: Final[str] = "--vrs"
VRS_PYTHON_EXEC: Final[str] = "python"


class CliHttpHelper:
    """Wrapper class for MPS CLI HttpHelper"""

    http_helper_: Optional[HttpHelper] = None

    @classmethod
    def create(cls, http_helper: HttpHelper):
        """Create the authenticator singleton"""
        if cls.http_helper_ is None:
            cls.http_helper_ = http_helper
        else:
            raise RuntimeError("Http helper already created")

    @classmethod
    def get(cls):
        """Get the authenticator singleton"""
        return cls.http_helper_


class CliAuthHelper:
    """Wrapper class for MPS CLI Authenticator"""

    # OAuth FRL|App ID| Client Token
    _CLIENT_TOKEN: Final[str] = "FRL|1651773608907002|93a02e233037a10b41cdc2648f648ef4"
    # OC App ID
    _CLIENT_APPLICATION: Final[int] = 7496476603813560

    authenticator_: Optional[Authenticator] = None

    @classmethod
    async def create(cls, http_helper: HttpHelper):
        """Create the authenticator singleton"""
        if cls.authenticator_ is None:
            cls.authenticator_ = Authenticator(
                http_helper=http_helper,
                client_token=cls._CLIENT_TOKEN,
                client_app=cls._CLIENT_APPLICATION,
            )

            # Persisted token from MPS CLI will work for Aria Studio and other way around too.
            # We can assume that people working with one of these apps won't work with the other.
            if await cls.authenticator_.load_and_validate_token():
                logger.info("Successfully loaded token")
                http_helper.set_auth_token(cls.get().auth_token)
        else:
            raise RuntimeError("Authenticator already created")

    @classmethod
    def get(cls):
        """Get the authenticator singleton"""
        return cls.authenticator_


def login_required(func):
    """Decorator to check if the user is logged in before running a function"""

    @wraps(func)
    async def decorated_function(*args, **kwargs):
        if CliAuthHelper.get().is_logged_in():
            return await func(*args, **kwargs)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return decorated_function


@log_exceptions
async def run_and_forget(cmd: List[str]):
    """This function is used to run the process and print the stdout/stderr"""
    logger.debug(f"Running command: {' '.join(cmd)}")

    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    logger.debug(f"Output: {stdout.decode()}")
    logger.debug(f"Stderr: {stderr.decode()}")

    if process.returncode != 0:
        logger.error(f"Error running command: {cmd}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This context manager is used to start up the aria studio server and shut it down
    when the context manager exits, which is usually at the end of the application.
    This is the recommended way to do startup and shutdown events
    """
    args = Args.get_args()
    ## Setup adb path
    if args.use_system_adb:
        adb_path = Path(shutil.which("adb"))
        if adb_path is None:
            raise RuntimeError("adb not found on system")
    else:
        system_name = platform.system()
        print(f"Starting up Aria Studio on {system_name}")

        # The adb path is relative to the project root
        adb_path = (
            Path(__file__).resolve().parent.parent
            / "tools"
            / system_name.lower()
            / "adb"
        )
        if system_name == "Windows":
            adb_path = adb_path.with_suffix(".exe")

    print(f"Using adb path: {adb_path}")
    instance = DeviceManager.get_instance()
    instance.set_adb_path(adb_path)

    if args.browser:
        # Start a new thread to open the browser after a short delay
        threading.Timer(
            1.0, webbrowser.open, args=[f"http://{LOCALHOST}:{args.port}"]
        ).start()

    async with HttpHelper() as http_helper:
        CliHttpHelper.create(http_helper)
        await CliAuthHelper.create(http_helper)
        yield
    logger.info("*****************Shutting down Aria Studio*********")
    HTTP_HELPER = None  # noqa: F841


def get_db_path() -> str:
    """Get the database path based on the logged in user alias"""
    db_path = CONFIG_DIR / CliAuthHelper.get().user / ARIA_STUDIO_DB
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


class MpsConfigParser(ConfigParser):
    """Custom ConfigParser class to handle the DEFAULT section, covert ini to json and update to ini"""

    def options(self, section: str, no_defaults: bool = False, **kwargs) -> List[str]:
        """To get options() without defaults"""
        if no_defaults:
            try:
                return list(self._sections[section].keys())
            except KeyError:
                raise NoSectionError(section)
        else:
            return super().options(section, **kwargs)

    def ini_to_json(self) -> dict:
        """Convert the config object to a dictionary"""
        dictionary = {}
        for section in self.sections():
            dictionary[section] = {}
            for option in self.options(section, no_defaults=True):
                dictionary[section][option] = self.get(section, option)
        # add default section to the dictionary
        default_section = self.default_section
        dictionary[default_section] = self.defaults()
        return dictionary

    def update_to_ini(self, updated_config: dict[str, dict]) -> None:
        """Update the config object with the new values from the request"""

        # update default section of config object
        default_section = self.default_section
        if default_section in updated_config:
            for key, value in updated_config[default_section].items():
                self.set(default_section, key, str(value))
            # remove the default section from the updated_config for further processing
            updated_config.pop(default_section)

        # Update the config object with the new values
        for section, section_config in updated_config.items():
            for key, value in section_config.items():
                self.set(section, key, str(value))
        # Write the updated config to the mps.ini file
        with open(CONFIG_FILE, "w") as f:
            self.write(f)
