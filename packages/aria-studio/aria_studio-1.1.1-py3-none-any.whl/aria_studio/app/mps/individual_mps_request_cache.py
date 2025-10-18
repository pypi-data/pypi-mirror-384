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
from typing import Any, Final, List, Mapping, Optional, Tuple

from aiosqlite import connect, Row
from aria_studio.app.common.types import DBIndividualMpsRequest, MpsRequestStage
from aria_studio.app.constants import TABLE_INDIVIDUAL_MPS_REQUESTS
from projectaria_tools.aria_mps_cli.cli_lib.types import MpsFeature

logger = logging.getLogger(__name__)


class IndividualMpsRequestCache:
    """SQLite cache for group MPS requests"""

    def __init__(self, db_path: Path):
        self._db_path: Path = db_path
        self._table_name: Final[str] = TABLE_INDIVIDUAL_MPS_REQUESTS

    async def put(self, **kwargs) -> None:
        """Set the cache entry for a given group name."""
        logger.info(f"Setting cache entry for {kwargs}")
        table_columns = {f.name for f in fields(DBIndividualMpsRequest)}
        if kwargs and not set(kwargs.keys()).issubset(table_columns):
            raise ValueError(f"Unknown kwargs: {set(kwargs.keys()) - table_columns}")
        if await self.get(kwargs["vrs_path"], kwargs["feature"]):
            kwargs = _fix_column_type(kwargs)
            vrs_path = kwargs.pop("vrs_path")
            feature = kwargs.pop("feature")
            placeholders = ", ".join([f"{column}=?" for column in kwargs.keys()])
            query = f"""
                UPDATE {self._table_name} SET {placeholders}
                WHERE vrs_path=? and feature=?
            """
            params = tuple(kwargs.values()) + (vrs_path, feature)
        else:
            kwargs = _fix_column_type(kwargs)
            columns = ", ".join(kwargs.keys())
            placeholders = ", ".join(["?"] * len(kwargs.keys()))
            query = f"""
                INSERT INTO {self._table_name}({columns})
                VALUES ({placeholders})
            """
            params = tuple(kwargs.values())
        await self._run_and_commit(query, params)

    async def remove(self, vrs_path: Path, feature: MpsFeature) -> None:
        """Delete the cache entry for a given vrs path ."""
        query: str = f"""
            DELETE FROM {self._table_name}
            WHERE vrs_path = ? and feature = ?
        """
        await self._run_and_commit(query, (str(vrs_path), feature.value))

    async def create_table(self):
        """Create the table if it doesn't exist."""
        query: str = f"""
            CREATE TABLE IF NOT EXISTS {self._table_name} (
            vrs_path TEXT NOT NULL,
            feature TEXT NOT NULL,
            request_id INTEGER NULL,
            output_path TEXT NULL,
            creation_time DATETIME NULL,
            status TEXT NOT NULL,
            stage TEXT NOT NULL,
            error_code INTEGER NULL,
            retry_failed INTEGER DEFAULT FALSE,
            force INTEGER DEFAULT FALSE,
            PRIMARY KEY (vrs_path, feature)
            )
        """
        await self._run_and_commit(query)

    async def get(
        self, vrs_path: Optional[Path] = None, feature: Optional[MpsFeature] = None
    ) -> List[DBIndividualMpsRequest]:
        """Get the cache entry for a given vrs_path and feature.
        If vrs_path is None, get all the entries for the feature.
        If feature is None, get all the entries for vrs_path.
        If both are None, get all the entries.
        """
        query = f"""
            SELECT * FROM {self._table_name}
        """
        vrs_path_clause = f" vrs_path = '{str(vrs_path)}'" if vrs_path else ""
        feature_clause = f" feature = '{feature.value}'" if feature else ""
        if vrs_path and feature:
            query = f"{query} WHERE {vrs_path_clause} AND {feature_clause}"
        elif feature:
            query = f"{query} WHERE {feature_clause}"
        elif vrs_path:
            query = f"{query} WHERE {vrs_path_clause}"
        reqs: List[DBIndividualMpsRequest] = []
        async with connect(self._db_path) as db:
            db.row_factory = Row
            cursor = await db.execute(query, ())
            async for row in cursor:
                reqs.append(DBIndividualMpsRequest(**row))
        return reqs

    async def get_incomplete_requests(self) -> List[DBIndividualMpsRequest]:
        """Get all incomplete requests from the cache"""
        reqs: List[DBIndividualMpsRequest] = []
        query = f"""
            SELECT * FROM {self._table_name}
            WHERE stage IN ('{MpsRequestStage.REQUESTOR.value}', '{MpsRequestStage.MONITOR.value}')
        """
        async with connect(self._db_path) as db:
            db.row_factory = Row
            cursor = await db.execute(query, ())
            async for row in cursor:
                reqs.append(DBIndividualMpsRequest(**row))
        return reqs

    async def delete_cache(self, vrs_path: Path) -> None:
        """Delete the cache entry for a given group name."""
        query = f"""
            DELETE FROM {self.cache_table}
            WHERE vrs_path=?
        """
        await self._run_and_commit(query, (vrs_path,))

    async def _run_and_commit(
        self, query: str, input: Optional[Tuple[Any]] = ()
    ) -> None:
        """Run a query and commit the changes to the DB."""
        logger.debug(f"Running query {query} with input {input}")
        async with connect(self._db_path) as db:
            await db.execute(query, input)
            await db.commit()


def _fix_column_type(kwargs) -> Mapping[str, Any]:
    """Fix the column type for a given group name."""
    if "feature" in kwargs and isinstance(kwargs["feature"], MpsFeature):
        kwargs["feature"] = kwargs["feature"].value
    if "stage" in kwargs and isinstance(kwargs["stage"], MpsRequestStage):
        kwargs["stage"] = kwargs["stage"].value
    kwargs["vrs_path"] = str(kwargs["vrs_path"])
    return kwargs
