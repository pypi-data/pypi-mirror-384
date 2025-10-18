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

from pathlib import Path
from typing import Final


KEY_ERROR: Final[str] = "error"
KEY_MESSAGE: Final[str] = "message"
MESSAGE_DEVICE_NOT_CONNECTED: Final[str] = "Device not connected"
MESSAGE_FILE_NOT_FOUND: Final[str] = "file not found"
COMPLETED: Final[str] = "completed"
STATUS: Final[str] = "status"
COPIED_FILES: Final[str] = "copied_files"
TOTAL_FILES: Final[str] = "total_files"
PROCESSING: Final[str] = "processing"
UTF_8: Final[str] = "utf-8"
MIME_IMAGE_JPEG: Final[str] = "image/jpeg"
MIME_IMAGE_GIF: Final[str] = "image/gif"
PERMISSION_DENIED: Final[str] = "Permission denied"
MESSAGE_INVALID_JSON: Final[str] = "Invalid JSON"
MESSAGE_DIRECTORY_ALREADY_EXISTS: Final[str] = "Directory already exists"
KEY_PATH: Final[str] = "path"
KEY_NAME: Final[str] = "name"
KEY_LAST_MODIFIED: Final[str] = "last_modified"
KEY_FILES: Final[str] = "files"
KEY_DIRECTORIES: Final[str] = "directories"
DEFAULT_PATH: Final[str] = Path.home()
MESSAGE_DIRECTORY_NOT_FOUND: Final[str] = "Directory not found"
KEY_USER: Final[str] = "user"
KEY_LOGGED_IN: Final[str] = "logged_in"
MESSAGE_LOGGED_IN_SUCCESS: Final[str] = "Logged in successfully"
MESSAGE_LOGGED_OUT_SUCCESS: Final[str] = "Logged out successfully"
MESSAGE_LOGGED_OUT_FAILED: Final[str] = "Logout failed"
METADATA: Final[str] = "metadata"
FULL_PATH: Final[str] = "full_path"

KEY_DEVICE_SERIAL: Final[str] = "device_serial"
KEY_SHARED_SESSION_ID: Final[str] = "shared_session_id"
KEY_RECORDING_PROFILE: Final[str] = "recording_profile"
KEY_TIME_SYNC_MODE: Final[str] = "time_sync_mode"
KEY_DEVICE_ID: Final[str] = "device_id"
KEY_FILENAME: Final[str] = "filename"
KEY_START_TIME: Final[str] = "start_time"
KEY_END_TIME: Final[str] = "end_time"
KEY_DURATION: Final[str] = "duration"
KEY_FILE_SIZE: Final[str] = "file_size"

NANOSECONDS_IN_SECOND: int = 1_000_000_000
KEY_FILE_PATH: Final[str] = "file_path"
KEY_FILE_NAME: Final[str] = "file_name"
CAPTURE_TIME_EPOCH: Final[str] = "capture_time_epoch"

MESSAGE_MPS_PREPARING: Final[str] = (
    "Selected files are being prepared to process by MPS"
)
MESSAGE_MPS_NOT_AUTHORIZED: Final[str] = "MPS is available only for logged in users"
MESSAGE_MPS_MISSING_FEATURES: Final[str] = (
    "'features' must contain valid MPS features list"
)
MESSAGE_MPS_MISSING_RECORDINGS: Final[str] = "'input' must contain valid path's list"

DOC_ID_QUERY_MPS_REQUESTS: Final[int] = 25430683893242854
DOC_ID_GET_MPS_REQUEST: Final[int] = 8602162363145386

QUERY_KEY_ID: Final[str] = "id"
QUERY_KEY_PAGE_SIZE: Final[str] = "page_size"
QUERY_KEY_CURSOR: Final[str] = "cursor"
# hard, server-side limit for the number of requests to be returned in a single response is 10 000
QUERY_DEFAULT_PAGE_SIZE: Final[int] = 1000

RESPONSE_KEY_DATA: Final[str] = "data"
RESPONSE_KEY_REQUEST: Final[str] = "request"
RESPONSE_KEY_REQUESTS: Final[str] = "requests"
RESPONSE_KEY_PAGE_INFO: Final[str] = "page_info"
RESPONSE_KEY_HAS_NEXT_PAGE: Final[str] = "has_next_page"
RESPONSE_KEY_END_CURSOR: Final[str] = "end_cursor"
RESPONSE_KEY_NODES: Final[str] = "nodes"

KEY_MMA_HEADER_AUTH: Final[str] = "Authorization"
KEY_MMA_HEADER_CONTENT_TYPE: Final[str] = "Content-Type"
KEY_MMA_VALUE_CONTENT_TYPE: Final[str] = "application/x-www-form-urlencoded"
KEY_MMA_RESPONSE_TOKEN: Final[str] = "native_sso_token"
KEY_MMA_RESPONSE_ETOKEN: Final[str] = "native_sso_etoken"
KEY_MMA_DATA_BLOB: Final[str] = "blob"
KEY_MMA_DATA_TOKEN: Final[str] = "request_token"
KEY_MMA_RESPONSE_ACCESS_TOKEN: Final[str] = "access_token"
KEY_MMA_RESPONSE_USER_ID: Final[str] = "frl_account_id"

TABLE_GROUPS: Final[str] = "groups"
TABLE_GROUP_FILES: Final[str] = "group_files"
TABLE_GROUP_MPS_REQUESTS: Final[str] = "group_mps_requests"
TABLE_GROUP_MPS_STATUS: Final[str] = "group_mps_status"
TABLE_INDIVIDUAL_MPS_REQUESTS: Final[str] = "individual_mps_requests"

LOGGING_YML_PATH: Final[Path] = Path(__file__).resolve().parent.parent / "logging.yml"
LOGGING_PATH: Final[Path] = Path("/tmp/logs/projectaria")
# This is the root aria studio cache directory.
CACHE_DIR: Final[Path] = Path.home().joinpath(".projectaria/ariastudiocache")
# Directory to store device cache files.
DEVICE_CACHE_DIR: Final[Path] = CACHE_DIR / "device"
# Directory to store local cache files.
LOCAL_CACHE_DIR: Final[Path] = CACHE_DIR / "local"
THUMBNAIL_JPEG: Final[str] = "thumbnail.jpeg"
THUMBNAIL_GIF: Final[str] = "thumbnail.gif"
METADATA_JSON: Final[str] = "metadata.json"

CLOSED_LOOP_TRAJECTORY_FILE: Final[str] = "closed_loop_trajectory.csv"
SEMI_DENSE_POINTS_FILE: Final[str] = "semidense_points.csv.gz"
VRS_TO_MULTI_SLAM_FILE = "vrs_to_multi_slam.json"
SLAM_FOLDER = "slam"
LOCALHOST: Final[str] = "127.0.0.1"
ARIA_STUDIO_DB: Final[str] = "aria_studio.db"
WIN32: Final[str] = "win32"
# System files/folders to exclude
WINDOWS_SYSTEM_ITEMS = {
    "AppData",
    "Application Data",
    "Cookies",
    "Local Settings",
    "NetHood",
    "PrintHood",
    "Recent",
    "SendTo",
    "Start Menu",
    "Templates",
    "My Documents",
    "ntuser.dat",
    "ntuser.ini",
    "NTUSER.DAT",
    "Tracing",
    "desktop.ini",
    "thumbs.db",
    "$Recycle.Bin",
    "System Volume Information",
}

UNIX_SYSTEM_ITEMS = {
    "lost+found",
    "proc",
    "mnt",
    "sys",
    "run",
    "boot",
    "srv",
    ".Trash",
    ".Trash-1000",
}

KEY_DATA: Final[str] = "data"
KEY_TITLE: Final[str] = "title"
KEY_DESCRIPTION: Final[str] = "description"
KEY_EXTRA_INFO: Final[str] = "extra_info"
QUERY_ID_USER_FEEDBACK_ARIA_STUDIO: Final[str] = "24659369687020076"
QUERY_CREATE_USER_FEEDBACK_ARIA_STUDIO: Final[str] = "24525365727133316"
KEY_ID: Final[str] = "id"
KEY_NODE: Final[str] = "node"
KEY_TASK_NUMBER: Final[str] = "task_number"
KEY_CREATE: Final[str] = "create"
KEY_ARIA_STUDIO_USER_FEEDBACK: Final[str] = "aria_studio_user_feedback"
