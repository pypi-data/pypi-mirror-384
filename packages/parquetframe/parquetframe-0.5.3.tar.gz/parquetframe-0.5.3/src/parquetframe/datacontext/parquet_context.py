"""
ParquetDataContext implementation for parquet file collections.

This module provides a DataContext implementation that can recursively discover
parquet files in a directory structure and present them as a queryable data lake
using DuckDB as the query engine.
"""

import logging
import warnings
from pathlib import Path
from typing import Any

from . import DataContext, DataContextError, SourceType

logger = logging.getLogger(__name__)

# Optional dependencies for parquet file handling
try:
    import pyarrow as pa
    import pyarrow.parquet as pq

    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False

try:
    import duckdb

    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False

try:
    import polars as pl

    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False


class ParquetDataContext(DataContext):
    """
    DataContext implementation for parquet file collections.

    This class recursively discovers parquet files in a directory,
    unifies their schemas, and provides a DuckDB-based query interface
    that treats the collection as a single virtual table.
    """

    def __init__(self, directory_path: str):
        """
        Initialize ParquetDataContext for a directory of parquet files.

        Args:
            directory_path: Path to directory containing parquet files
        """
        super().__init__(directory_path, SourceType.PARQUET)
        self.directory_path = Path(directory_path).resolve()
        self._discovered_files: list[Path] = []
        self._unified_schema: pa.Schema | None = None
        self._virtual_table_name = "parquet_data"
        self._engine_type = "duckdb"  # Default to DuckDB

        # Check dependencies
        if not PYARROW_AVAILABLE:
            raise DataContextError(
                "PyArrow is required for parquet support. "
                "Install with: pip install parquetframe[parquet]"
            )

    async def initialize(self) -> None:
        """
        Initialize the parquet data context.

        This method:
        1. Recursively discovers parquet files
        2. Analyzes and unifies schemas
        3. Initializes the query engine
        """
        if self._is_initialized:
            return

        logger.info(f"Initializing ParquetDataContext for: {self.directory_path}")

        # Step 1: Discover parquet files recursively
        await self._discover_parquet_files()

        if not self._discovered_files:
            raise DataContextError(f"No parquet files found in: {self.directory_path}")

        # Step 2: Unify schemas
        await self._unify_schemas()

        # Step 3: Initialize query engine
        await self._initialize_query_engine()

        self._is_initialized = True
        logger.info(
            f"ParquetDataContext initialized: {len(self._discovered_files)} files, "
            f"{len(self._unified_schema)} columns"
        )

    async def _discover_parquet_files(self) -> None:
        """
        Recursively discover parquet files using pathlib.

        Uses pathlib.Path.rglob() for efficient, cross-platform file discovery.
        """
        logger.info("Discovering parquet files recursively...")

        # Use pathlib's rglob for recursive discovery
        parquet_pattern = "**/*.parquet"
        discovered_paths = list(self.directory_path.rglob(parquet_pattern))

        # Filter to ensure we only have actual files
        self._discovered_files = [
            path
            for path in discovered_paths
            if path.is_file() and path.suffix.lower() == ".parquet"
        ]

        logger.info(f"Discovered {len(self._discovered_files)} parquet files")

        if logger.isEnabledFor(logging.DEBUG):
            for file_path in self._discovered_files[:10]:  # Log first 10 for debugging
                logger.debug(f"Found: {file_path}")
            if len(self._discovered_files) > 10:
                logger.debug(f"... and {len(self._discovered_files) - 10} more files")

    async def _unify_schemas(self) -> None:
        """
        Analyze and unify schemas from all discovered parquet files.

        This method:
        1. Reads schema from each file
        2. Identifies schema differences
        3. Creates a unified schema with promoted types
        4. Warns about any schema conflicts
        """
        logger.info("Unifying schemas across parquet files...")

        schemas = []
        schema_conflicts = []

        for file_path in self._discovered_files:
            try:
                # Read just the schema, not the data
                parquet_file = pq.ParquetFile(file_path)
                schema = parquet_file.schema_arrow
                schemas.append((file_path, schema))
            except Exception as e:
                logger.warning(f"Could not read schema from {file_path}: {e}")
                continue

        if not schemas:
            raise DataContextError("No valid parquet files with readable schemas found")

        # Start with the first schema as base
        base_file, base_schema = schemas[0]
        unified_fields = {field.name: field for field in base_schema}

        # Process additional schemas
        for file_path, schema in schemas[1:]:
            for field in schema:
                if field.name in unified_fields:
                    existing_field = unified_fields[field.name]
                    if existing_field.type != field.type:
                        # Try to promote types (e.g., int32 -> int64, int -> float)
                        promoted_type = self._promote_arrow_types(
                            existing_field.type, field.type
                        )
                        if promoted_type != existing_field.type:
                            unified_fields[field.name] = pa.field(
                                field.name, promoted_type
                            )
                            schema_conflicts.append(
                                f"Column '{field.name}': {existing_field.type} -> {promoted_type} "
                                f"(conflict between {base_file.name} and {file_path.name})"
                            )
                else:
                    # New column found
                    unified_fields[field.name] = field

        # Create unified schema
        self._unified_schema = pa.schema(list(unified_fields.values()))

        # Warn about schema conflicts
        if schema_conflicts:
            warnings.warn(
                "Schema conflicts detected and resolved:\n"
                + "\n".join(schema_conflicts),
                UserWarning,
                stacklevel=2,
            )

        logger.info(f"Unified schema created with {len(self._unified_schema)} columns")

    def _promote_arrow_types(
        self, type1: pa.DataType, type2: pa.DataType
    ) -> pa.DataType:
        """
        Promote Arrow data types to a compatible common type.

        Args:
            type1: First data type
            type2: Second data type

        Returns:
            Promoted data type that can accommodate both inputs
        """
        # If types are identical, no promotion needed
        if type1.equals(type2):
            return type1

        # Handle numeric type promotions
        if pa.types.is_integer(type1) and pa.types.is_integer(type2):
            # Promote to larger integer type
            if type1.bit_width < type2.bit_width:
                return type2
            else:
                return type1

        if pa.types.is_integer(type1) and pa.types.is_floating(type2):
            return type2  # Promote int to float

        if pa.types.is_floating(type1) and pa.types.is_integer(type2):
            return type1  # Promote int to float

        if pa.types.is_floating(type1) and pa.types.is_floating(type2):
            # Promote to higher precision float
            if type1.bit_width < type2.bit_width:
                return type2
            else:
                return type1

        # Handle string types
        if pa.types.is_string(type1) or pa.types.is_string(type2):
            return pa.string()  # Promote to string

        # Default: use string type for incompatible types
        logger.warning(f"Incompatible types {type1} and {type2}, promoting to string")
        return pa.string()

    async def _initialize_query_engine(self) -> None:
        """
        Initialize the query engine (DuckDB by default, Polars as fallback).
        """
        if DUCKDB_AVAILABLE:
            await self._initialize_duckdb()
        elif POLARS_AVAILABLE:
            await self._initialize_polars()
        else:
            raise DataContextError(
                "No query engine available. Install DuckDB or Polars:\n"
                "pip install duckdb  # Recommended\n"
                "pip install polars  # Alternative"
            )

    async def _initialize_duckdb(self) -> None:
        """Initialize DuckDB query engine."""
        logger.info("Initializing DuckDB query engine...")

        self._query_handler = duckdb.connect()
        self._engine_type = "duckdb"

        # Create a view that unions all parquet files
        file_paths = [str(path) for path in self._discovered_files]

        # DuckDB can read multiple parquet files as a single table
        files_str = ", ".join(f"'{path}'" for path in file_paths)
        create_view_sql = f"""
        CREATE VIEW {self._virtual_table_name} AS
        SELECT * FROM read_parquet([{files_str}], union_by_name=True)
        """

        try:
            self._query_handler.execute(create_view_sql)
            logger.info(
                f"Created DuckDB view '{self._virtual_table_name}' with {len(file_paths)} files"
            )
        except Exception as e:
            logger.error(f"Failed to create DuckDB view: {e}")
            raise DataContextError(f"Failed to initialize DuckDB view: {e}") from e

    async def _initialize_polars(self) -> None:
        """Initialize Polars query engine as fallback."""
        logger.info("Initializing Polars query engine...")

        try:
            # Create a lazy frame that scans all parquet files
            file_paths = [str(path) for path in self._discovered_files]

            if len(file_paths) == 1:
                self._query_handler = pl.scan_parquet(file_paths[0])
            else:
                # For multiple files, scan each and concatenate
                lazy_frames = [pl.scan_parquet(str(path)) for path in file_paths]
                self._query_handler = pl.concat(lazy_frames)

            self._engine_type = "polars"
            logger.info(f"Created Polars lazy frame with {len(file_paths)} files")
        except Exception as e:
            logger.error(f"Failed to create Polars lazy frame: {e}")
            raise DataContextError(f"Failed to initialize Polars: {e}") from e

    def get_schema_as_text(self) -> str:
        """
        Get schema as CREATE TABLE statement for LLM consumption.

        Returns:
            SQL CREATE TABLE statement representing the unified schema
        """
        if not self._unified_schema:
            return "-- No schema available --"

        # Convert Arrow schema to SQL CREATE TABLE statement
        columns = []
        for field in self._unified_schema:
            sql_type = self._arrow_to_sql_type(field.type)
            nullable = "NULL" if field.nullable else "NOT NULL"
            columns.append(f"  {field.name} {sql_type} {nullable}")

        columns_str = ",\n".join(columns)

        create_table_sql = f"""CREATE TABLE {self._virtual_table_name} (
{columns_str}
);

-- Data source: {len(self._discovered_files)} parquet files in {self.directory_path}
-- Total columns: {len(self._unified_schema)}"""

        return create_table_sql

    def _arrow_to_sql_type(self, arrow_type: pa.DataType) -> str:
        """Convert Arrow data type to SQL type string."""
        if pa.types.is_boolean(arrow_type):
            return "BOOLEAN"
        elif pa.types.is_integer(arrow_type):
            if arrow_type.bit_width <= 32:
                return "INTEGER"
            else:
                return "BIGINT"
        elif pa.types.is_floating(arrow_type):
            if arrow_type.bit_width <= 32:
                return "REAL"
            else:
                return "DOUBLE"
        elif pa.types.is_string(arrow_type) or pa.types.is_large_string(arrow_type):
            return "VARCHAR"
        elif pa.types.is_timestamp(arrow_type):
            return "TIMESTAMP"
        elif pa.types.is_date(arrow_type):
            return "DATE"
        elif pa.types.is_time(arrow_type):
            return "TIME"
        else:
            return "VARCHAR"  # Default fallback

    def get_table_names(self) -> list[str]:
        """Get list of available table names (just the virtual table)."""
        return [self._virtual_table_name]

    def get_table_schema(self, table_name: str) -> dict[str, Any]:
        """Get detailed schema for the virtual table."""
        if table_name != self._virtual_table_name:
            raise DataContextError(f"Table '{table_name}' not found")

        if not self._unified_schema:
            return {}

        schema_info = {
            "table_name": table_name,
            "source_type": "parquet_files",
            "source_location": str(self.directory_path),
            "file_count": len(self._discovered_files),
            "columns": [],
        }

        for field in self._unified_schema:
            column_info = {
                "name": field.name,
                "type": str(field.type),
                "nullable": field.nullable,
                "sql_type": self._arrow_to_sql_type(field.type),
            }
            schema_info["columns"].append(column_info)

        return schema_info

    async def execute(self, query: str) -> Any:
        """Execute SQL query using the configured engine."""
        if not self._is_initialized:
            await self.initialize()

        if self._engine_type == "duckdb":
            return self._query_handler.execute(query).fetchdf()
        elif self._engine_type == "polars":
            # For Polars, we'd need to translate SQL to Polars operations
            # This is complex, so for now we'll suggest using DuckDB
            raise DataContextError(
                "SQL execution with Polars engine not yet implemented. "
                "Please install DuckDB: pip install duckdb"
            )
        else:
            raise DataContextError(f"Unknown engine type: {self._engine_type}")

    async def validate_query(self, query: str) -> bool:
        """Validate SQL query without executing it."""
        if not self._is_initialized:
            await self.initialize()

        try:
            if self._engine_type == "duckdb":
                # DuckDB can explain queries to validate them
                explain_query = f"EXPLAIN {query}"
                self._query_handler.execute(explain_query)
                return True
        except Exception as e:
            logger.debug(f"Query validation failed: {e}")
            return False

        return False

    def close(self) -> None:
        """Close database connections and clean up resources."""
        if self._query_handler and self._engine_type == "duckdb":
            try:
                self._query_handler.close()
            except Exception as e:
                logger.warning(f"Error closing DuckDB connection: {e}")

        self._query_handler = None
        self._is_initialized = False
        logger.info("ParquetDataContext closed")
