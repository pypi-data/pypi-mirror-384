"""
SQL support for ParquetFrame using DuckDB.

This module provides SQL query capabilities on ParquetFrame objects,
supporting both pandas and Dask DataFrames with automatic JOIN operations.
"""

import warnings
from typing import Any, Optional, Union

try:
    import duckdb

    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False

import dask.dataframe as dd
import pandas as pd


def query_dataframes(
    main_df: Union[pd.DataFrame, dd.DataFrame],
    query: str,
    other_dfs: Optional[dict[str, Union[pd.DataFrame, dd.DataFrame]]] = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """
    Execute a SQL query on one or more DataFrames using DuckDB.

    Args:
        main_df: The main DataFrame, available as 'df' in the query.
        query: SQL query string to execute.
        other_dfs: Additional DataFrames for JOINs, keyed by table name.
        **kwargs: Additional arguments (reserved for future use).

    Returns:
        pandas DataFrame with query results.

    Raises:
        ImportError: If DuckDB is not installed.
        ValueError: If query execution fails.

    Examples:
        >>> df1 = pd.DataFrame({'a': [1, 2], 'b': ['x', 'y']})
        >>> df2 = pd.DataFrame({'a': [1, 2], 'c': ['p', 'q']})
        >>> result = query_dataframes(df1, "SELECT * FROM df JOIN other ON df.a = other.a", {'other': df2})
    """
    if not DUCKDB_AVAILABLE:
        raise ImportError(
            "DuckDB is required for SQL functionality. Install with: pip install parquetframe[sql]"
        )

    if other_dfs is None:
        other_dfs = {}

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

    try:
        # Register main DataFrame
        main_pandas = (
            main_df.compute() if isinstance(main_df, dd.DataFrame) else main_df
        )
        conn.register("df", main_pandas)

        # Register additional DataFrames
        for name, df in other_dfs.items():
            df_pandas = df.compute() if isinstance(df, dd.DataFrame) else df
            conn.register(name, df_pandas)

        # Execute query and return results
        result = conn.execute(query).fetchdf()
        return result

    except Exception as e:
        raise ValueError(f"SQL query execution failed: {e}") from e
    finally:
        conn.close()


class SQLError(Exception):
    """Custom exception for SQL-related errors."""

    pass


def validate_sql_query(query: str) -> bool:
    """
    Basic validation of SQL query syntax.

    Args:
        query: SQL query string to validate.

    Returns:
        True if query appears valid, False otherwise.

    Note:
        This is a basic validation. DuckDB will perform full validation during execution.
    """
    if not query or not query.strip():
        return False

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

    # Basic SELECT query check
    if not query_upper.startswith("SELECT") and not query_upper.startswith("WITH"):
        return False

    return True


def explain_query(
    main_df: Union[pd.DataFrame, dd.DataFrame],
    query: str,
    other_dfs: Optional[dict[str, Union[pd.DataFrame, dd.DataFrame]]] = None,
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
