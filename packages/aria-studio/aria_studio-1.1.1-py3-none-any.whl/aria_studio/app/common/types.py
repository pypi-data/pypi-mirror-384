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

import time
from dataclasses import dataclass, field
from enum import auto, Enum, IntEnum
from pathlib import Path
from typing import List, Mapping, Optional, Set, Tuple

from projectaria_tools.aria_mps_cli.cli_lib.types import MpsFeature

from pydantic import BaseModel, Field


@dataclass
class Group:
    """
    The class to represent a group. This will contain all the files in that group and other metadata about it.
    * Name of the group.
    * Path on device where this group is stored.
    * List of VRS files belonging to this group.
    """

    name: str
    path_on_device: Path
    creation_time: float = time.time()
    vrs_files: Set[Path] = field(default_factory=set)

    def __post_init__(self):
        """Convert the fields to their correct types."""
        self.vrs_files = [Path(f) for f in self.vrs_files]
        self.path_on_device = Path(self.path_on_device)


@dataclass
class FeatureStatus:
    """Represents the MPS status of a feature of a recording"""

    status: str
    # Error code is a string for more flexibility.
    error_code: Optional[str] = None
    progress: Optional[float] = None

    creation_time: Optional[int] = None
    output_path: Optional[Path] = None


class MpsRequestStage(str, Enum):
    """Status of the request. Used to track the status of a request in the DB"""

    def _generate_next_value_(name, start, count, last_values):
        return name.upper()

    REQUESTOR = auto()  # The request is with the Requestor SM
    MONITOR = auto()  # The request is with the Monitor SM
    SUCCESS = auto()  # The request SUCCEEDED
    ERROR = auto()  # The request FAILED


@dataclass
class DBIndividualMpsRequest:
    """DB entry for a individual MPS request"""

    vrs_path: Path
    feature: MpsFeature
    status: str
    stage: str
    request_id: Optional[int] = None
    creation_time: Optional[int] = None
    error_code: Optional[str] = None
    retry_failed: bool = False
    force: bool = False
    output_path: Optional[Path] = None

    def __post_init__(self):
        self.vrs_path = Path(self.vrs_path)
        self.feature = MpsFeature(self.feature)


@dataclass
class DBGroupMpsRequest:
    """DB entry for a group MPS request"""

    group_name: str
    stage: str
    request_id: Optional[int] = None
    creation_time: Optional[int] = None
    feature: MpsFeature = MpsFeature.MULTI_SLAM
    # Status and error code
    status: Mapping[Path, Tuple[str, str]] = field(default_factory=dict)
    retry_failed: bool = False
    force: bool = False
    output_path: Optional[Path] = None


class AriaError(IntEnum):
    """Aria error codes."""

    SUCCESS = 0

    GENERIC_DEVICE_ERROR = 1001
    DEVICE_NOT_CONNECTED = 1002
    PULL_FAILED = 1003
    DELETE_FAILED = 1004
    THUMBNAIL_NOT_FOUND = 1005
    LIST_THUMBNAIL_FAILED = 1006
    LIST_RECORDING_FAILED = 1007
    GIF_GENERATE_FAILED = 1008
    METADATA_READ_FAILED = 1009
    VRS_PULL_IN_PROGRESS = 1010
    NOT_A_VRS_FILE = 1011
    VRS_NOT_FOUND = 1012
    GET_STATUS_FAILED = 1013
    VRS_PULL_NOT_STARTED = 1014
    CANCEL_FAILED = 1015

    MMA_WRONG_PORT = 2001
    MMA_TOKEN_EXPIRED = 2002
    MMA_TOKEN_MISMATCH = 2003
    MMA_DECRYPT_BLOB_FAILED = 2004
    MMA_SET_USER_TOKEN_FAILED = 2005


__ERROR_TO_MESSAGE: Mapping[AriaError, str] = {
    AriaError.GENERIC_DEVICE_ERROR: "Generic device error",
    AriaError.DEVICE_NOT_CONNECTED: "Device not connected",
    AriaError.PULL_FAILED: "Failed to pull file from device",
    AriaError.DELETE_FAILED: "Failed to delete file from device",
    AriaError.THUMBNAIL_NOT_FOUND: "Thumbnail not found",
    AriaError.LIST_THUMBNAIL_FAILED: "Failed to list thumbnails",
    AriaError.LIST_RECORDING_FAILED: "Failed to list vrs files",
    AriaError.GIF_GENERATE_FAILED: "Failed to generate gif",
    AriaError.METADATA_READ_FAILED: "Failed to read metadata",
    AriaError.VRS_PULL_IN_PROGRESS: "Another import is in progress",
    AriaError.NOT_A_VRS_FILE: "Not a vrs file",
    AriaError.VRS_NOT_FOUND: "Vrs file not found on device",
    AriaError.GET_STATUS_FAILED: "Failed to get status of the device",
    AriaError.VRS_PULL_NOT_STARTED: "No import in progress",
    AriaError.MMA_WRONG_PORT: "Wrong port number",
    AriaError.MMA_TOKEN_EXPIRED: "Expired token",
    AriaError.MMA_TOKEN_MISMATCH: "Token mismatch between requests",
    AriaError.MMA_DECRYPT_BLOB_FAILED: "Failed to decrypt token's blob",
    AriaError.MMA_SET_USER_TOKEN_FAILED: "Failed to set user token",
}


def to_error_message(error_code: int) -> str:
    """
    Convert error code to a human readable message.
    """

    if error_code in __ERROR_TO_MESSAGE:
        return __ERROR_TO_MESSAGE[error_code]
    else:
        return "Unknown error"


class AriaException(Exception):
    """Aria exception."""

    def __init__(self, error_code: int, *args, **kwargs):
        self._error_code = error_code
        super().__init__(*args, **kwargs)

    @property
    def error_code(self) -> int:
        return self._error_code


class VisualizationException(Exception):
    """Rerun visualization exception."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class DiskStats(BaseModel):
    """
    Disk status of Project Aria Glasses
    """

    free_space: str = Field(..., description="The free space on the glasses' disk")
    total_space: str = Field(..., description="The total space on the glasses' disk")


@dataclass
class DeviceStatus:
    """Device status"""

    serial_number: str
    model: str
    wifi_ssid: Optional[str]
    battery_level: int
    import_in_progress: bool
    is_research_mode: bool
    diskstats: Optional[DiskStats] = None


@dataclass
class CopyStatus:
    """Copy status"""

    current_files: List[Path] = field(default_factory=list)
    copied_files: List[Path] = field(default_factory=list)
    deleted_files: List[Path] = field(default_factory=list)
    total_files: int = 0
    copied_bytes: int = 0
    total_bytes: int = 0
    error: Optional[str] = None
    error_files: List[Path] = field(default_factory=list)
