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

import os
import platform
from http import HTTPStatus
from pathlib import Path
from typing import Annotated, List, Optional

from aria_studio.app.constants import FULL_PATH, KEY_FILE_NAME
from aria_studio.app.local.local_file_manager import LocalFileManager
from aria_studio.app.local.local_log_manager import (
    LocalLogEvent,
    LocalLogManager,
    LocalLogScreen,
)
from aria_studio.app.return_codes import (
    FILE_NOT_FOUND_ERROR_CODE,
    FILENAME_NOT_PROVIDED_ERROR_CODE,
    GET_LOCAL_FILES_DETAILS_FAILED_ERROR_CODE,
    LOCAL_FILES_DELETE_FAILED_ERROR_CODE,
    LOCAL_FILES_FAILED_ERROR_CODE,
    LOCAL_THUMBNAIL_JPEG_FAILED_ERROR_CODE,
)
from aria_studio.app.utils import login_required
from aria_studio.utils.rerun_manager import RerunManager
from aria_studio.utils.vrs_rerun_task import VrsRerunTask

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DeleteLocalFilesRequest(BaseModel):
    files_to_delete: Optional[List[Path]] = None
    path_to_delete: Optional[Path] = None


class MediaModel(BaseModel):
    file_path: Path


class LocalFilesModel(BaseModel):
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    asc: bool = Field(False, description="Sort in ascending order")
    page: int = Field(1, description="Current page number")
    per_page: int = Field(6, description="Number of items per page")
    path: str = Field(..., description="Path to the directory")
    is_recursive: bool = Field(
        default=False, description="Flag to enable recursive file listing"
    )


class DeleteFilesResponse(BaseModel):
    message: str = Field(..., description="Delete message")


router = APIRouter()


@login_required
@router.post(
    "/delete",
    status_code=HTTPStatus.OK,
    summary="API to delete local vrs files",
    response_model=DeleteFilesResponse,
)
def delete_files(request: DeleteLocalFilesRequest) -> JSONResponse:
    if not request.files_to_delete and not request.path_to_delete:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="No files or folder is specified to delete.",
        )
    if request.path_to_delete:
        files_to_delete = list(request.path_to_delete.glob("*.vrs"))
    else:
        files_to_delete = request.files_to_delete

    try:
        file_manager = LocalFileManager.get_instance()
        file_manager.delete(files_to_delete)
        return DeleteFilesResponse(
            message=f"{len(files_to_delete)} file(s) deleted successfully."
        )
    except Exception:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=LOCAL_FILES_DELETE_FAILED_ERROR_CODE,
        )


@login_required
@router.get(
    "/thumbnail_jpeg",
    summary="Get the jpeg thumbnail for a specified file",
    status_code=HTTPStatus.OK,
    response_class=FileResponse,
)
def serve_file(file_path: Annotated[Path, Query()]):
    try:
        file_manager = LocalFileManager.get_instance()
        media_path = file_manager.get_thumbnail_jpeg(file_path)
        if media_path:
            return FileResponse(str(media_path))
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Thumbnail not found"
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=LOCAL_THUMBNAIL_JPEG_FAILED_ERROR_CODE,
        )


@router.get(
    "/details",
    status_code=HTTPStatus.OK,
    summary="API to view local vrs files metadata details",
)
def get_file_details(vrs_path: Path):
    # Return a JSON response with the metadata for the file at the given path
    try:
        file_manager = LocalFileManager.get_instance()
        return JSONResponse(
            status_code=HTTPStatus.OK, content=file_manager.get_metadata(vrs_path)
        )
    except Exception:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=GET_LOCAL_FILES_DETAILS_FAILED_ERROR_CODE,
        )


@router.post(
    "/files",
    status_code=HTTPStatus.OK,
    summary="API to view local vrs files with optional recursive file listing",
)
def local_files(request: LocalFilesModel, requestObj: Request):
    if not Path(request.path).is_dir():
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Directory not found"
        )
    try:
        file_manager = LocalFileManager.get_instance()

        # check if recursion is requested
        if request.is_recursive:
            output = get_files_recursively(Path(request.path), file_manager)
        else:
            # Use th original non recursive implementation
            output = file_manager.get_metadata_on_folder(Path(request.path))

            # Add full paths to non-recursively results too
            for file_info in output:
                file_path = Path(request.path) / file_info[KEY_FILE_NAME]
                file_info[FULL_PATH] = os.path.normpath(str(file_path.absolute()))

    except Exception:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=LOCAL_FILES_FAILED_ERROR_CODE,
        )
    output = sorted(output, key=lambda x: x[KEY_FILE_NAME])
    # Return the paginated data in old paginated form which is what the frontend expects
    return {
        "count": len(output),  # Total number of items
        "next": None,  # URL for the next page
        "previous": None,  # URL for the previous page
        "results": output,  # Items for the current page
    }


def get_files_recursively(
    directory: Path, file_manager: LocalFileManager
) -> list[dict[str, any]]:
    """
    Recursively get all files from the given directory and its subdirectories,
    including the full path for each file.

    Args:
        directory: Path to the directory
        file_manager: Instance of LocalFileManager

    Returns:
        List of file metadata with full paths
    """

    all_files: list[dict[str, any]] = []

    # Get metadata for files in current directory
    current_dir_files: list[dict[str, any]] = file_manager.get_metadata_on_folder(
        directory
    )

    # Add full path to each file metadata
    for file_info in current_dir_files:
        file_path: Path = directory / file_info[KEY_FILE_NAME]
        # Use os.path.normpath to ensure proper path format for each OS
        file_info[FULL_PATH]: str = os.path.normpath(str(file_path.absolute()))
        all_files.append(file_info)

    # Recursively process subdirectories
    for item in directory.iterdir():
        if item.is_dir():
            # Skip hidden directories (those starting with '.') on Unix-like systems
            if platform.system() != "Windows" and item.name.startswith("."):
                continue
            # Recursive call to get files from subdirectory
            subdirectory_files: list[dict[str, any]] = get_files_recursively(
                item, file_manager
            )
            all_files.extend(subdirectory_files)

    return all_files


@router.post(
    "/view_vrs",
    status_code=HTTPStatus.OK,
    summary="API to open VRS files using viewer_vrs",
)
async def view_vrs(request: MediaModel):
    logger.debug(request)
    if not request.file_path:
        await LocalLogManager.log(
            event=LocalLogEvent.VISUALIZATION,
            screen=LocalLogScreen.FILES,
            message="No VRS file provided for viewer_vrs",
        )
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail=FILENAME_NOT_PROVIDED_ERROR_CODE
        )
    elif not request.file_path.is_file():
        await LocalLogManager.log(
            event=LocalLogEvent.VISUALIZATION,
            screen=LocalLogScreen.FILES,
            message=f"Path {request.file_path} provided for viewer_vrs is not a file",
        )
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=FILE_NOT_FOUND_ERROR_CODE,
        )

    logger.info("Starting viewer_vrs")
    try:
        manager: RerunManager = RerunManager()
        await manager.start_frozen_rerun()
        await manager.start_viewer(VrsRerunTask(vrs=str(request.file_path)))
    except Exception as e:
        logger.error(f"Failed to launch viewer: {e}")
        await LocalLogManager.log(
            event=LocalLogEvent.VISUALIZATION,
            screen=LocalLogScreen.FILES,
            message=f"Failed to launch viewer: {e}",
        )
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Failed to launch viewer: {str(e)}",
        )
