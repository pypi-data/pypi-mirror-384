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
import os
import sys

from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import current_thread, Event, Thread
from typing import Final, Optional
from uuid import uuid4

import rerun as rr
from aria_studio.app.local.local_log_manager import (
    LocalLogEntry,
    LocalLogEvent,
    LocalLogManager,
    LocalLogScreen,
    LocalLogSurface,
)
from aria_studio.app.singleton_base import SingletonBase
from aria_studio.app.utils import run_and_forget

DEFAULT_MEMORY_LIMIT: Final[str] = "2GB"

logger = logging.getLogger(__name__)


class RerunTaskBase(ABC):
    """
    An abstract class representing a task that can be logged to Rerun.
    Performs actual visualization logic.
    """

    @abstractmethod
    def log_to_rerun(self, stop_event: Event) -> None:
        """
        Actual implementation of the visualization logic. This method will be called by the
        start_viewer method in a separate thread.

        Args:
            stop_event: An event object that can be used to verify, if task is stopped.
        """

        pass


class RerunManager(metaclass=SingletonBase):
    """
    A base class managing rerun playback of a single type. Implemented as a singleton to avoid
    conflicts with mutliple processes accessing the same rerun instance.
    """

    def __init__(self):
        self._current_thread: Optional[Thread] = None
        self._stop_event: Event = Event()
        self._thread_pool: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=1)

        self._start: Optional[float] = None
        self._screen: Optional[LocalLogScreen] = None

    async def start_viewer(
        self,
        task: RerunTaskBase,
        memory_limit: str = DEFAULT_MEMORY_LIMIT,
    ) -> None:
        """
        Initialize the Rerun viewer's thread and start streaming data to it
        """
        from aria_studio.utils.vrs_rerun_task import VrsRerunTask

        self._start = datetime.now().timestamp()
        self._screen = (
            LocalLogScreen.FILES
            if isinstance(task, VrsRerunTask)
            else LocalLogScreen.GROUPS
        )
        await LocalLogManager.log(
            event=LocalLogEvent.VISUALIZATION,
            screen=self._screen,
            message=f"Running rerun task {task}",
        )
        logger.info(f"Running rerun task {task}")

        # Clean up any existing thread first
        await self.cleanup()

        self._stop_event.clear()

        def wrapped_start_rerun():
            try:
                rr.init("Aria Studio VRS Player", recording_id=uuid4())
                # Create a empty blueprint and send it to the viewer to reset the view
                my_blueprint = rr.blueprint.Blueprint()
                rr.send_blueprint(my_blueprint, make_active=True)
                if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
                    # If running in a PyInstaller bundle, we use the bundled rerun binary to connect to it
                    rr.connect()
                else:
                    rr.spawn(memory_limit=memory_limit)
                # open in the browser: http://localhost:9090/?url=ws://localhost:9877
                # rr.serve(
                #     open_browser=False
                #     # default ports, can be redefined
                #     # web_port=9090,
                #     # ws_port=9877
                # )

                # Call the class method directly
                task.log_to_rerun(self._stop_event)
            except Exception as e:
                logger.error(f"Rerun viewer failed: {e}")
            finally:
                try:
                    rr.disconnect()
                except Exception as e:
                    logger.error(f"Error during rerun disconnect: {e}")
                self._stop_event.set()

        # Use ThreadPoolExecutor for better management
        self._thread_pool.submit(wrapped_start_rerun)
        self._current_thread = current_thread()

    async def cleanup(self):
        """
        Cleanup any existing viewer thread
        """

        if self._start is not None:
            end: float = datetime.now().timestamp()
            await LocalLogManager.log_event(
                LocalLogEntry(
                    timestamp=int(end),
                    surface=LocalLogSurface.BACK_END,
                    event=LocalLogEvent.VISUALIZATION,
                    screen=self._screen,
                    message=f"Closed preview in {self._screen.value}",
                    duration=(end - self._start),
                )
            )
        self._start = None
        self._screen = None

        if self._current_thread and self._current_thread.is_alive():
            self._stop_event.set()
            # Give the thread a chance to cleanup
            await asyncio.sleep(0.5)

            # Force cleanup if still alive
            if self._current_thread.is_alive():
                logger.warning("Force cleaning up Rerun viewer thread")
                self._thread_pool.shutdown(wait=False)
                self._thread_pool = ThreadPoolExecutor(max_workers=1)

    async def start_frozen_rerun(self):
        """
        Start the rerun viewer binary in the frozen application
        Rerun viewer is a separate binary that is bundled with the frozen application.
        To use this binary, we run the bundled one and to view the data, we connect to it.
        """
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            rerun_binary_path = os.path.join(
                sys._MEIPASS, "rerun_sdk", "rerun_cli", "rerun"
            )
            if sys.platform == "win32":
                rerun_binary_path += ".exe"
            command = [
                rerun_binary_path,
                "--memory-limit",
                DEFAULT_MEMORY_LIMIT,
            ]
            # Explicitly set the renderer to Vulkan on Linux to avoid the rerun viewer crashing
            if sys.platform == "linux":
                command += ["--renderer=vulkan"]
            logger.debug("Starting rerun binary in frozen application")
            logger.debug(f"Running command here: {' '.join(command)}")
            asyncio.create_task(
                run_and_forget(command),
                name="start_frozen_rerun",
            )
