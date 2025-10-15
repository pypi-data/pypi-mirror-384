"""
ParquetFrame: A universal data processing framework with multi-format support.

This package provides seamless switching between pandas and Dask DataFrames
based on file size thresholds, with automatic format detection for multiple
file types including CSV, JSON, Parquet, and ORC.

Supported formats:
    - CSV (.csv, .tsv) - Comma or tab-separated values
    - JSON (.json, .jsonl, .ndjson) - Regular or JSON Lines format
    - Parquet (.parquet, .pqt) - Columnar format (optimal performance)
    - ORC (.orc) - Optimized Row Columnar format

Examples:
    Multi-format usage:
        >>> import parquetframe as pqf
        >>> csv_df = pqf.read("sales.csv")  # Auto-detects CSV
        >>> json_df = pqf.read("events.jsonl")  # Auto-detects JSON Lines
        >>> parquet_df = pqf.read("data.parquet")  # Auto-detects Parquet
        >>> result = csv_df.groupby("region").sum().save("output.parquet")

    Manual control:
        >>> df = pqf.read("data.txt", format="csv")  # Force CSV format
        >>> df = pqf.read("large_data.csv", islazy=True)  # Force Dask
        >>> print(df.islazy)  # True
"""

from pathlib import Path

from .core import ParquetFrame

# Make ParquetFrame available as 'pf' for convenience
pf = ParquetFrame


# Convenience functions for more ergonomic usage
def read(
    file: str | Path,
    threshold_mb: float | None = None,
    islazy: bool | None = None,
    **kwargs,
) -> ParquetFrame:
    """
    Read a data file into a ParquetFrame with automatic format detection.

    This is a convenience function that wraps ParquetFrame.read().
    Supports CSV, JSON, Parquet, and ORC formats with automatic detection.

    Args:
        file: Path to the data file. Format auto-detected from extension.
        threshold_mb: Size threshold in MB for backend selection. Defaults to 100MB.
        islazy: Force backend selection (True=Dask, False=pandas, None=auto).
        **kwargs: Additional keyword arguments (format="csv|json|parquet|orc", etc.).

    Returns:
        ParquetFrame instance with loaded data.

    Examples:
        >>> import parquetframe as pqf
        >>> df = pqf.read("sales.csv")  # Auto-detect CSV format and backend
        >>> df = pqf.read("events.jsonl")  # Auto-detect JSON Lines format
        >>> df = pqf.read("data.parquet", threshold_mb=50)  # Custom threshold
        >>> df = pqf.read("data.txt", format="csv")  # Manual format override
    """
    return ParquetFrame.read(file, threshold_mb=threshold_mb, islazy=islazy, **kwargs)


def create_empty(islazy: bool = False) -> ParquetFrame:
    """
    Create an empty ParquetFrame.

    Args:
        islazy: Whether to initialize as Dask (True) or pandas (False).

    Returns:
        Empty ParquetFrame instance.

    Examples:
        >>> import parquetframe as pqf
        >>> empty_pf = pqf.create_empty()
        >>> empty_pf = pqf.create_empty(islazy=True)
    """
    return ParquetFrame(islazy=islazy)


__version__ = "0.4.2"
__all__ = ["ParquetFrame", "pf", "read", "create_empty"]
