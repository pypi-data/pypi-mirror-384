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
import shutil
from http import HTTPStatus
from pathlib import Path
from typing import Any, Dict, List, Mapping

import jsons

from aria_studio.app.groups.group_manager import (
    GroupManager,
    GroupMPSRequestExistsException,
)
from aria_studio.app.local.local_log_manager import (
    LocalLogEvent,
    LocalLogManager,
    LocalLogScreen,
)
from aria_studio.app.return_codes import (
    ADD_FILES_FAILED_ERROR_CODE,
    DELETE_GROUP_FAILED_ERROR_CODE,
    GROUP_MPS_REQUEST_EXISTS_ERROR_CODE,
    GROUP_NOT_CREATED_ERROR_CODE,
    IS_ALLOWED_GROUP_FAILED_ERROR_CODE,
    LIST_GROUPS_FAILED_ERROR_CODE,
    REMOVE_FILES_FAILED_ERROR_CODE,
)

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class GroupResponse(BaseModel):
    """
    Response providin singe group details
    """

    name: str = Field(..., description="THe name of the group")
    path_on_device: Path = Field(
        ..., description="The local path on the host device, where the group is stored"
    )
    creation_time: int = Field(..., description="The time the group was created")
    vrs_files: Dict[Path, bool] = Field(
        ..., description="The mapping of files to their existence"
    )


class CreateGroupModel(BaseModel):
    name: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)


class DeleteGroupsModel(BaseModel):
    names: List[str]


class AddFilesModel(BaseModel):
    name: str
    paths: List[Path]


class RemoveFilesModel(BaseModel):
    name: str
    paths: List[Path]


# TODO: Get logging working with FASTAPI
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/list",
    response_model=List[GroupResponse],
    summary="List all groups",
    status_code=HTTPStatus.OK,
)
async def list_groups() -> List[GroupResponse]:
    """
    Lists all the available groups
    """
    try:
        group_manager: GroupManager = await GroupManager.get_instance()
        groups = await group_manager.get_all()
        response: List[GroupResponse] = []
        for group in groups.values():
            response.append(
                GroupResponse(
                    name=group.name,
                    path_on_device=group.path_on_device,
                    creation_time=group.creation_time,
                    vrs_files={f: f.exists() for f in group.vrs_files},
                )
            )

        return response
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail=LIST_GROUPS_FAILED_ERROR_CODE
        )


@router.post("/create")
async def create_group(grp: CreateGroupModel) -> JSONResponse:
    """
    Create a group
    """
    group_path: Path = Path(grp.path)

    try:
        group_manager: GroupManager = await GroupManager.get_instance()
        await group_manager.create_group(grp.name, group_path)
        await LocalLogManager.log(
            event=LocalLogEvent.CREATE_GROUP,
            screen=LocalLogScreen.GROUPS,
            message=f"Group {grp.name} created with path {group_path}",
        )
        return JSONResponse(status_code=HTTPStatus.OK, content=None)
    except Exception as e:
        logger.exception(e)
        await LocalLogManager.log(
            event=LocalLogEvent.CREATE_GROUP,
            screen=LocalLogScreen.GROUPS,
            message=f"Cannot create group {grp.name} with path {group_path}",
        )
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail=GROUP_NOT_CREATED_ERROR_CODE
        )


@router.post("/delete")
async def delete_groups(request: DeleteGroupsModel) -> JSONResponse:
    """
    Delete groups from both database and filesystem
    """
    try:
        if not request.names:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="No groups provided"
            )

        deleted_groups: List[str] = []
        failed_groups: List[dict] = []

        for name in request.names:
            logger.debug(f"Deleting group {name}")
            try:
                # Get group filesystem path before deleting from database
                group_manager: GroupManager = await GroupManager.get_instance()
                group_path = await group_manager.get_group_path(name)

                # Delete from database first
                await group_manager.delete_group(name)

                # Delete folder if it exists
                if group_path and os.path.exists(group_path):
                    try:
                        shutil.rmtree(group_path)
                        logger.info(f"Successfully deleted group folder: {group_path}")
                    except OSError as os_err:
                        logger.error(
                            f"Failed to delete group folder {group_path}: {os_err}"
                        )
                        # TODO: If filesystem deletion fails, we might want to roll back the database deletion
                        # await group_manager.restore_group(name)
                        failed_groups.append(
                            {
                                "name": name,
                                "error": f"Database entry deleted but folder removal failed: {str(os_err)}",
                            }
                        )
                        continue

                deleted_groups.append(name)
                logger.info(
                    f"Successfully deleted group {name} from both database and filesystem"
                )

            except Exception as e:
                logger.error(f"Error deleting group {name}: {e}")
                failed_groups.append({"name": name, "error": str(e)})

        response_data = {
            "deleted_groups": deleted_groups,
            "failed_groups": failed_groups,
        }

        # If some deletions failed but others succeeded, return partial success
        if deleted_groups and failed_groups:
            return JSONResponse(
                status_code=HTTPStatus.PARTIAL_CONTENT, content=response_data
            )
        # If all failed, return error
        elif not deleted_groups and failed_groups:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=DELETE_GROUP_FAILED_ERROR_CODE,
            )
        # All succeeded
        return JSONResponse(content=response_data)

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=DELETE_GROUP_FAILED_ERROR_CODE,
        )


@router.post("/add_files")
async def add_files_to_group(inp: AddFilesModel) -> JSONResponse:
    """
    Add list of files to a group
    """
    logger.info(f"Adding {inp.paths} to group {inp.name}")
    try:
        group_manager: GroupManager = await GroupManager.get_instance()
        await group_manager.add_files(inp.name, inp.paths)

        await LocalLogManager.log(
            event=LocalLogEvent.CREATE_GROUP,
            screen=LocalLogScreen.FILES,
            message=f"Group {inp.name} was updated with files: {':'.join(str(path) for path in inp.paths)}",
        )
        return JSONResponse(status_code=HTTPStatus.OK, content=None)

    except GroupMPSRequestExistsException as e:
        logger.exception(e)
        await LocalLogManager.log(
            event=LocalLogEvent.CREATE_GROUP,
            screen=LocalLogScreen.FILES,
            message=f"Group {inp.name} MPS already requested, cannot add more files {':'.join(str(path) for path in inp.paths)}",
        )
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=GROUP_MPS_REQUEST_EXISTS_ERROR_CODE,
        )
    except Exception as e:
        logger.exception(e)
        await LocalLogManager.log(
            event=LocalLogEvent.CREATE_GROUP,
            screen=LocalLogScreen.FILES,
            message=f"Group {inp.name} cannot include files {':'.join(str(path) for path in inp.paths)}",
        )

        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail=ADD_FILES_FAILED_ERROR_CODE
        )


@router.post("/remove_files")
async def remove_files_from_group(inp: RemoveFilesModel) -> JSONResponse:
    """
    Remove a list of files from a group
    """
    logger.debug(f"Removing {inp.paths} from group {inp.name}")
    try:
        group_manager: GroupManager = await GroupManager.get_instance()
        group = await group_manager.remove_files(inp.name, inp.paths)
        return JSONResponse(status_code=HTTPStatus.OK, content=jsons.dump(group))
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail=REMOVE_FILES_FAILED_ERROR_CODE
        )


@router.get("/is_allowed")
async def is_allowed(group_name: str) -> JSONResponse:
    """
    Check if a group name is allowed to be used
    """
    result: Mapping[str, Any] = {}
    try:
        group_manager: GroupManager = await GroupManager.get_instance()
        result["allowed"] = not (await group_manager.exists(group_name))
        if result["allowed"]:
            result["detail"] = f"Group name '{group_name}' is allowed"
        else:
            result["detail"] = f"Group '{group_name}' already exists"
        return JSONResponse(status_code=HTTPStatus.OK, content=jsons.dump(result))
    except Exception:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=IS_ALLOWED_GROUP_FAILED_ERROR_CODE,
        )
