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

import logging
import stat
import sys
from datetime import datetime
from http import HTTPStatus
from json import JSONDecodeError
from pathlib import Path
from typing import List

from aria_studio.app.constants import (
    DEFAULT_PATH,
    KEY_NAME,
    KEY_PATH,
    UNIX_SYSTEM_ITEMS,
    WINDOWS_SYSTEM_ITEMS,
)

from aria_studio.app.return_codes import (
    CREATE_NEW_DIRECTORY_ERROR_CODE,
    DIRECTORY_EXISTS_ERROR_CODE,
    DIRECTORY_NOT_FOUND_ERROR_CODE,
    INVALID_JSON_ERROR_CODE,
    MISSING_PARAMS_PATH_AND_NAME_REQUIRED_ERROR_CODE,
    PERMISSION_DENIED_ERROR_CODE,
)
from aria_studio.app.utils import login_required
from fastapi import APIRouter, Request, status
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)
router = APIRouter()


class ItemInfo(BaseModel):
    name: str
    last_modified: str


class ExplorerResponse(BaseModel):
    """Response from the explorer endpoint"""

    current_path: str = Field(..., description="The current path")
    files: List[ItemInfo] = Field(..., description="List of files")
    directories: List[ItemInfo] = Field(..., description="List of directories")


class CreateNewDirectoryResponse(BaseModel):
    """Response from the create new directory endpoint"""

    message: str = Field(..., description="The message")


def is_system_item(path: Path) -> bool:
    """Check if the item is a system file/directory."""
    name = path.name

    # Check for hidden files (both Windows and Unix)
    if name.startswith(".") or name.startswith("~"):
        return True

    # Windows-specific checks
    if sys.platform.startswith("win"):
        try:
            # Check for hidden and system attributes
            attrs = path.stat().st_file_attributes
            if attrs & (stat.FILE_ATTRIBUTE_HIDDEN | stat.FILE_ATTRIBUTE_SYSTEM):
                return True
        except (AttributeError, OSError):
            pass

        # Check Windows system files
        if (
            name.lower() in map(str.lower, WINDOWS_SYSTEM_ITEMS)
            or name.endswith(".LOG1")
            or name.endswith(".LOG2")
            or name.endswith(".blf")
            or name.endswith(".regtrans-ms")
        ):
            return True

    # Unix-specific checks
    else:
        if name in UNIX_SYSTEM_ITEMS:
            return True

    return False


def sanitize_path(path: str) -> str:
    """Sanitize and validate path."""
    try:
        clean_path = Path(path).resolve()
        if ".." in str(clean_path):
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="Invalid path"
            )
        return str(clean_path)
    except (OSError, RuntimeError):
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Invalid path")


@login_required
@router.post("/file-explorer", response_model=ExplorerResponse)
async def file_explorer(request: Request) -> ExplorerResponse:
    """
    List non-system files and directories in the specified directory.

    Args:
        request (Request): FastAPI request object containing path in JSON body.
    """
    try:
        data = await request.json()
    except JSONDecodeError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail=INVALID_JSON_ERROR_CODE
        )

    raw_path = data.get(KEY_PATH, DEFAULT_PATH) or DEFAULT_PATH
    path = Path(sanitize_path(raw_path))

    if not path.exists():
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail=DIRECTORY_NOT_FOUND_ERROR_CODE
        )

    files = []
    directories = []

    try:
        items = list(path.iterdir())
    except PermissionError:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail=PERMISSION_DENIED_ERROR_CODE
        )

    for item in items:
        # Skip system files and hidden files
        if is_system_item(item):
            continue

        try:
            modified_time = datetime.fromtimestamp(item.stat().st_mtime).isoformat()
            item_info = ItemInfo(name=item.name, last_modified=modified_time)

            if item.is_file():
                files.append(item_info)
            elif item.is_dir():
                directories.append(item_info)

        except OSError:
            continue  # Skip files we can't access

    # Sort by last modified (newest first)
    files.sort(key=lambda x: x.last_modified, reverse=True)
    directories.sort(key=lambda x: x.last_modified, reverse=True)

    return ExplorerResponse(
        current_path=str(path), files=files, directories=directories
    )


@login_required
@router.post(
    "/create-new-directory",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateNewDirectoryResponse,
)
async def create_new_directory(request: Request) -> CreateNewDirectoryResponse:
    """
    Create a new directory with the specified name in the specified path.

    Args:
        path (str): The path where the new directory will be created.
        name (str): The name of the new directory.

    Returns:
        CreateNewDirectoryResponse: The response containing a success message if the directory was created successfully.
    """
    try:
        data = await request.json()
    except JSONDecodeError:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail=INVALID_JSON_ERROR_CODE
        )

    if KEY_PATH not in data or KEY_NAME not in data:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=MISSING_PARAMS_PATH_AND_NAME_REQUIRED_ERROR_CODE,
        )
    path = data.get(KEY_PATH)
    name = data.get(KEY_NAME)
    directory_path = Path(path) / name
    if directory_path.exists():
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=DIRECTORY_EXISTS_ERROR_CODE,
        )

    try:
        directory_path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail=PERMISSION_DENIED_ERROR_CODE
        )
    except Exception:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=CREATE_NEW_DIRECTORY_ERROR_CODE,
        )

    return CreateNewDirectoryResponse(
        message=f"Directory '{name}' created successfully at '{path}'"
    )
