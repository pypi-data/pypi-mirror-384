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
import time
from pathlib import Path
from typing import Any, List, Mapping, Optional, Tuple

from aiosqlite import connect, Row
from aria_studio.app.common.types import Group
from aria_studio.app.constants import (
    TABLE_GROUP_FILES,
    TABLE_GROUP_MPS_REQUESTS,
    TABLE_GROUPS,
)
from aria_studio.app.utils import get_db_path, login_required

logger = logging.getLogger(__name__)


class GroupMPSRequestExistsException(Exception):
    """Raised when a group already had MPS requested."""

    pass


class GroupManager:
    """
    The class to manage local groups. This will support all group operations.
    * Create a new group.
    * Delete a group.
    * List all groups.
    * Add files to a group.
    * Remove files from a group.
    """

    instance_: "GroupManager" = None
    lock_: asyncio.Lock = asyncio.Lock()

    @classmethod
    @login_required
    async def get_instance(cls):
        """Get the group manager singleton."""
        if cls.instance_ is None:
            async with cls.lock_:
                db_path = get_db_path()
                logger.debug(f"Creating group manager with {db_path}")
                cls.instance_ = GroupManager(db_path=db_path)
                await cls.instance_.async_init()
        return cls.instance_

    @classmethod
    async def reset(cls):
        """Reset the group manager singleton."""
        async with cls.lock_:
            logger.debug("Resetting group manager")
            cls.instance_ = None

    def __init__(self, db_path: Path):
        self._db_path: Path = db_path

    async def get_all(self) -> Mapping[str, Group]:
        """Return all groups."""
        groups: Mapping[str, Group] = {}
        query: str = f"""
            SELECT * FROM {TABLE_GROUPS}
        """
        async with connect(self._db_path) as db:
            db.row_factory = Row
            # Get group names
            async with db.execute(query) as cursor:
                async for row in cursor:
                    groups[row["name"]] = Group(**row)

            for _, group in groups.items():
                # Get VRS files
                group.vrs_files = await self._get_vrs_files(db, group.name)
        logger.debug(f"Groups: {groups}")
        return groups

    async def get(self, group_name: str) -> Optional[Group]:
        """Get a group by name."""
        query: str = f"""
            SELECT * FROM {TABLE_GROUPS}
            WHERE name='{group_name}'
        """
        async with connect(self._db_path) as db:
            db.row_factory = Row
            cursor = await db.execute(query)
            if row := await cursor.fetchone():
                group = Group(**row)
                # Get VRS files
                group.vrs_files = await self._get_vrs_files(db, group.name)
                return group
        return None

    async def create_group(self, group_name: str, group_path: Path):
        """Create a new group."""
        group_path = group_path / group_name
        logger.debug(f"Creating group {group_name} with path: {group_path}")

        if await self.exists(group_name):
            raise Exception(f"Group {group_name} already exists.")

        if group_path.exists():
            raise Exception(f"Path {group_path} path already exists.")

        group_path.mkdir(parents=True)
        query = f"""
            INSERT INTO {TABLE_GROUPS} (name, path_on_device, creation_time)
            VALUES (?, ?, ?)
        """
        await self._run_and_commit(
            [(query, (group_name, str(group_path), int(time.time())))]
        )

    async def delete_group(self, group_name: str) -> Group:
        """Delete a group. This will remove all group files and the group mps requests."""
        logger.debug(f"Deleting group {group_name}")
        if not await self.exists(group_name):
            raise Exception(f"Group {group_name} name doesn't exists.")

        query: str = f"""
            DELETE FROM {TABLE_GROUPS}
            WHERE name=?
        """
        await self._run_and_commit([(query, (group_name,))])

    async def get_group_path(self, name: str) -> str:
        group = await self.get(group_name=name)
        return group.path_on_device

    async def exists(self, group_name: str) -> bool:
        """Check if a group exists."""
        query: str = f"""
            SELECT name FROM {TABLE_GROUPS}
            WHERE name = ?
        """
        async with connect(self._db_path) as db:
            cursor = await db.execute(query, (group_name,))
            logger.debug(cursor.rowcount)
            return await cursor.fetchone() is not None

    async def add_files(self, group_name: str, files: List[Path]) -> None:
        """Add a list of VRS files to the group."""
        if not await self.exists(group_name):
            raise Exception(f"Group {group_name} doesn't exists.")

        for file in files:
            if not file.is_file():
                raise Exception(f"File {file} doesn't exist.")

        check_existing_mps_request_query: str = f"""
            SELECT group_name FROM {TABLE_GROUP_MPS_REQUESTS}
            WHERE group_name=?
        """

        async with connect(self._db_path) as db:
            cursor = await db.execute(check_existing_mps_request_query, (group_name,))
            if await cursor.fetchone() is not None:
                raise GroupMPSRequestExistsException(f"Group {group_name} is locked.")

        query_params: List[Tuple[str, Tuple[Any]]] = []
        query: str = f"""
            INSERT OR IGNORE INTO {TABLE_GROUP_FILES} (group_name, file_path)
            VALUES (?, ?)
        """
        for file in files:
            query_params.append((query, (group_name, str(file))))
        await self._run_and_commit(query_params)

    async def remove_files(self, group_name: str, files: List[Path]) -> Group:
        """Remove a list of VRS files from the group."""
        group: Group = await self.get(group_name)
        if group is None:
            raise Exception(f"Group {group_name} doesn't exists.")
        query: str = f"""
            DELETE FROM {TABLE_GROUP_FILES}
            WHERE group_name=? AND file_path IN ({', '.join(['?']*len(files))})
        """
        await self._run_and_commit([(query, (group_name, *[str(f) for f in files]))])
        return group

    async def async_init(self):
        """Initialize the database."""
        query_params: List[Tuple[str, Tuple[Any]]] = []
        query: str = f"""
            CREATE TABLE IF NOT EXISTS {TABLE_GROUPS} (
            name TEXT PRIMARY KEY,
            path_on_device TEXT,
            creation_time INTEGER
            )
        """
        query_params.append((query, ()))

        query: str = f"""
            CREATE TABLE IF NOT EXISTS {TABLE_GROUP_FILES} (
            group_name TEXT,
            file_path TEXT,
            PRIMARY KEY (group_name, file_path),
            FOREIGN KEY (group_name) REFERENCES {TABLE_GROUPS} (name) ON DELETE CASCADE
            )
        """
        query_params.append((query, ()))
        await self._run_and_commit(query_params)

    async def _get_vrs_files(self, db: connect, group_name: str) -> List[Path]:
        """Get all VRS files for a group."""
        query = f"""
            SELECT file_path FROM {TABLE_GROUP_FILES}
            WHERE group_name=?
        """
        db.row_factory = Row
        cursor = await db.execute(query, (group_name,))
        vrs_files: List[Path] = []
        async for row in cursor:
            vrs_files.append(Path(row["file_path"]))
        return vrs_files

    async def _run_and_commit(self, query_params: List[Tuple[str, Tuple[Any]]]) -> None:
        """Run a query and commit the changes to the DB."""
        async with connect(self._db_path) as db:
            await db.execute("PRAGMA FOREIGN_KEYS = ON")
            for query, input in query_params:
                await db.execute(query, input)
            await db.commit()
