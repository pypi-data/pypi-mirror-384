"""
Performance benchmarking utilities for ParquetFrame.

This module provides tools for benchmarking ParquetFrame operations
and comparing pandas vs Dask performance across different scenarios.
"""

import gc
import tempfile
import time
import warnings
from pathlib import Path
from typing import Any

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

import numpy as np
import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .core import ParquetFrame

console = Console()


class BenchmarkResult:
    """Container for benchmark results."""

    def __init__(
        self,
        operation: str,
        backend: str,
        execution_time: float,
        memory_peak: float,
        memory_end: float,
        file_size_mb: float,
        success: bool = True,
        error: str | None = None,
    ):
        self.operation = operation
        self.backend = backend
        self.execution_time = execution_time
        self.memory_peak = memory_peak
        self.memory_end = memory_end
        self.file_size_mb = file_size_mb
        self.success = success
        self.error = error

    def __str__(self) -> str:
        status = "[OK]" if self.success else "[FAIL]"
        return f"{status} {self.operation} ({self.backend}): {self.execution_time:.3f}s, {self.memory_peak:.1f}MB peak"


class PerformanceBenchmark:
    """Performance benchmarking suite for ParquetFrame."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.console = Console() if verbose else None
        self.results: list[BenchmarkResult] = []

    def create_test_data(
        self,
        rows: int = 10000,
        cols: int = 10,
        include_strings: bool = True,
        include_dates: bool = True,
    ) -> pd.DataFrame:
        """Create test dataset for benchmarking."""
        if self.verbose:
            self.console.print(f"Creating test dataset: {rows:,} rows × {cols} columns")

        data = {}
        cols_used = 0

        # Calculate how many columns of each type to create
        reserved_cols = 1 if include_dates else 0
        available_cols = cols - reserved_cols

        if include_strings:
            base_cols_per_type = available_cols // 3
        else:
            base_cols_per_type = available_cols // 2

        # Numeric columns
        for i in range(base_cols_per_type):
            data[f"numeric_{i}"] = np.random.randn(rows)
            cols_used += 1

        # Integer columns
        for i in range(base_cols_per_type):
            data[f"integer_{i}"] = np.random.randint(0, 1000, rows)
            cols_used += 1

        # String columns
        if include_strings:
            categories = ["A", "B", "C", "D", "E"]
            for i in range(base_cols_per_type):
                data[f"category_{i}"] = np.random.choice(categories, rows)
                cols_used += 1

        # Date column
        if include_dates and cols_used < cols:
            start_date = pd.Timestamp("2020-01-01")
            data["date"] = pd.date_range(start_date, periods=rows, freq="h")
            cols_used += 1

        # Fill remaining columns with numeric data
        while cols_used < cols:
            data[f"extra_{len([k for k in data.keys() if k.startswith('extra_')])}"] = (
                np.random.randn(rows)
            )
            cols_used += 1

        return pd.DataFrame(data)

    def benchmark_operation(
        self,
        operation_name: str,
        operation_func,
        backend: str,
        file_size_mb: float,
        *args,
        **kwargs,
    ) -> BenchmarkResult:
        """Benchmark a single operation."""

        # Clear memory before benchmark
        gc.collect()

        # Get initial memory usage
        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        else:
            initial_memory = 0  # Fallback when psutil not available

        start_time = time.perf_counter()
        peak_memory = initial_memory
        success = True
        error = None

        try:
            # Monitor memory during execution
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                operation_func(*args, **kwargs)

                # Update peak memory
                if PSUTIL_AVAILABLE:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    peak_memory = max(peak_memory, current_memory)

        except Exception as e:
            success = False
            error = str(e)

        end_time = time.perf_counter()
        execution_time = end_time - start_time

        # Get final memory usage
        if PSUTIL_AVAILABLE:
            final_memory = process.memory_info().rss / 1024 / 1024
        else:
            final_memory = 0

        benchmark_result = BenchmarkResult(
            operation=operation_name,
            backend=backend,
            execution_time=execution_time,
            memory_peak=peak_memory - initial_memory,
            memory_end=final_memory - initial_memory,
            file_size_mb=file_size_mb,
            success=success,
            error=error,
        )

        self.results.append(benchmark_result)

        if self.verbose:
            self.console.print(f"  {benchmark_result}")

        return benchmark_result

    def benchmark_read_operations(
        self, file_sizes: list[tuple[int, str]] = None
    ) -> list[BenchmarkResult]:
        """Benchmark read operations across different file sizes."""

        if file_sizes is None:
            file_sizes = [
                (1000, "1K rows"),
                (10000, "10K rows"),
                (100000, "100K rows"),
                (1000000, "1M rows"),
            ]

        if self.verbose:
            self.console.print(
                "\n[READ BENCHMARK] [bold blue]Benchmarking Read Operations[/bold blue]"
            )

        results = []

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            for rows, description in file_sizes:
                if self.verbose:
                    self.console.print(f"\n[TEST DATA] Testing with {description}")

                # Create test data
                test_df = self.create_test_data(rows=rows, cols=8)
                test_file = temp_path / f"test_{rows}.parquet"
                test_df.to_parquet(test_file)

                file_size_mb = test_file.stat().st_size / 1024 / 1024

                # Benchmark pandas read
                def read_pandas(file=test_file):
                    return ParquetFrame.read(file, islazy=False)

                result = self.benchmark_operation(
                    f"Read {description}", read_pandas, "pandas", file_size_mb
                )
                results.append(result)

                # Benchmark Dask read
                def read_dask(file=test_file):
                    return ParquetFrame.read(file, islazy=True)

                result = self.benchmark_operation(
                    f"Read {description}", read_dask, "Dask", file_size_mb
                )
                results.append(result)

        return results

    def benchmark_operations(
        self, operations: list[str] = None, data_size: int = 100000
    ) -> list[BenchmarkResult]:
        """Benchmark various operations on both backends."""

        if operations is None:
            operations = ["groupby", "filter", "sort", "aggregation", "join"]

        if self.verbose:
            self.console.print(
                "\n[OPS BENCHMARK] [bold blue]Benchmarking Operations[/bold blue]"
            )

        results = []

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test datasets
            df1 = self.create_test_data(rows=data_size, cols=6)
            df2 = self.create_test_data(
                rows=data_size // 10, cols=4
            )  # Smaller for joins

            test_file1 = temp_path / "data1.parquet"
            test_file2 = temp_path / "data2.parquet"
            df1.to_parquet(test_file1)
            df2.to_parquet(test_file2)

            file_size_mb = test_file1.stat().st_size / 1024 / 1024

            for backend in ["pandas", "Dask"]:
                if self.verbose:
                    self.console.print(f"\n[BACKEND] Testing {backend} backend")

                pf1 = ParquetFrame.read(test_file1, islazy=(backend == "Dask"))
                pf2 = ParquetFrame.read(test_file2, islazy=(backend == "Dask"))

                for operation in operations:
                    if operation == "groupby":

                        def op(pf=pf1):
                            result = pf.groupby("category_0")["numeric_0"].mean()
                            if hasattr(result, "compute"):
                                return result.compute()
                            return result

                    elif operation == "filter":

                        def op(pf=pf1):
                            result = pf.query("numeric_0 > 0")
                            return result

                    elif operation == "sort":

                        def op(pf=pf1):
                            result = pf.sort_values("numeric_0")
                            return result

                    elif operation == "aggregation":

                        def op(pf=pf1):
                            result = pf.agg(
                                {
                                    "numeric_0": ["mean", "std"],
                                    "integer_0": ["min", "max"],
                                }
                            )
                            if hasattr(result, "compute"):
                                return result.compute()
                            return result

                    elif operation == "join":

                        def op(pf1_arg=pf1, pf2_arg=pf2):
                            # Simple index-based merge
                            df1_sample = pf1_arg.head(1000)
                            df2_sample = pf2_arg.head(100)

                            if hasattr(df1_sample, "_df"):
                                df1_sample = df1_sample._df
                            if hasattr(df2_sample, "_df"):
                                df2_sample = df2_sample._df

                            if hasattr(df1_sample, "compute"):
                                df1_sample = df1_sample.compute()
                            if hasattr(df2_sample, "compute"):
                                df2_sample = df2_sample.compute()

                            # Reset index for merge
                            df1_sample = df1_sample.reset_index()
                            df2_sample = df2_sample.reset_index()

                            return pd.merge(
                                df1_sample, df2_sample, on="index", how="inner"
                            )

                    result = self.benchmark_operation(
                        operation.capitalize(), op, backend, file_size_mb
                    )
                    results.append(result)

        return results

    def benchmark_threshold_sensitivity(
        self, thresholds: list[float] = None, file_sizes_mb: list[float] = None
    ) -> list[BenchmarkResult]:
        """Benchmark sensitivity to threshold settings."""

        if thresholds is None:
            thresholds = [1, 5, 10, 20, 50]

        if file_sizes_mb is None:
            file_sizes_mb = [0.5, 2, 8, 15, 25]

        if self.verbose:
            self.console.print(
                "\n🎯 [bold blue]Benchmarking Threshold Sensitivity[/bold blue]"
            )

        results = []

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files of different sizes
            test_files = {}
            for target_mb in file_sizes_mb:
                # Estimate rows needed for target file size
                estimated_rows = int(target_mb * 10000)  # Rough estimate
                test_df = self.create_test_data(rows=estimated_rows, cols=10)

                test_file = temp_path / f"data_{target_mb}mb.parquet"
                test_df.to_parquet(test_file)

                actual_mb = test_file.stat().st_size / 1024 / 1024
                test_files[actual_mb] = test_file

            # Test each threshold with each file
            for threshold in thresholds:
                for actual_mb, test_file in test_files.items():

                    def read_with_threshold(file=test_file, thresh=threshold):
                        return ParquetFrame.read(file, threshold_mb=thresh)

                    expected_backend = "Dask" if actual_mb >= threshold else "pandas"

                    result = self.benchmark_operation(
                        f"Threshold {threshold}MB",
                        read_with_threshold,
                        expected_backend,
                        actual_mb,
                    )
                    results.append(result)

        return results

    def generate_report(self) -> None:
        """Generate a comprehensive performance report."""

        if not self.results:
            self.console.print("[yellow]No benchmark results available.[/yellow]")
            return

        # Group results by operation
        operation_groups = {}
        for result in self.results:
            if result.operation not in operation_groups:
                operation_groups[result.operation] = []
            operation_groups[result.operation].append(result)

        # Create summary table
        table = Table(title="Performance Benchmark Summary")
        table.add_column("Operation", style="cyan", no_wrap=True)
        table.add_column("Backend", style="magenta")
        table.add_column("Avg Time (s)", justify="right")
        table.add_column("Avg Memory (MB)", justify="right")
        table.add_column("Success Rate", justify="right")

        for operation, results in operation_groups.items():
            # Group by backend
            backend_stats = {}
            for result in results:
                if result.backend not in backend_stats:
                    backend_stats[result.backend] = {
                        "times": [],
                        "memory": [],
                        "successes": 0,
                        "total": 0,
                    }

                backend_stats[result.backend]["times"].append(result.execution_time)
                backend_stats[result.backend]["memory"].append(result.memory_peak)
                backend_stats[result.backend]["total"] += 1
                if result.success:
                    backend_stats[result.backend]["successes"] += 1

            for backend, stats in backend_stats.items():
                avg_time = sum(stats["times"]) / len(stats["times"])
                avg_memory = sum(stats["memory"]) / len(stats["memory"])
                success_rate = stats["successes"] / stats["total"] * 100

                table.add_row(
                    operation,
                    backend,
                    f"{avg_time:.3f}",
                    f"{avg_memory:.1f}",
                    f"{success_rate:.1f}%",
                )

        self.console.print(table)

        # Performance recommendations
        self.console.print("\n📋 [bold blue]Performance Recommendations[/bold blue]")

        # Find optimal thresholds
        threshold_results = [r for r in self.results if "Threshold" in r.operation]
        if threshold_results:
            # Analyze threshold performance
            optimal_threshold = self._analyze_optimal_threshold(threshold_results)
            if optimal_threshold:
                self.console.print(f"• Optimal threshold: {optimal_threshold}MB")

        # Backend recommendations
        backend_comparison = self._compare_backends()
        for recommendation in backend_comparison:
            self.console.print(f"• {recommendation}")

    def _analyze_optimal_threshold(
        self, results: list[BenchmarkResult]
    ) -> float | None:
        """Analyze threshold results to find optimal value."""
        # This is a simplified analysis - in practice, you'd want more sophisticated optimization
        threshold_performance = {}

        for result in results:
            # Extract threshold from operation name
            try:
                threshold_str = result.operation.split()[1].replace("MB", "")
                threshold = float(threshold_str)

                if threshold not in threshold_performance:
                    threshold_performance[threshold] = []

                # Score based on execution time and memory efficiency
                score = 1 / (result.execution_time + result.memory_peak / 100)
                threshold_performance[threshold].append(score)
            except Exception:  # nosec B112
                # Broad exception handling intentional for benchmark robustness
                # Individual threshold parsing failures should not stop analysis
                continue

        if not threshold_performance:
            return None

        # Find threshold with best average performance
        avg_scores = {
            t: sum(scores) / len(scores) for t, scores in threshold_performance.items()
        }

        return max(avg_scores, key=avg_scores.get)

    def _compare_backends(self) -> list[str]:
        """Compare backend performance and generate recommendations."""
        recommendations = []

        pandas_results = [
            r for r in self.results if r.backend == "pandas" and r.success
        ]
        dask_results = [r for r in self.results if r.backend == "Dask" and r.success]

        if pandas_results and dask_results:
            avg_pandas_time = sum(r.execution_time for r in pandas_results) / len(
                pandas_results
            )
            avg_dask_time = sum(r.execution_time for r in dask_results) / len(
                dask_results
            )

            avg_pandas_memory = sum(r.memory_peak for r in pandas_results) / len(
                pandas_results
            )
            avg_dask_memory = sum(r.memory_peak for r in dask_results) / len(
                dask_results
            )

            if avg_pandas_time < avg_dask_time:
                recommendations.append(
                    "pandas is faster for operations on small to medium datasets"
                )
            else:
                recommendations.append(
                    "Dask is faster for operations on large datasets"
                )

            if avg_pandas_memory > avg_dask_memory * 1.5:
                recommendations.append(
                    "Dask is more memory efficient for large datasets"
                )
            elif avg_pandas_memory < avg_dask_memory:
                recommendations.append(
                    "pandas is more memory efficient for small datasets"
                )

        return recommendations


def run_comprehensive_benchmark(
    output_file: str | None = None, verbose: bool = True
) -> dict[str, Any]:
    """Run a comprehensive performance benchmark suite."""

    benchmark = PerformanceBenchmark(verbose=verbose)

    if verbose:
        console.print(
            "🚀 [bold green]Starting ParquetFrame Performance Benchmark[/bold green]"
        )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console if verbose else None,
    ) as progress:
        # Read operations benchmark
        task = progress.add_task("Benchmarking read operations...", total=None)
        read_results = benchmark.benchmark_read_operations()
        progress.remove_task(task)

        # Operations benchmark
        task = progress.add_task("Benchmarking data operations...", total=None)
        op_results = benchmark.benchmark_operations()
        progress.remove_task(task)

        # Threshold sensitivity
        task = progress.add_task("Analyzing threshold sensitivity...", total=None)
        threshold_results = benchmark.benchmark_threshold_sensitivity()
        progress.remove_task(task)

    # Generate report
    if verbose:
        benchmark.generate_report()

    # Compile results
    all_results = {
        "read_operations": [r.__dict__ for r in read_results],
        "data_operations": [r.__dict__ for r in op_results],
        "threshold_analysis": [r.__dict__ for r in threshold_results],
        "summary": {
            "total_benchmarks": len(benchmark.results),
            "successful_benchmarks": sum(1 for r in benchmark.results if r.success),
            "average_execution_time": (
                sum(r.execution_time for r in benchmark.results)
                / len(benchmark.results)
                if benchmark.results
                else 0.0
            ),
            "average_memory_usage": (
                sum(r.memory_peak for r in benchmark.results) / len(benchmark.results)
                if benchmark.results
                else 0.0
            ),
        },
    }

    # Save results if requested
    if output_file:
        import json

        with open(output_file, "w") as f:
            json.dump(all_results, f, indent=2, default=str)
        if verbose:
            console.print(f"📊 Results saved to {output_file}")

    return all_results
