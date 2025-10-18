# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

# pyre-strict

import importlib.resources
import logging
import os
import platform
import signal
import subprocess
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Dict, Final, Optional

import pytest

__ENV_CHROME: Final[str] = "CHROME_EXEC_PATH"
__PLAYWRIGHT_CHROME_BIN: Final[str] = "executable_path"

__AS_SCRIPT: Final[str] = "aria_studio"
__AS_RUNNING_INFO: Final[str] = (
    "[INFO] Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)"
)

__logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def start_aria_studio() -> None:
    """
    Starts Aria Studio and waits until it is ready to serve requests.
    """

    script_file: AbstractContextManager[Path] = importlib.resources.path(
        __package__, __AS_SCRIPT
    )
    with script_file as script_path:
        if not script_path.exists():
            raise RuntimeError(f"Cannot find Aria Studio at {__AS_SCRIPT}")

    script_path: str = str(script_path)
    __logger.info(f">>>> Starting Aria Studio from {str(script_path)}")
    aria_studio = subprocess.Popen(
        [script_path, "--no-browser"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    while True:
        line: str = aria_studio.stdout.readline().decode("utf-8")
        if __AS_RUNNING_INFO in line:
            break

    __logger.info("<<<< Aria Studio has started")

    yield

    __logger.info(">>>> Test complete, closing Aria Studio")

    aria_studio.send_signal(
        signal.CTRL_C_EVENT if platform.system() == "Windows" else signal.SIGINT
    )
    _stdout, _stderr = aria_studio.communicate()

    __logger.info("<<<< Aria Studio has stopped")


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args) -> Dict:
    """
    Overrides browser_type_launch_args hook from pytest_playwright. Provides:
    - custom path to the headless Chrome binary through the dictionery returned from function,
    - custom paths to NodeJS binary and CLI library through environemnt variables
      set up in setup_playwright hook.

    Parameters
        browser_type_launch_args : Callable - hook from pytest_playwright.

    Returns
        Dict - dictionary with arguments to be passed to browser_type.launch() function in  pytest_playwright.

    Raises
        RuntimeError - if Chrome installation cannot be found.
    """

    if __ENV_CHROME not in os.environ:
        raise RuntimeError(
            """
This is local execution environment. Please install headless chrome from npm with:
~/fbsource/xplat/third-party/node/bin/npx @puppeteer/browsers install chrome-headless-shell@stable

Remember to not commit these changes. If you want to keep headless Chrome permanently, please install it 
outside fbsource and set the CHROME_EXEC_PATH environment variable to the output path:
export CHROME_EXEC_PATH=<path to chrome executable>
            """
        )
    else:
        chrome_exec_path: str = os.environ[__ENV_CHROME]

    return {**browser_type_launch_args, __PLAYWRIGHT_CHROME_BIN: chrome_exec_path}


@pytest.fixture(scope="session")
def base_url() -> str:
    """
    Implements base_url hook from pytest_playwright.

    Returns
        str - base URL for the test server.
    """

    return "http://127.0.0.1:8000"
