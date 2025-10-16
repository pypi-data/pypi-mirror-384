"""
DataContext module for parquetframe.

This module provides the core abstraction for managing different data sources
(parquet files, databases) in a unified way, enabling the LLM interface to work
seamlessly across different backends.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..exceptions import DataSourceError

if TYPE_CHECKING:
    from .database_context import DatabaseDataContext
    from .parquet_context import ParquetDataContext
logger = logging.getLogger(__name__)


class SourceType(Enum):
    """Enumeration of supported data source types."""

    PARQUET = "parquet"
    DATABASE = "database"


# Keep for backward compatibility
class DataContextError(DataSourceError):
    """Base exception for DataContext-related errors."""

    def __init__(
        self,
        message: str,
        cause: Exception = None,
        source_type: str = "unknown",
        source_location: str = "unknown",
    ):
        # Always use DataSourceError's standard formatting
        super().__init__(
            source_type=source_type,
            source_location=source_location,
            underlying_error=cause if cause else Exception(message),
        )


class DataContext(ABC):
    """
    Abstract base class for data source contexts.

    This class defines the interface that all data source implementations
    must follow, providing a consistent API for the CLI and LLM components.
    """

    def __init__(self, source_location: str, source_type: SourceType):
        """
        Initialize the DataContext.

        Args:
            source_location: Path to parquet directory or database connection URI
            source_type: Type of data source (parquet or database)
        """
        self.source_location = source_location
        self.source_type = source_type
        self._schema_cache: dict[str, Any] | None = None
        self._query_handler: Any | None = None
        self._is_initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if the context has been initialized."""
        return self._is_initialized

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the data context.

        This method should:
        - Establish connections
        - Discover available tables/files
        - Build the schema cache
        - Initialize the query handler
        """
        pass

    @abstractmethod
    def get_schema_as_text(self) -> str:
        """
        Get a standardized text representation of the schema.

        Returns:
            A string containing CREATE TABLE statements or equivalent
            schema definition that can be used by the LLM.
        """
        pass

    @abstractmethod
    def get_table_names(self) -> list[str]:
        """
        Get a list of all available table names.

        Returns:
            List of table names that can be queried.
        """
        pass

    @abstractmethod
    def get_table_schema(self, table_name: str) -> dict[str, Any]:
        """
        Get detailed schema information for a specific table.

        Args:
            table_name: Name of the table to describe

        Returns:
            Dictionary containing column names, types, and metadata
        """
        pass

    @abstractmethod
    async def execute(self, query: str) -> Any:
        """
        Execute a query against the data source.

        Args:
            query: SQL query or DataFrame operation to execute

        Returns:
            Query results (DataFrame, table, etc.)
        """
        pass

    @abstractmethod
    async def validate_query(self, query: str) -> bool:
        """
        Validate a query without executing it.

        Args:
            query: Query to validate

        Returns:
            True if query is valid, False otherwise
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close any open connections or resources."""
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class DataContextFactory:
    """
    Factory for creating DataContext instances.

    This factory uses dependency injection patterns to create the appropriate
    DataContext subclass based on the provided parameters, keeping the CLI
    logic clean and decoupled from specific implementations.
    """

    @staticmethod
    def create_from_path(path: str | Path) -> ParquetDataContext:
        """
        Create a ParquetDataContext for a directory of parquet files.

        Args:
            path: Path to directory containing parquet files

        Returns:
            Configured ParquetDataContext instance
        """
        from .parquet_context import ParquetDataContext

        # Validate path parameter
        if path is None or (isinstance(path, str) and not path.strip()):
            raise DataContextError(
                "Path cannot be empty or None",
                source_type="parquet",
                source_location=str(path) if path is not None else "<None>",
            )

        path_obj = Path(path).resolve()
        if not path_obj.exists():
            raise DataSourceError(
                source_type="parquet",
                source_location=str(path_obj),
                troubleshooting_steps=[
                    "Verify the path exists and is accessible",
                    "Check file permissions",
                    "Ensure the path is correctly formatted",
                ],
            )
        if not path_obj.is_dir():
            raise DataSourceError(
                source_type="parquet",
                source_location=str(path_obj),
                troubleshooting_steps=[
                    "Path must point to a directory, not a file",
                    "Use the parent directory containing parquet files",
                ],
            )

        logger.info(f"Creating ParquetDataContext for path: {path_obj}")
        return ParquetDataContext(str(path_obj))

    @staticmethod
    def create_from_db_uri(db_uri: str) -> DatabaseDataContext:
        """
        Create a DatabaseDataContext for a database connection.

        Args:
            db_uri: Database connection URI (e.g., postgresql://user:pass@host/db)

        Returns:
            Configured DatabaseDataContext instance
        """
        from .database_context import DatabaseDataContext

        if db_uri is None or not isinstance(db_uri, str) or not db_uri.strip():
            raise DataContextError(
                f"Failed to connect to database at '{db_uri or '<empty>'}'",
                source_type="database",
                source_location=str(db_uri) if db_uri is not None else "<empty>",
            )

        logger.info(f"Creating DatabaseDataContext for URI: {db_uri[:20]}...")
        return DatabaseDataContext(db_uri)

    @staticmethod
    def create_context(
        path: str | Path | None = None, db_uri: str | None = None
    ) -> DataContext:
        """
        Create a DataContext based on provided parameters.

        Args:
            path: Optional path to parquet directory
            db_uri: Optional database connection URI

        Returns:
            Appropriate DataContext subclass instance

        Raises:
            DataContextError: If both or neither parameters are provided
        """
        if path is not None and db_uri is not None:
            raise DataContextError("Cannot specify both path and db_uri")

        if path is None and db_uri is None:
            raise DataContextError("Must specify either path or db_uri")

        if path is not None:
            return DataContextFactory.create_from_path(path)
        else:
            return DataContextFactory.create_from_db_uri(db_uri)


# Importing here to avoid circular imports while making classes available at package level
def __getattr__(name: str):
    """Lazy import of DataContext implementations."""
    if name == "ParquetDataContext":
        from .parquet_context import ParquetDataContext

        return ParquetDataContext
    elif name == "DatabaseDataContext":
        from .database_context import DatabaseDataContext

        return DatabaseDataContext
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "DataContext",
    "DataContextFactory",
    "DataContextError",
    "SourceType",
    "ParquetDataContext",
    "DatabaseDataContext",
]
