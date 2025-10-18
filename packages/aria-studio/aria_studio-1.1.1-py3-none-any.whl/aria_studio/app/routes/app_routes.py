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
import random
import shutil

from datetime import datetime
from enum import auto, Enum, unique
from http import HTTPStatus
from typing import Final, List, Optional

from aria_studio.app.constants import CACHE_DIR
from aria_studio.app.local.app_info import AppInfoManager
from aria_studio.app.local.local_log_manager import (
    LocalLogEntry,
    LocalLogEvent,
    LocalLogManager,
    LocalLogScreen,
    LocalLogSurface,
    LogLevel,
)
from aria_studio.app.utils import CliHttpHelper, login_required

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field


_QUERY_ID_VERSION: Final[int] = 8637461982965576
_QUERY_ID_ANNOUNCEMENTS: Final[int] = 8601031413314256
_QUERY_ID_SUBMIT_BUG: Final[int] = 8570081129707140

_KEY_DATA: Final[str] = "data"
_KEY_RESPONSE_TITLE: Final[str] = "title"
_KEY_RESPONSE_DESCRIPTION: Final[str] = "description"
_KEY_RESPONSE_CLIENT_MUTATION_ID: Final[str] = "client_mutation_id"

_KEY_INPUT_APP_VERSION: Final[str] = "app_version"
_KEY_INPUT_CPU_ARCHITECTURE: Final[str] = "cpu_architecture"
_KEY_INPUT_HOST_OS_PRODUCT_TYPE: Final[str] = "host_os_product_type"
_KEY_INPUT_PRETTY_HOST_OS_PRODUCT_NAME: Final[str] = "pretty_host_os_product_name"

_KEY_INPUT_VISIBLE_ONLY: Final[str] = "visible_only"

_KEY_INPUT_TITLE: Final[str] = "title"
_KEY_INPUT_DESCRIPTION: Final[str] = "description"
_KEY_INPUT_EXTRA_INFO: Final[str] = "extra_info"

_KEY_RESPONSE_QUERY_VERSION: Final[str] = "query_version"
_KEY_RESPONSE_MESSAGE: Final[str] = "message"
_KEY_RESPONSE_MODE: Final[str] = "mode"
_KEY_RESPONSE_INSTRUCTION: Final[str] = "instruction"
_KEY_RESPONSE_LEARN_MORE: Final[str] = "learn_more_link"
_KEY_RESPONSE_READ_INSTRUCTION: Final[str] = "read_instruction_link"

_KEY_RESPONSE_QUERY_ANNOUNCEMENTS: Final[str] = "announcements"
_KEY_RESPONSE_VISIBLE_FROM: Final[str] = "visible_from"
_KEY_RESPONSE_CONTENT: Final[str] = "content"
_KEY_RESPONSE_SUBTITLE: Final[str] = "subtitle"
_KEY_RESPONSE_BODY: Final[str] = "body"

_CLIENT_MUTATION_ID_MIN: Final[int] = 1_000
_CLIENT_MUTATION_ID_MAX: Final[int] = 999_999_999

logger = logging.getLogger(__name__)

router = APIRouter()


class AriaStudioVersion(BaseModel):
    """Response from the application endpoint for application's version request"""

    version: str = Field(..., description="The current version of the Aria Studio")


class CacheClearResponse(BaseModel):
    """Response from the cache clear endpoint"""

    message: str = Field(..., description="Cache clear message")


@router.get(
    "/version",
    status_code=status.HTTP_200_OK,
    response_model=AriaStudioVersion,
    summary="Gets the Aria Studio Version",
)
async def check_version() -> AriaStudioVersion:
    """
    Gets the Aria Studio Version
    """
    app_info_manager: AppInfoManager = AppInfoManager()
    version = await app_info_manager.get_version()
    return AriaStudioVersion(version=version)


@unique
class UpdateMode(str, Enum):
    """
    The importance of the update
    """

    def _generate_next_value_(name, start, count, last_values):  # noqa: B902
        return name.upper()

    BLOCK = auto()
    HIGH = auto()

    def __str__(self):
        return self.name

    @classmethod
    def from_name(cls, name: str) -> "UpdateMode":
        for mode in cls:
            if mode.name == name:
                return mode
        raise ValueError(f"Unknown update mode: {name}")


class AriaStudioVersionUpdateResponse(BaseModel):
    """Response for query, if Aria Studio's update is available"""

    title: Optional[str] = Field(
        None, description="The title of the update", nullable=True
    )
    message: Optional[str] = Field(
        None, description="Details of the update", nullable=True
    )
    mode: Optional[UpdateMode] = Field(
        None, description="Importance of the update", nullable=True
    )
    learn_more_link: Optional[str] = Field(
        None,
        description="The link with more information about the update",
        nullable=True,
    )
    read_instruction_link: Optional[str] = Field(
        None,
        description="The link with detailed update instructions for Aria Studio",
        nullable=True,
    )
    instruction: Optional[str] = Field(
        None, description="Installation instructions for the update", nullable=True
    )


@login_required
@router.get(
    "/update",
    status_code=status.HTTP_200_OK,
    response_model=AriaStudioVersionUpdateResponse,
    summary="Gets the information, if Aria Studio's update is available",
)
async def check_update() -> AriaStudioVersionUpdateResponse:
    """
    Gets the information, if Aria Studio's update is available
    """
    app_info_manager: AppInfoManager = AppInfoManager()
    version = await app_info_manager.get_version()
    response = await CliHttpHelper.get().query_graph(
        doc_id=_QUERY_ID_VERSION,
        variables={
            _KEY_DATA: {
                _KEY_INPUT_APP_VERSION: version,
                _KEY_INPUT_CPU_ARCHITECTURE: f"{platform.machine()}-{platform.processor()}",
                _KEY_INPUT_HOST_OS_PRODUCT_TYPE: platform.system(),
                _KEY_INPUT_PRETTY_HOST_OS_PRODUCT_NAME: platform.platform(),
            }
        },
    )

    if response[_KEY_DATA][_KEY_RESPONSE_QUERY_VERSION] is None:
        return AriaStudioVersionUpdateResponse()

    title: str = response[_KEY_DATA][_KEY_RESPONSE_QUERY_VERSION][_KEY_RESPONSE_TITLE]
    await LocalLogManager.log(
        event=LocalLogEvent.UPDATE,
        screen=LocalLogScreen.HOME,
        message=f"Found valid update: {title}",
    )

    return AriaStudioVersionUpdateResponse(
        title=title,
        message=response[_KEY_DATA][_KEY_RESPONSE_QUERY_VERSION][_KEY_RESPONSE_MESSAGE],
        mode=UpdateMode.from_name(
            response[_KEY_DATA][_KEY_RESPONSE_QUERY_VERSION][_KEY_RESPONSE_MODE],
        ),
        learn_more_link=response[_KEY_DATA][_KEY_RESPONSE_QUERY_VERSION][
            _KEY_RESPONSE_LEARN_MORE
        ],
        read_instruction_link=response[_KEY_DATA][_KEY_RESPONSE_QUERY_VERSION][
            _KEY_RESPONSE_READ_INSTRUCTION
        ],
        instruction=response[_KEY_DATA][_KEY_RESPONSE_QUERY_VERSION][
            _KEY_RESPONSE_INSTRUCTION
        ],
    )


@router.get("/clear_cache", status_code=status.HTTP_200_OK, summary="Clears the cache")
async def clear_cache() -> None:
    """
    Clears the cache
    """
    try:
        logger.info("Clearing cache")
        if os.path.exists(CACHE_DIR):
            shutil.rmtree(CACHE_DIR)
            logger.info("Cache cleared")
        else:
            logger.info(f"Cache directory '{CACHE_DIR}' does not exist")
        return CacheClearResponse(message="Cache cleared")
    except PermissionError as e:
        logger.error(f"Error deleting cache directory: {e}")
        return CacheClearResponse(message=f"Error deleting cache directory: {e}")


class LogMessageRequest(BaseModel):
    """Logging request"""

    message: str = Field(..., description="A message to be logged")
    log_level: Optional[LogLevel] = Field(
        LogLevel.INFO, description="The log level to be used for logging"
    )


@router.post(
    "/log",
    status_code=status.HTTP_200_OK,
    summary="Puts provided message in persistent log",
)
def log_message(request: LogMessageRequest) -> None:
    """
    Puts provided message in persistent log.
    """
    if request.log_level == LogLevel.DEBUG:
        logger.debug(request.message)
    elif request.log_level == LogLevel.WARNING:
        logger.warning(request.message)
    elif request.log_level == LogLevel.ERROR:
        logger.error(request.message)
    else:
        logger.info(request.message)


class LogEventRequest(BaseModel):
    """The request to persistently log a specific event"""

    event: LocalLogEvent = Field(..., description="The event to be logged")
    screen: LocalLogScreen = Field(
        ..., description="The screen, where the event originated"
    )
    message: str = Field(..., description="A message to be logged")

    source: Optional[str] = Field(
        None, description="A place in code, where the event is logged"
    )
    duration: float = Field(
        0.0, description="The time between previous and current event of the same type"
    )

    navigate_from: Optional[LocalLogScreen] = Field(
        None, description="The screen, where user was before the event"
    )
    navigate_to: Optional[LocalLogScreen] = Field(
        None, description="The screen, where user is going to after serving the event"
    )

    session_id: Optional[str] = Field(
        None, description="The ID of the active session, if any"
    )


@router.post(
    "/log_event",
    status_code=status.HTTP_200_OK,
    summary="Puts provided message in persistent log",
)
async def log_event(request: LogEventRequest) -> None:
    """
    Puts provided message in persistent log.
    """
    await LocalLogManager.log_event(
        LocalLogEntry(
            timestamp=int(datetime.now().timestamp()),
            surface=LocalLogSurface.FRONT_END,
            event=request.event,
            screen=request.screen,
            message=request.message,
            source=request.source,
            duration=request.duration,
            navigate_from=request.navigate_from,
            navigate_to=request.navigate_to,
            session_id=request.session_id,
        )
    )


class AriaStudioQueryAnnouncementsContent(BaseModel):
    """
    Aria Studio's announcement's content
    """

    subtitle: Optional[str] = Field(
        None, description="The subtitle of the announcement's section", nullable=True
    )
    body: Optional[str] = Field(
        None, description="The content the announcement", nullable=True
    )


class AriaStudioQueryAnnouncementsResponse(BaseModel):
    """
    A single announcement related to Aria Studio
    """

    title: Optional[str] = Field(
        None, description="The title of the announcement", nullable=True
    )
    description: Optional[str] = Field(
        None, description="Additional information about the announcement", nullable=True
    )
    visible_from: Optional[str] = Field(
        None, description="Date, when announcement was made", nullable=True
    )

    content: List[AriaStudioQueryAnnouncementsContent] = Field(
        [], description="Content of the announcement"
    )


@login_required
@router.get(
    "/announcements",
    status_code=status.HTTP_200_OK,
    response_model=List[AriaStudioQueryAnnouncementsResponse],
    summary="Queries remote servers for announcements related to Aria Studio",
)
async def query_announcements(
    visible_only: bool = True,
) -> List[AriaStudioQueryAnnouncementsResponse]:
    """
    Queries remote servers for announcements related to Aria Studio.

    Args:
        visible_only (bool, optional): If True, only visible announcements will be returned.
                                       Defaults to True.
    """
    response = await CliHttpHelper.get().query_graph(
        doc_id=_QUERY_ID_ANNOUNCEMENTS,
        variables={
            _KEY_INPUT_VISIBLE_ONLY: visible_only,
        },
    )

    return [
        AriaStudioQueryAnnouncementsResponse(
            title=ann.get(_KEY_RESPONSE_TITLE),
            description=ann.get(_KEY_RESPONSE_DESCRIPTION),
            visible_from=ann.get(_KEY_RESPONSE_VISIBLE_FROM),
            content=[
                AriaStudioQueryAnnouncementsContent(
                    subtitle=content.get(_KEY_RESPONSE_SUBTITLE),
                    body=content.get(_KEY_RESPONSE_BODY),
                )
                for content in ann[_KEY_RESPONSE_CONTENT]
            ],
        )
        for ann in response[_KEY_DATA][_KEY_RESPONSE_QUERY_ANNOUNCEMENTS]
    ]


@unique
class UserReportType(str, Enum):
    """
    The user's report type to log.

    WARNING:
    keep in sync with UserReport in commonTypes.js
    """

    def _generate_next_value_(name, start, count, last_values):  # noqa: B902
        return name.upper()

    BUG = auto()
    FEEDBACK = auto()


class SubmitReportRequest(BaseModel):
    """
    The request to submit bug or feedback about Aria Studio to Meta infrastructure
    """

    report_type: UserReportType = Field(
        ..., description="The type of the report to submit"
    )
    title: str = Field(..., description="A title of the report")
    description: str = Field(..., description="A details of user's observation")


@router.post(
    "/submit_report",
    status_code=status.HTTP_200_OK,
    summary="Submits provided user report to Meta infrastructure",
)
async def submit_report(request: SubmitReportRequest) -> None:
    """
    Submits provided user report to Meta infrastructure
    """

    try:
        extra_info: str = await LocalLogManager.get_device_info_entry()
        await CliHttpHelper.get().query_graph(
            doc_id=_QUERY_ID_SUBMIT_BUG,
            variables={
                _KEY_DATA: {
                    _KEY_RESPONSE_CLIENT_MUTATION_ID: random.randint(
                        _CLIENT_MUTATION_ID_MIN, _CLIENT_MUTATION_ID_MAX
                    ),
                    _KEY_INPUT_TITLE: f"[{request.report_type.name}] {request.title}",
                    _KEY_INPUT_DESCRIPTION: request.description,
                    _KEY_INPUT_EXTRA_INFO: extra_info,
                },
            },
        )
        await LocalLogManager.log(
            event=LocalLogEvent.USER_REPORT,
            screen=LocalLogScreen.SIDEBAR,
            message=f"Submitted report: {request.title}",
        )
    except Exception as e:
        logger.error(f"Failed to submit report: {e}")
        await LocalLogManager.log(
            event=LocalLogEvent.USER_REPORT,
            screen=LocalLogScreen.SIDEBAR,
            message=f"Failed to submit report {request.title} due to: {e}",
        )
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Failed to submit report",
        )
