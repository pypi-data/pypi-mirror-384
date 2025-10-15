"""
BioFrame integration for ParquetFrame.

This module provides bioframe functionality with intelligent dispatching
to parallel Dask implementations when operating on lazy DataFrames.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from parquetframe.core import ParquetFrame

try:
    import bioframe as bf

    BIOFRAME_AVAILABLE = True
except ImportError:
    BIOFRAME_AVAILABLE = False

import pandas as pd


class BioAccessor:
    """
    Accessor for bioframe functions, providing parallel Dask implementations.

    This class is accessed via `ParquetFrame.bio` and automatically chooses
    between pandas (eager) and Dask (parallel) implementations based on the
    backend of the parent ParquetFrame.
    """

    def __init__(self, parquet_frame):
        """
        Initialize the BioAccessor.

        Args:
            parquet_frame: The parent ParquetFrame instance.
        """
        if not BIOFRAME_AVAILABLE:
            raise ImportError(
                "bioframe is required for genomics functionality. "
                "Install with: pip install parquetframe[bio]"
            )

        self._pf = parquet_frame
        self._df = parquet_frame._df
        self._is_lazy = parquet_frame.islazy

    def cluster(
        self,
        min_dist: int = 0,
        on: str | list | None = None,
        **kwargs: Any,
    ) -> ParquetFrame:
        """
        Cluster overlapping genomic intervals.

        For lazy (Dask) DataFrames, this performs partition-local clustering,
        which is highly effective but may not merge clusters spanning partition
        boundaries. For pandas DataFrames, uses standard bioframe clustering.

        Args:
            min_dist: Minimum distance between intervals to merge.
            on: Columns to use for grouping (default: None for standard chrom, start, end).
            **kwargs: Additional arguments passed to bioframe.cluster.

        Returns:
            New ParquetFrame with clustered intervals.

        Examples:
            >>> pf = ParquetFrame.read('regions.parquet')
            >>> clustered = pf.bio.cluster(min_dist=1000)
            >>> clustered = pf.bio.cluster(on='chrom', min_dist=0)
        """
        if self._is_lazy:
            print("🧬 Running parallelized genomic clustering (partition-local)...")

            def cluster_partition(df_part):
                """Apply bioframe clustering to a single partition."""
                if len(df_part) == 0:
                    return df_part
                try:
                    # Convert on parameter to list if it's a string
                    on_param = [on] if isinstance(on, str) else on
                    return bf.cluster(df_part, min_dist=min_dist, on=on_param, **kwargs)
                except Exception as e:
                    warnings.warn(
                        f"Clustering failed on partition: {e}",
                        UserWarning,
                        stacklevel=2,
                    )
                    return df_part

            # Get metadata by running on a small sample
            sample = self._df.head(1)  # head() on Dask already returns pandas
            if len(sample) > 0:
                meta_df = cluster_partition(sample)
            else:
                meta_df = sample

            # Apply clustering across all partitions
            result_ddf = self._df.map_partitions(cluster_partition, meta=meta_df)
            return self._pf.__class__(result_ddf, islazy=True)

        else:
            print("🧬 Running standard bioframe clustering...")

            # Handle empty DataFrames
            if len(self._df) == 0:
                return self._pf.__class__(self._df.copy(), islazy=False)

            try:
                # Convert on parameter to list if it's a string
                on_param = [on] if isinstance(on, str) else on
                result_df = bf.cluster(
                    self._df, min_dist=min_dist, on=on_param, **kwargs
                )
                return self._pf.__class__(result_df, islazy=False)
            except Exception as e:
                raise ValueError(f"Bioframe clustering failed: {e}") from e

    def overlap(
        self,
        other: ParquetFrame,
        how: str = "left",
        on: str | list | None = None,
        broadcast: bool = False,
        **kwargs: Any,
    ) -> ParquetFrame:
        """
        Perform genomic interval overlap operations.

        Args:
            other: Another ParquetFrame to overlap with.
            how: Type of overlap ('left', 'inner', 'outer').
            on: Columns to use for overlap (default: None for standard chrom, start, end).
            broadcast: If True, broadcast the smaller DataFrame for parallel join.
            **kwargs: Additional arguments passed to bioframe.overlap.

        Returns:
            New ParquetFrame with overlap results.

        Examples:
            >>> genes = ParquetFrame.read('genes.parquet')
            >>> peaks = ParquetFrame.read('peaks.parquet')
            >>> overlaps = genes.bio.overlap(peaks, broadcast=True)
        """
        if not isinstance(other, self._pf.__class__):
            raise TypeError("The second argument must be a ParquetFrame instance.")

        if self._is_lazy or other.islazy:
            if broadcast:
                print("🧬 Running parallelized genomic overlap using broadcasting...")

                # Determine which is larger for optimal broadcasting
                if self._is_lazy:
                    large_ddf = self._df
                    small_pdf = other._df.compute() if other.islazy else other._df
                    large_is_self = True
                else:
                    large_ddf = other._df
                    small_pdf = self._df
                    large_is_self = False

                def overlap_partition(df_part, small_df):
                    """Apply overlap to a single partition with broadcast DataFrame."""
                    if len(df_part) == 0:
                        return df_part
                    try:
                        if large_is_self:
                            return bf.overlap(
                                df_part, small_df, how=how, on=on, **kwargs
                            )
                        else:
                            return bf.overlap(
                                small_df, df_part, how=how, on=on, **kwargs
                            )
                    except Exception as e:
                        warnings.warn(
                            f"Overlap failed on partition: {e}",
                            UserWarning,
                            stacklevel=2,
                        )
                        return df_part[:0]  # Return empty DataFrame with same structure

                # Get metadata structure
                sample = large_ddf.head(1)  # head() on Dask already returns pandas
                if len(sample) > 0 and len(small_pdf) > 0:
                    meta_df = overlap_partition(sample, small_pdf.head(1))
                else:
                    meta_df = sample[:0] if len(sample) > 0 else small_pdf[:0]

                # Apply overlap across all partitions
                result_ddf = large_ddf.map_partitions(
                    overlap_partition, small_df=small_pdf, meta=meta_df
                )
                return self._pf.__class__(result_ddf, islazy=True)

            else:
                warnings.warn(
                    "Parallel overlap without broadcasting requires computing both DataFrames. "
                    "Consider using broadcast=True if one DataFrame is small.",
                    UserWarning,
                    stacklevel=2,
                )
                print("🧬 Computing DataFrames for genomic overlap...")

                df1_pandas = self._df.compute() if self._is_lazy else self._df
                df2_pandas = other._df.compute() if other.islazy else other._df

                result_df = bf.overlap(df1_pandas, df2_pandas, how=how, on=on, **kwargs)
                return self._pf.__class__(result_df, islazy=False)
        else:
            print("🧬 Running standard bioframe overlap...")
            try:
                result_df = bf.overlap(self._df, other._df, how=how, on=on, **kwargs)
                return self._pf.__class__(result_df, islazy=False)
            except Exception as e:
                raise ValueError(f"Bioframe overlap failed: {e}") from e

    def complement(
        self, view_df: pd.DataFrame | None = None, **kwargs: Any
    ) -> ParquetFrame:
        """
        Find complement intervals for genomic regions.

        Args:
            view_df: View DataFrame defining the genomic space (chromosome sizes).
            **kwargs: Additional arguments passed to bioframe.complement.

        Returns:
            New ParquetFrame with complement intervals.
        """
        if self._is_lazy:
            warnings.warn(
                "Complement operation on lazy DataFrames requires computation. "
                "Converting to pandas for processing.",
                UserWarning,
                stacklevel=2,
            )
            df_pandas = self._df.compute()
        else:
            df_pandas = self._df

        print("🧬 Computing genomic complement...")
        try:
            result_df = bf.complement(df_pandas, view_df=view_df, **kwargs)
            return self._pf.__class__(result_df, islazy=False)
        except Exception as e:
            raise ValueError(f"Bioframe complement failed: {e}") from e

    def merge(
        self, min_dist: int = 0, on: str | list | None = None, **kwargs: Any
    ) -> ParquetFrame:
        """
        Merge overlapping genomic intervals.

        This is similar to cluster but specifically for merging intervals.

        Args:
            min_dist: Minimum distance between intervals to merge.
            on: Columns to use for grouping (default: None for standard chrom, start, end).
            **kwargs: Additional arguments passed to bioframe.merge.

        Returns:
            New ParquetFrame with merged intervals.
        """
        if self._is_lazy:
            print("🧬 Running parallelized genomic merge (partition-local)...")

            def merge_partition(df_part):
                """Apply bioframe merge to a single partition."""
                if len(df_part) == 0:
                    return df_part
                try:
                    # Convert on parameter to list if it's a string
                    on_param = [on] if isinstance(on, str) else on
                    return bf.merge(df_part, min_dist=min_dist, on=on_param, **kwargs)
                except Exception as e:
                    warnings.warn(
                        f"Merge failed on partition: {e}", UserWarning, stacklevel=2
                    )
                    return df_part

            # Get metadata structure
            sample = self._df.head(1)  # head() on Dask already returns pandas
            if len(sample) > 0:
                meta_df = merge_partition(sample)
            else:
                meta_df = sample

            # Apply merge across all partitions
            result_ddf = self._df.map_partitions(merge_partition, meta=meta_df)
            return self._pf.__class__(result_ddf, islazy=True)

        else:
            print("🧬 Running standard bioframe merge...")

            # Handle empty DataFrames
            if len(self._df) == 0:
                return self._pf.__class__(self._df.copy(), islazy=False)

            try:
                # Convert on parameter to list if it's a string
                on_param = [on] if isinstance(on, str) else on
                result_df = bf.merge(self._df, min_dist=min_dist, on=on_param, **kwargs)
                return self._pf.__class__(result_df, islazy=False)
            except Exception as e:
                raise ValueError(f"Bioframe merge failed: {e}") from e

    def closest(self, other: ParquetFrame, **kwargs: Any) -> ParquetFrame:
        """
        Find closest genomic intervals between two DataFrames.

        Args:
            other: Another ParquetFrame to find closest intervals to.
            **kwargs: Additional arguments passed to bioframe.closest.

        Returns:
            New ParquetFrame with closest interval information.
        """
        if not isinstance(other, self._pf.__class__):
            raise TypeError("The second argument must be a ParquetFrame instance.")

        # Closest operation is complex for parallel implementation
        # Convert to pandas for accurate results
        if self._is_lazy or other.islazy:
            warnings.warn(
                "Closest operation requires computing DataFrames for accurate results.",
                UserWarning,
                stacklevel=2,
            )
            df1_pandas = self._df.compute() if self._is_lazy else self._df
            df2_pandas = other._df.compute() if other.islazy else other._df
        else:
            df1_pandas = self._df
            df2_pandas = other._df

        print("🧬 Finding closest genomic intervals...")
        try:
            result_df = bf.closest(df1_pandas, df2_pandas, **kwargs)
            return self._pf.__class__(result_df, islazy=False)
        except Exception as e:
            raise ValueError(f"Bioframe closest failed: {e}") from e


class BioError(Exception):
    """Custom exception for bioframe-related errors."""

    pass
