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
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DiskCache:
    """
    The class to manage the cache for thumbnails and metadata.
    """

    def __init__(self, cache_dir: Path):
        self._cache_dir: Path = cache_dir

    def get_cache_dir(self, vrs_file: Path) -> Path:
        """Get the cache directory for a VRS file. If it doesn't exist it will be created"""
        vrs_file_s = str(vrs_file)
        vrs_file_s = vrs_file_s[1:] if vrs_file_s.startswith("/") else vrs_file_s
        vrs_cache_dir = self._cache_dir / vrs_file_s.replace(".", "_")
        if not vrs_cache_dir.exists():
            vrs_cache_dir.mkdir(parents=True, exist_ok=True)
        return vrs_cache_dir

    def clear(self, vrs_file: Optional[Path] = None):
        """Clear cache"""
        if vrs_file:
            cache_dir = self.get_cache_dir(vrs_file)
            if cache_dir.exists():
                shutil.rmtree(str(cache_dir), ignore_errors=True)
        else:
            if self._cache_dir.exists():
                shutil.rmtree(str(self._cache_dir), ignore_errors=True)

    def get(self, vrs_file: str, filename: str) -> Optional[Path]:
        """Get the thumbnail for a VRS file from cache."""
        # Get the path to the cached image
        local_file: Path = self.get_cache_dir(vrs_file) / filename
        if local_file.is_file():
            return local_file
        return None
