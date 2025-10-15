# Copyright 2025 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Channel status information returned to users."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional


class ChannelStatus:
    """Channel status information returned to users.

    Provides access to channel status information including the channel name,
    status code, and latest committed offset token from Snowflake server.

    """

    def __init__(
        self,
        database_name: str,
        schema_name: str,
        pipe_name: str,
        channel_name: str,
        status_code: str,
        latest_committed_offset_token: Optional[str],
        created_on_ms: int,
        rows_inserted: int,
        rows_parsed: int,
        rows_error_count: int,
        last_error_offset_upper_bound: Optional[str],
        last_error_message: Optional[str],
        last_error_timestamp_ms: Optional[int],
        snowflake_avg_processing_latency_ms: Optional[int],
        last_refreshed_on_ms: int,
    ):
        """Initialize ChannelStatus.

        Args:
            database_name: The database name of the channel
            schema_name: The schema name of the channel
            pipe_name: The pipe name of the channel
            channel_name: The name of the channel
            status_code: The status code for the channel from Snowflake server
            latest_committed_offset_token: The latest committed offset token for the channel
            created_on_ms: The created on timestamp in ms for the channel
            rows_inserted: The rows inserted for the channel
            rows_parsed: The rows parsed for the channel
            rows_error_count: The rows error count for the channel
            last_error_offset_upper_bound: The last error offset upper bound for the channel
            last_error_message: The last error message for the channel
            last_error_timestamp_ms: The last error timestamp in ms for the channel
            snowflake_avg_processing_latency_ms: The snowflake avg processing latency in ms for the
                channel to ingest data in the snowflake server side
            last_refreshed_on_ms: The last refreshed on timestamp in ms for the channel
        """
        self._database_name = database_name
        self._schema_name = schema_name
        self._pipe_name = pipe_name
        self._channel_name = channel_name
        self._status_code = status_code
        self._latest_committed_offset_token = latest_committed_offset_token
        self._created_on_ms = created_on_ms
        self._rows_inserted = rows_inserted
        self._rows_parsed = rows_parsed
        self._rows_error_count = rows_error_count
        self._last_error_offset_upper_bound = last_error_offset_upper_bound
        self._last_error_message = last_error_message
        self._last_error_timestamp_ms = last_error_timestamp_ms
        self._snowflake_avg_processing_latency_ms = snowflake_avg_processing_latency_ms
        self._last_refreshed_on_ms = last_refreshed_on_ms

    @property
    def database_name(self) -> str:
        """Get the database name."""
        return self._database_name

    @property
    def schema_name(self) -> str:
        """Get the schema name."""
        return self._schema_name

    @property
    def pipe_name(self) -> str:
        """Get the pipe name."""
        return self._pipe_name

    @property
    def channel_name(self) -> str:
        """Get the channel name.

        Returns:
            str: The name of the channel
        """
        return self._channel_name

    @property
    def status_code(self) -> str:
        """Get the status code for the channel.

        Returns:
            str: The status code from Snowflake server
        """
        return self._status_code

    @property
    def latest_committed_offset_token(self) -> Optional[str]:
        """Get the latest committed offset token for the channel.

        Returns:
            Optional[str]: The latest committed offset token, or None if no commits yet
        """
        return self._latest_committed_offset_token

    @property
    def latest_offset_token(self) -> Optional[str]:
        """Get the latest committed offset token for the channel.

        Deprecated: Use latest_committed_offset_token instead.

        Returns:
            Optional[str]: The latest committed offset token, or None if no commits yet
        """
        return self._latest_committed_offset_token

    @property
    def created_on(self) -> datetime:
        """Get the created on timestamp for the channel."""
        return datetime.fromtimestamp(self._created_on_ms / 1000.0)

    @property
    def rows_inserted_count(self) -> int:
        """Get the rows inserted for the channel."""
        return self._rows_inserted

    @property
    def rows_parsed_count(self) -> int:
        """Get the rows parsed for the channel."""
        return self._rows_parsed

    @property
    def rows_error_count(self) -> int:
        """Get the rows error count for the channel."""
        return self._rows_error_count

    @property
    def last_error_offset_token_upper_bound(self) -> Optional[str]:
        """Get the last error offset token upper bound for the channel."""
        return self._last_error_offset_upper_bound

    @property
    def last_error_message(self) -> Optional[str]:
        """Get the last error message for the channel."""
        return self._last_error_message

    @property
    def last_error_timestamp(self) -> Optional[datetime]:
        """Get the last error timestamp for the channel."""
        if self._last_error_timestamp_ms is None:
            return None
        return datetime.fromtimestamp(self._last_error_timestamp_ms / 1000.0)

    @property
    def server_avg_processing_latency(self) -> Optional[timedelta]:
        """Get the snowflake avg processing latency for the channel."""
        if self._snowflake_avg_processing_latency_ms is None:
            return None
        return timedelta(milliseconds=self._snowflake_avg_processing_latency_ms)

    @property
    def last_refreshed_on(self) -> datetime:
        """Get the last refreshed on timestamp for the channel."""
        return datetime.fromtimestamp(self._last_refreshed_on_ms / 1000.0)

    def __repr__(self) -> str:
        """Return string representation of ChannelStatus."""
        return (
            f"ChannelStatus(database_name='{self.database_name}', "
            f"schema_name='{self.schema_name}', "
            f"pipe_name='{self.pipe_name}', "
            f"channel_name='{self.channel_name}', "
            f"status_code='{self.status_code}', "
            f"latest_committed_offset_token={self.latest_committed_offset_token!r}, "
            f"created_on={self.created_on}, "
            f"rows_inserted_count={self.rows_inserted_count}, "
            f"rows_parsed_count={self.rows_parsed_count}, "
            f"rows_error_count={self.rows_error_count}, "
            f"last_error_offset_upper_bound={self.last_error_offset_token_upper_bound!r}, "
            f"last_error_message={self.last_error_message!r}, "
            f"last_error_timestamp={self.last_error_timestamp}, "
            f"snowflake_avg_processing_latency={self.server_avg_processing_latency}, "
            f"last_refreshed_on={self.last_refreshed_on})"
        )

    def __str__(self) -> str:
        """Return human-readable string representation."""
        return f"Channel '{self.channel_name}': {self.status_code}"
