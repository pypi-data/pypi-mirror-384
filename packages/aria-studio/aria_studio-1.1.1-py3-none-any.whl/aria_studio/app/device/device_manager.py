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
import json
import logging
import re
import shutil
import subprocess
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Final, List, Optional, Set, Tuple, Union

from aria_studio.app.common.disk_cache import DiskCache
from aria_studio.app.common.types import (
    AriaError,
    AriaException,
    CopyStatus,
    DeviceStatus,
    DiskStats,
    to_error_message,
)
from aria_studio.app.constants import (
    DEVICE_CACHE_DIR,
    THUMBNAIL_GIF,
    THUMBNAIL_JPEG,
    WIN32,
)
from aria_studio.app.local.local_file_manager import LocalFileManager

from PIL import Image
from projectaria_tools.aria_mps_cli.cli_lib.common import log_exceptions

logger = logging.getLogger(__name__)

_ARIA_RECORDINGS_ROOT: Final[Path] = Path("/sdcard/recording")
_ARIA_THUMBNAILS_ROOT: Final[Path] = _ARIA_RECORDINGS_ROOT / "thumbnails"
_VRS_EXT: Final[str] = ".vrs"
_DEVICE_MONITOR_INTERVAL: Final[int] = 5
_ARIA_DEVICE_IDENTIFIER: Final[str] = "product:gemini model:Aria device:gemini"


class DeviceManager:
    """
    The class to manage the interaction with the Aria Device
    * Pull files from the device.
    * Delete files from the device.
    * List files on the device.
    * Fetch device status
        * Fetch Wi-Fi SSID
        * Fetch Bluetooth device name
        * Fetch battery status
    * Fetch thumbnails
    """

    __MODE_PARTNER: Final[str] = "partner"
    __MODE_RESEARCH: Final[str] = "research"

    _adb_path: Optional[Path] = None

    _instance: Optional["DeviceManager"] = None

    @classmethod
    def get_instance(cls):
        """Get the individual mps request manager singleton."""
        if cls._instance is None:
            logger.debug("Creating device manager")
            cls._instance = DeviceManager()
        return cls._instance

    @classmethod
    def set_adb_path(cls, adb_path: Path):
        """Set the path to adb executable."""
        if not adb_path.is_file():
            raise FileNotFoundError(f"adb path {str(adb_path)} does not exist")
        cls._adb_path = adb_path

    def __init__(self, max_concurrent_pulls: int = 1):
        self._copy_tasks: Set[asyncio.Task] = set()
        self._vrs_files_to_copy: List[Path] = []
        self._destination: Path = Path()
        self._semaphore: asyncio.Semaphore = asyncio.Semaphore(max_concurrent_pulls)
        self._copy_lock: asyncio.Lock = asyncio.Lock()
        self._copy_status: CopyStatus = CopyStatus()
        self._disk_cache: DiskCache = DiskCache(DEVICE_CACHE_DIR)
        self._device_monitor: asyncio.Task = asyncio.create_task(
            self.device_heartbeat()
        )
        self._is_connected: bool = False

    @property
    def cache(self):
        return self._disk_cache

    async def check_device_connected(self):
        """Check if the device is connected."""
        from aria_studio.app.local.local_log_manager import (
            LocalLogEvent,
            LocalLogManager,
            LocalLogScreen,
        )

        stdout, _stderr = await self._adb_command(["devices", "-l"])
        if _ARIA_DEVICE_IDENTIFIER not in stdout.decode("UTF-8"):
            if self._is_connected:
                self._is_connected = False
                await LocalLogManager.log(
                    event=LocalLogEvent.CONNECT_GLASSES,
                    screen=LocalLogScreen.SIDEBAR,
                    message="Device disconnected",
                )
            raise AriaException(AriaError.DEVICE_NOT_CONNECTED, "Device not connected")

        if not self._is_connected:
            self._is_connected = True
            await LocalLogManager.log(
                event=LocalLogEvent.CONNECT_GLASSES,
                screen=LocalLogScreen.SIDEBAR,
                message="Device connected",
            )

    @log_exceptions
    async def device_heartbeat(self):
        """
        Monitor the device status periodically and clear the cache if the device has
        been disconnected.
        """
        while True:
            try:
                await asyncio.sleep(_DEVICE_MONITOR_INTERVAL)
                # Ensure device connection
                await self.check_device_connected()
            except asyncio.CancelledError:
                # Clear the cache
                self._disk_cache.clear()
                # closing, leave the loop
                break
            except Exception:
                # Clear the cache
                self._disk_cache.clear()

    async def get_status(self) -> DeviceStatus:
        """Get the status of the device"""
        # Ensure device connection
        await self.check_device_connected()

        # Query device status concurrently
        status_tasks = [
            self._adb_command(
                ["shell", "getprop", "ro.serialno"], AriaError.GET_STATUS_FAILED
            ),
            self._adb_command(
                ["shell", "getprop", "ro.product.model"], AriaError.GET_STATUS_FAILED
            ),
            self._adb_command(
                ["shell", "dumpsys", "battery"], AriaError.GET_STATUS_FAILED
            ),
            self._adb_command(
                ["shell", "dumpsys", "wifi"], AriaError.GET_STATUS_FAILED
            ),
            self._adb_command(
                ["shell", "dumpsys", "diskstats", "|", "grep", "^Data"],
                AriaError.GET_STATUS_FAILED,
            ),
            self._adb_command(
                ["shell", "getprop", "ro.boot.devicemode"],
                AriaError.GET_STATUS_FAILED,
            ),
        ]

        status_results = await asyncio.gather(*status_tasks, return_exceptions=True)
        for result in status_results:
            if isinstance(result, AriaException):
                raise result
        serial_stdout, _ = status_results[0]
        model_stdout, _ = status_results[1]
        battery_stdout, _ = status_results[2]
        wifi_stdout, _ = status_results[3]
        diskstats_stdout, _ = status_results[4]
        device_mode_stdout, _ = status_results[5]

        # Get Serial number
        serial_number: str = serial_stdout.decode("UTF-8").strip()
        device_model: str = model_stdout.decode("UTF-8").strip()
        is_research_mode: bool = (
            device_mode_stdout.decode("UTF-8").strip() == self.__MODE_RESEARCH
        )

        # Get battery level
        match = re.search(r"level: (\d+)", battery_stdout.decode("UTF-8"))
        battery_level: int = int(match.group(1) if match else 0)

        # Get Wi-Fi SSID
        match = re.search(r"^ssid=(.*)$", wifi_stdout.decode("UTF-8"), re.MULTILINE)
        wifi_ssid: Optional[str] = match.group(1) if match else None

        diskstats: str = diskstats_stdout.decode("UTF-8")
        free_space, total_space = diskstats.split(":")[1].split("total")[0].split("/")
        diskstats: DiskStats = DiskStats(
            free_space=free_space.strip(), total_space=total_space.strip()
        )

        return DeviceStatus(
            serial_number=serial_number,
            model=device_model,
            wifi_ssid=wifi_ssid,
            battery_level=battery_level,
            diskstats=diskstats,
            import_in_progress=bool(
                self._copy_tasks and any(not task.done() for task in self._copy_tasks)
            ),
            is_research_mode=is_research_mode,
        )

    @log_exceptions
    async def delete_files(self, vrs_files: List[str]) -> None:
        """Delete files from the device."""
        # Delete vrs files
        vrs_and_metadata_files: List[Path] = [
            Path(_ARIA_RECORDINGS_ROOT, f"{f}*").as_posix() for f in vrs_files
        ]
        thumbnails: List[Path] = [
            (_ARIA_THUMBNAILS_ROOT / f"{Path(f).stem}*").as_posix() for f in vrs_files
        ]
        try:
            await self._adb_command(
                ["shell", "rm"] + vrs_and_metadata_files + thumbnails,
                AriaError.DELETE_FAILED,
            )
        except AriaException as e:
            if e.error_code == AriaError.DELETE_FAILED:
                logger.debug("No files found on device")
            else:
                raise

    @log_exceptions
    async def list_vrs_files(self) -> List[Path]:
        """List recordings on the device."""
        try:
            vrs_path: Path = Path(_ARIA_RECORDINGS_ROOT) / f"*{_VRS_EXT}"
            stdout, stderr = await self._adb_command(
                ["shell", "ls", vrs_path.as_posix()],
                AriaError.LIST_RECORDING_FAILED,
            )
        except AriaException as e:
            if e.error_code == AriaError.LIST_RECORDING_FAILED:
                logger.debug("No vrs files found on device")
                return []
            else:
                raise
        return [Path(p) for p in stdout.decode().splitlines()]

    async def _pull_file(
        self, file_path: Path, destination: Path, compress: bool = False
    ) -> Tuple[str, str]:
        """Pull a single file from the device."""
        return await self._adb_command(
            ["pull", file_path, destination], AriaError.PULL_FAILED
        )

    @log_exceptions
    async def get_thumbnail_jpeg(self, vrs_file: str) -> Path:
        """Get first thumbnail for the VRS file from ."""
        thumbnail_path = self._disk_cache.get_cache_dir(vrs_file) / THUMBNAIL_JPEG
        if thumbnail_path.exists():
            return thumbnail_path

        thumbnails: List[Path] = await self._list_thumbnails(vrs_file)
        # Copy any one thumbnail
        for thumbnail in thumbnails:
            try:
                img_data: str = await self._shell_cat(thumbnail.as_posix())
                Image.open(BytesIO(img_data)).rotate(-90).save(thumbnail_path)
                return thumbnail_path
            except Exception as e:
                logger.exception(e)
                continue
        # Couldn't copy a thumbnail
        raise AriaException(
            AriaError.THUMBNAIL_NOT_FOUND, f"No thumbnail found for {vrs_file}"
        )

    @log_exceptions
    async def get_thumbnail_gif(self, vrs_file: str) -> str:
        """Pull thumbnails and create a gif file from the thumbnails."""
        thumbnail_path = self._disk_cache.get_cache_dir(vrs_file) / THUMBNAIL_GIF
        if thumbnail_path.exists():
            return thumbnail_path

        thumbnails: List[Path] = await self._list_thumbnails(vrs_file)
        if not thumbnails:
            raise FileNotFoundError(f"No thumbnails found for {vrs_file}")
        # Read each thumbnail, rotate it and then add to gif
        rotated_images: List[Image] = []
        for thumbnail in thumbnails:
            try:
                img_data: str = await self._shell_cat(thumbnail)
                rotated_images.append(
                    Image.open(BytesIO(img_data)).rotate(-90).convert("RGBA")
                )
            except Exception as e:
                logger.exception(e)
                continue
        if not rotated_images:
            raise AriaException(
                AriaError.GIF_GENERATE_FAILED,
                f"Failed to generate gif for {vrs_file}",
            )
        rotated_images[0].save(
            thumbnail_path.as_posix(),
            save_all=True,
            append_images=rotated_images[1:],
            duration=500,  # Duration between frames in milliseconds
            loop=0,  # Loop forever
        )
        return thumbnail_path.as_posix()

    @log_exceptions
    async def get_metadata(self, vrs_file: str) -> Path:
        """Pull metadata file from device."""
        try:
            metadata = await self._shell_cat(
                Path(_ARIA_RECORDINGS_ROOT / f"{vrs_file}.json").as_posix(),
                AriaError.METADATA_READ_FAILED,
            )
            return json.loads(metadata.decode("UTF-8"))
        except json.JSONDecodeError:
            raise AriaException(
                AriaError.METADATA_READ_FAILED, "Not a valid json metadata"
            )
        return None

    async def _shell_cat(
        self, file_path: Path, error_code: Optional[AriaError] = None
    ) -> str:
        """Helper to run adb exec-out cat command to read binary files"""
        command = ["exec-out", "cat", Path(file_path).as_posix()]
        stdout, _stderr = await self._adb_command(command, error_code=error_code)
        return stdout

    async def _list_thumbnails(self, vrs_file: str) -> List[Path]:
        """List thumbnails for a VRS file."""
        thumbnail_pattern: str = f"{vrs_file[:-4]}_*.jpeg"
        # Return the modified path with the new stem and the .jpg extension
        thumbnail_path_on_aria: Path = _ARIA_THUMBNAILS_ROOT / thumbnail_pattern

        if sys.platform == WIN32:
            stdout, stderr = await self._adb_command_in_cmd(
                ["shell", "ls", thumbnail_path_on_aria.as_posix()],
                AriaError.LIST_THUMBNAIL_FAILED,
            )
        else:
            stdout, stderr = await self._adb_command(
                ["shell", "ls", thumbnail_path_on_aria.as_posix()],
                AriaError.LIST_THUMBNAIL_FAILED,
            )
        if not stdout:
            raise AriaException(AriaError.THUMBNAIL_NOT_FOUND)
        return [Path(p) for p in stdout.decode().splitlines()]

    #
    # Apis to copy files from device to local
    #
    @log_exceptions
    async def start_copy_vrs_files(
        self,
        vrs_files: List[str],
        destination: Path,
        delete_src_after_copy: bool = False,
    ):
        """Start copying files asynchronously."""
        from aria_studio.app.local.local_log_manager import (
            LocalLogEntry,
            LocalLogEvent,
            LocalLogManager,
            LocalLogScreen,
            LocalLogSurface,
        )

        start_import_time: float = datetime.now().timestamp()
        async with self._copy_lock:
            if self._copy_tasks and any(not task.done() for task in self._copy_tasks):
                error_code = AriaError.VRS_PULL_IN_PROGRESS
                await LocalLogManager.log(
                    event=LocalLogEvent.IMPORT_RECORDING,
                    screen=LocalLogScreen.GLASSES,
                    message="Import of VRS file was cancelled because another import is in progress",
                )
                raise AriaException(error_code, to_error_message(error_code))

            self._copy_status = CopyStatus()
            for vrs_file in vrs_files:
                if not vrs_file.endswith(_VRS_EXT):
                    await LocalLogManager.log(
                        event=LocalLogEvent.IMPORT_RECORDING,
                        screen=LocalLogScreen.GLASSES,
                        message=f"Import of VRS file {vrs_file} failed because it is not a VRS file",
                    )
                    raise AriaException(
                        AriaError.NOT_A_VRS_FILE, f"{vrs_file} is not a VRS file"
                    )

                logger.debug(f"Checking if {vrs_file} exists locally at {destination}")
                if (destination / vrs_file).exists():
                    await LocalLogManager.log(
                        event=LocalLogEvent.IMPORT_RECORDING,
                        screen=LocalLogScreen.GLASSES,
                        message=f"Import of VRS file {vrs_file} failed because it already exists locally at {destination}",
                    )
                    raise FileExistsError(
                        f"{vrs_file} already exists locally at {destination}"
                    )

            # It is now safe to start copying the files
            self._vrs_files_to_copy = [
                (_ARIA_RECORDINGS_ROOT / vrs_file).as_posix() for vrs_file in vrs_files
            ]
            total_bytes = await self._get_total_size(self._vrs_files_to_copy)
            self._copy_status.total_bytes = total_bytes
            self._copy_status.total_files = len(self._vrs_files_to_copy)
            logger.debug(f"Total size of files to copy: {total_bytes}")
            self._destination = destination
            self._copy_monitor_task: asyncio.Task = asyncio.create_task(
                self._copy_monitor(
                    self._vrs_files_to_copy,
                    destination,
                    delete_src_after_copy,
                )
            )

        end_import_time: float = datetime.now().timestamp()
        await LocalLogManager.log_event(
            LocalLogEntry(
                timestamp=int(end_import_time),
                surface=LocalLogSurface.BACK_END,
                event=LocalLogEvent.IMPORT_RECORDING,
                screen=LocalLogScreen.GLASSES,
                message=f"{len(vrs_files)} VRS files copied from ARIA Device to {destination} with delete_src_after_copy flag set to {delete_src_after_copy}",
                source=LocalLogEntry.get_caller(),
                duration=end_import_time - start_import_time,
                file_size=total_bytes,
            )
        )

    async def _copy_monitor(
        self,
        vrs_files_to_copy: List[str],
        destination: Path,
        delete_src_after_copy: bool,
    ):
        """
        Start and monitor the copy operation.
        This is a coroutine that runs in the background and updates progress.
        """

        for vrs_file in self._vrs_files_to_copy:
            destination_path_with_name: Path = destination / Path(vrs_file).name
            t = asyncio.create_task(
                self._copy_vrs_and_metadata(
                    Path(vrs_file),
                    destination_path_with_name,
                    delete_src_after_copy,
                ),
                name=f"Copying {vrs_file}",
            )
            self._copy_tasks.add(t)
            t.add_done_callback(self._copy_tasks.discard)
        try:
            await asyncio.gather(*self._copy_tasks)
        except Exception:
            await self.cancel_copy()

    @log_exceptions
    async def cancel_copy(self):
        """
        Cancel the current copy operation and clean up partial files.
        Handles ADB connection issues and ensures proper cleanup of temporary files.

        Raises:
            AriaException: If no copy is in progress or if the cancellation fails
        """
        if not self._copy_tasks:
            error_code = AriaError.VRS_PULL_NOT_STARTED
            raise AriaException(error_code, to_error_message(error_code))

        logger.debug("Starting import cancellation")

        # Track which files need cleanup
        partial_files = []
        try:
            # Identify any partial files that need cleanup
            for vrs_path in self._vrs_files_to_copy:
                file_path: Path = Path(vrs_path)
                local_path: Path = self._destination / file_path.name
                partial_path: Path = local_path.with_suffix(".partial")

                if partial_path.exists():
                    partial_files.append(partial_path)

                # Also check for partial metadata files
                metadata_partial = local_path.with_suffix(".vrs.json.partial")
                if metadata_partial.exists():
                    partial_files.append(metadata_partial)

            # Cancel all ongoing copy tasks
            for task in self._copy_tasks:
                if not task.done():
                    task.cancel()

            try:
                # Wait for tasks to clean up, with a timeout
                await asyncio.wait_for(
                    asyncio.gather(*self._copy_tasks, return_exceptions=True),
                    timeout=5.0,
                )
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for copy tasks to cancel")
                # Continue with cleanup even if tasks timeout

            # Clean up any partial files
            self._cleanup_partial_files(partial_files)

            # Reset copy status
            self._copy_status = CopyStatus()
            self._copy_tasks.clear()

            logger.debug("Import cancelled successfully")

        except asyncio.CancelledError:
            logger.debug("Cancel operation itself was cancelled")
            # Still attempt cleanup
            for partial_file in partial_files:
                try:
                    if partial_file.exists():
                        partial_file.unlink()
                except Exception:
                    pass
            raise

        except Exception as e:
            logger.error(f"Error during cancel operation: {str(e)}")
            # Check if it's an ADB failure
            if isinstance(e, AriaException) and e.error_code == AriaError.PULL_FAILED:
                logger.debug("ADB pull operation failed during cancel")
                # Still clean up partial files
                self._cleanup_partial_files(partial_files)
                raise

            # Raise a generic AriaException for other errors
            error_code = AriaError.CANCEL_FAILED
            raise AriaException(
                error_code, f"Failed to cancel import operation: {str(e)}"
            )

    @log_exceptions
    def _cleanup_partial_files(self, partial_files: List[Path]) -> None:
        """
        Clean up partial files.
        """
        for partial_file in partial_files:
            try:
                partial_file.unlink()
                logger.debug(f"Cleaned up partial file: {partial_file}")
            except Exception as e:
                logger.error(
                    f"Failed to clean up partial file {partial_file}: {str(e)}"
                )

    @log_exceptions
    async def get_copy_progress(self) -> CopyStatus:
        """Get the copy progress."""
        await self.check_device_connected()

        if self._copy_tasks and any(not task.done() for task in self._copy_tasks):
            copied_bytes = 0
            for file_path in self._vrs_files_to_copy:
                file_path: Path = Path(file_path)
                local_path: Path = self._destination / file_path.name
                local_path_partial: Path = local_path.with_suffix(".partial")
                if local_path.exists():
                    copied_bytes += local_path.stat().st_size
                elif local_path_partial.exists():
                    copied_bytes += local_path_partial.stat().st_size
            self._copy_status.copied_bytes = copied_bytes

        return self._copy_status

    @log_exceptions
    async def _copy_vrs_and_metadata(
        self, device_vrs_path: Path, local_vrs_path: Path, delete_src: bool
    ):
        """
        Copy a single vrs file from device to local along with the metadata file.
        The file is copied to a .partial file and then renamed.
        Optionally delete the file from device if delete_src is True.
        """
        from aria_studio.app.local.local_log_manager import (
            LocalLogEntry,
            LocalLogEvent,
            LocalLogManager,
            LocalLogScreen,
            LocalLogSurface,
        )

        start_import_time: float = datetime.now().timestamp()
        async with self._semaphore:
            logger.debug(f"Start copying {device_vrs_path} to {local_vrs_path}")
            self._copy_status.current_files.append(device_vrs_path.as_posix())

            async def __copy_file(device_file_path: Path, local_file_path: Path):
                """Copy a single file from device to local."""
                temp_dest_file: Path = local_file_path.with_suffix(".partial")
                await self._pull_file(device_file_path.as_posix(), temp_dest_file)
                temp_dest_file.rename(local_file_path)
                logger.debug(
                    f"Done copying {device_file_path.as_posix()} to {local_file_path}"
                )

            try:
                logger.debug(f"Copying {device_vrs_path} to {local_vrs_path}")
                await __copy_file(device_vrs_path, local_vrs_path)
                logger.debug(f"Copying metadata {device_vrs_path} to {local_vrs_path}")
                await __copy_file(
                    device_vrs_path.with_suffix(".vrs.json"),
                    local_vrs_path.with_suffix(".vrs.json"),
                )
                # This will save us file opening to create a thumbnail after the import
                # is complete.
                logger.debug(f"Copying thumbnail {device_vrs_path} to {local_vrs_path}")
                await self._copy_thumbnail_from_device_cache_to_local_file_cache(
                    device_vrs_path, local_vrs_path
                )
                self._copy_status.copied_files.append(local_vrs_path)
                self._copy_status.current_files.remove(device_vrs_path.as_posix())

                end_import_time: float = datetime.now().timestamp()
                file_size: int = local_vrs_path.stat().st_size
                await LocalLogManager.log_event(
                    LocalLogEntry(
                        timestamp=int(end_import_time),
                        surface=LocalLogSurface.BACK_END,
                        event=LocalLogEvent.IMPORT_RECORDING,
                        screen=LocalLogScreen.GLASSES,
                        message=f"Copied {device_vrs_path} VRS Recording of size {file_size}",
                        source=LocalLogEntry.get_caller(),
                        duration=end_import_time - start_import_time,
                        file_size=file_size,
                    )
                )

                if delete_src:
                    logger.debug(f"Deleting {device_vrs_path} from device")
                    try:
                        await self.delete_files([device_vrs_path.as_posix()])
                        self._copy_status.deleted_files.append(device_vrs_path)
                        logger.debug(f"Done deleting {device_vrs_path} from device")
                    except AriaException as e:
                        logger.exception(e)
                        # Swallow the exception and move on
                        logger.error(f"Failed to delete {device_vrs_path} from device")
            except asyncio.CancelledError:
                logger.error(f"Copy of {device_vrs_path} to {local_vrs_path} cancelled")
                raise
            except AriaException as e:
                logger.error(
                    f"Copy of {device_vrs_path.as_posix()} to {local_vrs_path} failed with {e.error_code}, {str(e)}"
                )
                self._copy_status.error = str(e)
                self._copy_status.error_files.append(device_vrs_path)
                raise

    async def _copy_thumbnail_from_device_cache_to_local_file_cache(
        self, device_vrs_path: Path, local_vrs_path: Path
    ) -> None:
        """
        Copy thumbnail from device cache.
        If thumbnail is not found, then no action.
        """

        try:
            thumbnail_path_device_cache = await self.get_thumbnail_jpeg(
                Path(device_vrs_path).name
            )
        except Exception as e:
            # Eat this exception as we don't want to fail the whole copy operation
            logger.error(e)
            logger.error(f"No thumbnail found for {device_vrs_path}")
            return

        # Copy the file from device cache to local
        file_manager = LocalFileManager.get_instance()
        thumbnail_path_local_cache = file_manager.cache.get_cache_dir(local_vrs_path)
        try:
            # Copy the file
            shutil.copy2(
                str(thumbnail_path_device_cache), str(thumbnail_path_local_cache)
            )
            logger.debug(
                f"File copied from {thumbnail_path_device_cache} to {thumbnail_path_local_cache}"
            )
        except Exception as e:
            logger.error(f"Error during thumbnail copy: {e}")

    async def _get_total_size(self, vrs_files: List[Path]) -> int:
        """Get the total size of files in a list."""
        total_size: int = 0
        size_tasks = [
            self._adb_command(["shell", "stat", "-c", "%s", vrs_file])
            for vrs_file in vrs_files
        ]

        results: List[Tuple[str, str] | BaseException] = await asyncio.gather(
            *size_tasks, return_exceptions=True
        )
        if any(isinstance(e, BaseException) for e in results):
            raise AriaException(
                AriaError.VRS_NOT_FOUND, to_error_message(AriaError.VRS_NOT_FOUND)
            )

        for stdout, _ in results:
            total_size += int(stdout.strip())
        return total_size

    async def _adb_command(
        self,
        command: List[str],
        error_code: AriaError = AriaError.GENERIC_DEVICE_ERROR,
    ) -> Tuple[str, str]:
        """Helper to execute adb command asynchronously."""
        command = [str(self._adb_path)] + [str(cmd) for cmd in command]
        process = await asyncio.create_subprocess_exec(
            *command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout_str = b""
        stderr_str = b""
        try:
            stdout_str, stderr_str = await process.communicate()
        except asyncio.CancelledError:
            logger.debug(f"Killing {command}")
            process.terminate()
            await process.wait()
            logger.debug(f"Killed {command}")
        if process.returncode != 0:
            stdout_str = stdout_str.decode("UTF-8")
            stderr_str = stderr_str.decode("UTF-8")
            logger.error(f"{command} failed with {process.returncode}")
            logger.error(f"stdout: {stdout_str}")
            logger.error(f"stderr: {stderr_str}")
            try:
                await self.check_device_connected()
            except AriaException:
                error_code = AriaError.DEVICE_NOT_CONNECTED
            raise AriaException(error_code, to_error_message(error_code))
        return stdout_str, stderr_str

    async def _adb_command_in_cmd(
        self,
        command: List[str],
        error_code: AriaError = AriaError.GENERIC_DEVICE_ERROR,
    ) -> Tuple[Union[str, bytes], Union[str, bytes]]:
        """Execute ADB command through CMD and return stdout/stderr."""
        try:
            full_command = ["cmd", "/c", str(self._adb_path)] + [
                str(cmd) for cmd in command
            ]

            process = await asyncio.create_subprocess_exec(
                *full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            stdout_data, stderr_data = await process.communicate()

            if process.returncode != 0:
                if isinstance(stdout_data, bytes):
                    stdout_str = stdout_data.decode("UTF-8")
                else:
                    stdout_str = stdout_data

                if isinstance(stderr_data, bytes):
                    stderr_str = stderr_data.decode("UTF-8")
                else:
                    stderr_str = stderr_data

                logger.error(f"{command} failed with {process.returncode}")
                logger.error(f"stdout: {stdout_str}")
                logger.error(f"stderr: {stderr_str}")

                try:
                    await self.check_device_connected()
                except AriaException:
                    error_code = AriaError.DEVICE_NOT_CONNECTED
                raise AriaException(error_code, to_error_message(error_code))

            return stdout_data, stderr_data

        except Exception as e:
            logger.error(f"Error in _adb_command_in_cmd: {str(e)}")
            raise
