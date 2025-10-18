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

import json
import logging
from pathlib import Path
from typing import Any, Final, List, Mapping, Optional, Tuple

from aria_studio.app.common.disk_cache import DiskCache
from aria_studio.app.constants import (
    KEY_DEVICE_ID,
    KEY_DEVICE_SERIAL,
    KEY_DURATION,
    KEY_END_TIME,
    KEY_FILE_NAME,
    KEY_FILE_PATH,
    KEY_FILE_SIZE,
    KEY_FILENAME,
    KEY_RECORDING_PROFILE,
    KEY_SHARED_SESSION_ID,
    KEY_START_TIME,
    KEY_TIME_SYNC_MODE,
    LOCAL_CACHE_DIR,
    METADATA_JSON,
    THUMBNAIL_JPEG,
)
from PIL import Image
from projectaria_tools.aria_mps_cli.cli_lib.common import log_exceptions

from projectaria_tools.core.data_provider import (
    create_vrs_data_provider,
    VrsDataProvider,
    VrsMetadata,
)
from projectaria_tools.core.stream_id import StreamId

logger = logging.getLogger(__name__)

# Key name -> Key type
_RELEVANT_KEYS: Mapping[str, type] = {
    KEY_START_TIME: int,
    KEY_END_TIME: int,
    KEY_FILE_SIZE: int,
    KEY_RECORDING_PROFILE: str,
}


__RGB_STREAM_ID: Final[StreamId] = StreamId("214-1")
__RGB_ROTATION: Final[int] = -90


class LocalFileManager:
    """The class to manage the local files."""

    instance_: Optional["LocalFileManager"] = None

    @classmethod
    def get_instance(cls):
        """Get the Local File Manager singleton."""
        if cls.instance_ is None:
            logger.debug("Creating file manager")
            cls.instance_ = LocalFileManager()
        return cls.instance_

    def __init__(self):
        logger.debug(f"Setting local cache dir to {LOCAL_CACHE_DIR}")
        self._disk_cache: DiskCache = DiskCache(LOCAL_CACHE_DIR)

    @property
    def cache(self):
        """Get the disk cache."""
        return self._disk_cache

    def delete(self, files_to_delete: List[Path]) -> None:
        """Delete the specified files and any associated cached files."""
        for path in files_to_delete:
            self._disk_cache.clear(path)
            path.unlink(missing_ok=True)
        logger.debug(f"Deleted files : {files_to_delete}")

    @log_exceptions
    def get_thumbnail_jpeg(self, vrs_file: Path) -> Optional[Path]:
        """
        Get the thumbnail for a VRS file.
        First check if the thumbnail is in cache, otherwise create a new one.
        """
        # Get the path to the cached image
        thumbnail = self._disk_cache.get(vrs_file, THUMBNAIL_JPEG)
        if not thumbnail:
            logger.debug(f"Thumbnail {vrs_file} not found in cache")
            thumbnail_img = _read_thumbnail_from_vrs(vrs_file)
            if thumbnail_img:
                thumbnail = self._disk_cache.get_cache_dir(vrs_file) / THUMBNAIL_JPEG
                logger.debug(f"Saving thumbnail to {thumbnail}")
                thumbnail_img.save(str(thumbnail))
        logger.debug(f"Returning thumbnail {thumbnail}")
        return thumbnail

    @log_exceptions
    def get_metadata(self, vrs_file: Path) -> Mapping[str, Any]:
        """Get metadata for a vrs file."""
        metadata_path = self._disk_cache.get(vrs_file, METADATA_JSON)
        if metadata_path:
            metadata = _load_json(metadata_path)
            if _is_valid(metadata):
                return metadata

        logger.debug(f"Metadata {vrs_file} not found in cache or is invalid")
        metadata_path = self._disk_cache.get_cache_dir(vrs_file) / METADATA_JSON

        # First check if we can load the metadata from the metadata file that was copied
        # over along with the vrs file
        metadata = _create_metadata_from_metadata_json_file(vrs_file)
        if _is_valid(metadata):
            metadata = _cleanup_metadata(metadata)
            _write_metadata(vrs_file, metadata, metadata_path)
            return metadata
        logger.debug(
            f"Metadata {vrs_file} not found next to the vrs file or is invalid"
        )

        # Worst case we create a VRS metadata file for the vrs file
        metadata, thumbnail_img = _read_metadata_and_thumbnail_from_vrs(vrs_file)
        if _is_valid(metadata):
            metadata = _cleanup_metadata(metadata)
            _write_metadata(vrs_file, metadata, metadata_path)
            if thumbnail_img:
                thumbnail = self._disk_cache.get_cache_dir(vrs_file) / THUMBNAIL_JPEG
                logger.debug(f"Saving thumbnail to {thumbnail}")
                thumbnail_img.save(thumbnail)
            return metadata
        logger.debug(
            f"Metadata {vrs_file} not found in vrs file. This is not a valid vrs file."
        )
        raise RuntimeError(b"Invalid vrs file {vrs_file}")

    def get_metadata_on_folder(self, folder_path: Path) -> List[Mapping[str, Any]]:
        """Get metadata for all the vrs files in a folder."""
        metadata_list: List[Mapping[str, Any]] = []
        for file in folder_path.glob("*.vrs"):
            try:
                metadata_list.append(self.get_metadata(file))
            except Exception as e:
                logger.debug(f"Error reading metadata for {file}: {e}")
        return metadata_list


def _cleanup_metadata(metadata: Mapping[str, Any]) -> Mapping[str, Any]:
    """Cleanup the metadata by removing any fields that are not needed."""
    clean_metadata: Mapping[str, Any] = {}
    for key, key_type in _RELEVANT_KEYS.items():
        value = metadata[key]
        # Check that the type is correct and remove it from the dictionary otherwise
        if not isinstance(value, key_type):
            value = key_type(value)
        clean_metadata[key] = value

    return clean_metadata


def _is_valid(metadata: Optional[Mapping[str, Any]]) -> bool:
    """Check if the metadata is valid."""
    if not metadata:
        return False
    for key in _RELEVANT_KEYS:
        if key not in metadata:
            return False
    return True


def _load_json(file_path: Path) -> Optional[Mapping[str, Any]]:
    """Load the metadata from a json file.
    Returns None if the file does not exist or is invalid."""
    if not file_path.is_file():
        logger.debug(f"Metadata file {file_path} does not exist")
        return None
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading metadata file {file_path}: {e}")
    return None


def _create_metadata_from_metadata_json_file(
    vrs_path: Path,
) -> Optional[Mapping[str, Any]]:
    """Create metadata from a json file that was copied over alongwith the vrs file
    on import."""
    # Load the JSON data into a dictionary
    metadata_path = vrs_path.with_suffix(".vrs.json")
    if metadata_path.is_file():
        with open(str(metadata_path), "r") as f:
            metadata = json.load(f)
        return metadata


@log_exceptions
def _read_metadata_and_thumbnail_from_vrs(
    file_path: Path,
) -> Tuple[Mapping[str, Any], Optional[Image.Image]]:
    """
    Create a VRS metadata file for the given vrs path by reading the vrs file.
    """

    provider: VrsDataProvider = create_vrs_data_provider(str(file_path))
    streams: List[StreamId] = provider.get_all_streams()
    if __RGB_STREAM_ID in streams:
        image_data, _ = provider.get_image_data_by_index(__RGB_STREAM_ID, 0)
        image: Image.Image = Image.fromarray(image_data.to_numpy_array()).rotate(
            __RGB_ROTATION
        )
    else:
        image = None

    vrs_metadata: VrsMetadata = provider.get_metadata()
    data: Mapping[str, Any] = {
        KEY_DEVICE_SERIAL: vrs_metadata.device_serial,
        KEY_SHARED_SESSION_ID: vrs_metadata.shared_session_id,
        KEY_RECORDING_PROFILE: vrs_metadata.recording_profile,
        KEY_TIME_SYNC_MODE: vrs_metadata.time_sync_mode,
        KEY_DEVICE_ID: vrs_metadata.device_id,
        KEY_FILENAME: vrs_metadata.filename,
        KEY_START_TIME: vrs_metadata.start_time_epoch_sec,
        KEY_END_TIME: vrs_metadata.end_time_epoch_sec,
        KEY_DURATION: vrs_metadata.duration_sec,
        KEY_FILE_SIZE: file_path.stat().st_size,
    }

    return data, image


@log_exceptions
def _read_thumbnail_from_vrs(file_path: Path) -> Optional[Image.Image]:
    """
    Create a thumbnail for a VRS file by taking first frame from RGB stream.
    """
    provider: VrsDataProvider = create_vrs_data_provider(str(file_path))
    streams: List[StreamId] = provider.get_all_streams()
    if __RGB_STREAM_ID in streams:
        image_data, _ = provider.get_image_data_by_index(__RGB_STREAM_ID, 0)
        return Image.fromarray(image_data.to_numpy_array()).rotate(__RGB_ROTATION)

    return None


def _write_metadata(
    vrs_file: Path, metadata: Mapping[str, Any], metadata_path: Path
) -> Mapping[str, Any]:
    """Write the metadata to a json file."""
    # Always use the filename and file_path from the file listing
    metadata[KEY_FILE_NAME] = vrs_file.name
    metadata[KEY_FILE_PATH] = str(vrs_file.parent)
    with open(metadata_path, "w") as f:
        json.dump(metadata, f)
