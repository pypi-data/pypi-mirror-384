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

import argparse
import asyncio
import logging
import os

from aria_studio.utils.rerun_manager import DEFAULT_MEMORY_LIMIT, RerunManager
from aria_studio.utils.vrs_rerun_task import VrsRerunTask

logger = logging.getLogger(__name__)


def pars_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vrs", type=str, required=True, help="path to vrs file")
    parser.add_argument(
        "--imu_skip_count",
        "-s",
        type=int,
        default=1,
        help="IMU and Gyro subsampling rate",
    )
    parser.add_argument(
        "--down_sampling_factor",
        "-d",
        type=int,
        default=1,
        help="Downsampling factor for image data",
    )
    parser.add_argument(
        "--jpeg_quality",
        "-q",
        type=int,
        default=100,
        choices=range(1, 101),
        help="JPEG quality for JPEG compression",
    )
    parser.add_argument(
        "--memory_limit",
        "-m",
        type=str,
        default=DEFAULT_MEMORY_LIMIT,
        help="Memory limit for rerun",
    )
    return parser.parse_args()


def check_args(args: argparse.Namespace) -> None:
    # check if file path exists
    if os.path.exists(args.vrs):
        logger.info("using vrs file {}".format(args.vrs))
    else:
        logger.error("vrs file does not exist")
        exit(1)

    # check validity of imu and dsf args
    if args.imu_skip_count < 1 or args.down_sampling_factor < 1:
        logger.error("imu_skip_count and down_sampling_factor must be greater than 1 ")
        exit(1)


def main():
    logging.basicConfig(
        format="%(name)s %(asctime)-15s [%(filename)s:%(lineno)d] [%(levelname)s] %(message)s",
        level=logging.INFO,
    )
    args = pars_args()
    check_args(args)

    # Create manager and run viewer
    manager: RerunManager = RerunManager()
    asyncio.run(
        manager.start_viewer(
            VrsRerunTask(
                vrs=args.vrs,
                memory_limit=args.memory_limit,
                imu_skip_count=args.imu_skip_count,
                down_sampling_factor=args.down_sampling_factor,
                jpeg_quality=args.jpeg_quality,
            )
        )
    )


if __name__ == "__main__":
    main()
