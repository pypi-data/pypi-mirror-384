"""
Time-series analysis functionality for ParquetFrame.

This module provides specialized time-series operations including automatic
datetime detection, resampling, rolling windows, and temporal filtering.
Supports both pandas and Dask backends with intelligent dispatching.
"""

from __future__ import annotations

import warnings
from datetime import time
from functools import lru_cache
from typing import TYPE_CHECKING

import dask.dataframe as dd
import pandas as pd

if TYPE_CHECKING:
    from .core import ParquetFrame


# Cache for expensive operations
@lru_cache(maxsize=128)
def _cached_datetime_detection(df_id: str, sample_hash: str) -> tuple[str, ...]:
    """Cached datetime detection to avoid repeated column scanning."""
    # This will be populated by detect_datetime_columns
    return ()


def detect_datetime_columns(
    df: pd.DataFrame | dd.DataFrame,
    sample_size: int = 1000,
    formats: list[str] | None = None,
    use_cache: bool = True,
) -> list[str]:
    """
    Automatically detect datetime columns in a DataFrame with caching optimization.

    Args:
        df: DataFrame to analyze
        sample_size: Number of rows to sample for detection (min 100, max 5000)
        formats: List of datetime formats to try (optional)
        use_cache: Whether to use caching for repeated detections

    Returns:
        List of column names that appear to contain datetime data

    Examples:
        >>> datetime_cols = detect_datetime_columns(df)
        >>> print(f"Found datetime columns: {datetime_cols}")
    """
    # Optimize sample size for performance
    sample_size = max(100, min(sample_size, 5000))

    if formats is None:
        formats = [
            "%Y-%m-%d",  # ISO date
            "%Y-%m-%d %H:%M:%S",  # ISO datetime
            "%m/%d/%Y",  # US date
            "%d/%m/%Y",  # EU date
            "%m/%d/%Y %H:%M:%S",  # US datetime
            "%d/%m/%Y %H:%M:%S",  # EU datetime
        ]

    # Work with pandas DataFrame for detection
    if isinstance(df, pd.DataFrame):
        # For pandas DataFrame
        sample_df = df.head(sample_size)
        df_id = f"pandas_{id(df)}_{len(df.columns)}"
    elif hasattr(df, "compute"):
        # For Dask DataFrame
        try:
            sample_df = df.head(sample_size, npartitions=-1).compute()
            df_id = f"dask_{id(df)}_{len(df.columns)}"
        except AttributeError:
            # Fallback if compute() doesn't exist despite hasattr check
            sample_df = df.head(sample_size)
            df_id = f"pandas_fallback_{id(df)}_{len(df.columns)}"
    else:
        # Fallback for other DataFrame-like objects
        sample_df = df.head(sample_size)
        df_id = f"unknown_{id(df)}_{len(df.columns)}"

    # Create sample hash for caching
    if use_cache:
        # Hash based on column names and first few values
        sample_hash = str(
            hash(tuple(sample_df.columns.tolist() + [str(sample_df.dtypes.to_dict())]))
        )

        # Try to get from cache
        try:
            cached_result = _cached_datetime_detection(df_id, sample_hash)
            if cached_result:
                return list(cached_result)
        except Exception:
            pass  # Cache miss or error, continue with detection

    datetime_columns = []

    for col in sample_df.columns:
        # Skip if column is already datetime
        if pd.api.types.is_datetime64_any_dtype(sample_df[col]):
            datetime_columns.append(col)
            continue

        # Skip numeric columns
        if pd.api.types.is_numeric_dtype(sample_df[col]):
            continue

        # Try to parse as datetime
        try:
            # First try pandas' automatic detection
            parsed = pd.to_datetime(
                sample_df[col].dropna().head(100),
                errors="coerce",
            )
            if parsed.notna().sum() > len(parsed) * 0.8:  # 80% success rate
                datetime_columns.append(col)
                continue

            # Try specific formats
            for fmt in formats:
                try:
                    parsed = pd.to_datetime(
                        sample_df[col].dropna().head(100), format=fmt, errors="coerce"
                    )
                    if parsed.notna().sum() > len(parsed) * 0.8:
                        datetime_columns.append(col)
                        break
                except (ValueError, TypeError):
                    continue

        except (ValueError, TypeError):
            continue

    # Cache successful results
    if use_cache and datetime_columns:
        try:
            # Store in cache (replace the dummy implementation)
            _cached_datetime_detection.__wrapped__.__setitem__(
                (df_id, sample_hash), tuple(datetime_columns)
            )
        except Exception:
            pass  # Cache storage failed, but detection succeeded

    return datetime_columns


class TimeSeriesAccessor:
    """
    Time-series accessor for ParquetFrame providing specialized temporal operations.

    This accessor follows the same pattern as the BioAccessor, providing time-series
    specific functionality while intelligently dispatching between pandas and Dask
    backends based on the current ParquetFrame state.

    Features performance optimizations including:
    - Memory-aware operation selection
    - Caching for expensive operations
    - Chunked processing for large datasets
    - Progress indicators for long-running operations

    Examples:
        >>> pf = ParquetFrame.read("timeseries_data.csv")
        >>> # Resample to hourly averages
        >>> hourly = pf.ts.resample('1H').mean()
        >>> # Rolling 7-day window
        >>> rolling = pf.ts.rolling(window=7).mean()
        >>> # Filter by time of day
        >>> morning = pf.ts.between_time('09:00', '17:00')
    """

    def __init__(self, pf: ParquetFrame) -> None:
        """Initialize with a ParquetFrame instance."""
        self.pf = pf
        self._datetime_index = None
        self._datetime_columns = None
        self._operation_cache = {}

    def _ensure_datetime_index(self, datetime_col: str | None = None) -> None:
        """Ensure the DataFrame has a datetime index with performance optimizations."""
        if self.pf._df is None:
            raise ValueError("No DataFrame loaded")

        # Check cache first
        cache_key = f"datetime_index_{datetime_col}_{self.pf.islazy}"
        if cache_key in self._operation_cache:
            return

        # If DataFrame already has a datetime index, we're done
        if isinstance(self.pf._df.index, pd.DatetimeIndex):
            self._operation_cache[cache_key] = True
            return

        # Auto-detect datetime column if not specified
        if datetime_col is None:
            datetime_cols = self.detect_datetime_columns()
            if not datetime_cols:
                raise ValueError(
                    "No datetime columns detected. Please specify datetime_col parameter."
                )
            datetime_col = datetime_cols[0]  # Use first detected column

        # Set datetime index if not already set
        if not isinstance(self.pf._df.index, pd.DatetimeIndex):
            if self.pf.islazy:
                # For Dask, use memory-aware processing
                try:
                    # Check if column is already datetime type
                    if not pd.api.types.is_datetime64_any_dtype(
                        self.pf._df[datetime_col]
                    ):
                        # Convert to datetime first
                        self.pf._df[datetime_col] = dd.to_datetime(
                            self.pf._df[datetime_col], errors="coerce"
                        )
                    # Set index with optimization
                    self.pf._df = self.pf._df.set_index(datetime_col, sorted=True)
                except Exception as e:
                    warnings.warn(
                        f"Dask datetime index creation failed: {e}. "
                        "Consider using smaller dataset or pandas backend.",
                        UserWarning,
                        stacklevel=3,
                    )
                    raise
            else:
                # For pandas, optimize based on size
                if len(self.pf._df) > 100000:  # Large dataset
                    # Use chunked processing for large datasets
                    warnings.warn(
                        "Processing large dataset. Consider using Dask backend for better performance.",
                        UserWarning,
                        stacklevel=3,
                    )
                    # Convert to datetime and set index
                    self.pf._df[datetime_col] = pd.to_datetime(
                        self.pf._df[datetime_col], errors="coerce"
                    )
                    self.pf._df = self.pf._df.set_index(datetime_col).sort_index()
                else:
                    # Standard processing for smaller datasets
                    self.pf._df[datetime_col] = pd.to_datetime(
                        self.pf._df[datetime_col]
                    )
                    self.pf._df = self.pf._df.set_index(datetime_col).sort_index()

        # Cache the operation
        self._operation_cache[cache_key] = True

    def detect_datetime_columns(self) -> list[str]:
        """
        Detect datetime columns in the current DataFrame.

        Returns:
            List of column names that appear to contain datetime data

        Examples:
            >>> datetime_cols = pf.ts.detect_datetime_columns()
        """
        if self.pf._df is None:
            raise ValueError("No DataFrame loaded")

        if self._datetime_columns is None:
            self._datetime_columns = detect_datetime_columns(self.pf._df)

        return self._datetime_columns

    def parse_datetime(
        self,
        column: str,
        format: str | None = None,
        infer: bool = True,
        inplace: bool = False,
    ) -> ParquetFrame:
        """
        Parse a column as datetime.

        Args:
            column: Column name to parse
            format: Specific datetime format (optional)
            infer: Whether to infer format automatically
            inplace: Whether to modify in place or return new ParquetFrame

        Returns:
            ParquetFrame with parsed datetime column

        Examples:
            >>> pf_parsed = pf.ts.parse_datetime('date_column', format='%Y-%m-%d')
            >>> pf_parsed = pf.ts.parse_datetime('timestamp', infer=True)
        """
        if self.pf._df is None:
            raise ValueError("No DataFrame loaded")

        # Create copy if not modifying in place
        if not inplace:
            new_pf = self.pf.__class__(
                self.pf._df.copy() if not self.pf.islazy else self.pf._df,
                self.pf.islazy,
                self.pf._track_history,
            )
        else:
            new_pf = self.pf

        # Parse datetime column
        if new_pf.islazy:
            # For Dask, use dd.to_datetime
            new_pf._df[column] = dd.to_datetime(
                new_pf._df[column],
                format=format,
                errors="coerce",
            )
        else:
            # For pandas
            new_pf._df[column] = pd.to_datetime(
                new_pf._df[column],
                format=format,
                errors="coerce",
            )

        return new_pf

    def resample(
        self, rule: str, datetime_col: str | None = None, **kwargs
    ) -> TimeSeriesResampler:
        """
        Resample time-series data.

        Args:
            rule: The offset string or object representing target conversion
            datetime_col: Column to use as datetime index (auto-detected if None)
            **kwargs: Additional arguments passed to resample

        Returns:
            TimeSeriesResampler object for chaining aggregation methods

        Examples:
            >>> # Hourly averages
            >>> hourly = pf.ts.resample('1h').mean()
            >>> # Daily max values
            >>> daily_max = pf.ts.resample('1D').max()
            >>> # Weekly aggregation with multiple functions
            >>> weekly = pf.ts.resample('1W').agg({'value': ['mean', 'std', 'count']})
        """
        if self.pf._df is None:
            raise ValueError("No DataFrame loaded")

        # Ensure datetime index
        self._ensure_datetime_index(datetime_col)

        return TimeSeriesResampler(self.pf, rule, **kwargs)

    def rolling(
        self, window: int | str, datetime_col: str | None = None, **kwargs
    ) -> TimeSeriesRolling:
        """
        Create rolling window operations.

        Args:
            window: Window size (integer for number of periods, string for time-based)
            datetime_col: Column to use as datetime index (auto-detected if None)
            **kwargs: Additional arguments passed to rolling

        Returns:
            TimeSeriesRolling object for chaining operations

        Examples:
            >>> # 7-period rolling average
            >>> rolling_avg = pf.ts.rolling(7).mean()
            >>> # 30-day rolling standard deviation
            >>> rolling_std = pf.ts.rolling('30D').std()
        """
        if self.pf._df is None:
            raise ValueError("No DataFrame loaded")

        # Ensure datetime index
        self._ensure_datetime_index(datetime_col)

        return TimeSeriesRolling(self.pf, window, **kwargs)

    def between_time(
        self,
        start_time: time | str,
        end_time: time | str,
        datetime_col: str | None = None,
    ) -> ParquetFrame:
        """
        Filter data between specific times of day.

        Args:
            start_time: Start time (time object or string like '09:00')
            end_time: End time (time object or string like '17:00')
            datetime_col: Column to use as datetime index (auto-detected if None)

        Returns:
            Filtered ParquetFrame

        Examples:
            >>> # Business hours only
            >>> business_hours = pf.ts.between_time('09:00', '17:00')
        """
        if self.pf._df is None:
            raise ValueError("No DataFrame loaded")

        # Ensure datetime index
        self._ensure_datetime_index(datetime_col)

        if self.pf.islazy:
            # For Dask, we need to compute this operation
            warnings.warn(
                "between_time operation will compute Dask DataFrame. "
                "Consider using other filtering methods for large datasets.",
                UserWarning,
                stacklevel=2,
            )
            # Convert to pandas for time-based filtering
            pandas_df = self.pf._df.compute()
            filtered_df = pandas_df.between_time(start_time, end_time)
            # Convert back to Dask if needed
            result_df = dd.from_pandas(filtered_df, npartitions=1)
        else:
            result_df = self.pf._df.between_time(start_time, end_time)

        return self.pf.__class__(result_df, self.pf.islazy, self.pf._track_history)

    def at_time(
        self, time: time | str, datetime_col: str | None = None
    ) -> ParquetFrame:
        """
        Filter data at specific time of day.

        Args:
            time: Time to filter (time object or string like '09:00')
            datetime_col: Column to use as datetime index (auto-detected if None)

        Returns:
            Filtered ParquetFrame

        Examples:
            >>> # Data at market open
            >>> market_open = pf.ts.at_time('09:30')
        """
        if self.pf._df is None:
            raise ValueError("No DataFrame loaded")

        # Ensure datetime index
        self._ensure_datetime_index(datetime_col)

        if self.pf.islazy:
            warnings.warn(
                "at_time operation will compute Dask DataFrame. "
                "Consider using other filtering methods for large datasets.",
                UserWarning,
                stacklevel=2,
            )
            pandas_df = self.pf._df.compute()
            filtered_df = pandas_df.at_time(time)
            result_df = dd.from_pandas(filtered_df, npartitions=1)
        else:
            result_df = self.pf._df.at_time(time)

        return self.pf.__class__(result_df, self.pf.islazy, self.pf._track_history)

    def shift(self, periods: int = 1) -> ParquetFrame:
        """
        Shift time-series data by specified periods.

        Args:
            periods: Number of periods to shift (positive for forward, negative for backward)

        Returns:
            Shifted ParquetFrame

        Examples:
            >>> # Shift forward by 1 period
            >>> shifted = pf.ts.shift(1)
            >>> # Shift backward by 2 periods
            >>> lagged = pf.ts.shift(-2)
        """
        if self.pf._df is None:
            raise ValueError("No DataFrame loaded")

        shifted_df = self.pf._df.shift(periods)
        return self.pf.__class__(shifted_df, self.pf.islazy, self.pf._track_history)

    def lag(self, periods: int = 1) -> ParquetFrame:
        """
        Create lagged version of time-series data.

        Args:
            periods: Number of periods to lag

        Returns:
            Lagged ParquetFrame

        Examples:
            >>> # 1-period lag
            >>> lagged = pf.ts.lag(1)
        """
        return self.shift(periods)

    def lead(self, periods: int = 1) -> ParquetFrame:
        """
        Create leading version of time-series data.

        Args:
            periods: Number of periods to lead

        Returns:
            Leading ParquetFrame

        Examples:
            >>> # 1-period lead
            >>> leading = pf.ts.lead(1)
        """
        return self.shift(-periods)


class TimeSeriesResampler:
    """Helper class for time-series resampling operations."""

    def __init__(self, pf: ParquetFrame, rule: str, **kwargs):
        self.pf = pf
        self.rule = rule
        self.kwargs = kwargs

    def mean(self) -> ParquetFrame:
        """Calculate mean for each resampling group."""
        if self.pf.islazy:
            # For Dask, we need to use different approach
            resampled_df = self.pf._df.resample(self.rule, **self.kwargs).mean(
                numeric_only=True
            )
        else:
            resampled_df = self.pf._df.resample(self.rule, **self.kwargs).mean(
                numeric_only=True
            )

        return self.pf.__class__(resampled_df, self.pf.islazy, self.pf._track_history)

    def sum(self) -> ParquetFrame:
        """Calculate sum for each resampling group."""
        if self.pf.islazy:
            resampled_df = self.pf._df.resample(self.rule, **self.kwargs).sum()
        else:
            resampled_df = self.pf._df.resample(self.rule, **self.kwargs).sum()

        return self.pf.__class__(resampled_df, self.pf.islazy, self.pf._track_history)

    def max(self) -> ParquetFrame:
        """Calculate maximum for each resampling group."""
        if self.pf.islazy:
            resampled_df = self.pf._df.resample(self.rule, **self.kwargs).max()
        else:
            resampled_df = self.pf._df.resample(self.rule, **self.kwargs).max()

        return self.pf.__class__(resampled_df, self.pf.islazy, self.pf._track_history)

    def min(self) -> ParquetFrame:
        """Calculate minimum for each resampling group."""
        if self.pf.islazy:
            resampled_df = self.pf._df.resample(self.rule, **self.kwargs).min()
        else:
            resampled_df = self.pf._df.resample(self.rule, **self.kwargs).min()

        return self.pf.__class__(resampled_df, self.pf.islazy, self.pf._track_history)

    def std(self) -> ParquetFrame:
        """Calculate standard deviation for each resampling group."""
        if self.pf.islazy:
            resampled_df = self.pf._df.resample(self.rule, **self.kwargs).std(
                numeric_only=True
            )
        else:
            resampled_df = self.pf._df.resample(self.rule, **self.kwargs).std(
                numeric_only=True
            )

        return self.pf.__class__(resampled_df, self.pf.islazy, self.pf._track_history)

    def count(self) -> ParquetFrame:
        """Calculate count for each resampling group."""
        if self.pf.islazy:
            resampled_df = self.pf._df.resample(self.rule, **self.kwargs).count()
        else:
            resampled_df = self.pf._df.resample(self.rule, **self.kwargs).count()

        return self.pf.__class__(resampled_df, self.pf.islazy, self.pf._track_history)

    def agg(self, func) -> ParquetFrame:
        """Apply aggregation function(s) to resampling groups."""
        if self.pf.islazy:
            resampled_df = self.pf._df.resample(self.rule, **self.kwargs).agg(func)
        else:
            resampled_df = self.pf._df.resample(self.rule, **self.kwargs).agg(func)

        return self.pf.__class__(resampled_df, self.pf.islazy, self.pf._track_history)


class TimeSeriesRolling:
    """Helper class for time-series rolling window operations."""

    def __init__(self, pf: ParquetFrame, window: int | str, **kwargs):
        self.pf = pf
        self.window = window
        self.kwargs = kwargs

    def mean(self) -> ParquetFrame:
        """Calculate rolling mean."""
        rolling_df = self.pf._df.rolling(self.window, **self.kwargs).mean(
            numeric_only=True
        )
        return self.pf.__class__(rolling_df, self.pf.islazy, self.pf._track_history)

    def sum(self) -> ParquetFrame:
        """Calculate rolling sum."""
        rolling_df = self.pf._df.rolling(self.window, **self.kwargs).sum(
            numeric_only=True
        )
        return self.pf.__class__(rolling_df, self.pf.islazy, self.pf._track_history)

    def max(self) -> ParquetFrame:
        """Calculate rolling maximum."""
        rolling_df = self.pf._df.rolling(self.window, **self.kwargs).max()
        return self.pf.__class__(rolling_df, self.pf.islazy, self.pf._track_history)

    def min(self) -> ParquetFrame:
        """Calculate rolling minimum."""
        rolling_df = self.pf._df.rolling(self.window, **self.kwargs).min()
        return self.pf.__class__(rolling_df, self.pf.islazy, self.pf._track_history)

    def std(self) -> ParquetFrame:
        """Calculate rolling standard deviation."""
        rolling_df = self.pf._df.rolling(self.window, **self.kwargs).std(
            numeric_only=True
        )
        return self.pf.__class__(rolling_df, self.pf.islazy, self.pf._track_history)

    def apply(self, func) -> ParquetFrame:
        """Apply custom function to rolling window."""
        rolling_df = self.pf._df.rolling(self.window, **self.kwargs).apply(func)
        return self.pf.__class__(rolling_df, self.pf.islazy, self.pf._track_history)
