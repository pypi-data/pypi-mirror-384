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
from threading import Event
from typing import Iterator

import numpy as np
import rerun as rr

from aria_studio.utils.rerun_manager import RerunTaskBase

from projectaria_tools.core import data_provider
from projectaria_tools.core.sensor_data import SensorData, SensorDataType, TimeDomain
from projectaria_tools.core.stream_id import StreamId

logger = logging.getLogger(__name__)

# Sensor labels used in aria glasses
_CAMERA_RGB_LABEL: str = "camera-rgb"
_CAMERA_ET_LABEL: str = "camera-et"
_CAMERA_SLAM_LEFT_LABEL: str = "camera-slam-left"
_CAMERA_SLAM_RIGHT_LABEL: str = "camera-slam-right"
_IMU_LEFT_LABEL: str = "imu-left"
_IMU_RIGHT_LABEL: str = "imu-right"
_MAGNETOMETER_LABEL: str = "mag0"


class VrsRerunTask(RerunTaskBase):
    """
    A task to log vrs data to rerun. Visualizes all the streams present in the vrs file.

    This task is intended to be used with the RerunManager class.
    """

    def __init__(
        self,
        vrs: str,
        imu_skip_count: int = 1,
        down_sampling_factor: int = 1,
        jpeg_quality: int = 100,
    ):
        self._vrs = vrs
        self._imu_skip_count = imu_skip_count
        self._down_sampling_factor = down_sampling_factor
        self._jpeg_quality = jpeg_quality

    def log_to_rerun(self, stop_event: Event) -> None:
        # create provider,activate streams and check validity
        provider = data_provider.create_vrs_data_provider(self._vrs)

        if provider is None:
            logger.error("Failed to create a provider")
            rr.disconnect()
            return

        streams_in_vrs = provider.get_all_streams()
        # create deliver options and deactivate all streams
        deliver_option = provider.get_default_deliver_queued_options()
        deliver_option.deactivate_stream_all()

        stream_mappings = {
            "camera-slam-left": StreamId("1201-1"),
            "camera-slam-right": StreamId("1201-2"),
            "camera-rgb": StreamId("214-1"),
            "camera-eyetracking": StreamId("211-1"),
            "imu-right": StreamId("1202-1"),
            "imu-left": StreamId("1202-2"),
            "mag": StreamId("1203-1"),
        }

        # activate the required streams
        for stream_id in stream_mappings.values():
            if stream_id in streams_in_vrs:
                deliver_option.activate_stream(stream_id)

        # set imu skip count using set_subsample_rate method if imu stream is pressent in vrs
        imu_streams = filter(
            lambda x: x in streams_in_vrs,
            [stream_mappings["imu-left"], stream_mappings["imu-right"]],
        )
        if imu_streams:
            for imu in imu_streams:
                deliver_option.set_subsample_rate(imu, self._imu_skip_count)

        # create a data iterable with chosen options
        data_stream = provider.deliver_queued_sensor_data(deliver_option)

        # iterate through data and plot
        for data in data_stream:
            # Check stop event
            if stop_event.is_set():
                logger.info("Stopping rerun viewer...")
                break

            device_time_ns = data.get_time_ns(TimeDomain.DEVICE_TIME)
            rr.set_time_nanos("device_time", device_time_ns)
            label = provider.get_label_from_stream_id(data.stream_id())

            if (
                data.sensor_data_type() == SensorDataType.IMAGE
                and label == _CAMERA_RGB_LABEL
            ):
                img = self._load_img_data(data, self._down_sampling_factor)
                rotated_img = np.rot90(img, k=1, axes=(1, 0))
                rr.log(
                    _CAMERA_RGB_LABEL,
                    rr.Image(rotated_img).compress(jpeg_quality=self._jpeg_quality),
                )

            elif (
                data.sensor_data_type() == SensorDataType.IMAGE
                and label == _CAMERA_ET_LABEL
            ):
                img = self._load_img_data(data, self._down_sampling_factor)
                rr.log(
                    _CAMERA_ET_LABEL,
                    rr.Image(img).compress(jpeg_quality=self._jpeg_quality),
                )

            elif (
                data.sensor_data_type() == SensorDataType.IMAGE
                and label == _CAMERA_SLAM_LEFT_LABEL
            ):
                img = self._load_img_data(data, self._down_sampling_factor)
                rotated_img = np.rot90(img, k=1, axes=(1, 0))
                rr.log(
                    _CAMERA_SLAM_LEFT_LABEL,
                    rr.Image(rotated_img).compress(jpeg_quality=self._jpeg_quality),
                )

            elif (
                data.sensor_data_type() == SensorDataType.IMAGE
                and label == _CAMERA_SLAM_RIGHT_LABEL
            ):
                img = self._load_img_data(data, self._down_sampling_factor)
                rotated_img = np.rot90(img, k=1, axes=(1, 0))
                rr.log(
                    _CAMERA_SLAM_RIGHT_LABEL,
                    rr.Image(rotated_img).compress(jpeg_quality=self._jpeg_quality),
                )

            elif (
                data.sensor_data_type() == SensorDataType.IMU
                and label == _IMU_LEFT_LABEL
            ):
                imu_data = data.imu_data()
                rr.log("imu-left-accl/x", rr.Scalar(imu_data.accel_msec2[0]))
                rr.log("imu-left-accl/y", rr.Scalar(imu_data.accel_msec2[1]))
                rr.log("imu-left-accl/z", rr.Scalar(imu_data.accel_msec2[2]))
                rr.log("imu-left-gyro/x", rr.Scalar(imu_data.gyro_radsec[0]))
                rr.log("imu-left-gyro/y", rr.Scalar(imu_data.gyro_radsec[1]))
                rr.log("imu-left-gyro/z", rr.Scalar(imu_data.gyro_radsec[2]))

            elif (
                data.sensor_data_type() == SensorDataType.IMU
                and label == _IMU_RIGHT_LABEL
            ):
                imu_data = data.imu_data()
                rr.log("imu-right-accl/x", rr.Scalar(imu_data.accel_msec2[0]))
                rr.log("imu-right-accl/y", rr.Scalar(imu_data.accel_msec2[1]))
                rr.log("imu-right-accl/z", rr.Scalar(imu_data.accel_msec2[2]))
                rr.log("imu-right-gyro/x", rr.Scalar(imu_data.gyro_radsec[0]))
                rr.log("imu-right-gyro/y", rr.Scalar(imu_data.gyro_radsec[1]))
                rr.log("imu-right-gyro/z", rr.Scalar(imu_data.gyro_radsec[2]))

            elif (
                data.sensor_data_type() == SensorDataType.MAGNETOMETER
                and label == _MAGNETOMETER_LABEL
            ):
                mag_data = data.magnetometer_data()
                rr.log("mag/x", rr.Scalar(mag_data.mag_tesla[0] * 1e6))
                rr.log("mag/y", rr.Scalar(mag_data.mag_tesla[1] * 1e6))
                rr.log("mag/z", rr.Scalar(mag_data.mag_tesla[2] * 1e6))

    def _load_img_data(
        self, data: Iterator[SensorData], down_sampling_factor: int
    ) -> np.ndarray:
        img = data.image_data_and_record()[0].to_numpy_array()
        img = img[::down_sampling_factor, ::down_sampling_factor]
        return img

    def __str__(self):
        return f"""VrsRerunTask: (
    vrs: {self._vrs}, 
    imu_skip_count: {self._imu_skip_count}, 
    down_sampling_factor: {self._down_sampling_factor}, 
    jpeg_quality: {self._jpeg_quality},
)"""
