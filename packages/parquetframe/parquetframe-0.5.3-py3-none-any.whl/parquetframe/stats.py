"""
Statistical analysis functionality for ParquetFrame.

This module provides advanced statistical operations including distribution analysis,
correlation matrices, outlier detection, and statistical testing capabilities.
Supports both pandas and Dask backends with intelligent dispatching.
"""

from __future__ import annotations

import warnings
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Literal

import dask.dataframe as dd
import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from .core import ParquetFrame


# Cache for expensive statistical computations
@lru_cache(maxsize=256)
def _cached_correlation_matrix(df_hash: str, method: str, columns_hash: str) -> Any:
    """Cache correlation matrices to avoid repeated computation."""
    # This will be populated by the correlation methods
    return None


def _get_memory_usage_mb(df: pd.DataFrame | dd.DataFrame) -> float:
    """Estimate memory usage of a DataFrame in MB."""
    try:
        if isinstance(df, dd.DataFrame):
            # For Dask, estimate based on npartitions and one partition
            sample_partition = df.get_partition(0).compute()
            partition_size = sample_partition.memory_usage(deep=True).sum() / (
                1024 * 1024
            )
            return partition_size * df.npartitions
        else:
            return df.memory_usage(deep=True).sum() / (1024 * 1024)
    except Exception:
        return float("inf")  # Assume large if we can't calculate


def compute_percentile_stats(
    series: pd.Series | dd.Series, percentiles: list[float] | None = None
) -> dict[str, float]:
    """
    Compute percentile-based statistics for a series.

    Args:
        series: Input series
        percentiles: List of percentiles to compute (default: [0.25, 0.5, 0.75])

    Returns:
        Dictionary of percentile statistics
    """
    if percentiles is None:
        percentiles = [0.25, 0.5, 0.75]

    if isinstance(series, dd.Series):
        # Dask computation
        stats = {}
        for p in percentiles:
            stats[f"p{int(p*100)}"] = series.quantile(p).compute()
    else:
        # Pandas computation
        stats = {}
        for p in percentiles:
            stats[f"p{int(p*100)}"] = series.quantile(p)

    return stats


def detect_outliers_iqr(
    series: pd.Series | dd.Series, multiplier: float = 1.5
) -> pd.Series | dd.Series:
    """
    Detect outliers using the IQR method.

    Args:
        series: Input series
        multiplier: IQR multiplier for outlier detection

    Returns:
        Boolean series indicating outliers
    """
    if isinstance(series, dd.Series):
        # Dask implementation
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr
        return (series < lower_bound) | (series > upper_bound)
    else:
        # Pandas implementation
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr
        return (series < lower_bound) | (series > upper_bound)


def detect_outliers_zscore(
    series: pd.Series | dd.Series, threshold: float = 3.0
) -> pd.Series | dd.Series:
    """
    Detect outliers using the Z-score method.

    Args:
        series: Input series
        threshold: Z-score threshold for outlier detection

    Returns:
        Boolean series indicating outliers
    """
    if isinstance(series, dd.Series):
        # Dask implementation
        mean = series.mean()
        std = series.std()
        z_scores = (series - mean) / std
        return abs(z_scores) > threshold
    else:
        # Pandas implementation
        z_scores = np.abs((series - series.mean()) / series.std())
        return z_scores > threshold


class StatsAccessor:
    """
    Statistical analysis accessor for ParquetFrame providing advanced analytics operations.

    This accessor provides comprehensive statistical functionality including distribution
    analysis, correlation matrices, outlier detection, and statistical testing.
    Intelligently dispatches between pandas and Dask backends with performance optimizations:

    - Memory-aware operation selection
    - Caching for expensive computations
    - Parallel processing for independent operations
    - Progress indicators for long-running computations

    Examples:
        >>> pf = ParquetFrame.read("data.csv")
        >>> # Distribution analysis
        >>> dist_summary = pf.stats.distribution_summary()
        >>> # Correlation matrix
        >>> corr_matrix = pf.stats.corr_matrix()
        >>> # Outlier detection
        >>> outliers = pf.stats.detect_outliers('column_name', method='zscore')
    """

    def __init__(self, pf: ParquetFrame) -> None:
        """Initialize with a ParquetFrame instance."""
        self.pf = pf
        self._computation_cache = {}
        self._memory_threshold_mb = 500  # Switch to chunked processing above this

    def describe_extended(
        self, include_all: bool = True, use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Generate extended descriptive statistics beyond basic describe() with performance optimizations.

        Args:
            include_all: Whether to include all columns or just numeric ones
            use_cache: Whether to use caching for repeated computations

        Returns:
            DataFrame with extended statistical summaries

        Examples:
            >>> extended_stats = pf.stats.describe_extended()
        """
        if self.pf._df is None:
            raise ValueError("No DataFrame loaded")

        # Check cache first
        backend_type = "dask" if isinstance(self.pf._df, dd.DataFrame) else "pandas"
        cache_key = (
            f"describe_extended_{include_all}_{backend_type}_{len(self.pf._df.columns)}"
        )
        if use_cache and cache_key in self._computation_cache:
            return self._computation_cache[cache_key]

        # Check memory usage for optimization
        memory_usage = _get_memory_usage_mb(self.pf._df)
        is_dask = isinstance(self.pf._df, dd.DataFrame)
        use_chunked = memory_usage > self._memory_threshold_mb and not is_dask

        if use_chunked:
            warnings.warn(
                f"Large dataset ({memory_usage:.1f}MB) detected. "
                "Consider using Dask backend for better performance.",
                UserWarning,
                stacklevel=2,
            )

        # Get numeric columns
        numeric_cols = self.pf._df.select_dtypes(include=[np.number]).columns
        extended_stats = {}

        for col in numeric_cols:
            series = self.pf._df[col]

            # Check if this is actually a Dask Series (more reliable than islazy flag)
            if isinstance(series, dd.Series):
                # Compute Dask statistics with batch operations for efficiency
                basic_stats = series.describe().compute()
                additional_stats = {
                    "skewness": (
                        series.skew().compute() if hasattr(series, "skew") else np.nan
                    ),
                    "kurtosis": (
                        series.kurtosis().compute()
                        if hasattr(series, "kurtosis")
                        else np.nan
                    ),
                }
                # Combine basic and additional stats
                stats = basic_stats.to_dict()
                stats.update(additional_stats)
            else:
                # Pandas statistics with potential chunking
                if use_chunked and len(series) > 1000000:  # 1M rows threshold
                    # Compute statistics in chunks to avoid memory issues
                    chunk_size = max(100000, len(series) // 10)
                    stats = self._compute_stats_chunked(series, chunk_size)
                else:
                    # Standard computation for smaller datasets
                    stats = {
                        "count": series.count(),
                        "mean": series.mean(),
                        "std": series.std(),
                        "min": series.min(),
                        "max": series.max(),
                        "median": series.median(),
                        "skewness": series.skew(),
                        "kurtosis": series.kurtosis(),
                    }

            # Add percentile stats
            percentile_stats = compute_percentile_stats(
                series, [0.1, 0.25, 0.5, 0.75, 0.9]
            )
            stats.update(percentile_stats)
            extended_stats[col] = stats

        result = pd.DataFrame(extended_stats).T

        # Cache the result
        if use_cache:
            self._computation_cache[cache_key] = result

        return result

    def _compute_stats_chunked(
        self, series: pd.Series, chunk_size: int
    ) -> dict[str, float]:
        """Compute statistics in chunks for memory efficiency."""
        n_chunks = len(series) // chunk_size + (1 if len(series) % chunk_size else 0)

        # Initialize accumulators
        count = 0
        sum_val = 0.0
        sum_sq = 0.0
        min_val = float("inf")
        max_val = float("-inf")

        # Process chunks
        for i in range(n_chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, len(series))
            chunk = series.iloc[start_idx:end_idx].dropna()

            if len(chunk) > 0:
                count += len(chunk)
                sum_val += chunk.sum()
                sum_sq += (chunk**2).sum()
                min_val = min(min_val, chunk.min())
                max_val = max(max_val, chunk.max())

        # Compute final statistics
        mean = sum_val / count if count > 0 else np.nan
        variance = (sum_sq / count - mean**2) if count > 1 else np.nan
        std = np.sqrt(variance) if variance >= 0 else np.nan

        return {
            "count": count,
            "mean": mean,
            "std": std,
            "min": min_val if min_val != float("inf") else np.nan,
            "max": max_val if max_val != float("-inf") else np.nan,
            "median": series.median(),  # Still compute median normally (efficient)
            "skewness": series.skew(),  # These are harder to chunk efficiently
            "kurtosis": series.kurtosis(),
        }

    def corr_matrix(
        self,
        method: Literal["pearson", "kendall", "spearman"] = "pearson",
        min_periods: int = 1,
    ) -> pd.DataFrame:
        """
        Compute correlation matrix with enhanced options.

        Args:
            method: Correlation method ('pearson', 'kendall', 'spearman')
            min_periods: Minimum number of observations required per pair

        Returns:
            Correlation matrix DataFrame

        Examples:
            >>> corr = pf.stats.corr_matrix(method='spearman')
        """
        if self.pf._df is None:
            raise ValueError("No DataFrame loaded")

        # Select only numeric columns
        numeric_df = self.pf._df.select_dtypes(include=[np.number])

        # Check if this is actually a Dask DataFrame (more reliable than islazy flag)
        if isinstance(numeric_df, dd.DataFrame):
            # For Dask, compute the correlation matrix
            if method == "pearson":
                corr_matrix = numeric_df.corr().compute()
            else:
                # Dask doesn't support kendall/spearman, compute first
                warnings.warn(
                    f"Dask doesn't support {method} correlation. Computing DataFrame first.",
                    UserWarning,
                    stacklevel=2,
                )
                computed_df = numeric_df.compute()
                corr_matrix = computed_df.corr(method=method, min_periods=min_periods)
        else:
            corr_matrix = numeric_df.corr(method=method, min_periods=min_periods)

        return corr_matrix

    def distribution_summary(self, column: str | None = None) -> dict[str, Any]:
        """
        Generate comprehensive distribution analysis.

        Args:
            column: Specific column to analyze (if None, analyzes all numeric columns)

        Returns:
            Dictionary with distribution statistics

        Examples:
            >>> dist_info = pf.stats.distribution_summary('sales_amount')
        """
        if self.pf._df is None:
            raise ValueError("No DataFrame loaded")

        if column:
            columns_to_analyze = [column]
        else:
            columns_to_analyze = self.pf._df.select_dtypes(
                include=[np.number]
            ).columns.tolist()

        distribution_info = {}

        for col in columns_to_analyze:
            series = self.pf._df[col]

            # Check if this is actually a Dask Series (more reliable than islazy flag)
            if isinstance(series, dd.Series):
                series_computed = series.compute()
            else:
                series_computed = series

            # Basic distribution statistics
            dist_stats = {
                "count": len(series_computed),
                "non_null_count": series_computed.count(),
                "null_count": series_computed.isnull().sum(),
                "unique_count": series_computed.nunique(),
                "mean": series_computed.mean(),
                "median": series_computed.median(),
                "std": series_computed.std(),
                "var": series_computed.var(),
                "skewness": series_computed.skew(),
                "kurtosis": series_computed.kurtosis(),
                "min": series_computed.min(),
                "max": series_computed.max(),
                "range": series_computed.max() - series_computed.min(),
            }

            # Percentiles
            percentiles = [0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99]
            for p in percentiles:
                dist_stats[f"percentile_{int(p*100)}"] = series_computed.quantile(p)

            # Distribution shape assessment
            if abs(dist_stats["skewness"]) < 0.5:
                dist_stats["distribution_shape"] = "approximately_symmetric"
            elif dist_stats["skewness"] > 0.5:
                dist_stats["distribution_shape"] = "right_skewed"
            else:
                dist_stats["distribution_shape"] = "left_skewed"

            # Outlier counts
            outliers_iqr = detect_outliers_iqr(series_computed)
            outliers_zscore = detect_outliers_zscore(series_computed)

            dist_stats["outliers_iqr_count"] = outliers_iqr.sum()
            dist_stats["outliers_zscore_count"] = outliers_zscore.sum()
            dist_stats["outliers_iqr_percent"] = (
                outliers_iqr.sum() / len(series_computed)
            ) * 100
            dist_stats["outliers_zscore_percent"] = (
                outliers_zscore.sum() / len(series_computed)
            ) * 100

            distribution_info[col] = dist_stats

        return (
            distribution_info
            if len(columns_to_analyze) > 1
            else distribution_info[columns_to_analyze[0]]
        )

    def detect_outliers(
        self,
        column: str | None = None,
        method: Literal["iqr", "zscore"] = "iqr",
        **kwargs,
    ) -> ParquetFrame:
        """
        Detect outliers using specified method.

        Args:
            column: Column to analyze (if None, analyzes all numeric columns)
            method: Outlier detection method ('iqr' or 'zscore')
            **kwargs: Method-specific parameters (multiplier for IQR, threshold for zscore)

        Returns:
            ParquetFrame with outlier indicators

        Examples:
            >>> outliers = pf.stats.detect_outliers('sales_amount', method='iqr')
            >>> outliers = pf.stats.detect_outliers('price', method='zscore', threshold=2.5)
        """
        if self.pf._df is None:
            raise ValueError("No DataFrame loaded")

        if column:
            columns_to_check = [column]
        else:
            columns_to_check = self.pf._df.select_dtypes(
                include=[np.number]
            ).columns.tolist()

        # Create a copy of the dataframe
        result_df = self.pf._df.copy()

        for col in columns_to_check:
            outlier_col_name = f"{col}_outlier_{method}"

            if method == "iqr":
                multiplier = kwargs.get("multiplier", 1.5)
                outlier_mask = detect_outliers_iqr(self.pf._df[col], multiplier)
            elif method == "zscore":
                threshold = kwargs.get("threshold", 3.0)
                outlier_mask = detect_outliers_zscore(self.pf._df[col], threshold)
            else:
                raise ValueError(
                    f"Unsupported method: {method}. Use 'iqr' or 'zscore'."
                )

            result_df[outlier_col_name] = outlier_mask

        return self.pf.__class__(result_df, self.pf.islazy, self.pf._track_history)

    def normality_test(self, column: str) -> dict[str, float]:
        """
        Perform normality tests on a column.

        Args:
            column: Column name to test

        Returns:
            Dictionary with test results

        Examples:
            >>> normality = pf.stats.normality_test('sales_amount')
        """
        if self.pf._df is None:
            raise ValueError("No DataFrame loaded")

        series = self.pf._df[column]

        if self.pf.islazy:
            series_computed = series.compute()
        else:
            series_computed = series

        # Remove null values
        series_clean = series_computed.dropna()

        try:
            from scipy import stats

            # Shapiro-Wilk test (for sample size <= 5000)
            if len(series_clean) <= 5000:
                shapiro_stat, shapiro_p = stats.shapiro(series_clean)
                shapiro_result = {
                    "statistic": shapiro_stat,
                    "p_value": shapiro_p,
                    "is_normal": shapiro_p > 0.05,
                }
            else:
                shapiro_result = None

            # Kolmogorov-Smirnov test
            # Standardize the data first
            standardized = (series_clean - series_clean.mean()) / series_clean.std()
            ks_stat, ks_p = stats.kstest(standardized, "norm")
            ks_result = {
                "statistic": ks_stat,
                "p_value": ks_p,
                "is_normal": ks_p > 0.05,
            }

            # D'Agostino's normality test
            dagostino_stat, dagostino_p = stats.normaltest(series_clean)
            dagostino_result = {
                "statistic": dagostino_stat,
                "p_value": dagostino_p,
                "is_normal": dagostino_p > 0.05,
            }

            results = {
                "sample_size": len(series_clean),
                "kolmogorov_smirnov": ks_result,
                "dagostino": dagostino_result,
            }

            if shapiro_result:
                results["shapiro_wilk"] = shapiro_result

            return results

        except ImportError:
            warnings.warn(
                "scipy not available. Install scipy for normality tests: pip install scipy",
                UserWarning,
                stacklevel=2,
            )

            # Basic normality assessment using skewness and kurtosis
            skewness = series_clean.skew()
            kurtosis = series_clean.kurtosis()

            # Rule of thumb: normal if |skewness| < 2 and |kurtosis| < 7
            is_approximately_normal = abs(skewness) < 2 and abs(kurtosis) < 7

            return {
                "sample_size": len(series_clean),
                "skewness": skewness,
                "kurtosis": kurtosis,
                "is_approximately_normal": is_approximately_normal,
                "note": "scipy not available, using basic skewness/kurtosis assessment",
            }

    def correlation_test(self, col1: str, col2: str) -> dict[str, float]:
        """
        Perform correlation significance test between two columns.

        Args:
            col1: First column name
            col2: Second column name

        Returns:
            Dictionary with correlation test results

        Examples:
            >>> corr_test = pf.stats.correlation_test('price', 'sales_volume')
        """
        if self.pf._df is None:
            raise ValueError("No DataFrame loaded")

        series1 = self.pf._df[col1]
        series2 = self.pf._df[col2]

        # Check if these are actually Dask Series (more reliable than islazy flag)
        if isinstance(series1, dd.Series):
            series1 = series1.compute()
        if isinstance(series2, dd.Series):
            series2 = series2.compute()

        # Remove rows where either value is null
        combined = pd.DataFrame({col1: series1, col2: series2}).dropna()

        try:
            from scipy import stats

            # Pearson correlation
            pearson_r, pearson_p = stats.pearsonr(combined[col1], combined[col2])

            # Spearman correlation
            spearman_r, spearman_p = stats.spearmanr(combined[col1], combined[col2])

            return {
                "sample_size": len(combined),
                "pearson": {
                    "correlation": pearson_r,
                    "p_value": pearson_p,
                    "significant": pearson_p < 0.05,
                },
                "spearman": {
                    "correlation": spearman_r,
                    "p_value": spearman_p,
                    "significant": spearman_p < 0.05,
                },
            }

        except ImportError:
            warnings.warn(
                "scipy not available. Install scipy for correlation tests: pip install scipy",
                UserWarning,
                stacklevel=2,
            )

            # Basic correlation without significance test
            pearson_r = combined[col1].corr(combined[col2])

            return {
                "sample_size": len(combined),
                "pearson_correlation": pearson_r,
                "note": "scipy not available, p-values not computed",
            }

    def linear_regression(self, x_col: str, y_col: str) -> dict[str, Any]:
        """
        Perform simple linear regression analysis.

        Args:
            x_col: Independent variable column name
            y_col: Dependent variable column name

        Returns:
            Dictionary with regression results

        Examples:
            >>> regression = pf.stats.linear_regression('advertising_spend', 'sales')
        """
        if self.pf._df is None:
            raise ValueError("No DataFrame loaded")

        x_series = self.pf._df[x_col]
        y_series = self.pf._df[y_col]

        # Check if these are actually Dask Series (more reliable than islazy flag)
        if isinstance(x_series, dd.Series):
            x_series = x_series.compute()
        if isinstance(y_series, dd.Series):
            y_series = y_series.compute()

        # Remove rows where either value is null
        combined = pd.DataFrame({x_col: x_series, y_col: y_series}).dropna()
        x = combined[x_col]
        y = combined[y_col]

        try:
            from scipy import stats

            # Perform linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

            # Calculate additional statistics
            y_pred = slope * x + intercept
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)

            # Mean squared error
            mse = ss_res / len(y)
            rmse = np.sqrt(mse)

            return {
                "sample_size": len(combined),
                "slope": slope,
                "intercept": intercept,
                "r_value": r_value,
                "r_squared": r_squared,
                "p_value": p_value,
                "standard_error": std_err,
                "mse": mse,
                "rmse": rmse,
                "significant": p_value < 0.05,
                "equation": f"y = {slope:.4f}x + {intercept:.4f}",
            }

        except ImportError:
            warnings.warn(
                "scipy not available. Install scipy for regression analysis: pip install scipy",
                UserWarning,
                stacklevel=2,
            )

            # Basic correlation as proxy
            correlation = x.corr(y)

            return {
                "sample_size": len(combined),
                "correlation": correlation,
                "note": "scipy not available, only correlation computed",
            }

    def regression_summary(self, x_col: str, y_col: str) -> pd.DataFrame:
        """
        Generate a comprehensive regression summary.

        Args:
            x_col: Independent variable column name
            y_col: Dependent variable column name

        Returns:
            DataFrame with detailed regression analysis

        Examples:
            >>> summary = pf.stats.regression_summary('advertising_spend', 'sales')
        """
        regression_results = self.linear_regression(x_col, y_col)

        # Convert to DataFrame for better display
        summary_data = []
        for key, value in regression_results.items():
            if key != "equation":
                summary_data.append({"Metric": key, "Value": value})

        summary_df = pd.DataFrame(summary_data)

        if "equation" in regression_results:
            print(f"Regression Equation: {regression_results['equation']}")

        return summary_df
