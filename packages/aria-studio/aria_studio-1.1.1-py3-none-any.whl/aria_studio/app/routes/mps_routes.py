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

from dataclasses import asdict
from http import HTTPStatus
from pathlib import Path

from typing import Annotated, Dict, List, Mapping, Optional, Set, Tuple

import jsons

from aria_studio.app.common.types import FeatureStatus, Group, VisualizationException

from aria_studio.app.constants import (
    KEY_ARIA_STUDIO_USER_FEEDBACK,
    KEY_CREATE,
    KEY_DATA,
    KEY_DESCRIPTION,
    KEY_EXTRA_INFO,
    KEY_ID,
    KEY_NODE,
    KEY_TASK_NUMBER,
    KEY_TITLE,
    MESSAGE_MPS_PREPARING,
    QUERY_CREATE_USER_FEEDBACK_ARIA_STUDIO,
    QUERY_ID_USER_FEEDBACK_ARIA_STUDIO,
)
from aria_studio.app.groups.group_manager import GroupManager
from aria_studio.app.local.local_log_manager import (
    LocalLogEvent,
    LocalLogManager,
    LocalLogScreen,
)
from aria_studio.app.mps.group_mps_request_manager import GroupMpsRequestManager
from aria_studio.app.mps.individual_mps_request_manager import (
    IndividualMpsRequestManager,
)
from aria_studio.app.return_codes import (
    FILE_NOT_FOUND_ERROR_CODE,
    MULTI_REQUEST_FAILED_ERROR_CODE,
    MULTI_REQUEST_FAILED_INVALID_GROUP_ERROR_CODE,
    MULTI_STATUS_FAILED_ERROR_CODE,
    NO_GROUPS_PROVIDED_ERROR_CODE,
    NO_VRS_FILES_OR_GROUP_PROVIDED_ERROR_CODE,
    NO_VRS_FILES_PROVIDED_ERROR_CODE,
    SINGLE_REQUEST_FAILED_ERROR_CODE,
)

from aria_studio.app.utils import CliHttpHelper, login_required, MpsConfigParser
from aria_studio.utils.mps_multi_rerun_task import (
    MpsMultiRerunTask,
    MpsMultiSingleRerunTask,
)
from aria_studio.utils.mps_single_rerun_task import MpsSingleRerunTask
from aria_studio.utils.rerun_manager import RerunManager

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from projectaria_tools.aria_mps_cli.cli_lib.common import Config

from projectaria_tools.aria_mps_cli.cli_lib.constants import (
    CONFIG_FILE,
    ConfigKey,
    ConfigSection,
)
from projectaria_tools.aria_mps_cli.cli_lib.types import MpsFeature, MpsRequest
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router: APIRouter = APIRouter()

logging_counter: int = 0


class MpsIndividualModel(BaseModel):
    """
    Arguments for MPS single feature processing mode.
    See MPS CLI argument list for more details:
    https://facebookresearch.github.io/projectaria_tools/docs/ARK/mps/request_mps/mps_cli_guide#command-line-reference
    """

    features: Set[MpsFeature] = Field(
        ..., description="Set of MPS features to request mps for"
    )
    input: List[Path] = Field(..., description="List of input file paths")

    retry_failed: Optional[bool] = Field(None, description="Retry failed mps request")
    force: Optional[bool] = Field(
        None, description="Force request mps for already requested file"
    )
    persist_on_failure: Optional[bool] = Field(
        False, description="Persist data on failure for debugging"
    )


class MpsMultiFeatureModel(BaseModel):
    """
    Arguments for MPS multi feature processing mode.
    See MPS CLI argument list for more details:
    https://facebookresearch.github.io/projectaria_tools/docs/ARK/mps/request_mps/mps_cli_guide#command-line-reference
    """

    groups: List[str] = Field(..., description="List of groups to process")

    retry_failed: Optional[bool] = Field(None, description="Retry failed mps request")
    force: Optional[bool] = Field(
        None, description="Force request mps for already requested file"
    )
    persist_on_failure: Optional[bool] = Field(
        False, description="Persist data on failure for debugging"
    )


class MultiRecordingRequestModel(BaseModel):
    force: bool = False
    suffix: str = ""
    retry_failed: bool = False
    output_dir: Path = ""


class IndividualStatusModel(BaseModel):
    vrs_paths: List[Path]


class IndividualRetryRequest(BaseModel):
    vrs_paths: List[Path] = Field(..., min_items=1)


class GroupHighLevelStatusModel(BaseModel):
    groups: List[str]


class ViewMpsRequest(BaseModel):
    vrs_path: Optional[Path] = None
    mps_path: Optional[Path] = None
    group_name: Optional[str] = None


class SingleRequestResponse(BaseModel):
    message: str


class MultiRequestResponse(BaseModel):
    message: str


class InvalidGroup(BaseModel):
    group_name: str
    deleted_files: List[str]


class InvalidGroupsResponse(BaseModel):
    msg: str
    invalid_groups: List[InvalidGroup]


def remove_none_values(d):
    """
    Recursively remove None values from a dictionary and empty lists.
    """

    if isinstance(d, dict):
        for key in list(d.keys()):
            if d[key] is None:
                del d[key]
            elif isinstance(d[key], list) and not d[key]:
                del d[key]
            else:
                remove_none_values(d[key])
    return d


@login_required
@router.get("/get-all-requests/")
async def get_all_requests() -> JSONResponse:
    requests: List[MpsRequest] = await CliHttpHelper.get().query_all_mps_requests()
    await LocalLogManager.log(
        event=LocalLogEvent.MPS_STATUS,
        screen=LocalLogScreen.SERVICES,
        message=f"Listing all {len(requests)} past user's MPS requests",
    )

    return {"requests": [remove_none_values(asdict(req)) for req in requests]}


@login_required
@router.post(
    "/view_mps",
    status_code=HTTPStatus.OK,
    summary="API to view MPS results along with the vrs file",
)
async def view_mps(request: ViewMpsRequest):
    """
    Execute a system call to open a file with viewer_mps.
    """

    if request.group_name:
        if request.vrs_path:
            # Return file data from group
            task: MpsMultiSingleRerunTask = MpsMultiSingleRerunTask(
                vrs=str(request.vrs_path), group_name=str(request.group_name)
            )
            try:
                # Verify the group exists and contains the file
                group = await task.get_group()
                if request.vrs_path not in group.vrs_files:
                    raise HTTPException(
                        status_code=HTTPStatus.NOT_FOUND,
                        detail="VRS file not found in group",
                    )
            except VisualizationException:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND, detail="Group not found"
                )
        else:
            # Return group data
            task: MpsMultiRerunTask = MpsMultiRerunTask(group_name=request.group_name)
            try:
                await task.get_group()
            except VisualizationException:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND, detail="Group not found"
                )
    elif request.vrs_path:
        # Return file data
        task: MpsSingleRerunTask = MpsSingleRerunTask(vrs=str(request.vrs_path))
    else:
        await LocalLogManager.log(
            event=LocalLogEvent.VISUALIZATION,
            screen=LocalLogScreen.FILES,
            message="Neither VRS file nor group provided for viewer_mps",
        )
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=NO_VRS_FILES_OR_GROUP_PROVIDED_ERROR_CODE,
        )
    manager: RerunManager = RerunManager()
    await manager.start_frozen_rerun()
    await manager.start_viewer(task)


@login_required
# TODO: T188502985 Remove old endpoint after the demo
# @router.post("/single/request")
@router.post(
    "/request-single/",
    status_code=status.HTTP_202_ACCEPTED,
    summary="API to request single MPS feature",
    response_model=SingleRequestResponse,
)
async def single_request(request: MpsIndividualModel):
    await LocalLogManager.log(
        event=LocalLogEvent.MPS_REQUEST,
        screen=LocalLogScreen.FILES,
        message=f"Requested MPS processing for {request.input} file",
    )

    if not request.input:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail=NO_VRS_FILES_PROVIDED_ERROR_CODE
        )
    for vrs_path in request.input:
        if not vrs_path.is_file():
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail=FILE_NOT_FOUND_ERROR_CODE
            )
        try:
            individual_request_manager: IndividualMpsRequestManager = (
                await IndividualMpsRequestManager.get_instance()
            )
            await individual_request_manager.create_request(
                vrs_path,
                request.features,
                request.force,
                request.retry_failed,
                request.persist_on_failure,
            )
        except Exception as e:
            logger.exception(e)
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=SINGLE_REQUEST_FAILED_ERROR_CODE,
            )

    return SingleRequestResponse(message=MESSAGE_MPS_PREPARING)


@login_required
@router.post(
    "/individual/retry",
    status_code=status.HTTP_201_CREATED,
    summary="API to retry failed inidividual MPS feature requests",
)
async def single_retry(request: IndividualRetryRequest):
    retried: bool = False
    logger.debug(f"Individual retry request for {request}")
    for vrs_path in set(request.vrs_paths):
        individual_request_manager: IndividualMpsRequestManager = (
            await IndividualMpsRequestManager.get_instance()
        )
        retried = await individual_request_manager.retry_if_failed(vrs_path) or retried
    return status.HTTP_201_CREATED if retried else status.HTTP_204_NO_CONTENT


@login_required
# TODO: T188502985 Remove old endpoint after the demo
# @router.post("/single/status")
@router.post("/check-processing-status/")
async def single_status(request: IndividualStatusModel):
    global logging_counter
    if logging_counter % 30 == 0:
        logging_counter = 0

    if not request.vrs_paths:
        await LocalLogManager.log(
            event=LocalLogEvent.MPS_STATUS,
            screen=LocalLogScreen.FILES,
            message="Cannot get MPS status for Recordings without providing their paths",
        )
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail=NO_VRS_FILES_PROVIDED_ERROR_CODE
        )
    status_per_file: Mapping[Path, Mapping[MpsFeature, FeatureStatus]] = {}
    for vrs_path in set(request.vrs_paths):
        if not vrs_path.is_file():
            await LocalLogManager.log(
                event=LocalLogEvent.MPS_STATUS,
                screen=LocalLogScreen.FILES,
                message=f"Cannot get MPS status for Recording {vrs_path}",
            )
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail=FILE_NOT_FOUND_ERROR_CODE
            )
        individual_request_manager: IndividualMpsRequestManager = (
            await IndividualMpsRequestManager.get_instance()
        )
        status_per_file[vrs_path] = await individual_request_manager.check_status(
            vrs_path
        )
    # TODO: T188502985 Remove old endpoint after the demo and fix the output schema
    # return status_per_file
    output_old_schema = {}
    for vrs_path, feature_status in status_per_file.items():
        last_request_time = 0
        for _, feature_status_item in feature_status.items():
            if feature_status_item and feature_status_item.creation_time:
                last_request_time = max(
                    last_request_time, feature_status_item.creation_time
                )

        output_old_schema[vrs_path] = {
            "features": feature_status,
            "last_request_date": last_request_time if last_request_time > 0 else None,
        }

        if logging_counter == 0:
            # check is performed about every 2 seconds, log it every minute
            await LocalLogManager.log(
                event=LocalLogEvent.MPS_STATUS,
                screen=LocalLogScreen.FILES,
                message=f"MPS status for {vrs_path} is: {', '.join([f'{k}: {v.status}' for k, v in feature_status.items()])}",
            )
            logger.debug(jsons.dump(output_old_schema, indent=2))

    logging_counter += 1
    return output_old_schema


class InvalidGroupsError(Exception):
    def __init__(self, response: InvalidGroupsResponse):
        self.response = response
        super().__init__(response.msg)


@login_required
@router.post(
    "/multi/request",
    status_code=HTTPStatus.ACCEPTED,
    response_model=MultiRequestResponse | InvalidGroupsResponse,
    summary="API to request multi MPS feature",
)
async def multi_request(
    request: MpsMultiFeatureModel,
) -> MultiRequestResponse | InvalidGroupsResponse:
    await LocalLogManager.log(
        event=LocalLogEvent.MPS_REQUEST,
        screen=LocalLogScreen.GROUPS,
        message=f"Requested MPS processing for {request.groups} file",
    )
    try:
        if not request.groups:
            raise Exception("No groups provided")
        group_mps_manager: GroupMpsRequestManager = (
            await GroupMpsRequestManager.get_instance()
        )
        # check if the groups are valid (there are no deleted files)
        group_manager: GroupManager = await GroupManager.get_instance()
        invalid_groups: List[InvalidGroup] = []
        for group_name in request.groups:
            deleted_files: List[str] = []
            group: Group = await group_manager.get(group_name)
            for file in group.vrs_files:
                if not file.exists():
                    deleted_files.append(file.name)
            if deleted_files:
                invalid_groups.append(
                    InvalidGroup(group_name=group_name, deleted_files=deleted_files)
                )
        if invalid_groups:
            raise InvalidGroupsError(
                InvalidGroupsResponse(
                    msg=MULTI_REQUEST_FAILED_INVALID_GROUP_ERROR_CODE,
                    invalid_groups=invalid_groups,
                )
            )
        for g in request.groups:
            await group_mps_manager.create_request(
                g, request.force, request.retry_failed, request.persist_on_failure
            )
        return MultiRequestResponse(message=MESSAGE_MPS_PREPARING)

    except InvalidGroupsError as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=e.response.dict(),
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail=MULTI_REQUEST_FAILED_ERROR_CODE
        )


def _get_high_level_status(
    status: Mapping[Path, Mapping[MpsFeature, FeatureStatus]],
) -> Tuple[Optional[str], Optional[int]]:
    logger.debug(f"Status is {status}")
    if not status:
        return None, None
    processing: bool = False
    for _, feature_feature_status in status.items():
        feature_status = feature_feature_status[MpsFeature.MULTI_SLAM]
        if feature_status.status == "Error":
            return "Failed", feature_status.error_code
        elif feature_status.status != "Success":
            processing = True
    s = "Processing" if processing else "Success"
    return s, None


@login_required
# TODO: T188502985 Remove old endpoint after the demo
# @router.post("/multi/status_summary")
@router.post("/multi/high_level_status")
async def multi_status_summary(request: GroupHighLevelStatusModel):
    ## TODO: strongly type the response
    global logging_counter
    if logging_counter % 30 == 0:
        logging_counter = 0

    status_by_group: Dict[str, str] = {}
    if not request.groups:
        await LocalLogManager.log(
            event=LocalLogEvent.MPS_STATUS,
            screen=LocalLogScreen.GROUPS,
            message="Cannot get MPS status for groups without providing their names",
        )
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail=NO_GROUPS_PROVIDED_ERROR_CODE
        )
    group_mps_manager: GroupMpsRequestManager = (
        await GroupMpsRequestManager.get_instance()
    )
    for group in request.groups:
        status = await group_mps_manager.check_status(group)
        status_by_group[group], err_code = _get_high_level_status(status)

        if logging_counter == 0:
            # check is performed about every 2 seconds, log it every minute
            await LocalLogManager.log(
                event=LocalLogEvent.MPS_STATUS,
                screen=LocalLogScreen.GROUPS,
                message=f"MPS status for {group} is: {status_by_group[group]}",
            )
            logger.info(f"MPS status for {group} is: {status_by_group[group]}")

    logging_counter += 1
    return JSONResponse(status_code=HTTPStatus.OK, content=jsons.dump(status_by_group))


@login_required
@router.get("/multi/status")
async def multi_status(group: str, vrs_path: Annotated[Path | None, Query()] = None):
    try:
        ## TODO: strongly type the response
        group_mps_manager: GroupMpsRequestManager = (
            await GroupMpsRequestManager.get_instance()
        )
        status_by_file = await group_mps_manager.check_status(group)
        output_old_schema = {}
        if status_by_file and vrs_path:
            if status_by_file and vrs_path not in status_by_file:
                await LocalLogManager.log(
                    event=LocalLogEvent.MPS_STATUS,
                    screen=LocalLogScreen.GROUPS,
                    message=f"Requested MPS status for VRS file {vrs_path} not found in group {group}",
                )
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND, detail="File not found"
                )
            # TODO: T188502985 Remove old endpoint after the demo and fix the output schema
            # return status_per_file
            # return status.get(vrs_path, {})
            if vrs_path not in status_by_file:
                await LocalLogManager.log(
                    event=LocalLogEvent.MPS_STATUS,
                    screen=LocalLogScreen.GROUPS,
                    message=f"Requested MPS status for VRS file {vrs_path} not found in group {group}",
                )
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND, detail="File not found"
                )
            feature_status = status_by_file[vrs_path]
            last_request_time = 0
            for _, f_status in feature_status.items():
                last_request_time = max(last_request_time, f_status.creation_time or 0)

            output_old_schema[vrs_path] = {
                "features": feature_status,
                "last_request_date": (
                    last_request_time if last_request_time > 0 else None
                ),
            }
        elif status_by_file:
            group_status, err_code = _get_high_level_status(status_by_file)
            last_request_time = 0
            for _, feature_status in status_by_file.items():
                for _, feature_status_item in feature_status.items():
                    last_request_time = max(
                        last_request_time, feature_status_item.creation_time or 0
                    )
            last_request_time = last_request_time if last_request_time > 0 else None
            group_manager: GroupManager = await GroupManager.get_instance()
            output_old_schema[group] = {
                "features": {
                    MpsFeature.MULTI_SLAM: FeatureStatus(
                        status=group_status,
                        # Error code is a string for more flexibility.
                        error_code=err_code,
                        creation_time=last_request_time,
                        output_path=(await group_manager.get(group)).path_on_device,
                    ),
                },
                "last_request_date": last_request_time,
            }

        try:
            status: str = output_old_schema[
                vrs_path if vrs_path is not None else group
            ]["features"][MpsFeature.MULTI_SLAM].status
        except KeyError:
            # it group not in the output schema, it means that it has not been requested yet
            status: str = "None"

        await LocalLogManager.log(
            event=LocalLogEvent.MPS_STATUS,
            screen=LocalLogScreen.GROUPS,
            message=f"MPS status for group {group} is {status}",
        )
        return output_old_schema
    except Exception as e:
        await LocalLogManager.log(
            event=LocalLogEvent.MPS_STATUS,
            screen=LocalLogScreen.GROUPS,
            message=f"Cannot get MPS status for group {group}",
        )
        logger.exception(e)
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail=MULTI_STATUS_FAILED_ERROR_CODE
        )


class DefaultConfig(BaseModel):
    """Default section of MPS CLI settings response"""

    log_dir: Optional[str] = Field(
        None, description="The local path to stroe logs from MPS CLI"
    )
    status_check_interval: Optional[int] = Field(
        None, description="Status check interval in seconds"
    )


class HashConfig(BaseModel):
    """Hash section of MPS CLI settings response"""

    concurrent_hashes: Optional[int] = Field(
        None, description="Number of concurrent hashes"
    )
    chunk_size: Optional[int] = Field(None, description="Hash chunk size")


class HealthCheckConfig(BaseModel):
    """Health check section of MPS CLI settings response"""

    concurrent_health_checks: Optional[int] = Field(
        None, description="Number of concurrent health checks"
    )


class EncryptionConfig(BaseModel):
    """Encryption section of MPS CLI settings response"""

    chunk_size: Optional[int] = Field(None, description="Encryption chunk size")
    concurrent_encryptions: Optional[int] = Field(
        None, description="Number of concurrent encryptions"
    )
    delete_encrypted_files: Optional[bool] = Field(
        None, description="Delete encrypted files"
    )


class UploadConfig(BaseModel):
    """Upload section of MPS CLI settings response"""

    backoff: Optional[float] = Field(None, description="Backoff time in seconds")
    concurrent_uploads: Optional[int] = Field(
        None, description="Number of concurrent uploads"
    )
    interval: Optional[int] = Field(None, description="Upload interval in seconds")
    max_chunk_size: Optional[int] = Field(None, description="Max chunk size")
    min_chunk_size: Optional[int] = Field(None, description="Min chunk size")
    retries: Optional[int] = Field(None, description="Number of retries")
    smoothing_window_size: Optional[int] = Field(
        None, description="Smoothing window size"
    )
    target_chunk_upload_secs: Optional[int] = Field(
        None, description="Target chunk upload time in seconds"
    )


class DownloadConfig(BaseModel):
    """Download section of MPS CLI settings response"""

    backoff: Optional[float] = Field(None, description="Backoff factor")
    chunk_size: Optional[int] = Field(None, description="Chunk size")
    concurrent_downloads: Optional[int] = Field(
        None, description="Number of concurrent downloads"
    )
    delete_zip: Optional[bool] = Field(None, description="Delete zip file")
    interval: Optional[int] = Field(None, description="Download interval in seconds")
    retries: Optional[int] = Field(None, description="Number of retries")


class GraphQLConfig(BaseModel):
    """GraphQL section of MPS CLI settings response"""

    backoff: Optional[float] = Field(None, description="Backoff factor")
    interval: Optional[int] = Field(None, description="GraphQL interval in seconds")
    retries: Optional[int] = Field(None, description="Number of retries")


class MPSConfig(BaseModel):
    """MPS CLI settings response model"""

    DEFAULT: Optional[DefaultConfig] = Field(
        None, description="Default section of MPS CLI settings response"
    )
    HASH: Optional[HashConfig] = Field(
        None, description="Hash section of MPS CLI settings response"
    )
    HEALTH_CHECK: Optional[HealthCheckConfig] = Field(
        None, description="Health check section of MPS CLI settings response"
    )
    ENCRYPTION: Optional[EncryptionConfig] = Field(
        None, description="Encryption section of MPS CLI settings response"
    )
    UPLOAD: Optional[UploadConfig] = Field(
        None, description="Upload section of MPS CLI settings response"
    )
    DOWNLOAD: Optional[DownloadConfig] = Field(
        None, description="Download section of MPS CLI settings response"
    )
    GRAPHQL: Optional[GraphQLConfig] = Field(
        None, description="GraphQL section of MPS CLI settings response"
    )


@router.get(
    "/settings",
    response_model=MPSConfig,
    status_code=status.HTTP_200_OK,
    summary="API to read the mps.ini file for MPS CLI configuration",
)
def get_mps_settings() -> MPSConfig:
    if not CONFIG_FILE.is_file():
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Config file not found"
        )
    try:
        config = MpsConfigParser(inline_comment_prefixes="#")
        config.read(CONFIG_FILE)
        json_data = config.ini_to_json()
        return MPSConfig(**json_data)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Unable to read config"
        )


@router.post(
    "/settings",
    status_code=status.HTTP_200_OK,
    summary="API to update the mps.ini file",
)
def update_mps_config(request: MPSConfig) -> JSONResponse:
    if not CONFIG_FILE.is_file():
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Config file not found"
        )
    try:
        config = MpsConfigParser(inline_comment_prefixes="#")
        config.read(CONFIG_FILE)
        # remove the unset values from the request model
        updated_config = request.dict(exclude_unset=True)
        config.update_to_ini(updated_config)
        # Reload the config from the Project Aria Tools mps cli Config class to update the values
        Config.reload()
        return JSONResponse(
            status_code=HTTPStatus.OK,
            content={"message": "Config updated successfully"},
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Failed to update config"
        )


@router.post(
    "/settings_restore",
    status_code=status.HTTP_200_OK,
    summary="API to restore the mps.ini file to its default values",
)
async def restore_mps_config() -> JSONResponse:
    try:
        c = MpsConfigParser()
        # Access the default config from the Project Aria Tools mps cli Config class
        # c.read_dict(Config.DEFAULT_CONFIG)
        # Default config values to use till new PAT release, delete after new PAT release
        DEFAULT_CONFIG: Dict[str, Dict[str, str]] = {
            ConfigSection.DEFAULT: {
                ConfigKey.LOG_DIR: "/tmp/logs/projectaria/mps/ # Path to log directory",
                ConfigKey.STATUS_CHECK_INTERVAL: "30 # Status check interval in seconds",
            },
            ConfigSection.HASH: {
                ConfigKey.CONCURRENT_HASHES: "4 # Maximum number of recordings whose hashes will be calculated concurrently",
                ConfigKey.CHUNK_SIZE: "10485760 # 10 * 2**20 (10MB)",
            },
            ConfigSection.HEALTH_CHECK: {
                ConfigKey.CONCURRENT_HEALTH_CHECKS: "2  # Maximum number of checks that can run concurrently",
            },
            ConfigSection.ENCRYPTION: {
                ConfigKey.CHUNK_SIZE: "52428800 # 50 * 2**20 (50MB)",
                ConfigKey.CONCURRENT_ENCRYPTIONS: "5 # Maximum number of recordings that will be encrypted concurrently",
                ConfigKey.DELETE_ENCRYPTED_FILES: "true # Delete encrypted files after upload is done",
            },
            ConfigSection.UPLOAD: {
                ConfigKey.BACKOFF: "1.5 # Backoff factor for retries",
                ConfigKey.CONCURRENT_UPLOADS: "4 # Maximum number of concurrent uploads",
                ConfigKey.INTERVAL: "20 # Interval between runs",
                ConfigKey.MAX_CHUNK_SIZE: "104857600 # 100 * 2**20 (100 MB)",
                ConfigKey.MIN_CHUNK_SIZE: "5242880 # 5 * 2**20 (5MB)",
                ConfigKey.RETRIES: "10 # Number of times to retry a failed upload",
                ConfigKey.SMOOTHING_WINDOW_SIZE: "10 # Size of the smoothing window",
                ConfigKey.TARGET_CHUNK_UPLOAD_SECS: "3 # Target duration to upload a chunk",
            },
            ConfigSection.DOWNLOAD: {
                ConfigKey.BACKOFF: "1.5 # Backoff factor for retries",
                ConfigKey.CHUNK_SIZE: "10485760 # 10 * 2**20 (10MB)",
                ConfigKey.CONCURRENT_DOWNLOADS: "10 # Maximum number of concurrent downloads",
                ConfigKey.DELETE_ZIP: "true # Delete zip files after extracting",
                ConfigKey.INTERVAL: "20 # Interval between runs",
                ConfigKey.RETRIES: "10 # Number of times to retry a failed upload",
            },
            ConfigSection.GRAPHQL: {
                ConfigKey.BACKOFF: "1.5 # Backoff factor for retries",
                ConfigKey.INTERVAL: "4 # Interval between runs",
                ConfigKey.RETRIES: "3 # Number of times to retry a failed upload",
            },
        }
        c.read_dict(DEFAULT_CONFIG)
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with CONFIG_FILE.open("w") as fd:
            c.write(fd)
        # Reload the Config from the Project Aria Tools mps cli Config class to update the values
        Config.reload()
        return JSONResponse(
            status_code=HTTPStatus.OK,
            content={"message": "Config restored successfully"},
        )
    except Exception as e:
        await LocalLogManager.log(
            event=LocalLogEvent.MPS_SETTINGS,
            screen=LocalLogScreen.SETTINGS,
            message="Failed to restore default config of MPS",
        )
        logger.exception(e)
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Failed to restore config"
        )


class AriaStudioUserFeedbackResponse(BaseModel):
    task_number: str = Field(..., description="The task number of the user feedback")


class DebugSharingMpsIndividualModel(MpsIndividualModel):
    title: str = Field(..., description="Title of the user feedback")
    description: str = Field(..., description="Description of the user feedback")
    ticket_type: str = Field("BUG", description="Type of the user feedback")


class DebugSharingMpsMultiFeatureModel(MpsMultiFeatureModel):
    title: str = Field(..., description="Title of the user feedback")
    description: str = Field(..., description="Description of the user feedback")
    ticket_type: str = Field("BUG", description="Type of the user feedback")


async def create_user_feedback(
    title: str, description: str, ticket_type: str = "BUG"
) -> str:
    """
    Create user feedback via GraphQL and return feedback_id.
    Args:
        title (str): The title of the user feedback ticket.
        description (str): The detailed description of the user feedback.
        ticket_type (str, optional): The type/category of the ticket being created.
            Defaults to "BUG". This value is prefixed to the title.
    Returns:
        str: The feedback_id of the newly created user feedback ticket.
    Raises:
        HTTPException: If the feedback creation fails, an HTTP 400 error is raised.
    """
    try:
        variables = {
            KEY_DATA: {
                KEY_TITLE: f"{ticket_type} {title}",
                KEY_DESCRIPTION: description,
                KEY_EXTRA_INFO: await LocalLogManager.get_device_info_entry(),
            }
        }

        response = await CliHttpHelper.get().query_graph(
            doc_id=QUERY_CREATE_USER_FEEDBACK_ARIA_STUDIO,
            variables=variables,
        )
        return response[KEY_DATA][KEY_CREATE][KEY_ARIA_STUDIO_USER_FEEDBACK][KEY_ID]
    except Exception as e:
        logger.exception("Failed to create user feedback", exc_info=e)
        await LocalLogManager.log(
            event=LocalLogEvent.MPS_REQUEST,
            screen=LocalLogScreen.FILES,
            message="Failed to create user feedback",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user feedback",
        )


async def poll_task_number(
    feedback_id: str, max_retries: int = 5, delay: float = 10.0
) -> Optional[int]:
    """
    Polls for the task number associated with the given feedback_id.
    Args:
        feedback_id (str): The unique identifier for the user feedback whose task number is being polled.
        max_retries (int, optional): The maximum number of polling attempts before giving up. Defaults to 5.
        delay (float, optional): The delay (in seconds) between polling attempts. Defaults to 10.0.
    Returns:
        Optional[int]: The task number associated with the feedback_id if found within the retry limit,
        otherwise None.
    Raises:
        This function does not raise, but logs errors internally if polling fails.
    """
    for attempt in range(max_retries):
        try:
            response = await CliHttpHelper.get().query_graph(
                doc_id=QUERY_ID_USER_FEEDBACK_ARIA_STUDIO,
                variables={KEY_ID: feedback_id},
            )
            task_number = response[KEY_DATA][KEY_NODE][KEY_TASK_NUMBER]
            if task_number:
                return task_number
        except Exception as e:
            logger.info(f"Polling attempt {attempt+1} failed", exc_info=e)
            await LocalLogManager.log(
                event=LocalLogEvent.MPS_REQUEST,
                screen=LocalLogScreen.FILES,
                message=f"Polling attempt {attempt+1} failed",
            )
        await asyncio.sleep(delay)
    return None


@login_required
@router.post(
    "/debug_sharing_single",
    status_code=status.HTTP_200_OK,
    response_model=AriaStudioUserFeedbackResponse,
    summary="Create task in meta for user feedback submitted through Aria Studio",
)
async def debug_sharing_single(
    request: DebugSharingMpsIndividualModel,
) -> AriaStudioUserFeedbackResponse:
    """
    Handles single-file user feedback for Aria Studio.
    """
    if not request.input:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=NO_VRS_FILES_PROVIDED_ERROR_CODE,
        )

    for vrs_path in request.input:
        if not vrs_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=FILE_NOT_FOUND_ERROR_CODE,
            )

    log_message = f"Requested Debug Sharing MPS processing for {request.input} file"
    await LocalLogManager.log(
        event=LocalLogEvent.MPS_REQUEST,
        screen=LocalLogScreen.FILES,
        message=log_message,
    )

    input_filenames = [path.name for path in request.input]
    description = "\n".join(
        [request.description, f"Input: {', '.join(input_filenames)}"]
    )

    feedback_id = await create_user_feedback(
        request.title, description, request.ticket_type
    )

    individual_request_manager = await IndividualMpsRequestManager.get_instance()
    failed_tasks = []
    for vrs_path in request.input:
        try:
            await individual_request_manager.create_request(
                vrs_path,
                request.features,
                request.force,
                request.retry_failed,
                request.persist_on_failure,
                feedback_id,
            )
        except Exception as e:
            logger.exception("Failed to create individual MPS request", exc_info=e)
            failed_tasks.append((vrs_path, str(e)))

    if failed_tasks:
        for vrs_path, error in failed_tasks:
            log_message = (
                f"Failed to create individual MPS request for {vrs_path}: {error}"
            )
            await LocalLogManager.log(
                event=LocalLogEvent.MPS_REQUEST,
                screen=LocalLogScreen.FILES,
                message=log_message,
            )
        if len(failed_tasks) == len(request.input):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=SINGLE_REQUEST_FAILED_ERROR_CODE,
            )

    task_number = await poll_task_number(feedback_id)
    if not task_number:
        await LocalLogManager.log(
            event=LocalLogEvent.MPS_REQUEST,
            screen=LocalLogScreen.FILES,
            message="Failed to fetch task number",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch task number",
        )

    return AriaStudioUserFeedbackResponse(task_number=task_number)


@login_required
@router.post(
    "/debug_sharing_multi_mps",
    status_code=status.HTTP_200_OK,
    response_model=AriaStudioUserFeedbackResponse,
    summary="Create task in meta for user feedback submitted through Aria Studio",
)
async def debug_sharing_multi_mps(
    request: DebugSharingMpsMultiFeatureModel,
) -> AriaStudioUserFeedbackResponse:
    """
    Handles multi-group user feedback for Aria Studio.
    """
    if not request.groups:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No groups provided"
        )

    # Validate all groups and collect invalid ones
    group_manager = await GroupManager.get_instance()
    invalid_groups = []
    for group_name in request.groups:
        group = await group_manager.get(group_name)
        deleted_files = [file.name for file in group.vrs_files if not file.exists()]
        if deleted_files:
            invalid_groups.append(
                InvalidGroup(group_name=group_name, deleted_files=deleted_files)
            )
    if invalid_groups:
        # Raise immediately if any group is invalid
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=InvalidGroupsResponse(
                msg=MULTI_REQUEST_FAILED_INVALID_GROUP_ERROR_CODE,
                invalid_groups=invalid_groups,
            ).dict(),
        )

    log_message = f"Requested MPS processing for {request.groups} file"
    await LocalLogManager.log(
        event=LocalLogEvent.MPS_REQUEST,
        screen=LocalLogScreen.GROUPS,
        message=log_message,
    )

    # Collect file names from all groups
    all_filenames = []
    for group_name in request.groups:
        group = await group_manager.get(group_name)
        group_filenames = [file.name for file in group.vrs_files]
        all_filenames.extend(group_filenames)

    description = "\n".join(
        [
            request.description,
            f"Groups: {', '.join(request.groups)}",
            f"Files: {', '.join(all_filenames)}",
        ]
    )
    feedback_id = await create_user_feedback(
        request.title, description, request.ticket_type
    )

    # Try to submit requests for all groups, log failures, and only raise if all fail
    group_mps_manager = await GroupMpsRequestManager.get_instance()
    failed_groups = []
    succeeded = False
    for group_name in request.groups:
        try:
            await group_mps_manager.create_request(
                group_name,
                request.force,
                request.retry_failed,
                request.persist_on_failure,
                feedback_id,
            )
            succeeded = True
        except Exception as e:
            logger.exception(
                f"Failed to create group MPS request for {group_name}", exc_info=e
            )
            failed_groups.append((group_name, str(e)))
            await LocalLogManager.log(
                event=LocalLogEvent.MPS_REQUEST,
                screen=LocalLogScreen.GROUPS,
                message=f"Failed to create group MPS request for {group_name}: {e}",
            )

    if not succeeded:
        # All requests failed
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MULTI_REQUEST_FAILED_ERROR_CODE,
        )

    # Continue as normal if at least one succeeded
    task_number = await poll_task_number(feedback_id)
    if not task_number:
        await LocalLogManager.log(
            event=LocalLogEvent.MPS_REQUEST,
            screen=LocalLogScreen.GROUPS,
            message="Failed to fetch task number",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch task number",
        )
    return AriaStudioUserFeedbackResponse(task_number=task_number)
