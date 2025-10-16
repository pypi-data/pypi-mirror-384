"""
SQL support for ParquetFrame using DuckDB.

This module provides SQL query capabilities on ParquetFrame objects,
supporting both pandas and Dask DataFrames with automatic JOIN operations,
performance profiling, and query optimization.
"""

from __future__ import annotations

import hashlib
import time
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

try:
    import duckdb

    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False

import dask.dataframe as dd
import pandas as pd

if TYPE_CHECKING:
    from .core import ParquetFrame

# Global query result cache
_QUERY_CACHE: dict[str, tuple] = {}
_CACHE_ENABLED = True
_MAX_CACHE_SIZE = 100


@dataclass
class QueryContext:
    """
    Context object for SQL query execution with optimization hints.

    Attributes:
        format_hints: Format hints for file reading (e.g., {'df': 'csv'})
        predicate_pushdown: Enable predicate pushdown optimization
        projection_pushdown: Enable projection pushdown optimization
        enable_parallel: Enable parallel query execution
        memory_limit: Memory limit for query execution (e.g., '1GB')
        temp_directory: Directory for temporary files
        enable_statistics: Enable query statistics collection
        custom_pragmas: Additional DuckDB PRAGMA statements
    """

    format_hints: dict[str, str] = field(default_factory=dict)
    predicate_pushdown: bool = True
    projection_pushdown: bool = True
    enable_parallel: bool = True
    memory_limit: str | None = None
    temp_directory: str | Path | None = None
    enable_statistics: bool = False
    custom_pragmas: dict[str, Any] = field(default_factory=dict)

    def to_duckdb_pragmas(self) -> list[str]:
        """Convert context to DuckDB PRAGMA statements."""
        pragmas = []

        if not self.predicate_pushdown:
            pragmas.append("PRAGMA enable_optimizer=false")

        if not self.enable_parallel:
            pragmas.append("PRAGMA threads=1")

        if self.memory_limit:
            pragmas.append(f"PRAGMA memory_limit='{self.memory_limit}'")

        if self.temp_directory:
            pragmas.append(f"PRAGMA temp_directory='{self.temp_directory}'")

        if self.enable_statistics:
            pragmas.append("PRAGMA enable_profiling=true")
            pragmas.append("PRAGMA profiling_output='query_profiling.json'")

        # Add custom pragmas
        for pragma, value in self.custom_pragmas.items():
            if value is True:
                pragmas.append(f"PRAGMA {pragma}=true")
            elif value is False:
                pragmas.append(f"PRAGMA {pragma}=false")
            elif value is not None:
                pragmas.append(f"PRAGMA {pragma}='{value}'")

        return pragmas


@dataclass
class QueryResult:
    """
    Enhanced query result with execution metadata and profiling information.

    Attributes:
        data: The pandas DataFrame result
        execution_time: Query execution time in seconds
        row_count: Number of rows in the result
        column_count: Number of columns in the result
        query: The original SQL query
        from_cache: Whether the result came from cache
        memory_usage: Approximate memory usage in MB
        duckdb_profile: Optional DuckDB query profiling information
        query_plan: Optional query execution plan
    """

    data: pd.DataFrame
    execution_time: float
    row_count: int
    column_count: int
    query: str
    from_cache: bool = False
    memory_usage: float | None = None
    duckdb_profile: dict | None = None
    query_plan: str | None = None

    def __post_init__(self):
        """Calculate memory usage after initialization."""
        if self.memory_usage is None:
            try:
                # Estimate memory usage in MB
                self.memory_usage = self.data.memory_usage(deep=True).sum() / (
                    1024 * 1024
                )
            except Exception:
                self.memory_usage = 0.0

    # Convenience properties for easier access
    @property
    def rows(self) -> int:
        """Number of rows in the result."""
        return self.row_count

    @property
    def columns(self) -> int:
        """Number of columns in the result."""
        return self.column_count

    @property
    def cached(self) -> bool:
        """Whether the result came from cache."""
        return self.from_cache

    @property
    def dataframe(self) -> ParquetFrame:
        """The result data as a ParquetFrame."""
        from .core import ParquetFrame

        return ParquetFrame(self.data, islazy=False)

    @property
    def memory_usage_mb(self) -> float:
        """Memory usage in MB."""
        return self.memory_usage or 0.0

    def summary(self) -> str:
        """Get a summary of the query execution."""
        cache_info = " (from cache)" if self.from_cache else ""
        return (
            f"Query executed in {self.execution_time:.3f}s{cache_info}\n"
            f"Result: {self.row_count} rows × {self.column_count} columns\n"
            f"Memory usage: {self.memory_usage:.2f} MB"
        )


def _generate_cache_key(query: str, df_shapes: dict) -> str:
    """Generate a cache key for a query and DataFrame shapes."""
    # Include query and shapes of all DataFrames to ensure cache validity
    key_data = f"{query}_{str(sorted(df_shapes.items()))}"
    return hashlib.md5(key_data.encode()).hexdigest()


def _manage_cache_size():
    """Remove oldest cache entries if cache is too large."""
    global _QUERY_CACHE
    if len(_QUERY_CACHE) > _MAX_CACHE_SIZE:
        # Remove oldest entries (simple FIFO)
        keys_to_remove = list(_QUERY_CACHE.keys())[:-_MAX_CACHE_SIZE]
        for key in keys_to_remove:
            del _QUERY_CACHE[key]


def clear_query_cache():
    """Clear the SQL query result cache."""
    global _QUERY_CACHE
    _QUERY_CACHE.clear()


def set_cache_enabled(enabled: bool):
    """Enable or disable query result caching."""
    global _CACHE_ENABLED
    _CACHE_ENABLED = enabled


def get_cache_stats() -> dict:
    """Get cache statistics."""
    return {
        "enabled": _CACHE_ENABLED,
        "entries": len(_QUERY_CACHE),
        "max_size": _MAX_CACHE_SIZE,
    }


class SQLBuilder:
    """
    Fluent SQL query builder for ParquetFrame operations.

    Provides a chainable interface for building SQL queries in a more
    programmatic way than writing raw SQL strings.
    """

    def __init__(self, parent_frame: ParquetFrame):
        """Initialize the SQL builder with a parent ParquetFrame."""
        self._parent = parent_frame
        self._select_cols = ["*"]
        self._where_conditions = []
        self._group_by_cols = []
        self._having_conditions = []
        self._order_by_clauses = []
        self._limit_count = None
        self._joins = []
        self._profile = False
        self._use_cache = True
        self._context = None

    def select(self, *columns: str) -> SQLBuilder:
        """Set the columns to select.

        Args:
            *columns: Column names to select

        Returns:
            Self for method chaining

        Examples:
            >>> pf.select("name", "age")
            >>> pf.select("COUNT(*) as count", "AVG(salary) as avg_sal")
        """
        if columns:
            self._select_cols = list(columns)
        return self

    def where(self, condition: str) -> SQLBuilder:
        """Add a WHERE condition.

        Args:
            condition: SQL WHERE condition

        Returns:
            Self for method chaining

        Examples:
            >>> pf.select("*").where("age > 25")
            >>> pf.select("*").where("status = 'active'").where("salary > 50000")
        """
        self._where_conditions.append(condition)
        return self

    def group_by(self, *columns: str) -> SQLBuilder:
        """Add GROUP BY columns.

        Args:
            *columns: Column names to group by

        Returns:
            Self for method chaining

        Examples:
            >>> pf.select("category", "COUNT(*)").group_by("category")
        """
        self._group_by_cols.extend(columns)
        return self

    def having(self, condition: str) -> SQLBuilder:
        """Add a HAVING condition.

        Args:
            condition: SQL HAVING condition

        Returns:
            Self for method chaining

        Examples:
            >>> pf.select("category", "COUNT(*) as cnt").group_by("category").having("cnt > 10")
        """
        self._having_conditions.append(condition)
        return self

    def order_by(self, *columns: str) -> SQLBuilder:
        """Add ORDER BY columns.

        Args:
            *columns: Column names/expressions to order by. Can include direction.

        Returns:
            Self for method chaining

        Examples:
            >>> pf.select("*").order_by("name")
            >>> pf.select("*").order_by("salary DESC")  # Use single string with direction
            >>> pf.select("*").order_by("age DESC", "name")
        """
        # If two arguments and second looks like a direction, combine them
        if len(columns) == 2 and columns[1].upper() in ["ASC", "DESC"]:
            self._order_by_clauses.append(f"{columns[0]} {columns[1].upper()}")
        else:
            self._order_by_clauses.extend(columns)
        return self

    def limit(self, count: int) -> SQLBuilder:
        """Add a LIMIT clause.

        Args:
            count: Number of rows to limit to

        Returns:
            Self for method chaining

        Examples:
            >>> pf.select("*").order_by("salary", "DESC").limit(10)
        """
        self._limit_count = count
        return self

    def join(
        self,
        other_frame: ParquetFrame,
        condition: str,
        join_type: str = "JOIN",
        alias: str = "other",
    ) -> SQLBuilder:
        """Add a JOIN clause.

        Args:
            other_frame: ParquetFrame to join with
            condition: JOIN condition (ON clause)
            join_type: Type of join (JOIN, LEFT JOIN, RIGHT JOIN, etc.)
            alias: Alias for the joined table

        Returns:
            Self for method chaining

        Examples:
            >>> pf.select("df.name", "other.city").join(cities, "df.city_id = other.id")
        """
        self._joins.append(
            {
                "frame": other_frame,
                "condition": condition,
                "join_type": join_type,
                "alias": alias,
            }
        )
        return self

    def left_join(
        self, other_frame: ParquetFrame, condition: str, alias: str = "other"
    ) -> SQLBuilder:
        """Add a LEFT JOIN clause.

        Args:
            other_frame: ParquetFrame to join with
            condition: JOIN condition (ON clause)
            alias: Alias for the joined table

        Returns:
            Self for method chaining
        """
        return self.join(other_frame, condition, "LEFT", alias)

    def right_join(
        self, other_frame: ParquetFrame, condition: str, alias: str = "other"
    ) -> SQLBuilder:
        """Add a RIGHT JOIN clause.

        Args:
            other_frame: ParquetFrame to join with
            condition: JOIN condition (ON clause)
            alias: Alias for the joined table

        Returns:
            Self for method chaining
        """
        return self.join(other_frame, condition, "RIGHT", alias)

    def inner_join(
        self, other_frame: ParquetFrame, condition: str, alias: str = "other"
    ) -> SQLBuilder:
        """Add an INNER JOIN clause.

        Args:
            other_frame: ParquetFrame to join with
            condition: JOIN condition (ON clause)
            alias: Alias for the joined table

        Returns:
            Self for method chaining
        """
        return self.join(other_frame, condition, "INNER", alias)

    def full_join(
        self, other_frame: ParquetFrame, condition: str, alias: str = "other"
    ) -> SQLBuilder:
        """Add a FULL JOIN clause.

        Args:
            other_frame: ParquetFrame to join with
            condition: JOIN condition (ON clause)
            alias: Alias for the joined table

        Returns:
            Self for method chaining
        """
        return self.join(other_frame, condition, "FULL", alias)

    def profile(self, enabled: bool = True) -> SQLBuilder:
        """Enable query profiling.

        Args:
            enabled: Whether to enable profiling

        Returns:
            Self for method chaining
        """
        self._profile = enabled
        return self

    def cache(self, enabled: bool = True) -> SQLBuilder:
        """Control query caching.

        Args:
            enabled: Whether to enable caching

        Returns:
            Self for method chaining
        """
        self._use_cache = enabled
        return self

    def hint(self, **hints: Any) -> SQLBuilder:
        """Add optimization hints to the query.

        Args:
            **hints: Optimization hints (same as QueryContext parameters)

        Returns:
            Self for method chaining

        Examples:
            >>> pf.select("*").hint(memory_limit='1GB').execute()
            >>> pf.select("*").hint(enable_parallel=False, predicate_pushdown=True).execute()
        """
        if self._context is None:
            self._context = QueryContext(**hints)
        else:
            # Update existing context with new hints
            for key, value in hints.items():
                setattr(self._context, key, value)
        return self

    def build(self) -> str:
        """Build the SQL query string.

        Returns:
            Complete SQL query string
        """
        query_parts = []

        # SELECT clause
        query_parts.append(f"SELECT {', '.join(self._select_cols)}")

        # FROM clause
        query_parts.append("FROM df")

        # JOIN clauses
        for join in self._joins:
            join_type = join["join_type"].upper()
            if not join_type.endswith("JOIN"):
                join_type = f"{join_type} JOIN"
            query_parts.append(f"{join_type} {join['alias']} ON {join['condition']}")

        # WHERE clause
        if self._where_conditions:
            query_parts.append(f"WHERE {' AND '.join(self._where_conditions)}")

        # GROUP BY clause
        if self._group_by_cols:
            query_parts.append(f"GROUP BY {', '.join(self._group_by_cols)}")

        # HAVING clause
        if self._having_conditions:
            query_parts.append(f"HAVING {' AND '.join(self._having_conditions)}")

        # ORDER BY clause
        if self._order_by_clauses:
            query_parts.append(f"ORDER BY {', '.join(self._order_by_clauses)}")

        # LIMIT clause
        if self._limit_count is not None:
            query_parts.append(f"LIMIT {self._limit_count}")

        return " ".join(query_parts)

    def execute(self) -> ParquetFrame | QueryResult:
        """Execute the built SQL query.

        Returns:
            ParquetFrame with results, or QueryResult if profiling is enabled
        """
        query = self.build()

        # Prepare other frames for JOINs
        other_frames = {}
        for join in self._joins:
            other_frames[join["alias"]] = join["frame"]

        return self._parent.sql(
            query,
            profile=self._profile,
            use_cache=self._use_cache,
            context=self._context,
            **other_frames,
        )


def parameterize_query(query: str, **params: Any) -> str:
    """
    Simple parameterized query support using named parameters.

    Args:
        query: SQL query string with {param_name} placeholders
        **params: Named parameters to substitute

    Returns:
        Query string with parameters substituted

    Examples:
        >>> parameterize_query("SELECT * FROM df WHERE age > {min_age}", min_age=25)
        "SELECT * FROM df WHERE age > 25"
        >>> parameterize_query("SELECT * WHERE name = '{name}'", name="John")
        "SELECT * WHERE name = 'John'"
    """
    try:
        return query.format(**params)
    except KeyError as e:
        raise ValueError(f"Missing required parameter: {e.args[0]}") from e


def build_join_query(
    main_table: str = "df",
    select_cols: list[str] | None = None,
    joins: list[dict] | None = None,
    where_conditions: list[str] | None = None,
    group_by: list[str] | None = None,
    having_conditions: list[str] | None = None,
    order_by: list[str] | None = None,
    limit: int | None = None,
) -> str:
    """
    Build a SQL query with JOIN operations using a structured approach.

    Args:
        main_table: Name of the main table (default "df")
        select_cols: List of columns to select
        joins: List of join dictionaries with 'table', 'condition', 'type' keys
        where_conditions: List of WHERE conditions
        group_by: List of GROUP BY columns
        having_conditions: List of HAVING conditions
        order_by: List of ORDER BY clauses
        limit: LIMIT value

    Returns:
        Complete SQL query string

    Examples:
        >>> joins = [{'table': 'users', 'condition': 'df.user_id = users.id', 'type': 'LEFT'}]
        >>> build_join_query(select_cols=['df.name', 'users.email'], joins=joins)
        "SELECT df.name, users.email FROM df LEFT JOIN users ON df.user_id = users.id"
    """
    parts = []

    # SELECT
    select_clause = "*" if not select_cols else ", ".join(select_cols)
    parts.append(f"SELECT {select_clause}")

    # FROM
    parts.append(f"FROM {main_table}")

    # JOINs
    if joins:
        for join in joins:
            join_type = join.get("type", "INNER").upper()
            if not join_type.endswith("JOIN"):
                join_type = f"{join_type} JOIN"
            parts.append(f"{join_type} {join['table']} ON {join['condition']}")

    # WHERE
    if where_conditions:
        parts.append(f"WHERE {' AND '.join(where_conditions)}")

    # GROUP BY
    if group_by:
        parts.append(f"GROUP BY {', '.join(group_by)}")

    # HAVING
    if having_conditions:
        parts.append(f"HAVING {' AND '.join(having_conditions)}")

    # ORDER BY
    if order_by:
        parts.append(f"ORDER BY {', '.join(order_by)}")

    # LIMIT
    if limit is not None:
        parts.append(f"LIMIT {limit}")

    return " ".join(parts)


def query_dataframes_from_files(
    main_file: str | Path,
    query: str,
    other_files: dict[str, str | Path] | None = None,
    format_hints: dict[str, str] | None = None,
    profile: bool = False,
    use_cache: bool = True,
    threshold_mb: float = 100.0,
    **kwargs: Any,
) -> pd.DataFrame | QueryResult:
    """
    Execute a SQL query directly on files of various formats using DuckDB.

    This function reads files into DataFrames and then executes the SQL query,
    with intelligent backend selection (pandas vs Dask) based on file size.

    Args:
        main_file: Main file path, available as 'df' in the query
        query: SQL query string to execute
        other_files: Additional files for JOINs, keyed by table name
        format_hints: Optional format hints for ambiguous files (e.g., {'df': 'csv'})
        profile: If True, return QueryResult with execution metadata
        use_cache: If True, use cached results for identical queries
        threshold_mb: File size threshold for Dask vs pandas selection
        **kwargs: Additional arguments passed to file readers

    Returns:
        pandas DataFrame with query results, or QueryResult if profile=True

    Raises:
        ImportError: If DuckDB is not installed
        FileNotFoundError: If any specified file is not found
        ValueError: If query execution fails

    Examples:
        >>> # Query CSV files directly
        >>> result = query_dataframes_from_files(
        ...     "sales.csv",
        ...     "SELECT * FROM df WHERE amount > 100"
        ... )
        >>>
        >>> # Join different format files
        >>> result = query_dataframes_from_files(
        ...     "sales.csv",
        ...     "SELECT * FROM df JOIN customers ON df.customer_id = customers.id",
        ...     other_files={'customers': 'customers.json'}
        ... )
    """
    from .core import ParquetFrame

    if other_files is None:
        other_files = {}
    if format_hints is None:
        format_hints = {}

    # Read main file
    main_format = format_hints.get("df")
    main_pf = ParquetFrame.read(
        main_file, format=main_format, threshold_mb=threshold_mb, **kwargs
    )

    # Read other files
    other_pfs = {}
    for name, file_path in other_files.items():
        format_hint = format_hints.get(name)
        other_pfs[name] = ParquetFrame.read(
            file_path, format=format_hint, threshold_mb=threshold_mb, **kwargs
        )

    # Execute query using existing dataframe method
    result = main_pf.sql(query, profile=profile, use_cache=use_cache, **other_pfs)

    # If not profiling and result is ParquetFrame, return the underlying DataFrame
    if not profile and hasattr(result, "_df"):
        return result._df

    return result


def query_dataframes(
    main_df: pd.DataFrame | dd.DataFrame,
    query: str,
    other_dfs: dict[str, pd.DataFrame | dd.DataFrame] | None = None,
    profile: bool = False,
    use_cache: bool = True,
    context: QueryContext | None = None,
    **kwargs: Any,
) -> pd.DataFrame | QueryResult:
    """
    Execute a SQL query on one or more DataFrames using DuckDB with profiling and caching.

    Args:
        main_df: The main DataFrame, available as 'df' in the query.
        query: SQL query string to execute.
        other_dfs: Additional DataFrames for JOINs, keyed by table name.
        profile: If True, return QueryResult with execution metadata.
        use_cache: If True, use cached results for identical queries.
        context: Optional QueryContext with optimization hints and settings.
        **kwargs: Additional arguments (reserved for future use).

    Returns:
        pandas DataFrame with query results, or QueryResult if profile=True.

    Raises:
        ImportError: If DuckDB is not installed.
        ValueError: If query execution fails.

    Examples:
        >>> df1 = pd.DataFrame({'a': [1, 2], 'b': ['x', 'y']})
        >>> df2 = pd.DataFrame({'a': [1, 2], 'c': ['p', 'q']})
        >>> result = query_dataframes(df1, "SELECT * FROM df JOIN other ON df.a = other.a", {'other': df2})
        >>>
        >>> # With profiling
        >>> result = query_dataframes(df1, "SELECT COUNT(*) FROM df", profile=True)
        >>> print(result.summary())  # Shows execution time and metadata
        >>>
        >>> # With optimization hints
        >>> ctx = QueryContext(memory_limit='1GB', enable_parallel=False)
        >>> result = query_dataframes(df1, query, context=ctx)
    """
    if not DUCKDB_AVAILABLE:
        raise ImportError(
            "DuckDB is required for SQL functionality. Install with: pip install parquetframe[sql]"
        )

    if other_dfs is None:
        other_dfs = {}

    # Generate cache key if caching is enabled
    cache_key = None
    if use_cache and _CACHE_ENABLED:
        df_shapes = {"df": main_df.shape}
        df_shapes.update({name: df.shape for name, df in other_dfs.items()})
        cache_key = _generate_cache_key(query, df_shapes)

        # Check cache
        if cache_key in _QUERY_CACHE:
            cached_data = _QUERY_CACHE[cache_key]
            if len(cached_data) == 2:
                # Old cache format (data, time)
                cached_result, cached_time = cached_data
                cached_profile = None
                cached_plan = None
            else:
                # New cache format (data, time, profile, plan)
                cached_result, cached_time, cached_profile, cached_plan = cached_data

            if profile:
                return QueryResult(
                    data=cached_result.copy(),
                    execution_time=cached_time,
                    row_count=len(cached_result),
                    column_count=len(cached_result.columns),
                    query=query,
                    from_cache=True,
                    duckdb_profile=cached_profile,
                    query_plan=cached_plan,
                )
            else:
                return cached_result.copy()

    # Start timing
    start_time = time.time()

    # Warn about Dask DataFrame computation
    has_dask = isinstance(main_df, dd.DataFrame) or any(
        isinstance(df, dd.DataFrame) for df in other_dfs.values()
    )
    if has_dask:
        warnings.warn(
            "SQL queries on Dask DataFrames will trigger computation and convert to pandas. "
            "This may consume significant memory for large datasets.",
            UserWarning,
            stacklevel=3,
        )

    # Create DuckDB connection
    conn = duckdb.connect(database=":memory:")

    # Apply optimization context if provided
    if context is None:
        context = QueryContext()

    try:
        # Apply DuckDB PRAGMAs from context
        for pragma in context.to_duckdb_pragmas():
            try:
                conn.execute(pragma)
            except Exception as e:
                warnings.warn(
                    f"Failed to apply optimization hint '{pragma}': {e}",
                    UserWarning,
                    stacklevel=2,
                )

        # Enable profiling if requested
        duckdb_profile = None
        query_plan = None
        if profile:
            try:
                conn.execute("PRAGMA enable_profiling=true")
                conn.execute("PRAGMA profiling_mode='detailed'")
            except Exception:
                # Profiling not supported in some DuckDB versions
                pass

        # Register main DataFrame
        main_pandas = (
            main_df.compute() if isinstance(main_df, dd.DataFrame) else main_df
        )
        conn.register("df", main_pandas)

        # Register additional DataFrames
        for name, df in other_dfs.items():
            df_pandas = df.compute() if isinstance(df, dd.DataFrame) else df
            conn.register(name, df_pandas)

        # Execute query and measure time
        result = conn.execute(query).fetchdf()
        execution_time = time.time() - start_time

        # Capture profiling information if enabled
        if profile:
            try:
                # Get query plan
                explain_result = conn.execute(f"EXPLAIN {query}").fetchall()
                query_plan = "\n".join(str(row[0]) for row in explain_result)
            except Exception:
                query_plan = None

            try:
                # Get profiling information
                profile_result = conn.execute("PRAGMA profile_info").fetchall()
                if profile_result:
                    duckdb_profile = {
                        "profile_info": [
                            dict(zip(["query", "time"], row, strict=False))
                            for row in profile_result
                        ]
                    }
            except Exception:
                duckdb_profile = None

        # Cache the result if caching is enabled
        if cache_key and _CACHE_ENABLED:
            cache_data = (result.copy(), execution_time)
            if profile:
                cache_data = (result.copy(), execution_time, duckdb_profile, query_plan)
            _QUERY_CACHE[cache_key] = cache_data
            _manage_cache_size()

        # Return result with profiling info if requested
        if profile:
            return QueryResult(
                data=result,
                execution_time=execution_time,
                row_count=len(result),
                column_count=len(result.columns),
                query=query,
                from_cache=False,
                duckdb_profile=duckdb_profile,
                query_plan=query_plan,
            )
        else:
            return result

    except Exception as e:
        # Enhanced error handling with query context
        error_msg = f"SQL query execution failed: {str(e)}"

        # Add query fragment for debugging
        if query and len(query) < 200:
            error_msg += f"\n\nQuery: {query}"
        elif query:
            error_msg += f"\n\nQuery (first 200 chars): {query[:200]}..."

        # Add suggestions based on error type
        error_str = str(e).lower()
        if "column" in error_str and "does not exist" in error_str:
            error_msg += "\n\nSuggestion: Check column names in your query. Available columns can be viewed with df.columns"
        elif "table" in error_str and (
            "does not exist" in error_str or "not found" in error_str
        ):
            error_msg += "\n\nSuggestion: Make sure you're using 'df' for the main DataFrame and correct aliases for JOINs"
        elif "syntax error" in error_str:
            error_msg += "\n\nSuggestion: Check SQL syntax. Common issues: missing commas, unmatched quotes, incorrect keywords"
        elif "aggregate" in error_str or "group by" in error_str:
            error_msg += "\n\nSuggestion: When using aggregation functions, ensure all non-aggregated columns are in GROUP BY"

        raise ValueError(error_msg) from e
    finally:
        conn.close()


class SQLError(Exception):
    """Custom exception for SQL-related errors."""

    pass


def validate_sql_query(
    query: str, df_columns: list[str] | None = None
) -> tuple[bool, list[str]]:
    """
    Enhanced validation of SQL query syntax and column references.

    Args:
        query: SQL query string to validate.
        df_columns: Optional list of available DataFrame columns for validation.

    Returns:
        Tuple of (is_valid, list_of_warnings)

    Note:
        This is a basic validation. DuckDB will perform full validation during execution.
    """
    warnings_list = []

    if not query or not query.strip():
        return False, ["Query is empty"]

    query_upper = query.strip().upper()

    # Check for potentially dangerous operations (basic safety)
    dangerous_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE"]
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            warnings.warn(
                f"Query contains potentially destructive keyword '{keyword}'. "
                "This will be executed on in-memory data only.",
                UserWarning,
                stacklevel=2,
            )
            warnings_list.append(f"Contains potentially destructive keyword: {keyword}")

    # Check for query type - allow basic SQL commands but flag dangerous ones
    has_dangerous_keywords = any(
        keyword in query_upper
        for keyword in ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE"]
    )

    # Basic SELECT/WITH query check - but allow dangerous queries to be considered "valid" with warnings
    if (
        not query_upper.startswith("SELECT")
        and not query_upper.startswith("WITH")
        and not has_dangerous_keywords
    ):
        return False, ["Query must start with SELECT or WITH"]

    # For dangerous queries, mark as invalid but include the warning
    if has_dangerous_keywords:
        # We already added the warning above, so just mark as invalid
        return False, warnings_list

    # Basic syntax checks
    if query_upper.count("(") != query_upper.count(")"):
        warnings_list.append("Unmatched parentheses detected")

    # Check for common syntax issues
    if "SELECT *" in query_upper and "GROUP BY" in query_upper:
        warnings_list.append("Using SELECT * with GROUP BY may cause issues")

    # Column validation if DataFrame columns provided
    if df_columns:
        # Simple column name extraction (basic - could be improved with proper SQL parsing)
        # Look for patterns like "column_name" or "df.column_name"
        import re

        # Find potential column references
        column_pattern = r"\b(?:df\.)?([a-zA-Z_][a-zA-Z0-9_]*)\b"
        potential_columns = re.findall(column_pattern, query)

        # Filter out SQL keywords and common functions
        sql_keywords = {
            "SELECT",
            "FROM",
            "WHERE",
            "GROUP",
            "BY",
            "ORDER",
            "HAVING",
            "JOIN",
            "INNER",
            "LEFT",
            "RIGHT",
            "FULL",
            "ON",
            "AS",
            "AND",
            "OR",
            "NOT",
            "NULL",
            "IS",
            "IN",
            "LIKE",
            "COUNT",
            "SUM",
            "AVG",
            "MIN",
            "MAX",
            "CASE",
            "WHEN",
            "THEN",
            "ELSE",
            "END",
            "DISTINCT",
            "DF",
            "OTHER",  # Common table aliases
        }

        unknown_columns = []
        for col in set(potential_columns):
            if col.upper() not in sql_keywords and col not in df_columns:
                unknown_columns.append(col)

        if unknown_columns:
            warnings_list.append(
                f"Potential unknown columns: {', '.join(unknown_columns)}"
            )

    return (
        len(warnings_list) == 0
        or all("unknown columns" not in w.lower() for w in warnings_list),
        warnings_list,
    )


def explain_query(
    main_df: pd.DataFrame | dd.DataFrame,
    query: str,
    other_dfs: dict[str, pd.DataFrame | dd.DataFrame] | None = None,
) -> str:
    """
    Get the execution plan for a SQL query without executing it.

    Args:
        main_df: The main DataFrame.
        query: SQL query string.
        other_dfs: Additional DataFrames for JOINs.

    Returns:
        String representation of the query execution plan.
    """
    if not DUCKDB_AVAILABLE:
        raise ImportError("DuckDB is required for SQL functionality.")

    if other_dfs is None:
        other_dfs = {}

    conn = duckdb.connect(database=":memory:")

    try:
        # Register DataFrames (use small samples for explain)
        main_sample = main_df.head(1)
        if isinstance(main_sample, dd.DataFrame):
            main_sample = main_sample.compute()
        conn.register("df", main_sample)

        for name, df in other_dfs.items():
            df_sample = df.head(1)
            if isinstance(df_sample, dd.DataFrame):
                df_sample = df_sample.compute()
            conn.register(name, df_sample)

        # Get execution plan
        explain_query = f"EXPLAIN {query}"
        result = conn.execute(explain_query).fetchall()

        return "\n".join(str(row[0]) for row in result)

    except Exception as e:
        raise SQLError(f"Failed to explain query: {e}") from e
    finally:
        conn.close()
