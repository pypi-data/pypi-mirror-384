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
import functools
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Mapping, Optional, Tuple, Union

from aria_studio.app.common.types import FeatureStatus, MpsRequestStage
from aria_studio.app.groups.group_manager import GroupManager
from aria_studio.app.local.local_log_manager import (
    LocalLogEntry,
    LocalLogEvent,
    LocalLogManager,
    LocalLogScreen,
    LocalLogSurface,
)
from aria_studio.app.mps.group_mps_request_cache import GroupMpsRequestCache
from aria_studio.app.utils import CliHttpHelper, get_db_path, login_required

from projectaria_tools.aria_mps_cli.cli_lib.common import log_exceptions
from projectaria_tools.aria_mps_cli.cli_lib.multi_recording_mps import MultiRecordingMps
from projectaria_tools.aria_mps_cli.cli_lib.multi_recording_request import (
    MultiRecordingModel,
    MultiRecordingRequest,
)
from projectaria_tools.aria_mps_cli.cli_lib.request_monitor import (
    RequestMonitor,
    RequestMonitorModel,
)
from projectaria_tools.aria_mps_cli.cli_lib.types import MpsFeature, MpsRequestSource


logger = logging.getLogger(__name__)


class GroupMpsRequestManager:
    """
    The manager for Group MPS requests.
    """

    instance_: "GroupMpsRequestManager" = None
    lock_: asyncio.Lock = asyncio.Lock()

    @classmethod
    @login_required
    async def get_instance(cls):
        """Get the group mps request manager singleton."""
        if cls.instance_ is None:
            async with cls.lock_:
                db_path = get_db_path()
                logger.debug(f"Creating group manager with {db_path}")
                cls.instance_ = GroupMpsRequestManager(db_path=db_path)
                await cls.instance_.async_init()
        return cls.instance_

    @classmethod
    async def reset(cls):
        """Reset the individual mps request manager singleton."""
        async with cls.lock_:
            logger.debug("Resetting group manager")
            cls.instance_ = None

    def __init__(self, db_path: Path):
        self._initiazed: bool = False
        self._request_cache = GroupMpsRequestCache(db_path=db_path)
        self._requestor: MultiRecordingRequest  # Requestor StateMachine
        self._request_monitor: RequestMonitor  # RequestMonitor StateMachine
        self._active_requests: Mapping[str, MultiRecordingMps] = {}
        self._request_tasks: Mapping[str, asyncio.Task] = {}

    @log_exceptions
    async def _on_state_changed(
        self, group_name: str, model: Union[MultiRecordingModel, RequestMonitorModel]
    ):
        """Called when the state of a model changes."""
        logger.debug(f"State changed for {model}")
        status: Mapping[Path, Tuple[str, str]] = {}

        for rec in model.recordings:
            vrs_status = model.get_status(rec.path)
            status[rec.path] = (vrs_status.status, vrs_status.error_code)

        if isinstance(model, MultiRecordingModel):
            if model.feature_request:
                creation_time, request_id = (
                    model.feature_request.creation_time,
                    model.feature_request.fbid,
                )
            else:
                creation_time, request_id = None, None

            # Set stage based on the state
            stage = MpsRequestStage.REQUESTOR
            if model.is_SUCCESS_PAST_OUTPUT():
                stage = MpsRequestStage.SUCCESS
            elif model.is_FAILURE():
                stage = MpsRequestStage.ERROR
            elif model.is_SUCCESS_NEW_REQUEST():
                await LocalLogManager.log_event(
                    LocalLogEntry(
                        timestamp=int(datetime.now().timestamp()),
                        surface=LocalLogSurface.BACK_END,
                        event=LocalLogEvent.MPS_UPLOAD,
                        screen=LocalLogScreen.GROUPS,
                        message=f"Uploaded Recordings for {group_name} to MPS",
                        source=LocalLogEntry.get_caller(),
                        mps_features=[MpsFeature.MULTI_SLAM],
                        is_forced=model.is_force,
                    )
                )

            await self._request_cache.put(
                group_name=group_name,
                force=model.is_force,
                retry_failed=model.is_retry_failed,
                creation_time=creation_time,
                request_id=request_id,
                status=status,
                stage=stage,
                feature=MpsFeature.MULTI_SLAM,
            )
        elif isinstance(model, RequestMonitorModel):
            fr = model.feature_request

            # Set stage based on the state
            stage = MpsRequestStage.MONITOR
            if model.is_SUCCESS():
                stage = MpsRequestStage.SUCCESS

                group_manager = await GroupManager.get_instance()
                group = await group_manager.get(group_name)

                await LocalLogManager.log_event(
                    LocalLogEntry(
                        timestamp=int(datetime.now().timestamp()),
                        surface=LocalLogSurface.BACK_END,
                        event=LocalLogEvent.MPS_DOWNLOAD,
                        screen=LocalLogScreen.GROUPS,
                        message=f"Dowloaded MPS output for {group_name} to {group.path_on_device}",
                        source=LocalLogEntry.get_caller(),
                        mps_features=[MpsFeature.MULTI_SLAM],
                    )
                )
            elif model.is_FAILURE():
                stage = MpsRequestStage.ERROR

            await self._request_cache.put(
                group_name=group_name,
                # if a recording made it to request monitor then it means that force and
                # retry_failed flags were already applied
                force=False,
                retry_failed=False,
                stage=stage,
                feature=MpsFeature.MULTI_SLAM,
                request_id=fr.fbid,
                status=status,
                creation_time=fr.creation_time,
            )

    @log_exceptions
    async def create_request(
        self,
        group_name: str,
        force: bool,
        retry_failed: bool,
        persist_on_failure: bool = False,
        feedback_id: Optional[str] = None,
    ) -> bool:
        """
        Create a group MPS request for a group.
        """
        logger.debug(f"Group Request for {group_name}.")
        self._ensure_initialized()

        # Only once active request per group is allowed
        if group_name in self._active_requests:
            logger.debug(f"Found request for {group_name}")
            await LocalLogManager.log_event(
                LocalLogEntry(
                    timestamp=int(datetime.now().timestamp()),
                    surface=LocalLogSurface.BACK_END,
                    event=LocalLogEvent.MPS_REQUEST,
                    screen=LocalLogScreen.GROUPS,
                    message=f"Found previous MPS request for {group_name} group.",
                    source=LocalLogEntry.get_caller(),
                    mps_features=[MpsFeature.MULTI_SLAM],
                    is_forced=force,
                )
            )
            return False

        group_manager = await GroupManager.get_instance()
        if group := await group_manager.get(group_name):
            vrs_paths_in_group = group.vrs_files
            if len(vrs_paths_in_group) < 2:
                await LocalLogManager.log_event(
                    LocalLogEntry(
                        timestamp=int(datetime.now().timestamp()),
                        surface=LocalLogSurface.BACK_END,
                        event=LocalLogEvent.MPS_REQUEST,
                        screen=LocalLogScreen.GROUPS,
                        message=f"Cannot request MPS processing for {group_name} while it has less than 2 recordings",
                        source=LocalLogEntry.get_caller(),
                        mps_features=[MpsFeature.MULTI_SLAM],
                        is_forced=force,
                    )
                )
                raise Exception(
                    f"Group {group_name} has less than 2 recordings. Please add more."
                )
        else:
            await LocalLogManager.log_event(
                LocalLogEntry(
                    timestamp=int(datetime.now().timestamp()),
                    surface=LocalLogSurface.BACK_END,
                    event=LocalLogEvent.MPS_REQUEST,
                    screen=LocalLogScreen.GROUPS,
                    message=f"Cannot request MPS processing for non-existing group: {group_name}",
                    source=LocalLogEntry.get_caller(),
                    mps_features=[MpsFeature.MULTI_SLAM],
                    is_forced=force,
                )
            )
            raise Exception(f"Group {group_name} not found")

        group_mps: MultiRecordingMps = MultiRecordingMps(
            recordings=vrs_paths_in_group,
            output_dir=group.path_on_device,
            force=force,
            retry_failed=retry_failed,
            http_helper=CliHttpHelper.get(),
            requestor=self._requestor,
            request_monitor=self._request_monitor,
            name=group_name,
            source=MpsRequestSource.ARIA_STUDIO,
            on_state_changed=functools.partial(self._on_state_changed, group_name),
            persist_on_failure=persist_on_failure,
            feedback_id=feedback_id,
        )
        t = asyncio.create_task(group_mps.run(), name="f{group_name}_multi_slam")
        self._request_tasks[group_name] = t
        self._active_requests[group_name] = group_mps

        def __on_done(
            requests: Mapping[str, MultiRecordingMps],
            tasks: Mapping[str, asyncio.Task],
            group_name: str,
            task: asyncio.Task,
        ) -> None:
            """
            callback to remove the task from the active requests once it is done
            """
            logger.debug(f"Task {task} for group {group_name} done.")
            requests.pop(group_name)
            tasks.pop(group_name)

        t.add_done_callback(
            functools.partial(
                __on_done,
                self._active_requests,
                self._request_tasks,
                group_name,
                # task is passed by the callback
            )
        )

        await LocalLogManager.log_event(
            LocalLogEntry(
                timestamp=int(datetime.now().timestamp()),
                surface=LocalLogSurface.BACK_END,
                event=LocalLogEvent.MPS_REQUEST,
                screen=LocalLogScreen.GROUPS,
                message=f"Requested MPS processing for {group_name} group",
                source=LocalLogEntry.get_caller(),
                mps_features=[MpsFeature.MULTI_SLAM],
                is_forced=force,
            )
        )
        return True

    @log_exceptions
    async def check_status(
        self, group_name: str
    ) -> Mapping[Path, Mapping[MpsFeature, FeatureStatus]]:
        """
        Check the status of a request for an individual recording.
        """
        self._ensure_initialized()
        group_manager = await GroupManager.get_instance()
        if not await group_manager.exists(group_name):
            logger.debug(f"Group {group_name} not found")
            raise Exception(f"Group {group_name} not found")

        rec_status_by_feature: Mapping[Path, Mapping[MpsFeature, FeatureStatus]] = {}
        if group_name in self._active_requests:
            logger.debug(f"Group {group_name} found in active requests.")
            group_mps = self._active_requests[group_name]
            for r in group_mps.recordings:
                creation_time: Optional[int] = None
                if req_db := await self._request_cache.get(group_name):
                    creation_time = req_db.creation_time
                rec_status_by_feature[r] = {
                    MpsFeature.MULTI_SLAM: FeatureStatus(
                        **asdict(group_mps.get_status(r)),
                        creation_time=creation_time,
                    )
                }
        else:
            logger.debug(f"Group {group_name} not found in active requests.")
            if request := await self._request_cache.get(group_name):
                group = await group_manager.get(group_name)
                vrs_paths_in_group = group.vrs_files
                for r in vrs_paths_in_group:
                    if r in request.status:
                        status, error_code = request.status[r]
                    else:
                        status, error_code = "UNKNOWN", None

                    rec_status_by_feature[r] = {
                        MpsFeature.MULTI_SLAM: FeatureStatus(
                            status=status,
                            creation_time=request.creation_time,
                            error_code=error_code,
                            # TODO: Get the output path from the database
                            output_path=group.path_on_device,
                        )
                    }
        return rec_status_by_feature

    @log_exceptions
    async def async_init(self):
        """
        Initializes the shared RequestMonitor object. Creates it, if necessary with common HttpHelper object.
        """
        if not self._initiazed:
            self._request_monitor = RequestMonitor(http_helper=CliHttpHelper.get())
            self._requestor = MultiRecordingRequest(http_helper=CliHttpHelper.get())
            await self._request_cache.create_table()
            self._initiazed = True
            incomplete_reqs = await self._request_cache.get_incomplete_requests()
            logger.debug(f"incomplete requests {incomplete_reqs}")
            for grp in incomplete_reqs:
                # If the request made it out of the requestor, it means the request was
                # already submitted to the server. At startup, we can ignore the force
                # and retry failed flags, as they have already been honored when
                # the request was made, before shutdown.
                force = grp.force and grp.stage == MpsRequestStage.REQUESTOR
                retry_failed = grp.force and grp.stage == MpsRequestStage.REQUESTOR
                await self.create_request(
                    grp.group_name, force=force, retry_failed=retry_failed
                )

    def _ensure_initialized(self) -> None:
        """
        Ensure that async_init is called
        """
        if not self._initiazed:
            raise Exception("Request Manager hasn't been initialized.")
