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
from dataclasses import fields
from pathlib import Path
from typing import Any, List, Mapping, Optional, Tuple

from aiosqlite import connect, Row
from aria_studio.app.common.types import DBGroupMpsRequest, MpsRequestStage
from aria_studio.app.constants import (
    TABLE_GROUP_FILES,
    TABLE_GROUP_MPS_REQUESTS,
    TABLE_GROUP_MPS_STATUS,
    TABLE_GROUPS,
)
from projectaria_tools.aria_mps_cli.cli_lib.types import MpsFeature

logger = logging.getLogger(__name__)


class GroupMpsRequestCache:
    """SQLite cache for group MPS requests"""

    def __init__(self, db_path: Path):
        self._db_path: Path = db_path

    async def put(self, **kwargs) -> None:
        """Set the cache entry for a given group name."""
        per_file_status: Mapping[Path, str] = kwargs.pop("status", {})
        query_params: List[Tuple[str, Tuple[Any]]] = []

        table_columns = {f.name for f in fields(DBGroupMpsRequest)}
        if kwargs and not set(kwargs.keys()).issubset(table_columns):
            raise ValueError(f"Unknown kwargs: {set(kwargs.keys()) - table_columns}")
        kwargs = _fix_column_type(kwargs)
        group_name = kwargs["group_name"]
        update: bool = False
        if await self.get(group_name):
            update = True
            kwargs.pop("group_name")
            placeholders = ", ".join([f"{column}=?" for column in kwargs.keys()])
            query = f"""
                UPDATE {TABLE_GROUP_MPS_REQUESTS} SET {placeholders}
                WHERE group_name=?
            """
            params = tuple(kwargs.values()) + (group_name,)
        else:
            columns = ", ".join(kwargs.keys())
            placeholders = ", ".join(["?"] * len(kwargs.keys()))
            query = f"""
                INSERT INTO {TABLE_GROUP_MPS_REQUESTS}({columns})
                VALUES ({placeholders})
            """
            params = tuple(kwargs.values())
        query_params.append((query, params))

        # Add  status and error codes
        if per_file_status:
            for file_path, status_error_code in per_file_status.items():
                status, error_code = status_error_code
                if update:
                    query = f"""
                        UPDATE {TABLE_GROUP_MPS_STATUS} SET status=?, error_code=?
                        WHERE group_name=? AND file_path=?
                    """
                    params = (status, error_code, group_name, str(file_path))
                else:
                    query = f"""
                        INSERT INTO {TABLE_GROUP_MPS_STATUS}(group_name, file_path, status, error_code)
                        VALUES (?, ?, ?, ?)
                    """
                    params = (
                        group_name,
                        str(file_path),
                        str(status),
                        str(error_code),
                    )
                query_params.append((query, params))
        await self._run_and_commit(query_params)

    async def create_table(self):
        """Create the table if it doesn't exist."""
        query_params: List[Tuple[str, Tuple[Any]]] = []
        query: str = f"""
            CREATE TABLE IF NOT EXISTS {TABLE_GROUP_MPS_REQUESTS} (
            group_name TEXT PRIMARY KEY,
            request_id INTEGER NULL,
            output_path TEXT NULL,
            feature TEXT NOT NULL,
            creation_time DATETIME NULL,
            stage TEXT NOT NULL,
            retry_failed INTEGER DEFAULT FALSE,
            force INTEGER DEFAULT FALSE,
            FOREIGN KEY (group_name) REFERENCES groups (name) ON DELETE CASCADE
            )
        """
        query_params.append((query, ()))
        # Status and Error codes
        query: str = f"""
            CREATE TABLE IF NOT EXISTS {TABLE_GROUP_MPS_STATUS} (
                group_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                status TEXT NOT NULL,
                error_code TEXT NULL,
                PRIMARY KEY (group_name, file_path),
                FOREIGN KEY (group_name) REFERENCES {TABLE_GROUPS} (name) ON DELETE CASCADE,
                FOREIGN KEY (group_name, file_path) REFERENCES {TABLE_GROUP_FILES} (group_name, file_path) ON DELETE CASCADE
            )
        """
        query_params.append((query, ()))
        await self._run_and_commit(query_params)

    async def get(self, group_name: str) -> Optional[DBGroupMpsRequest]:
        """Get the cache entry for a given group name."""
        query = f"""
            SELECT * FROM {TABLE_GROUP_MPS_REQUESTS}
            WHERE group_name = ?
        """
        query_error_codes: str = f"""
            SELECT file_path, status, error_code FROM {TABLE_GROUP_MPS_STATUS}
            WHERE group_name = ?
        """
        async with connect(self._db_path) as db:
            db.row_factory = Row
            cursor = await db.execute(query, (group_name,))
            cursor_error_codes = await db.execute(query_error_codes, (group_name,))
            if row := await cursor.fetchone():
                req_status = {
                    Path(file_path): (status, error_code)
                    for file_path, status, error_code in await cursor_error_codes.fetchall()
                }
                return DBGroupMpsRequest(**row, status=req_status)
        return None

    async def get_incomplete_requests(self) -> List[DBGroupMpsRequest]:
        """Get all incomplete requests from the cache"""
        reqs: List[DBGroupMpsRequest] = []
        query = f"""
            SELECT * FROM {TABLE_GROUP_MPS_REQUESTS}
            WHERE stage IN ('{MpsRequestStage.REQUESTOR.value}', '{MpsRequestStage.MONITOR.value}')
        """
        async with connect(self._db_path) as db:
            db.row_factory = Row
            cursor = await db.execute(query, ())
            async for row in cursor:
                reqs.append(DBGroupMpsRequest(**row))
        return reqs

    async def _run_and_commit(self, query_params: List[Tuple[str, Tuple[Any]]]) -> None:
        """Run a query and commit the changes to the DB."""
        async with connect(self._db_path) as db:
            await db.execute("PRAGMA FOREIGN_KEYS = ON")
            for query, input in query_params:
                await db.execute(query, input)
            await db.commit()


def _fix_column_type(kwargs) -> Mapping[str, Any]:
    """Fix the column type for a given group name."""
    if "feature" in kwargs and isinstance(kwargs["feature"], MpsFeature):
        kwargs["feature"] = kwargs["feature"].value
    if "stage" in kwargs and isinstance(kwargs["stage"], MpsRequestStage):
        kwargs["stage"] = kwargs["stage"].value
    return kwargs
