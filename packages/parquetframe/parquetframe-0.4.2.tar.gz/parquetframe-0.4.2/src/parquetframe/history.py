"""
History management for ParquetFrame interactive sessions.

This module provides Parquet-based persistent storage for:
- Interactive sessions
- Query history (SQL and natural language)
- AI interactions and results
- Script export functionality
"""

import time
import uuid
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import pandas as pd
except ImportError as e:
    raise ImportError(
        "History management requires pandas and pyarrow. "
        "Install with: pip install pandas pyarrow"
    ) from e


@dataclass
class QueryRecord:
    """Represents a single query in history."""

    session_id: str
    query_id: str
    query_text: str
    query_type: str  # 'sql' or 'natural_language'
    timestamp: float
    execution_time_ms: float | None = None
    success: bool = True
    error_message: str | None = None
    result_rows: int | None = None
    ai_generated: bool = False
    natural_language_input: str | None = None
    ai_attempts: int = 1


@dataclass
class SessionRecord:
    """Represents an interactive session."""

    session_id: str
    start_time: float
    end_time: float | None = None
    data_source: str | None = None
    data_source_type: str | None = None  # 'parquet' or 'database'
    ai_enabled: bool = False
    total_queries: int = 0
    successful_queries: int = 0


@dataclass
class AIMessage:
    """Represents an AI interaction."""

    session_id: str
    message_id: str
    timestamp: float
    natural_language_input: str
    generated_sql: str | None = None
    success: bool = False
    error_message: str | None = None
    attempts: int = 1
    final_result: str | None = None


class HistoryManager:
    """Manages persistent history storage using Parquet files."""

    def __init__(self, history_dir: Path | None = None):
        """
        Initialize history manager.

        Args:
            history_dir: Directory for history storage. Defaults to ~/.parquetframe
        """
        if history_dir is None:
            history_dir = Path.home() / ".parquetframe"

        self.history_dir = history_dir
        self.history_dir.mkdir(parents=True, exist_ok=True)

        # Define parquet file paths
        self.sessions_path = self.history_dir / "sessions.parquet"
        self.queries_path = self.history_dir / "queries.parquet"
        self.ai_messages_path = self.history_dir / "ai_messages.parquet"

        self._init_parquet_files()

    def _init_parquet_files(self) -> None:
        """Initialize empty Parquet files if they don't exist."""
        # Initialize sessions file
        if not self.sessions_path.exists():
            empty_sessions = pd.DataFrame(
                {
                    "session_id": pd.Series([], dtype="string"),
                    "start_time": pd.Series([], dtype="float64"),
                    "end_time": pd.Series([], dtype="float64"),
                    "data_source": pd.Series([], dtype="string"),
                    "data_source_type": pd.Series([], dtype="string"),
                    "ai_enabled": pd.Series([], dtype="bool"),
                    "total_queries": pd.Series([], dtype="int64"),
                    "successful_queries": pd.Series([], dtype="int64"),
                }
            )
            empty_sessions.to_parquet(self.sessions_path, index=False)

        # Initialize queries file
        if not self.queries_path.exists():
            empty_queries = pd.DataFrame(
                {
                    "query_id": pd.Series([], dtype="string"),
                    "session_id": pd.Series([], dtype="string"),
                    "query_text": pd.Series([], dtype="string"),
                    "query_type": pd.Series([], dtype="string"),
                    "timestamp": pd.Series([], dtype="float64"),
                    "execution_time_ms": pd.Series([], dtype="float64"),
                    "success": pd.Series([], dtype="bool"),
                    "error_message": pd.Series([], dtype="string"),
                    "result_rows": pd.Series([], dtype="int64"),
                    "ai_generated": pd.Series([], dtype="bool"),
                    "natural_language_input": pd.Series([], dtype="string"),
                    "ai_attempts": pd.Series([], dtype="int64"),
                }
            )
            empty_queries.to_parquet(self.queries_path, index=False)

        # Initialize AI messages file
        if not self.ai_messages_path.exists():
            empty_ai_messages = pd.DataFrame(
                {
                    "message_id": pd.Series([], dtype="string"),
                    "session_id": pd.Series([], dtype="string"),
                    "timestamp": pd.Series([], dtype="float64"),
                    "natural_language_input": pd.Series([], dtype="string"),
                    "generated_sql": pd.Series([], dtype="string"),
                    "success": pd.Series([], dtype="bool"),
                    "error_message": pd.Series([], dtype="string"),
                    "attempts": pd.Series([], dtype="int64"),
                    "final_result": pd.Series([], dtype="string"),
                }
            )
            empty_ai_messages.to_parquet(self.ai_messages_path, index=False)

    def create_session(
        self,
        data_source: str | None = None,
        data_source_type: str | None = None,
        ai_enabled: bool = False,
    ) -> str:
        """
        Create a new session record.

        Args:
            data_source: Path to data source or database URI
            data_source_type: Type of data source ('parquet' or 'database')
            ai_enabled: Whether AI functionality is enabled

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())

        # Create new session record
        new_session = pd.DataFrame(
            [
                {
                    "session_id": session_id,
                    "start_time": time.time(),
                    "end_time": None,
                    "data_source": data_source,
                    "data_source_type": data_source_type,
                    "ai_enabled": ai_enabled,
                    "total_queries": 0,
                    "successful_queries": 0,
                }
            ]
        )

        # Append to existing sessions
        if self.sessions_path.exists() and self.sessions_path.stat().st_size > 0:
            existing_sessions = pd.read_parquet(self.sessions_path)
            # Ensure consistent dtypes before concatenation
            if len(existing_sessions) > 0:
                # Suppress pandas FutureWarning about concat with empty/NA entries
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore", category=FutureWarning, message=".*concat.*empty.*"
                    )
                    sessions_df = pd.concat(
                        [existing_sessions, new_session], ignore_index=True
                    )
            else:
                sessions_df = new_session
        else:
            sessions_df = new_session

        sessions_df.to_parquet(self.sessions_path, index=False)
        return session_id

    def end_session(self, session_id: str) -> None:
        """Mark a session as ended."""
        if not self.sessions_path.exists():
            return

        # Load sessions
        sessions_df = pd.read_parquet(self.sessions_path)

        # Update the specific session
        mask = sessions_df["session_id"] == session_id
        if not mask.any():
            return

        # Calculate query counts
        total_queries = 0
        successful_queries = 0
        if self.queries_path.exists() and self.queries_path.stat().st_size > 0:
            queries_df = pd.read_parquet(self.queries_path)
            session_queries = queries_df[queries_df["session_id"] == session_id]
            total_queries = len(session_queries)
            successful_queries = len(session_queries[session_queries["success"]])

        # Update session record
        sessions_df.loc[mask, "end_time"] = time.time()
        sessions_df.loc[mask, "total_queries"] = total_queries
        sessions_df.loc[mask, "successful_queries"] = successful_queries

        sessions_df.to_parquet(self.sessions_path, index=False)

    def log_query(
        self,
        session_id: str,
        query_text: str,
        query_type: str = "sql",
        execution_time_ms: float | None = None,
        success: bool = True,
        error_message: str | None = None,
        result_rows: int | None = None,
        ai_generated: bool = False,
        natural_language_input: str | None = None,
        ai_attempts: int = 1,
    ) -> str:
        """
        Log a query execution.

        Args:
            session_id: Session ID
            query_text: The SQL query text
            query_type: Type of query ('sql' or 'natural_language')
            execution_time_ms: Execution time in milliseconds
            success: Whether query was successful
            error_message: Error message if failed
            result_rows: Number of result rows
            ai_generated: Whether query was generated by AI
            natural_language_input: Original natural language input
            ai_attempts: Number of AI attempts

        Returns:
            Query ID
        """
        query_id = str(uuid.uuid4())

        # Create new query record
        new_query = pd.DataFrame(
            [
                {
                    "query_id": query_id,
                    "session_id": session_id,
                    "query_text": query_text,
                    "query_type": query_type,
                    "timestamp": time.time(),
                    "execution_time_ms": execution_time_ms,
                    "success": success,
                    "error_message": error_message,
                    "result_rows": result_rows,
                    "ai_generated": ai_generated,
                    "natural_language_input": natural_language_input,
                    "ai_attempts": ai_attempts,
                }
            ]
        )

        # Append to existing queries
        if self.queries_path.exists() and self.queries_path.stat().st_size > 0:
            existing_queries = pd.read_parquet(self.queries_path)
            # Ensure consistent dtypes before concatenation
            if len(existing_queries) > 0:
                # Suppress pandas FutureWarning about concat with empty/NA entries
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore", category=FutureWarning, message=".*concat.*empty.*"
                    )
                    queries_df = pd.concat(
                        [existing_queries, new_query], ignore_index=True
                    )
            else:
                queries_df = new_query
        else:
            queries_df = new_query

        queries_df.to_parquet(self.queries_path, index=False)
        return query_id

    def log_ai_message(
        self,
        session_id: str,
        natural_language_input: str,
        generated_sql: str | None = None,
        success: bool = False,
        error_message: str | None = None,
        attempts: int = 1,
        final_result: str | None = None,
    ) -> str:
        """
        Log an AI interaction.

        Args:
            session_id: Session ID
            natural_language_input: User's natural language input
            generated_sql: SQL generated by AI
            success: Whether AI generation was successful
            error_message: Error message if failed
            attempts: Number of attempts made
            final_result: Final result summary

        Returns:
            Message ID
        """
        message_id = str(uuid.uuid4())

        # Create new AI message record
        new_message = pd.DataFrame(
            [
                {
                    "message_id": message_id,
                    "session_id": session_id,
                    "timestamp": time.time(),
                    "natural_language_input": natural_language_input,
                    "generated_sql": generated_sql,
                    "success": success,
                    "error_message": error_message,
                    "attempts": attempts,
                    "final_result": final_result,
                }
            ]
        )

        # Append to existing AI messages
        if self.ai_messages_path.exists() and self.ai_messages_path.stat().st_size > 0:
            existing_messages = pd.read_parquet(self.ai_messages_path)
            # Ensure consistent dtypes before concatenation
            if len(existing_messages) > 0:
                # Suppress pandas FutureWarning about concat with empty/NA entries
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore", category=FutureWarning, message=".*concat.*empty.*"
                    )
                    messages_df = pd.concat(
                        [existing_messages, new_message], ignore_index=True
                    )
            else:
                messages_df = new_message
        else:
            messages_df = new_message

        messages_df.to_parquet(self.ai_messages_path, index=False)
        return message_id

    def get_session_history(
        self, session_id: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get query history for a session or all sessions.

        Args:
            session_id: Specific session ID, or None for all sessions
            limit: Maximum number of queries to return

        Returns:
            List of query records
        """
        if not self.queries_path.exists() or self.queries_path.stat().st_size == 0:
            return []

        queries_df = pd.read_parquet(self.queries_path)

        if session_id:
            queries_df = queries_df[queries_df["session_id"] == session_id]

        # Sort by timestamp descending and limit
        queries_df = queries_df.sort_values("timestamp", ascending=False).head(limit)

        # Handle NaN values before converting to dict
        queries_df = queries_df.where(pd.notna(queries_df), None)
        return queries_df.to_dict("records")

    def get_recent_sessions(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get recent sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session records
        """
        if not self.sessions_path.exists() or self.sessions_path.stat().st_size == 0:
            return []

        sessions_df = pd.read_parquet(self.sessions_path)
        sessions_df = sessions_df.sort_values("start_time", ascending=False).head(limit)

        # Handle NaN values before converting to dict
        sessions_df = sessions_df.where(pd.notna(sessions_df), None)
        return sessions_df.to_dict("records")

    def export_session_script(
        self,
        session_id: str,
        output_path: Path,
        include_ai_queries: bool = True,
        include_failed_queries: bool = False,
    ) -> None:
        """
        Export session queries as SQL script.

        Args:
            session_id: Session ID to export
            output_path: Output file path
            include_ai_queries: Whether to include AI-generated queries
            include_failed_queries: Whether to include failed queries
        """
        # Get session info
        if not self.sessions_path.exists():
            raise ValueError("No sessions found")

        sessions_df = pd.read_parquet(self.sessions_path)
        session_mask = sessions_df["session_id"] == session_id

        if not session_mask.any():
            raise ValueError(f"Session {session_id} not found")

        # Handle NaN values before converting to dict
        session_row = sessions_df[session_mask].iloc[0]
        # Replace NaN with None for JSON serialization
        session = session_row.where(pd.notna(session_row), None).to_dict()

        # Get queries with filters
        if not self.queries_path.exists():
            queries_df = pd.DataFrame()
        else:
            queries_df = pd.read_parquet(self.queries_path)
            queries_df = queries_df[queries_df["session_id"] == session_id]

            if not include_ai_queries:
                queries_df = queries_df[~queries_df["ai_generated"]]

            if not include_failed_queries:
                queries_df = queries_df[queries_df["success"]]

            # Sort by timestamp
            queries_df = queries_df.sort_values("timestamp")

        # Handle NaN values before converting to dict (fixes JSON serialization issues)
        queries_df = queries_df.where(pd.notna(queries_df), None)
        queries = queries_df.to_dict("records")

        # Generate script content
        script_lines = []
        script_lines.append("-- ParquetFrame Session Export")
        script_lines.append(f"-- Session ID: {session_id}")
        script_lines.append(
            f"-- Start Time: {datetime.fromtimestamp(session['start_time'])}"
        )
        if session["end_time"]:
            script_lines.append(
                f"-- End Time: {datetime.fromtimestamp(session['end_time'])}"
            )
        script_lines.append(f"-- Data Source: {session['data_source'] or 'Unknown'}")
        script_lines.append(f"-- AI Enabled: {session['ai_enabled']}")
        script_lines.append(f"-- Total Queries: {len(queries)}")
        script_lines.append("")

        for i, query in enumerate(queries, 1):
            script_lines.append(f"-- Query {i}")
            script_lines.append(
                f"-- Timestamp: {datetime.fromtimestamp(query['timestamp'])}"
            )

            if query["ai_generated"] and query["natural_language_input"]:
                script_lines.append(
                    f"-- Natural Language: {query['natural_language_input']}"
                )

            if query["execution_time_ms"]:
                script_lines.append(
                    f"-- Execution Time: {query['execution_time_ms']:.2f}ms"
                )

            if not query["success"] and query["error_message"]:
                script_lines.append(f"-- ERROR: {query['error_message']}")

            script_lines.append(query["query_text"])
            script_lines.append("")

        # Write script file
        with open(output_path, "w") as f:
            f.write("\n".join(script_lines))

    def get_statistics(self) -> dict[str, Any]:
        """Get overall usage statistics."""
        stats = {
            "total_sessions": 0,
            "total_queries": 0,
            "total_ai_messages": 0,
            "successful_queries": 0,
            "query_success_rate": 0.0,
            "successful_ai_messages": 0,
            "ai_success_rate": 0.0,
            "recent_sessions_7d": 0,
        }

        # Session statistics
        if self.sessions_path.exists() and self.sessions_path.stat().st_size > 0:
            sessions_df = pd.read_parquet(self.sessions_path)
            stats["total_sessions"] = len(sessions_df)

            # Recent sessions (last 7 days)
            cutoff_time = time.time() - (7 * 24 * 3600)
            recent_mask = sessions_df["start_time"] > cutoff_time
            stats["recent_sessions_7d"] = len(sessions_df[recent_mask])

        # Query statistics
        if self.queries_path.exists() and self.queries_path.stat().st_size > 0:
            queries_df = pd.read_parquet(self.queries_path)
            stats["total_queries"] = len(queries_df)

            successful_queries = len(queries_df[queries_df["success"]])
            stats["successful_queries"] = successful_queries
            stats["query_success_rate"] = (
                successful_queries / len(queries_df) if len(queries_df) > 0 else 0
            )

        # AI message statistics
        if self.ai_messages_path.exists() and self.ai_messages_path.stat().st_size > 0:
            ai_messages_df = pd.read_parquet(self.ai_messages_path)
            stats["total_ai_messages"] = len(ai_messages_df)

            successful_ai = len(ai_messages_df[ai_messages_df["success"]])
            stats["successful_ai_messages"] = successful_ai
            stats["ai_success_rate"] = (
                successful_ai / len(ai_messages_df) if len(ai_messages_df) > 0 else 0
            )

        return stats

    def cleanup_old_records(self, days_to_keep: int = 30) -> int:
        """
        Clean up old records.

        Args:
            days_to_keep: Number of days of history to retain

        Returns:
            Number of records deleted
        """
        cutoff_time = time.time() - (days_to_keep * 24 * 3600)
        deleted_count = 0

        # Clean up queries
        if self.queries_path.exists() and self.queries_path.stat().st_size > 0:
            queries_df = pd.read_parquet(self.queries_path)
            old_count = len(queries_df)
            queries_df = queries_df[queries_df["timestamp"] >= cutoff_time]

            if len(queries_df) < old_count:
                queries_df.to_parquet(self.queries_path, index=False)
                deleted_count += old_count - len(queries_df)

        # Clean up AI messages
        if self.ai_messages_path.exists() and self.ai_messages_path.stat().st_size > 0:
            ai_messages_df = pd.read_parquet(self.ai_messages_path)
            old_count = len(ai_messages_df)
            ai_messages_df = ai_messages_df[ai_messages_df["timestamp"] >= cutoff_time]

            if len(ai_messages_df) < old_count:
                ai_messages_df.to_parquet(self.ai_messages_path, index=False)
                deleted_count += old_count - len(ai_messages_df)

        # Clean up old sessions (only those that ended before cutoff)
        if self.sessions_path.exists() and self.sessions_path.stat().st_size > 0:
            sessions_df = pd.read_parquet(self.sessions_path)
            old_count = len(sessions_df)

            # Keep sessions that are still ongoing or ended after cutoff
            mask = (sessions_df["end_time"].isna()) | (
                sessions_df["end_time"] >= cutoff_time
            )
            sessions_df = sessions_df[mask]

            if len(sessions_df) < old_count:
                sessions_df.to_parquet(self.sessions_path, index=False)
                deleted_count += old_count - len(sessions_df)

        return deleted_count
