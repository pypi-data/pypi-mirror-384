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
import itertools
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Mapping, Optional, Set, Union

from aria_studio.app.common.types import (
    DBIndividualMpsRequest,
    FeatureStatus,
    MpsRequestStage,
)
from aria_studio.app.local.local_log_manager import (
    LocalLogEntry,
    LocalLogEvent,
    LocalLogManager,
    LocalLogScreen,
    LocalLogSurface,
)
from aria_studio.app.mps.individual_mps_request_cache import IndividualMpsRequestCache
from aria_studio.app.utils import CliHttpHelper, get_db_path, login_required

from projectaria_tools.aria_mps_cli.cli_lib.common import log_exceptions
from projectaria_tools.aria_mps_cli.cli_lib.constants import DisplayStatus
from projectaria_tools.aria_mps_cli.cli_lib.request_monitor import (
    RequestMonitor,
    RequestMonitorModel,
)
from projectaria_tools.aria_mps_cli.cli_lib.single_recording_mps import (
    SingleRecordingMps,
)
from projectaria_tools.aria_mps_cli.cli_lib.single_recording_request import (
    SingleRecordingModel,
    SingleRecordingRequest,
)
from projectaria_tools.aria_mps_cli.cli_lib.types import MpsFeature, MpsRequestSource

logger = logging.getLogger(__name__)


class IndividualMpsRequestManager:
    """The manager for the individual request."""

    instance_: "IndividualMpsRequestManager" = None
    lock_: asyncio.Lock = asyncio.Lock()

    @classmethod
    @login_required
    async def get_instance(cls):
        """Get the individual mps request manager singleton."""
        if cls.instance_ is None:
            async with cls.lock_:
                db_path = get_db_path()
                logger.debug(f"Creating individual mps manager with {db_path}")
                cls.instance_ = IndividualMpsRequestManager(db_path=db_path)
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
        self._request_cache = IndividualMpsRequestCache(db_path=db_path)
        self._requestor: Optional[SingleRecordingRequest] = None
        self._request_monitor: Optional[RequestMonitor] = None
        self._active_requests: Mapping[
            Path, Mapping[MpsFeature, SingleRecordingMps]
        ] = {}
        self._request_tasks: Mapping[Path, Mapping[MpsFeature, asyncio.Task]] = {}

    @log_exceptions
    async def _on_state_changed(
        self, model: Union[SingleRecordingModel, RequestMonitorModel]
    ):
        """Called when the state of a model changes."""
        logger.debug(f"State changed for {model}")
        output_path: Optional[Path] = None
        if isinstance(model, SingleRecordingModel):
            status = model.get_status()
            if model.past_feature_request:
                creation_time, request_id = (
                    model.past_feature_request.creation_time,
                    model.past_feature_request.fbid,
                )
            else:
                creation_time, request_id = None, None

            # Set stage based on the state
            stage = MpsRequestStage.REQUESTOR
            if model.is_SUCCESS_PAST_OUTPUT():
                stage = MpsRequestStage.SUCCESS
                output_path = model.recording.output_path / model.feature.value.lower()
            elif model.is_FAILURE():
                stage = MpsRequestStage.ERROR
            elif model.is_SUCCESS_NEW_REQUEST():
                await LocalLogManager.log_event(
                    LocalLogEntry(
                        timestamp=int(datetime.now().timestamp()),
                        surface=LocalLogSurface.BACK_END,
                        event=LocalLogEvent.MPS_UPLOAD,
                        screen=LocalLogScreen.FILES,
                        message=f"Uploaded {model.recording.path} to MPS",
                        source=LocalLogEntry.get_caller(),
                        mps_features=[model.feature],
                        is_forced=model.is_force,
                        file_size=model.recording.path.stat().st_size,
                    )
                )

            await self._request_cache.put(
                vrs_path=model.recording.path,
                force=model.is_force,
                retry_failed=model.is_retry_failed,
                creation_time=creation_time,
                request_id=request_id,
                status=status.status,
                stage=stage,
                feature=model.feature,
                error_code=status.error_code,
                output_path=str(output_path),
            )
        elif isinstance(model, RequestMonitorModel):
            status = model.get_status(model.recordings[0])
            fr = model.feature_request

            # Set stage based on the state
            stage = MpsRequestStage.MONITOR
            if model.is_SUCCESS():
                stage = MpsRequestStage.SUCCESS
                output_path = (
                    model.recordings[0].output_path / model.feature.value.lower()
                )
                await LocalLogManager.log_event(
                    LocalLogEntry(
                        timestamp=int(datetime.now().timestamp()),
                        surface=LocalLogSurface.BACK_END,
                        event=LocalLogEvent.MPS_DOWNLOAD,
                        screen=LocalLogScreen.FILES,
                        message=f"Downloaded MPS output for {model.feature} from {model.recordings[0].path} to {output_path}",
                        source=LocalLogEntry.get_caller(),
                        mps_features=[model.feature],
                    )
                )
            elif model.is_FAILURE():
                stage = MpsRequestStage.ERROR

            await self._request_cache.put(
                vrs_path=model.recordings[0].path,
                # if a recording made it to request monitor then it means that force and
                # retry_failed flags were already applied
                force=False,
                retry_failed=False,
                status=status.status,
                stage=stage,
                feature=model.feature,
                request_id=fr.fbid,
                error_code=status.error_code,
                creation_time=fr.creation_time,
                output_path=str(output_path),
            )

    @log_exceptions
    async def create_request(
        self,
        vrs_path: Path,
        features: Set[MpsFeature],
        force: bool,
        retry_failed: bool,
        persist_on_failure: bool = False,
        feedback_id: Optional[str] = None,
    ) -> bool:
        """Create a request for an individual recording.
        when retry_failed is set, we will retry all the failed features
        when force is set, we will resubmit only the finished (success and failed)
        features"""
        try:
            self._ensure_initialized()

            self._active_requests[vrs_path] = self._active_requests.get(vrs_path, {})
            pending_features: Set[MpsFeature] = features - set(
                self._active_requests[vrs_path].keys()
            )

            if not pending_features:
                logger.debug(f"No pending features for {vrs_path}")

                await LocalLogManager.log_event(
                    LocalLogEntry(
                        timestamp=int(datetime.now().timestamp()),
                        surface=LocalLogSurface.BACK_END,
                        event=LocalLogEvent.MPS_REQUEST,
                        screen=LocalLogScreen.FILES,
                        message=f"Cannot request MPS processing for {vrs_path} file without specifying any features",
                        source=LocalLogEntry.get_caller(),
                        mps_features=list(features),
                        is_forced=force,
                    )
                )
                return False

            self._request_tasks[vrs_path] = self._request_tasks.get(vrs_path, {})

            single_recording_mps = SingleRecordingMps(
                recording=vrs_path,
                features=pending_features,
                force=force,
                retry_failed=retry_failed,
                http_helper=CliHttpHelper.get(),
                requestor=self._requestor,
                request_monitor=self._request_monitor,
                source=MpsRequestSource.ARIA_STUDIO,
                on_state_changed=functools.partial(self._on_state_changed),
                persist_on_failure=persist_on_failure,
                feedback_id=feedback_id,
            )

            t = asyncio.create_task(
                single_recording_mps.run(), name=f"{vrs_path}-{features}"
            )

            for f in pending_features:
                self._request_tasks[vrs_path][f] = t
                self._active_requests[vrs_path][f] = single_recording_mps

            t.add_done_callback(
                lambda task: asyncio.create_task(
                    self.__on_done(
                        self._active_requests,
                        self._request_tasks,
                        vrs_path,
                        pending_features,
                        task,
                    )
                )
            )
            await LocalLogManager.log_event(
                LocalLogEntry(
                    timestamp=int(datetime.now().timestamp()),
                    surface=LocalLogSurface.BACK_END,
                    event=LocalLogEvent.MPS_REQUEST,
                    screen=LocalLogScreen.FILES,
                    message=f"Requested MPS processing with [{','.join([f.value for f in features])}] features for {vrs_path} file",
                    source=LocalLogEntry.get_caller(),
                    mps_features=list(features),
                    is_forced=force,
                )
            )

            return True

        except Exception as e:
            logger.exception(f"Error creating request for {vrs_path}: {e}")
            await LocalLogManager.log_event(
                LocalLogEntry(
                    timestamp=int(datetime.now().timestamp()),
                    surface=LocalLogSurface.BACK_END,
                    event=LocalLogEvent.MPS_REQUEST,
                    screen=LocalLogScreen.FILES,
                    message=f"Error creating request for {vrs_path}: {e}",
                    source=LocalLogEntry.get_caller(),
                    mps_features=list(features),
                    is_forced=force,
                )
            )
            return False

    async def __on_done(
        self,
        requests: Mapping[Path, Mapping[MpsFeature, SingleRecordingMps]],
        tasks: Mapping[Path, Mapping[MpsFeature, asyncio.Task]],
        vrs_path: Path,
        features: Set[MpsFeature],
        task: asyncio.Task,
    ):
        """callback to remove the task from the active requests once it is done"""
        try:
            exc = task.exception()
            if exc:
                logger.error(f"Task failed with error: {exc}")

                await LocalLogManager.log_event(
                    LocalLogEntry(
                        timestamp=int(datetime.now().timestamp()),
                        surface=LocalLogSurface.BACK_END,
                        event=LocalLogEvent.MPS_REQUEST,
                        screen=LocalLogScreen.FILES,
                        message=f"Task failed with error: {exc}",
                        source=LocalLogEntry.get_caller(),
                        mps_features=list(features),
                    )
                )
            logger.debug(f"Task {task.get_name()} completed")

            for f in features:
                tasks[vrs_path].pop(f, None)  # Safe pop
                requests[vrs_path].pop(f, None)

        except Exception as e:
            logger.error(f"Error in task cleanup: {e}")

    @log_exceptions
    async def check_status(self, vrs_path: Path) -> Mapping[MpsFeature, FeatureStatus]:
        """Check the status of a request for an individual recording."""
        self._ensure_initialized()
        rec_status_by_feature: Mapping[MpsFeature, FeatureStatus] = {}
        requests_for_db: List[DBIndividualMpsRequest] = await self._request_cache.get(
            vrs_path
        )
        # First fetch the status from the active requests
        if vrs_path in self._active_requests:
            vrs_path_requests = self._active_requests[vrs_path]
            for feature, req in vrs_path_requests.items():
                if req_db := next(
                    (r for r in requests_for_db if r.feature == feature), None
                ):
                    creation_time = req_db.creation_time
                else:
                    creation_time = None
                rec_status_by_feature[feature] = FeatureStatus(
                    **asdict(req.get_status(feature)),
                    creation_time=creation_time,
                )
        active_features: Set[MpsFeature] = set(rec_status_by_feature.keys())

        # If we didn't fund the request in active requests, then we need to check the db
        for req_db in requests_for_db:
            if req_db.feature not in active_features:
                rec_status_by_feature[req_db.feature] = FeatureStatus(
                    status=req_db.status,
                    error_code=req_db.error_code,
                    creation_time=req_db.creation_time,
                    output_path=req_db.output_path,
                )
        return rec_status_by_feature

    @log_exceptions
    async def retry_if_failed(self, vrs_path: Path) -> bool:
        """
        Retry a request for an individual recording if it failed.
        We find all the failed features and submit one single request for all of them.
        """
        self._ensure_initialized()
        feature_status = await self.check_status(vrs_path)
        # If no feature is specified then retry all the failed ones
        features_to_retry: Set[MpsFeature] = {
            f for f, s in feature_status.items() if s.status == DisplayStatus.ERROR
        }

        if features_to_retry:
            logger.debug(f"Retrying {features_to_retry} for {vrs_path}")
            return await self.create_request(
                vrs_path, features=features_to_retry, force=False, retry_failed=True
            )
        else:
            logger.debug(f"No failed features to retry for {vrs_path}")

        return False

    @log_exceptions
    async def async_init(self):
        """
        Initializes the shared RequestMonitor object. Creates it, if necessary with
        common HttpHelper object.
        """
        if not self._initiazed:
            self._request_monitor = RequestMonitor(http_helper=CliHttpHelper.get())
            self._requestor = SingleRecordingRequest(http_helper=CliHttpHelper.get())
            await self._request_cache.create_table()
            incomplete_reqs: List[
                DBIndividualMpsRequest
            ] = await self._request_cache.get_incomplete_requests()
            logger.debug(f"Incomplete requests {incomplete_reqs}")
            self._initiazed = True
            reqs_grouped_by_vrs_path = itertools.groupby(
                incomplete_reqs, lambda x: (x.vrs_path)
            )
            for vrs_path, reqs in reqs_grouped_by_vrs_path:
                vrs_path = Path(vrs_path)
                features: Set[MpsFeature] = {req.feature for req in reqs}
                await self.create_request(
                    vrs_path=vrs_path,
                    features=features,
                    # TODO: T190663167: featurewise separation of retry_failed and force flags on startup
                    force=any(req.force for req in reqs),
                    retry_failed=any(req.retry_failed for req in reqs),
                )

    def _ensure_initialized(self):
        """Ensure that async_init is called"""
        if not self._initiazed:
            raise ValueError("IndividualRequestManager has not been initialized.")
