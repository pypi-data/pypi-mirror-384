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

import os
from pathlib import Path
from threading import Event
from typing import List

from aria_studio.utils.rerun_manager import RerunTaskBase

from projectaria_tools.core.mps import MpsDataPaths, MpsDataPathsProvider
from projectaria_tools.utils.rerun_viewer_mps import log_mps_to_rerun


class MpsSingleRerunTask(RerunTaskBase):
    """
    A task to log MPS single feature data to rerun.
    Visualizes all the streams present in the vrs file and overlays available MPS data.

    This task is intended to be used with the RerunManager class.
    """

    def __init__(
        self,
        vrs: str,
    ):
        self._vrs: str = vrs

    def log_to_rerun(self, stop_event: Event) -> None:
        vrs_path: Path = Path(self._vrs)
        folder_path: Path = vrs_path.parent / f"mps_{vrs_path.stem}_vrs"

        mps_data_paths_provider: MpsDataPathsProvider = MpsDataPathsProvider(
            str(folder_path)
        )
        mps_data_paths: MpsDataPaths = mps_data_paths_provider.get_data_paths()

        trajectory: List[str] = (
            [str(mps_data_paths.slam.closed_loop_trajectory)]
            if os.path.exists(mps_data_paths.slam.closed_loop_trajectory)
            else []
        )
        points: List[str] = (
            [str(mps_data_paths.slam.semidense_points)]
            if os.path.exists(mps_data_paths.slam.semidense_points)
            else []
        )

        if os.path.exists(mps_data_paths.eyegaze.personalized_eyegaze):
            eyegaze = mps_data_paths.eyegaze.personalized_eyegaze
        elif os.path.exists(mps_data_paths.eyegaze.general_eyegaze):
            eyegaze = mps_data_paths.eyegaze.general_eyegaze
        else:
            eyegaze = None

        hands = (
            mps_data_paths.hand_tracking.hand_tracking_results
            if os.path.exists(mps_data_paths.hand_tracking.hand_tracking_results)
            else None
        )
        use_hand_tracking_results = True
        if hands is None:
            hands = (
                mps_data_paths.hand_tracking.wrist_and_palm_poses
                if os.path.exists(mps_data_paths.hand_tracking.wrist_and_palm_poses)
                else None
            )
            use_hand_tracking_results = False

        log_mps_to_rerun(
            vrs_path=self._vrs,
            trajectory_files=trajectory,
            points_files=points,
            eye_gaze_file=eyegaze,
            wrist_and_palm_poses_file=hands if not use_hand_tracking_results else None,
            hand_tracking_results_file=hands if use_hand_tracking_results else None,
        )

    def __str__(self):
        return f"MpsSingleRerunTask: (vrs: {self._vrs})"
