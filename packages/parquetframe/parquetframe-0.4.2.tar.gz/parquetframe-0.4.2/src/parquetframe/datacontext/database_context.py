"""
DatabaseDataContext implementation for relational databases.

This module provides a DataContext implementation that can connect to various
relational databases using SQLAlchemy, introspect their schemas, and provide
a unified query interface.
"""

import logging
from typing import Any

from . import DataContext, DataContextError, SourceType

logger = logging.getLogger(__name__)

# Optional dependencies for database connectivity
try:
    from sqlalchemy import MetaData, create_engine, inspect, text
    from sqlalchemy.engine import Engine
    from sqlalchemy.engine.reflection import Inspector

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class DatabaseDataContext(DataContext):
    """
    DataContext implementation for relational databases.

    This class connects to databases via SQLAlchemy, introspects schemas,
    and provides a unified interface for executing SQL queries across
    different database systems (PostgreSQL, MySQL, SQLite, etc.).
    """

    def __init__(self, connection_uri: str):
        """
        Initialize DatabaseDataContext with a connection URI.

        Args:
            connection_uri: SQLAlchemy connection URI
                          (e.g., 'postgresql://user:pass@host/db')
        """
        super().__init__(connection_uri, SourceType.DATABASE)
        self.connection_uri = connection_uri
        self._engine: Engine | None = None
        self._inspector: Inspector | None = None
        self._metadata: MetaData | None = None
        self._table_schemas: dict[str, dict[str, Any]] = {}

        # Check dependencies
        if not SQLALCHEMY_AVAILABLE:
            raise DataContextError(
                "SQLAlchemy is required for database support. "
                "Install with: pip install parquetframe[db]"
            )

        if not PANDAS_AVAILABLE:
            raise DataContextError(
                "Pandas is required for database result handling. "
                "Install with: pip install pandas"
            )

    async def initialize(self) -> None:
        """
        Initialize the database data context.

        This method:
        1. Creates SQLAlchemy engine and tests connection
        2. Creates inspector for schema introspection
        3. Discovers available schemas and tables
        4. Caches table metadata
        """
        if self._is_initialized:
            return

        logger.info(f"Initializing DatabaseDataContext for URI: {self._masked_uri()}")

        try:
            # Step 1: Create engine and test connection
            self._engine = create_engine(self.connection_uri)

            # Test connection
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info("Database connection established successfully")

            # Step 2: Create inspector
            self._inspector = inspect(self._engine)

            # Step 3: Discover schemas and tables
            await self._discover_database_structure()

            # Step 4: Cache table schemas
            await self._cache_table_schemas()

            self._is_initialized = True
            logger.info(
                f"DatabaseDataContext initialized with {len(self._table_schemas)} tables"
            )

        except Exception as e:
            logger.error(f"Failed to initialize database context: {e}")
            raise DataContextError(f"Database initialization failed: {e}") from e

    def _masked_uri(self) -> str:
        """Return connection URI with password masked for logging."""
        try:
            from sqlalchemy.engine.url import make_url

            url = make_url(self.connection_uri)
            if url.password:
                # Replace password with asterisks
                url = url.set(password="***")
            return str(url)
        except Exception:
            # Fallback: mask everything after @ symbol if present
            if "@" in self.connection_uri:
                parts = self.connection_uri.split("@", 1)
                return f"{parts[0][:20]}...@{parts[1]}"
            else:
                return self.connection_uri[:30] + "..."

    async def _discover_database_structure(self) -> None:
        """
        Discover database schemas, tables, and views using Inspector.

        Uses SQLAlchemy's Inspector for lightweight schema discovery.
        """
        logger.info("Discovering database structure...")

        try:
            # Get available schemas
            schemas = self._inspector.get_schema_names()
            logger.debug(f"Found {len(schemas)} schemas: {schemas}")

            # For each schema, get tables
            all_tables = []

            # Get tables from default schema (None)
            default_tables = self._inspector.get_table_names()
            for table_name in default_tables:
                all_tables.append((None, table_name))

            # Get tables from named schemas
            for schema in schemas:
                try:
                    schema_tables = self._inspector.get_table_names(schema=schema)
                    for table_name in schema_tables:
                        all_tables.append((schema, table_name))
                except Exception as e:
                    logger.warning(f"Could not access schema '{schema}': {e}")
                    continue

            # Also get views
            try:
                default_views = self._inspector.get_view_names()
                for view_name in default_views:
                    all_tables.append((None, view_name))

                for schema in schemas:
                    try:
                        schema_views = self._inspector.get_view_names(schema=schema)
                        for view_name in schema_views:
                            all_tables.append((schema, view_name))
                    except Exception as e:
                        logger.debug(f"Could not get views from schema '{schema}': {e}")
            except Exception as e:
                logger.debug(f"Views not supported or accessible: {e}")

            # Store discovered tables
            self._discovered_tables = all_tables
            logger.info(f"Discovered {len(all_tables)} tables and views")

        except Exception as e:
            logger.error(f"Failed to discover database structure: {e}")
            raise DataContextError(f"Schema discovery failed: {e}") from e

    async def _cache_table_schemas(self) -> None:
        """
        Cache detailed schema information for all discovered tables.

        This uses Inspector to get column details for each table.
        """
        logger.info("Caching table schemas...")

        for schema, table_name in self._discovered_tables:
            try:
                # Get column information
                columns = self._inspector.get_columns(table_name, schema=schema)

                # Get primary key information
                try:
                    pk_constraint = self._inspector.get_pk_constraint(
                        table_name, schema=schema
                    )
                    primary_keys = pk_constraint.get("constrained_columns", [])
                except Exception:
                    primary_keys = []

                # Get foreign key information
                try:
                    fk_constraints = self._inspector.get_foreign_keys(
                        table_name, schema=schema
                    )
                except Exception:
                    fk_constraints = []

                # Get index information
                try:
                    indexes = self._inspector.get_indexes(table_name, schema=schema)
                except Exception:
                    indexes = []

                # Format table name (include schema if not default)
                full_table_name = f"{schema}.{table_name}" if schema else table_name

                # Store schema information
                self._table_schemas[full_table_name] = {
                    "table_name": table_name,
                    "schema": schema,
                    "full_name": full_table_name,
                    "columns": columns,
                    "primary_keys": primary_keys,
                    "foreign_keys": fk_constraints,
                    "indexes": indexes,
                }

                logger.debug(
                    f"Cached schema for {full_table_name}: {len(columns)} columns"
                )

            except Exception as e:
                logger.warning(f"Could not cache schema for {table_name}: {e}")
                continue

        logger.info(f"Cached schemas for {len(self._table_schemas)} tables")

    def get_schema_as_text(self) -> str:
        """
        Get schema as CREATE TABLE statements for LLM consumption.

        Returns:
            SQL CREATE TABLE statements for all tables
        """
        if not self._table_schemas:
            return "-- No schema available --"

        statements = []
        statements.append(f"-- Database: {self._masked_uri()}")
        statements.append(f"-- Total tables: {len(self._table_schemas)}")
        statements.append("")

        for table_info in self._table_schemas.values():
            statements.append(self._table_to_create_statement(table_info))
            statements.append("")

        return "\n".join(statements)

    def _table_to_create_statement(self, table_info: dict[str, Any]) -> str:
        """Convert table schema info to CREATE TABLE statement."""
        table_name = table_info["full_name"]
        columns = table_info["columns"]
        primary_keys = table_info["primary_keys"]

        # Build column definitions
        column_defs = []
        for col in columns:
            col_name = col["name"]
            col_type = self._sqlalchemy_type_to_sql_string(col["type"])
            nullable = "" if col["nullable"] else " NOT NULL"
            default = f" DEFAULT {col['default']}" if col.get("default") else ""

            column_defs.append(f"  {col_name} {col_type}{nullable}{default}")

        # Add primary key constraint if present
        if primary_keys:
            pk_cols = ", ".join(primary_keys)
            column_defs.append(f"  PRIMARY KEY ({pk_cols})")

        columns_str = ",\n".join(column_defs)

        return f"""CREATE TABLE {table_name} (
{columns_str}
);"""

    def _sqlalchemy_type_to_sql_string(self, sa_type) -> str:
        """Convert SQLAlchemy type to standard SQL type string."""
        type_str = str(sa_type).upper()

        # Common type mappings
        if "VARCHAR" in type_str or "TEXT" in type_str:
            return "VARCHAR"
        elif "INTEGER" in type_str or "INT" in type_str:
            return "INTEGER"
        elif "BIGINT" in type_str:
            return "BIGINT"
        elif "SMALLINT" in type_str:
            return "SMALLINT"
        elif "DECIMAL" in type_str or "NUMERIC" in type_str:
            return "DECIMAL"
        elif "REAL" in type_str or "FLOAT" in type_str:
            return "REAL"
        elif "DOUBLE" in type_str:
            return "DOUBLE"
        elif "BOOLEAN" in type_str or "BOOL" in type_str:
            return "BOOLEAN"
        elif "TIMESTAMP" in type_str:
            return "TIMESTAMP"
        elif "DATE" in type_str:
            return "DATE"
        elif "TIME" in type_str:
            return "TIME"
        else:
            return "VARCHAR"  # Default fallback

    def get_table_names(self) -> list[str]:
        """Get list of available table names."""
        return list(self._table_schemas.keys())

    def get_table_schema(self, table_name: str) -> dict[str, Any]:
        """Get detailed schema for a specific table."""
        if table_name not in self._table_schemas:
            # Try case-insensitive lookup
            table_name_lower = table_name.lower()
            matches = [
                name
                for name in self._table_schemas.keys()
                if name.lower() == table_name_lower
            ]
            if matches:
                table_name = matches[0]
            else:
                available = ", ".join(self._table_schemas.keys())
                raise DataContextError(
                    f"Table '{table_name}' not found. Available tables: {available}"
                )

        table_info = self._table_schemas[table_name].copy()

        # Add formatted column information
        formatted_columns = []
        for col in table_info["columns"]:
            formatted_col = {
                "name": col["name"],
                "type": str(col["type"]),
                "sql_type": self._sqlalchemy_type_to_sql_string(col["type"]),
                "nullable": col["nullable"],
                "default": col.get("default"),
                "primary_key": col["name"] in table_info["primary_keys"],
            }
            formatted_columns.append(formatted_col)

        table_info["formatted_columns"] = formatted_columns
        table_info["source_type"] = "database"
        table_info["source_location"] = self._masked_uri()

        return table_info

    async def execute(self, query: str) -> Any:
        """Execute SQL query and return results as pandas DataFrame."""
        if not self._is_initialized:
            await self.initialize()

        try:
            logger.debug(f"Executing query: {query[:100]}...")

            with self._engine.connect() as conn:
                result = pd.read_sql_query(text(query), conn)

            logger.debug(f"Query executed successfully, returned {len(result)} rows")
            return result

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise DataContextError(f"Query execution failed: {e}") from e

    async def validate_query(self, query: str) -> bool:
        """Validate SQL query without executing it."""
        if not self._is_initialized:
            await self.initialize()

        try:
            # Try to get query execution plan
            explain_query = f"EXPLAIN {query}"

            with self._engine.connect() as conn:
                conn.execute(text(explain_query))

            return True

        except Exception as e:
            logger.debug(f"Query validation failed: {e}")
            return False

    def close(self) -> None:
        """Close database connections and clean up resources."""
        if self._engine:
            try:
                self._engine.dispose()
            except Exception as e:
                logger.warning(f"Error disposing database engine: {e}")

        self._engine = None
        self._inspector = None
        self._metadata = None
        self._is_initialized = False
        logger.info("DatabaseDataContext closed")
