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
from pathlib import Path
from typing import Any, Awaitable, Callable, Final, List, Mapping, Optional

from aria_studio.app.common.types import CopyStatus, DeviceStatus, DiskStats

from aria_studio.app.constants import (
    KEY_DURATION,
    KEY_END_TIME,
    KEY_FILE_SIZE,
    KEY_RECORDING_PROFILE,
    KEY_START_TIME,
)
from aria_studio.app.device.device_manager import (
    AriaError,
    AriaException,
    DeviceManager,
)
from aria_studio.app.return_codes import (
    CANCEL_IMPORT_ERROR_CODE,
    CANCEL_NO_IMPORT_ERROR_CODE,
    DELETE_FILES_FAILED_CODE,
    DEVICE_NOT_CONNECTED_CODE,
    DEVICE_STATUS_FAILED_CODE,
    FILE_NOT_FOUND_ERROR_CODE,
    IMPORT_FILES_ALREADY_EXISTS_ERROR_CODE,
    IMPORT_FILES_ERROR_CODE,
    IMPORT_PROGRESS_ERROR_CODE,
    LIST_GLASSES_FILES_FAILED_ERROR_CODE,
)
from aria_studio.app.utils import login_required
from fastapi import APIRouter, HTTPException, status
from fastapi.param_functions import Query
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

DEFAULT_PAGE = Query(1, ge=1)
DEFAULT_PER_PAGE = Query(6, ge=1)

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectedResponse(BaseModel):
    """Response from the connected endpoint"""

    connected: bool = Field(..., description="Is the device connected")


@login_required
@router.get(
    "/connected",
    status_code=status.HTTP_200_OK,
    response_model=ConnectedResponse,
    summary="Is the device connected?",
)
async def connected() -> ConnectedResponse:
    """Check if the device is connected"""
    try:
        device_manager: DeviceManager = DeviceManager.get_instance()
        await device_manager.check_device_connected()
        return ConnectedResponse(connected=True)
    except AriaException as e:
        logger.exception(e)
        return ConnectedResponse(connected=False)


class DeviceStatusResponse(BaseModel):
    """Response from the status endpoint"""

    serial_number: str = Field(..., description="Serial number of the device")
    wifi_ssid: Optional[str] = Field(
        None, description="Wi-Fi SSID of the device if connected. None if not connected"
    )
    battery_level: int = Field(0, description="Battery level in percentage (0 to 100)")
    import_in_progress: bool = Field(..., description="Is an import in progress")
    diskstats: DiskStats = Field(..., description="Aria Glasses device memory")
    is_research_mode: bool = Field(
        False, description="Is the device in research mode. Only available for Aria"
    )


@login_required
@router.get(
    "/status",
    status_code=status.HTTP_200_OK,
    response_model=Optional[DeviceStatusResponse],
    summary="Get the device status (serial number, wifi ssid and battery level) of the device. If not connected to a device, return null",
)
async def device_status() -> Optional[DeviceStatusResponse]:
    """
    Retrieve the device status. If the device is not connected, return None.
    """
    try:
        device_manager: DeviceManager = DeviceManager.get_instance()
        device_status: DeviceStatus = await device_manager.get_status()
        return DeviceStatusResponse(
            serial_number=device_status.serial_number,
            wifi_ssid=device_status.wifi_ssid,
            battery_level=device_status.battery_level,
            import_in_progress=device_status.import_in_progress,
            diskstats=device_status.diskstats,
            is_research_mode=device_status.is_research_mode,
        )
    except AriaException as e:
        if e.error_code == AriaError.DEVICE_NOT_CONNECTED:
            return None
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=DEVICE_STATUS_FAILED_CODE,
        )


class VrsFile(BaseModel):
    """Response from the list files api for each file"""

    file_name: str = Field(..., description="The name of the vrs file")
    recording_profile: str = Field(
        ..., description="The recording profile of the vrs file"
    )
    start_time: int = Field(
        ...,
        description="The start time when the vrs file was recorded. Seconds since epoch",
    )
    end_time: int = Field(
        ...,
        description="The end time when the recording was stopped. Seconds since epoch",
    )
    file_size: int = Field(..., description="The size of the vrs file in bytes")


class ListFilesResponse(BaseModel):
    """Response from the list files api"""

    count: int = Field(..., description="The total number of files")
    next: Optional[str] = Field(None, description="Don't rely on this")
    previous: Optional[str] = Field(None, description="Don't rely on this")
    results: List[VrsFile] = Field(..., description="The list of vrs files")


@login_required
@router.get(
    "/list-files",
    status_code=status.HTTP_200_OK,
    response_model=ListFilesResponse,
    summary="List all the vrs files on the device and their metadata",
)
async def list_files(
    sort_by: Optional[str] = None,
    asc: bool = True,
) -> ListFilesResponse:
    """
    Retrieve a list of files from the device, along with the necessary metadata.
    """
    files: List[VrsFile] = []

    try:
        device_manager: DeviceManager = DeviceManager.get_instance()
        vrs_files: List[Path] = await device_manager.list_vrs_files()
        for vrs_file in vrs_files:
            try:
                vrs_metadata: Mapping[str, Any] = await device_manager.get_metadata(
                    vrs_file
                )
                files.append(
                    VrsFile(
                        file_name=vrs_file.name,
                        recording_profile=vrs_metadata[KEY_RECORDING_PROFILE],
                        start_time=vrs_metadata[KEY_START_TIME],
                        end_time=vrs_metadata[KEY_END_TIME],
                        file_size=vrs_metadata[KEY_FILE_SIZE],
                    )
                )
            except AriaException as e:
                logger.error(f"Error retrieving metadata for {vrs_file}: {e}")
    except AriaException as e:
        if e.error_code == AriaError.DEVICE_NOT_CONNECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=LIST_GLASSES_FILES_FAILED_ERROR_CODE,
            )
        logger.error(f"Error retrieving list of files: {e}")
        logger.exception(e)

    return ListFilesResponse(
        count=len(files),
        results=_sort_glasses_files(files, sort_by, asc),
        previous=None,
        next=None,
    )


def _sort_glasses_files(
    files: List[VrsFile],
    sort_by: Optional[str] = None,
    asc: bool = True,
) -> List[VrsFile]:
    PROFILE_PREFIX: Final[str] = "profile"

    if sort_by is None:
        return files

    def get_value(file):
        if sort_by == KEY_RECORDING_PROFILE:
            profile = file.recording_profile
            return (
                int(profile[len(PROFILE_PREFIX) :])
                if profile.startswith(PROFILE_PREFIX)
                else profile
            )
        elif sort_by == KEY_DURATION:
            return file.end_time - file.start_time
        elif sort_by == KEY_FILE_SIZE:
            return file.file_size

        # by default sort by date
        return file.start_time

    return sorted(
        files,
        key=lambda x: get_value(x),
        reverse=asc,
    )


class DeleteFilesRequest(BaseModel):
    """Delete files request"""

    files_to_delete: List[str] = Field([], description="List of file names to delete")


class DeleteFilesResponse(BaseModel):
    """Delete files response"""

    success: bool = Field(..., description="Whether the delete request was successful")


@login_required
@router.post(
    "/delete-files",
    status_code=status.HTTP_200_OK,
    summary="Delete vrs files, metadata and thumbnails associated with the list of vrs files",
)
async def delete_files(request: DeleteFilesRequest) -> None:
    """
    Delete specified files from the device.
    """
    try:
        device_manager: DeviceManager = DeviceManager.get_instance()
        vrs_files: List[Path] = request.files_to_delete
        if not request.files_to_delete:
            vrs_files: List[Path] = await device_manager.list_vrs_files()
        await device_manager.delete_files(vrs_files)
        return DeleteFilesResponse(success=True)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=DELETE_FILES_FAILED_CODE
        )


class ImportFilesRequest(BaseModel):
    """Import files request"""

    destination_path: str = Field(..., description="The path to copy the file")
    files_to_import: List[str] = Field(
        ..., description="List of file names to import", min_items=1
    )
    delete: bool = Field(
        default=False, description="Delete files from device after import"
    )


class ImportStatusResponse(BaseModel):
    """Import status response"""

    current_files: List[str] = Field(
        ...,
        description="The current files being imported. This is all the files being imported concurrently",
    )
    copied_files: List[str] = Field(
        ..., description="The files that have already been copied"
    )
    deleted_files: List[str] = Field(
        ..., description="The files that have already been deleted"
    )
    total_files: int = Field(..., description="The number of files to import")
    copied_bytes: int = Field(..., description="The number of bytes copied")
    total_bytes: int = Field(..., description="The number of bytes to copy")
    error: Optional[str] = Field(None, description="The import error if any")
    error_files: List[str] = Field(
        [], description="The list of files that failed to import"
    )


@login_required
@router.post(
    "/import-files",
    status_code=status.HTTP_201_CREATED,
    response_model=ImportStatusResponse,
    summary="Initiate the import of vrs files from the device. If another import is in progress, exception is thrown.",
)
async def import_files(request: ImportFilesRequest) -> ImportStatusResponse:
    """Initiate the import of vrs files from the device."""
    try:
        device_manager: DeviceManager = DeviceManager.get_instance()
        await device_manager.start_copy_vrs_files(
            request.files_to_import,
            destination=Path(request.destination_path),
            delete_src_after_copy=request.delete,
        )
        return await import_progress()
    except AriaException:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail=IMPORT_FILES_ERROR_CODE,
        )
    except FileExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=IMPORT_FILES_ALREADY_EXISTS_ERROR_CODE,
        )


@login_required
@router.get(
    "/import-progress",
    status_code=status.HTTP_200_OK,
    response_model=ImportStatusResponse,
    summary="Get the import progress of vrs files from the device. If no import is in progress, return 400.",
)
async def import_progress() -> ImportStatusResponse:
    """Get the import progress of vrs files from the device. If no import is in progress, return 400."""
    try:
        device_manager: DeviceManager = DeviceManager.get_instance()
        import_status: CopyStatus = await device_manager.get_copy_progress()

        return ImportStatusResponse(
            current_files=[Path(f).name for f in import_status.current_files],
            copied_files=[Path(f).name for f in import_status.copied_files],
            deleted_files=[Path(f).name for f in import_status.deleted_files],
            total_files=import_status.total_files,
            copied_bytes=import_status.copied_bytes,
            total_bytes=import_status.total_bytes,
            error=import_status.error,
            error_files=[Path(f).name for f in import_status.error_files],
        )
    except AriaException as e:
        if e.error_code == AriaError.DEVICE_NOT_CONNECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=DEVICE_NOT_CONNECTED_CODE,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=IMPORT_PROGRESS_ERROR_CODE,
        )


class ImportCancelResponse(BaseModel):
    """Import cancel response"""

    success: bool = Field(..., description="Whether the import was cancelled")


@login_required
@router.post(
    "/cancel-import",
    status_code=status.HTTP_200_OK,
    response_model=ImportCancelResponse,
    summary="Cancel the ongoing import of vrs files from the device.",
)
async def cancel_import() -> ImportCancelResponse:
    """
    Cancel the ongoing import of vrs files from the device.
    """
    try:
        device_manager: DeviceManager = DeviceManager.get_instance()
        await device_manager.cancel_copy()
        return ImportCancelResponse(success=True)
    except AriaException as e:
        logger.error(f"Failed to cancel import: {str(e)}")
        if e.error_code == AriaError.VRS_PULL_NOT_STARTED:
            # No import in progress
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=CANCEL_NO_IMPORT_ERROR_CODE,
            )
        elif e.error_code == AriaError.DEVICE_NOT_CONNECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=DEVICE_NOT_CONNECTED_CODE,
            )
        elif e.error_code == AriaError.PULL_FAILED:
            # Return false but don't raise an exception since this is an expected failure case
            return ImportCancelResponse(success=False)
        elif e.error_code == AriaError.CANCEL_FAILED:
            # Generic cancellation failure
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=CANCEL_IMPORT_ERROR_CODE,
            )
        else:
            # Unknown Aria error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=CANCEL_IMPORT_ERROR_CODE,
            )
    except Exception as e:
        logger.error(f"Unexpected error while cancelling import: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=CANCEL_IMPORT_ERROR_CODE,
        )


@login_required
@router.get(
    "/thumbnail_jpeg/{vrs_file}",
    status_code=status.HTTP_200_OK,
    summary="Get the jpeg thumbnail for a specified file",
)
async def thumbnail_jpeg(
    vrs_file: str,
) -> Response:
    """
    Retrieve the thumbnail for a specified file.
    Args:
        vrs_file (str): The name of the file to retrieve the thumbnail for.
    Returns:
        Response: The FileResponse object containing the thumbnail or
                  an empty Response in case there is no thumbnail for selected VRS file.
    Raises:
        HTTPException: If the device is not connected or if there is an error retrieving the thumbnail.
    """
    device_manager: DeviceManager = DeviceManager.get_instance()
    return await _get_thumbnail(vrs_file, device_manager.get_thumbnail_jpeg)


@login_required
@router.get(
    "/thumbnail_gif/{vrs_file}",
    status_code=status.HTTP_200_OK,
    summary="Get the gif thumbnail for a specified file",
)
async def thumbnail_gif(vrs_file: str) -> Response:
    """
    Retrieve the gif thumbnail for a specified file.
    Args:
        vrs_file (str): The name of the file to retrieve the thumbnail for.
    Returns:
        Response: The FileResponse object containing the thumbnail or
                  an empty Response in case there is no thumbnail for selected VRS file.
    Raises:
        HTTPException: If the device is not connected or if there is an error retrieving the thumbnail.
    """
    device_manager: DeviceManager = DeviceManager.get_instance()
    return await _get_thumbnail(vrs_file, device_manager.get_thumbnail_gif)


async def _get_thumbnail(
    vrs_file: str, callback: Callable[[str], Awaitable[Path]]
) -> Response:
    try:
        thumbnail: Path = await callback(vrs_file)
        return FileResponse(thumbnail)
    except AriaException as e:
        if e.error_code == AriaError.DEVICE_NOT_CONNECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=DEVICE_NOT_CONNECTED_CODE,
            )

        # Returns an empty response if the file is not found.
        # Treat it as nothing to display for provided recording.
        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=FILE_NOT_FOUND_ERROR_CODE
        )
