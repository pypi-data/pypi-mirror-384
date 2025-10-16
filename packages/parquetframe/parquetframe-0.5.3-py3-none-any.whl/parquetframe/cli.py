"""
Command Line Interface for ParquetFrame.

This module provides a powerful CLI for interacting with parquet files,
including batch processing and interactive modes.
"""

import sys
from pathlib import Path
from typing import Any

try:
    import click
    from rich.console import Console
    from rich.table import Table
except ImportError as e:
    print("CLI dependencies not installed. Install with: pip install parquetframe[cli]")
    print(f"Missing: {e.name}")
    sys.exit(1)

from .core import ParquetFrame
from .exceptions import (
    check_dependencies,
    format_dependency_status,
    suggest_installation_commands,
)

try:
    from .interactive import start_interactive_session

    INTERACTIVE_AVAILABLE = True
except ImportError:
    INTERACTIVE_AVAILABLE = False

try:
    from .benchmark import PerformanceBenchmark, run_comprehensive_benchmark

    BENCHMARK_AVAILABLE = True
except ImportError:
    BENCHMARK_AVAILABLE = False

try:
    import yaml

    from .workflows import WorkflowEngine, WorkflowError, create_example_workflow

    WORKFLOW_AVAILABLE = True
except ImportError:
    WORKFLOW_AVAILABLE = False

try:
    from .sql import validate_sql_query

    SQL_AVAILABLE = True
except ImportError:
    SQL_AVAILABLE = False

try:
    from .workflow_history import WorkflowHistoryManager

    WORKFLOW_HISTORY_AVAILABLE = True
except ImportError:
    WORKFLOW_HISTORY_AVAILABLE = False

try:
    from .workflow_visualization import WorkflowVisualizer

    WORKFLOW_VISUALIZATION_AVAILABLE = True
except ImportError:
    WORKFLOW_VISUALIZATION_AVAILABLE = False

# Global console for rich output
console = Console(force_terminal=False, color_system="auto")


@click.group()
@click.version_option()
def main():
    """
    ParquetFrame CLI - A powerful tool for working with data files.

    Supports multiple file formats (CSV, JSON, Parquet, ORC) with automatic
    format detection. Intelligently switches between pandas and Dask backends
    based on file size and provides both batch processing and interactive modes.

    Examples:
        pframe run sales.csv --query "amount > 100" --head 10
        pframe run events.jsonl --format json --describe
        pframe interactive --path ./data_lake/
        pframe info data.parquet
        pframe info logs.orc --format orc
    """
    pass


@main.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option(
    "--query", "-q", help="Pandas/Dask query to filter data (e.g., 'age > 30')"
)
@click.option(
    "--columns", "-c", help="Comma-separated columns to select (e.g., 'name,age,city')"
)
@click.option("--head", "-h", type=int, help="Display first N rows")
@click.option("--tail", "-t", type=int, help="Display last N rows")
@click.option("--sample", "-s", type=int, help="Display N random sample rows")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Save result to output file (supports .parquet, .csv, .json)",
)
@click.option(
    "--save-script", "-S", type=click.Path(), help="Save session as Python script"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["csv", "json", "parquet", "orc"]),
    help="Manually specify file format (overrides auto-detection)",
)
@click.option(
    "--threshold",
    type=float,
    default=100,
    help="File size threshold in MB for Dask vs pandas (default: 100)",
)
@click.option("--force-dask", is_flag=True, help="Force use of Dask backend")
@click.option("--force-pandas", is_flag=True, help="Force use of pandas backend")
@click.option("--describe", is_flag=True, help="Show statistical description of data")
@click.option("--info", is_flag=True, help="Show data info (dtypes, null counts, etc.)")
def run(
    filepath,
    query,
    columns,
    head,
    tail,
    sample,
    output,
    save_script,
    format,
    threshold,
    force_dask,
    force_pandas,
    describe,
    info,
):
    """
    Run operations on data files in batch mode.

    This command processes files in various formats (CSV, JSON, Parquet, ORC)
    with automatic format detection and intelligent backend selection.
    Optionally saves results and/or generates Python scripts.

    Supported formats:
        - CSV (.csv, .tsv) - Comma or tab-separated values
        - JSON (.json, .jsonl, .ndjson) - Regular or JSON Lines format
        - Parquet (.parquet, .pqt) - Columnar format (optimal performance)
        - ORC (.orc) - Optimized Row Columnar format

    Examples:
        pframe run sales.csv --query "amount > 100" --columns "name,total" --head 10
        pframe run events.jsonl --force-dask --describe
        pframe run data.parquet --output filtered.csv --save-script process.py
        pframe run data.txt --format csv --query "status == 'active'"
    """
    # Determine backend selection
    islazy = None
    if force_dask and force_pandas:
        click.echo("Error: Cannot use both --force-dask and --force-pandas", err=True)
        sys.exit(1)
    elif force_dask:
        islazy = True
    elif force_pandas:
        islazy = False

    # Enable session tracking for script generation
    ParquetFrame._current_session_tracking = save_script is not None

    try:
        # Read the file with format detection
        if format:
            console.print(
                f"[bold blue]Reading file:[/bold blue] {filepath} (format: {format})"
            )
            pf = ParquetFrame.read(
                filepath, format=format, threshold_mb=threshold, islazy=islazy
            )
        else:
            console.print(
                f"[bold blue]Reading file:[/bold blue] {filepath} (auto-detecting format)"
            )
            pf = ParquetFrame.read(filepath, threshold_mb=threshold, islazy=islazy)

        # Apply query filter
        if query:
            console.print(f"[bold yellow]Applying query:[/bold yellow] {query}")
            pf = pf.query(query)

        # Select columns
        if columns:
            cols = [col.strip() for col in columns.split(",")]
            console.print(
                f"[bold yellow]Selecting columns:[/bold yellow] {', '.join(cols)}"
            )
            pf = pf[cols]

        # Show info if requested
        if info:
            console.print("\n[bold green]Data Info:[/bold green]")
            if pf.islazy:
                # For Dask, show basic info
                console.print("Backend: Dask DataFrame")
                console.print(f"Columns: {list(pf.columns)}")
                console.print(f"Partitions: {pf._df.npartitions}")
            else:
                # For pandas, show detailed info
                pf.info()

        # Show description if requested
        if describe:
            console.print("\n[bold green]Statistical Description:[/bold green]")
            desc = pf.describe()
            if pf.islazy:
                desc = desc.compute()
            _display_dataframe_as_table(desc, "Statistical Description")

        # Apply data limitation operations that affect final output
        if head:
            pf = pf.head(head)
            console.print(f"\n[bold green]First {head} rows:[/bold green]")
            sample_data = pf
            # Check if sample_data is a ParquetFrame or DataFrame and handle accordingly
            if hasattr(sample_data, "islazy") and sample_data.islazy:
                sample_data = sample_data._df.compute()
            elif hasattr(sample_data, "_df") and hasattr(sample_data._df, "compute"):
                sample_data = sample_data._df.compute()
            elif hasattr(sample_data, "compute"):
                sample_data = sample_data.compute()
            elif hasattr(sample_data, "_df"):
                sample_data = sample_data._df
            _display_dataframe_as_table(sample_data, f"First {head} Rows")

        elif tail:
            pf = pf.tail(tail)
            console.print(f"\n[bold green]Last {tail} rows:[/bold green]")
            sample_data = pf
            if hasattr(sample_data, "islazy") and sample_data.islazy:
                sample_data = sample_data._df.compute()
            elif hasattr(sample_data, "_df") and hasattr(sample_data._df, "compute"):
                sample_data = sample_data._df.compute()
            elif hasattr(sample_data, "compute"):
                sample_data = sample_data.compute()
            elif hasattr(sample_data, "_df"):
                sample_data = sample_data._df
            _display_dataframe_as_table(sample_data, f"Last {tail} Rows")

        elif sample:
            pf = pf.sample(sample)
            console.print(f"\n[bold green]Random sample of {sample} rows:[/bold green]")
            sample_data = pf
            if hasattr(sample_data, "islazy") and sample_data.islazy:
                sample_data = sample_data._df.compute()
            elif hasattr(sample_data, "_df") and hasattr(sample_data._df, "compute"):
                sample_data = sample_data._df.compute()
            elif hasattr(sample_data, "compute"):
                sample_data = sample_data.compute()
            elif hasattr(sample_data, "_df"):
                sample_data = sample_data._df
            _display_dataframe_as_table(sample_data, f"Random Sample ({sample} rows)")

        # Default: show first 5 rows if no specific display was requested
        elif not info and not describe:
            console.print("\n[bold green]Preview (first 5 rows):[/bold green]")
            sample_data = pf.head(5)
            if hasattr(sample_data, "islazy") and sample_data.islazy:
                sample_data = sample_data._df.compute()
            elif hasattr(sample_data, "_df") and hasattr(sample_data._df, "compute"):
                sample_data = sample_data._df.compute()
            elif hasattr(sample_data, "compute"):
                sample_data = sample_data.compute()
            elif hasattr(sample_data, "_df"):
                sample_data = sample_data._df
            _display_dataframe_as_table(sample_data, "Preview")

        # Save output if requested
        if output:
            console.print(f"\nSaving to: {output}", style="bold blue")
            pf.save(output, save_script=save_script)
        elif save_script and pf._track_history:
            # Save script even if no output file
            pf._save_history_script(save_script)

        console.print(
            "\n[bold green][SUCCESS] Operation completed successfully![/bold green]"
        )

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@main.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option(
    "--format",
    "-f",
    type=click.Choice(["csv", "json", "parquet", "orc"]),
    help="Manually specify file format (overrides auto-detection)",
)
def info(filepath, format):
    """
    Display detailed information about a data file.

    Shows file size, format, column information, data types, and basic statistics.
    Supports CSV, JSON, Parquet, and ORC formats with automatic detection.

    Examples:
        pframe info sales.csv
        pframe info events.jsonl
        pframe info data.parquet
        pframe info logs.orc
        pframe info data.txt --format csv
    """
    try:
        # Get file info
        file_path = Path(filepath)
        file_size = file_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)

        console.print(f"\n[bold blue]File Information:[/bold blue] {filepath}")

        # Try to read the file to get format and schema information
        try:
            if format:
                console.print(f"[dim]Using specified format: {format}[/dim]")
                pf = ParquetFrame.read(
                    filepath, format=format, threshold_mb=1000
                )  # Force pandas for info
            else:
                console.print("[dim]Auto-detecting file format...[/dim]")
                pf = ParquetFrame.read(
                    filepath, threshold_mb=1000, islazy=False
                )  # Force pandas for info

            # Detect format from our core functionality
            from .core import detect_format

            detected_format = detect_format(filepath, format)

            # Create info table
            info_table = Table(title="File Details")
            info_table.add_column("Property", style="cyan", no_wrap=True)
            info_table.add_column("Value", style="white")

            info_table.add_row("File Path", str(file_path.absolute()))
            info_table.add_row(
                "File Size", f"{file_size:,} bytes ({file_size_mb:.2f} MB)"
            )
            info_table.add_row("Detected Format", detected_format.value.upper())

            # Determine backend used and recommended
            backend_used = "Dask (lazy)" if pf.islazy else "pandas (eager)"
            backend_recommended = (
                "Dask (lazy)" if file_size_mb >= 100 else "pandas (eager)"
            )
            info_table.add_row("Backend Used", backend_used)
            info_table.add_row("Recommended Backend", backend_recommended)

            # Data shape information
            info_table.add_row("Rows", f"{len(pf):,}")
            info_table.add_row("Columns", str(len(pf.columns)))

            console.print(info_table)

            # Show schema information
            console.print("\n[bold green]Data Schema:[/bold green]")
            schema_table = Table()
            schema_table.add_column("Column", style="cyan")
            schema_table.add_column("Type", style="yellow")
            schema_table.add_column("Non-Null Count", style="white")

            # Get DataFrame for analysis
            df = pf._df if not pf.islazy else pf._df.compute()

            for col in df.columns:
                dtype = str(df[col].dtype)
                non_null_count = f"{df[col].count():,}"
                schema_table.add_row(col, dtype, non_null_count)

            console.print(schema_table)

            # Show sample data
            console.print("\n[bold green]Sample Data (first 3 rows):[/bold green]")
            sample_data = df.head(3)
            _display_dataframe_as_table(sample_data, "Sample")

            # Basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) > 0:
                console.print("\n[bold green]Numeric Column Statistics:[/bold green]")
                stats = df[numeric_cols].describe()
                _display_dataframe_as_table(stats, "Statistics")

        except Exception as e:
            console.print(f"[yellow]Could not analyze file content: {e}[/yellow]")

            # Fall back to basic file info
            info_table = Table(title="Basic File Details")
            info_table.add_column("Property", style="cyan", no_wrap=True)
            info_table.add_column("Value", style="white")

            info_table.add_row("File Path", str(file_path.absolute()))
            info_table.add_row(
                "File Size", f"{file_size:,} bytes ({file_size_mb:.2f} MB)"
            )
            info_table.add_row("File Extension", file_path.suffix or "(none)")

            # Try to detect format from extension
            try:
                from .core import detect_format

                detected_format = detect_format(filepath, format)
                info_table.add_row("Likely Format", detected_format.value.upper())
            except Exception:
                info_table.add_row("Format", "Unknown")
                info_table.add_row("Format", "Unknown")

            console.print(info_table)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@main.command()
@click.option(
    "--output", "-o", type=click.Path(), help="Save benchmark results to JSON file"
)
@click.option(
    "--quiet", "-q", is_flag=True, help="Run benchmark in quiet mode (less output)"
)
@click.option(
    "--operations",
    help="Comma-separated list of operations to benchmark (groupby,filter,sort,aggregation,join)",
)
@click.option(
    "--file-sizes",
    help="Comma-separated list of test file sizes in rows (e.g., '1000,10000,100000')",
)
def benchmark(output, quiet, operations, file_sizes):
    """
    Run performance benchmarks for ParquetFrame operations.

    This command runs comprehensive performance tests comparing pandas
    and Dask backends across different file sizes and operations.

    Examples:
        pframe benchmark
        pframe benchmark --output results.json --quiet
        pframe benchmark --operations "groupby,filter,sort"
        pframe benchmark --file-sizes "1000,50000,200000"
    """
    if not BENCHMARK_AVAILABLE:
        console.print(
            "[bold red]Error:[/bold red] Benchmark functionality requires additional dependencies."
        )
        console.print("Please install with: pip install parquetframe[cli] psutil")
        sys.exit(1)

    # Parse operations if provided
    ops_list = None
    if operations:
        ops_list = [op.strip() for op in operations.split(",")]
        valid_ops = {"groupby", "filter", "sort", "aggregation", "join"}
        invalid_ops = set(ops_list) - valid_ops
        if invalid_ops:
            console.print(
                f"[bold red]Error:[/bold red] Invalid operations: {', '.join(invalid_ops)}"
            )
            console.print(f"Valid operations: {', '.join(sorted(valid_ops))}")
            sys.exit(1)

    # Parse file sizes if provided
    file_sizes_list = None
    if file_sizes:
        try:
            sizes = [int(size.strip()) for size in file_sizes.split(",")]
            file_sizes_list = [(size, f"{size:,} rows") for size in sizes]
        except ValueError:
            console.print(
                "[bold red]Error:[/bold red] Invalid file sizes. Use comma-separated integers."
            )
            sys.exit(1)

    try:
        verbose = not quiet

        if verbose:
            console.print(
                "[BENCHMARK] [bold green]Starting ParquetFrame Performance Benchmark[/bold green]"
            )
            console.print("This may take several minutes...\n")

        # Create custom benchmark if needed
        if ops_list or file_sizes_list:
            benchmark_obj = PerformanceBenchmark(verbose=verbose)
            results = []

            # Run read operations benchmark
            if file_sizes_list:
                read_results = benchmark_obj.benchmark_read_operations(file_sizes_list)
                results.extend(read_results)
            else:
                read_results = benchmark_obj.benchmark_read_operations()
                results.extend(read_results)

            # Run operations benchmark
            if ops_list:
                op_results = benchmark_obj.benchmark_operations(ops_list)
                results.extend(op_results)
            else:
                op_results = benchmark_obj.benchmark_operations()
                results.extend(op_results)

            # Run threshold analysis
            threshold_results = benchmark_obj.benchmark_threshold_sensitivity()
            results.extend(threshold_results)

            if verbose:
                benchmark_obj.generate_report()

            # Compile custom results
            all_results = {
                "read_operations": [r.__dict__ for r in read_results],
                "data_operations": [r.__dict__ for r in op_results],
                "threshold_analysis": [r.__dict__ for r in threshold_results],
                "summary": {
                    "total_benchmarks": len(results),
                    "successful_benchmarks": sum(1 for r in results if r.success),
                    "average_execution_time": (
                        sum(r.execution_time for r in results) / len(results)
                        if results
                        else 0
                    ),
                    "average_memory_usage": (
                        sum(r.memory_peak for r in results) / len(results)
                        if results
                        else 0
                    ),
                },
            }
        else:
            # Run comprehensive benchmark
            all_results = run_comprehensive_benchmark(output_file=None, verbose=verbose)

        # Save results if requested
        if output:
            import json

            with open(output, "w") as f:
                json.dump(all_results, f, indent=2, default=str)
            if verbose:
                console.print(
                    f"\n[RESULTS] [bold blue]Results saved to:[/bold blue] {output}"
                )

        if verbose:
            console.print(
                "\n[bold green][SUCCESS] Benchmark completed successfully![/bold green]"
            )

    except KeyboardInterrupt:
        console.print("\n[yellow]Benchmark interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error during benchmark:[/bold red] {e}")
        if verbose:
            import traceback

            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@main.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option(
    "--column",
    "-c",
    help="Specific column to analyze (if not specified, analyzes all numeric columns)",
)
@click.option(
    "--method",
    type=click.Choice(["pearson", "spearman", "kendall"]),
    default="pearson",
    help="Correlation method for correlation matrix",
)
@click.option(
    "--outlier-method",
    type=click.Choice(["iqr", "zscore"]),
    default="iqr",
    help="Method for outlier detection",
)
@click.option(
    "--zscore-threshold",
    type=float,
    default=3.0,
    help="Z-score threshold for outlier detection",
)
@click.option(
    "--iqr-multiplier",
    type=float,
    default=1.5,
    help="IQR multiplier for outlier detection",
)
@click.option(
    "--correlation-test",
    nargs=2,
    help="Test correlation between two columns (e.g., --correlation-test col1 col2)",
)
@click.option(
    "--normality-test",
    help="Test normality of specified column",
)
@click.option(
    "--linear-regression",
    nargs=2,
    help="Perform linear regression (e.g., --linear-regression x_col y_col)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["csv", "json", "parquet", "orc"]),
    help="Manually specify file format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Save analysis results to file (JSON format)",
)
@click.option(
    "--threshold",
    type=float,
    default=100,
    help="File size threshold in MB for backend selection",
)
def analyze(
    filepath,
    column,
    method,
    outlier_method,
    zscore_threshold,
    iqr_multiplier,
    correlation_test,
    normality_test,
    linear_regression,
    format,
    output,
    threshold,
):
    """
    Perform statistical analysis on data files.

    This command provides comprehensive statistical analysis including
    distribution summaries, correlation analysis, outlier detection,
    and statistical testing.

    Examples:
        pframe analyze data.csv --column sales_amount
        pframe analyze data.parquet --correlation-test price demand
        pframe analyze data.json --outlier-method zscore --zscore-threshold 2.5
        pframe analyze data.csv --normality-test revenue --output analysis.json
        pframe analyze data.parquet --linear-regression advertising sales
    """
    try:
        # Read the file
        console.print(f"[bold blue]Loading file:[/bold blue] {filepath}")
        if format:
            pf = ParquetFrame.read(filepath, format=format, threshold_mb=threshold)
        else:
            pf = ParquetFrame.read(filepath, threshold_mb=threshold)

        results = {}

        # Basic distribution analysis
        if column:
            console.print(
                f"[bold green]Distribution Analysis for column '{column}':[/bold green]"
            )
            dist_summary = pf.stats.distribution_summary(column)
            results["distribution_summary"] = {column: dist_summary}

            # Display key statistics
            key_stats = [
                ("Count", dist_summary["count"]),
                ("Mean", f"{dist_summary['mean']:.4f}"),
                ("Median", f"{dist_summary['median']:.4f}"),
                ("Std Dev", f"{dist_summary['std']:.4f}"),
                ("Skewness", f"{dist_summary['skewness']:.4f}"),
                ("Kurtosis", f"{dist_summary['kurtosis']:.4f}"),
                ("Distribution Shape", dist_summary["distribution_shape"]),
                (
                    "Outliers (IQR)",
                    f"{dist_summary['outliers_iqr_count']} ({dist_summary['outliers_iqr_percent']:.2f}%)",
                ),
                (
                    "Outliers (Z-score)",
                    f"{dist_summary['outliers_zscore_count']} ({dist_summary['outliers_zscore_percent']:.2f}%)",
                ),
            ]

            stats_table = Table(title=f"Distribution Statistics - {column}")
            stats_table.add_column("Statistic", style="cyan", no_wrap=True)
            stats_table.add_column("Value", style="white")

            for stat_name, stat_value in key_stats:
                stats_table.add_row(stat_name, str(stat_value))

            console.print(stats_table)

        else:
            # Analyze all numeric columns
            console.print("[bold green]Extended Statistical Summary:[/bold green]")
            extended_stats = pf.stats.describe_extended()
            results["extended_statistics"] = extended_stats.to_dict()

            # Display correlation matrix
            console.print(
                f"\n[bold green]Correlation Matrix ({method.title()}):[/bold green]"
            )
            corr_matrix = pf.stats.corr_matrix(method=method)
            results["correlation_matrix"] = corr_matrix.to_dict()
            _display_dataframe_as_table(
                corr_matrix, f"Correlation Matrix - {method.title()}"
            )

        # Outlier detection
        if column:
            console.print(
                f"\n[bold green]Outlier Detection ({outlier_method.upper()}):[/bold green]"
            )
            kwargs = {}
            if outlier_method == "zscore":
                kwargs["threshold"] = zscore_threshold
            elif outlier_method == "iqr":
                kwargs["multiplier"] = iqr_multiplier

            outliers_pf = pf.stats.detect_outliers(
                column, method=outlier_method, **kwargs
            )
            outlier_col = f"{column}_outlier_{outlier_method}"
            outlier_count = outliers_pf.pandas_df[outlier_col].sum()
            total_count = len(outliers_pf.pandas_df)

            console.print(
                f"Found {outlier_count} outliers out of {total_count} records ({outlier_count/total_count*100:.2f}%)"
            )
            results["outlier_detection"] = {
                "method": outlier_method,
                "column": column,
                "outlier_count": int(outlier_count),
                "total_count": int(total_count),
                "outlier_percentage": float(outlier_count / total_count * 100),
            }

        # Correlation test
        if correlation_test:
            col1, col2 = correlation_test
            console.print(
                f"\n[bold green]Correlation Test: {col1} vs {col2}:[/bold green]"
            )
            corr_result = pf.stats.correlation_test(col1, col2)
            results["correlation_test"] = corr_result

            # Display results
            if "note" not in corr_result:  # Full scipy results
                pearson_r = corr_result["pearson"]["correlation"]
                pearson_p = corr_result["pearson"]["p_value"]
                spearman_r = corr_result["spearman"]["correlation"]
                spearman_p = corr_result["spearman"]["p_value"]

                console.print(
                    f"Pearson: r={pearson_r:.4f}, p-value={pearson_p:.4f} ({'significant' if pearson_p < 0.05 else 'not significant'})"
                )
                console.print(
                    f"Spearman: r={spearman_r:.4f}, p-value={spearman_p:.4f} ({'significant' if spearman_p < 0.05 else 'not significant'})"
                )
            else:
                console.print(
                    f"Correlation: r={corr_result['pearson_correlation']:.4f}"
                )
                console.print(corr_result["note"])

        # Normality test
        if normality_test:
            console.print(
                f"\n[bold green]Normality Test for '{normality_test}':[/bold green]"
            )
            normality_result = pf.stats.normality_test(normality_test)
            results["normality_test"] = normality_result

            if "note" not in normality_result:  # Full scipy results
                console.print(f"Sample size: {normality_result['sample_size']}")

                if "shapiro_wilk" in normality_result:
                    sw = normality_result["shapiro_wilk"]
                    console.print(
                        f"Shapiro-Wilk: statistic={sw['statistic']:.4f}, p-value={sw['p_value']:.4f} ({'normal' if sw['is_normal'] else 'not normal'})"
                    )

                ks = normality_result["kolmogorov_smirnov"]
                console.print(
                    f"Kolmogorov-Smirnov: statistic={ks['statistic']:.4f}, p-value={ks['p_value']:.4f} ({'normal' if ks['is_normal'] else 'not normal'})"
                )

                dag = normality_result["dagostino"]
                console.print(
                    f"D'Agostino: statistic={dag['statistic']:.4f}, p-value={dag['p_value']:.4f} ({'normal' if dag['is_normal'] else 'not normal'})"
                )
            else:
                console.print(f"Skewness: {normality_result['skewness']:.4f}")
                console.print(f"Kurtosis: {normality_result['kurtosis']:.4f}")
                console.print(
                    f"Approximately normal: {normality_result['is_approximately_normal']}"
                )
                console.print(normality_result["note"])

        # Linear regression
        if linear_regression:
            x_col, y_col = linear_regression
            console.print(
                f"\n[bold green]Linear Regression: {x_col} -> {y_col}:[/bold green]"
            )
            regression_result = pf.stats.linear_regression(x_col, y_col)
            results["linear_regression"] = regression_result

            if "note" not in regression_result:  # Full scipy results
                console.print(f"Equation: {regression_result['equation']}")
                console.print(f"R²: {regression_result['r_squared']:.4f}")
                console.print(
                    f"P-value: {regression_result['p_value']:.4f} ({'significant' if regression_result['significant'] else 'not significant'})"
                )
                console.print(f"RMSE: {regression_result['rmse']:.4f}")
            else:
                console.print(f"Correlation: {regression_result['correlation']:.4f}")
                console.print(regression_result["note"])

        # Save results if requested
        if output:
            import json

            with open(output, "w") as f:
                json.dump(results, f, indent=2, default=str)
            console.print(
                f"\n[bold blue]Analysis results saved to:[/bold blue] {output}"
            )

        console.print(
            "\n[bold green][SUCCESS] Statistical analysis completed![/bold green]"
        )

    except Exception as e:
        console.print(f"[bold red]Error during analysis:[/bold red] {e}")
        sys.exit(1)


@main.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option(
    "--datetime-col",
    help="Specify datetime column (auto-detected if not provided)",
)
@click.option(
    "--resample",
    help="Resampling frequency (e.g., '1H', '1D', '1W') - requires --agg",
)
@click.option(
    "--agg",
    type=click.Choice(["mean", "sum", "max", "min", "std", "count"]),
    help="Aggregation function for resampling",
)
@click.option(
    "--rolling",
    help="Rolling window size (e.g., '7', '30D') - requires --agg",
)
@click.option(
    "--shift",
    type=int,
    help="Shift time series by N periods (positive=forward, negative=backward)",
)
@click.option(
    "--between-time",
    nargs=2,
    help="Filter between times (e.g., --between-time 09:00 17:00)",
)
@click.option(
    "--at-time",
    help="Filter at specific time (e.g., --at-time 12:00)",
)
@click.option(
    "--detect-datetime",
    is_flag=True,
    help="Show detected datetime columns and exit",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["csv", "json", "parquet", "orc"]),
    help="Manually specify file format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Save results to output file",
)
@click.option(
    "--threshold",
    type=float,
    default=100,
    help="File size threshold in MB for backend selection",
)
def timeseries(
    filepath,
    datetime_col,
    resample,
    agg,
    rolling,
    shift,
    between_time,
    at_time,
    detect_datetime,
    format,
    output,
    threshold,
):
    """
    Perform time-series analysis on data files.

    This command provides time-series specific operations including
    resampling, rolling windows, time-based filtering, and datetime detection.

    Examples:
        pframe timeseries data.csv --detect-datetime
        pframe timeseries data.parquet --resample 1H --agg mean
        pframe timeseries data.csv --rolling 7 --agg mean --datetime-col timestamp
        pframe timeseries data.json --between-time 09:00 17:00 --output filtered.csv
        pframe timeseries data.parquet --shift 1 --output lagged.parquet
    """
    try:
        # Read the file
        console.print(f"[bold blue]Loading file:[/bold blue] {filepath}")
        if format:
            pf = ParquetFrame.read(filepath, format=format, threshold_mb=threshold)
        else:
            pf = ParquetFrame.read(filepath, threshold_mb=threshold)

        # Detect datetime columns if requested
        if detect_datetime:
            console.print("[bold green]Detecting datetime columns:[/bold green]")
            detected_cols = pf.ts.detect_datetime_columns()

            if detected_cols:
                console.print(f"Found {len(detected_cols)} datetime column(s):")
                for col in detected_cols:
                    console.print(f"  • {col}")
            else:
                console.print("No datetime columns detected.")
            return

        # Validate operations
        if (resample or rolling) and not agg:
            console.print(
                "[bold red]Error:[/bold red] --resample and --rolling require --agg option"
            )
            sys.exit(1)

        result_pf = pf
        operation_description = []

        # Apply resampling
        if resample and agg:
            console.print(
                f"[bold green]Resampling to {resample} with {agg} aggregation:[/bold green]"
            )
            resampler = result_pf.ts.resample(resample, datetime_col=datetime_col)

            if agg == "mean":
                result_pf = resampler.mean()
            elif agg == "sum":
                result_pf = resampler.sum()
            elif agg == "max":
                result_pf = resampler.max()
            elif agg == "min":
                result_pf = resampler.min()
            elif agg == "std":
                result_pf = resampler.std()
            elif agg == "count":
                result_pf = resampler.count()

            operation_description.append(f"resampled to {resample} ({agg})")

        # Apply rolling window
        elif rolling and agg:
            console.print(
                f"[bold green]Applying rolling window {rolling} with {agg} aggregation:[/bold green]"
            )
            roller = result_pf.ts.rolling(rolling, datetime_col=datetime_col)

            if agg == "mean":
                result_pf = roller.mean()
            elif agg == "sum":
                result_pf = roller.sum()
            elif agg == "max":
                result_pf = roller.max()
            elif agg == "min":
                result_pf = roller.min()
            elif agg == "std":
                result_pf = roller.std()

            operation_description.append(f"rolling {rolling} ({agg})")

        # Apply shift
        if shift:
            console.print(
                f"[bold green]Shifting time series by {shift} periods:[/bold green]"
            )
            result_pf = result_pf.ts.shift(shift)
            operation_description.append(f"shifted by {shift} periods")

        # Apply time filtering
        if between_time:
            start_time, end_time = between_time
            console.print(
                f"[bold green]Filtering between {start_time} and {end_time}:[/bold green]"
            )
            result_pf = result_pf.ts.between_time(
                start_time, end_time, datetime_col=datetime_col
            )
            operation_description.append(f"filtered between {start_time}-{end_time}")

        if at_time:
            console.print(f"[bold green]Filtering at time {at_time}:[/bold green]")
            result_pf = result_pf.ts.at_time(at_time, datetime_col=datetime_col)
            operation_description.append(f"filtered at {at_time}")

        # Show results
        if operation_description:
            console.print(
                f"\n[bold blue]Applied operations:[/bold blue] {', '.join(operation_description)}"
            )

            # Display sample of results
            sample_df = result_pf.pandas_df.head(10)
            _display_dataframe_as_table(
                sample_df, "Time Series Results (first 10 rows)"
            )

            console.print(f"Total rows after operations: {len(result_pf.pandas_df)}")

        # Save results if requested
        if output:
            result_pf.save(output)
            console.print(f"\n[bold blue]Results saved to:[/bold blue] {output}")

        console.print(
            "\n[bold green][SUCCESS] Time-series analysis completed![/bold green]"
        )

    except Exception as e:
        console.print(f"[bold red]Error during time-series analysis:[/bold red] {e}")
        sys.exit(1)


@main.command()
@click.argument("workflow_file", type=click.Path(exists=True), required=False)
@click.option(
    "--validate", "-v", is_flag=True, help="Validate workflow file without executing"
)
@click.option(
    "--variables",
    "-V",
    help="Set workflow variables as key=value pairs (e.g., 'input_dir=data,output_dir=results')",
)
@click.option(
    "--list-steps", is_flag=True, help="List all available workflow step types"
)
@click.option(
    "--create-example",
    type=click.Path(),
    help="Create an example workflow file at the specified path",
)
@click.option("--quiet", "-q", is_flag=True, help="Run in quiet mode (minimal output)")
@click.option(
    "--visualize",
    type=click.Choice(["graphviz", "networkx", "mermaid"]),
    help="Generate workflow visualization (requires graphviz, networkx, or mermaid)",
)
@click.option(
    "--viz-output",
    type=click.Path(),
    help="Output path for visualization (e.g., workflow.svg, workflow.png)",
)
@click.option(
    "--viz-format",
    type=click.Choice(["svg", "png", "pdf", "dot"]),
    default="svg",
    help="Visualization output format (default: svg)",
)
def workflow(
    workflow_file,
    validate,
    variables,
    list_steps,
    create_example,
    quiet,
    visualize,
    viz_output,
    viz_format,
):
    """
    Execute or manage YAML workflow files.

    Workflows allow you to define complex data processing pipelines
    in YAML format with multiple steps including reading, filtering,
    transforming, aggregating, and saving data.

    Examples:
        pframe workflow my_pipeline.yml
        pframe workflow my_pipeline.yml --variables "input_dir=data,min_age=21"
        pframe workflow --validate my_pipeline.yml
        pframe workflow --create-example example.yml
        pframe workflow --list-steps
        pframe workflow my_pipeline.yml --visualize graphviz --viz-output dag.svg
    """
    if not WORKFLOW_AVAILABLE:
        console.print(
            "[bold red]Error:[/bold red] Workflow functionality requires additional dependencies."
        )
        console.print("Please install with: pip install parquetframe[cli]")
        sys.exit(1)

    # Handle list-steps option
    if list_steps:
        from .workflows import STEP_REGISTRY

        console.print("\n[STEPS] [bold blue]Available Workflow Steps[/bold blue]")

        step_descriptions = {
            "read": "Read data from parquet files",
            "filter": "Filter data using queries",
            "select": "Select specific columns",
            "groupby": "Perform group by operations and aggregations",
            "save": "Save data to parquet files",
            "transform": "Apply custom transformations",
        }

        for step_type in sorted(STEP_REGISTRY.keys()):
            desc = step_descriptions.get(step_type, "Custom workflow step")
            console.print(f"  • [cyan]{step_type:10}[/cyan] - {desc}")
        return

    # Handle create-example option
    if create_example:
        try:
            example_workflow = create_example_workflow()
            with open(create_example, "w") as f:
                yaml.dump(example_workflow, f, indent=2, default_flow_style=False)
            console.print(
                f"[SUCCESS] [bold green]Example workflow created at:[/bold green] {create_example}"
            )
            console.print("\n[TIP] Edit the workflow file and run with:")
            console.print(f"   pframe workflow {create_example}")
        except Exception as e:
            console.print(f"[bold red]Error creating example workflow:[/bold red] {e}")
            sys.exit(1)
        return

    # Workflow file is required for validation and execution
    if not workflow_file:
        console.print("[bold red]Error:[/bold red] Workflow file is required.")
        console.print("\n[TIP] Try:")
        console.print(
            "  pframe workflow --create-example my_workflow.yml  # Create an example"
        )
        console.print(
            "  pframe workflow --list-steps                     # List available steps"
        )
        sys.exit(1)

    # Parse variables
    workflow_variables = {}
    if variables:
        try:
            for pair in variables.split(","):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    # Try to convert to appropriate type
                    try:
                        # Try int first
                        workflow_variables[key.strip()] = int(value.strip())
                    except ValueError:
                        try:
                            # Try float
                            workflow_variables[key.strip()] = float(value.strip())
                        except ValueError:
                            # Keep as string
                            workflow_variables[key.strip()] = value.strip()
                else:
                    console.print(
                        f"[yellow]Warning:[/yellow] Invalid variable format: {pair}. Use key=value"
                    )
        except Exception as e:
            console.print(f"[bold red]Error parsing variables:[/bold red] {e}")
            sys.exit(1)

    # Create workflow engine
    engine = WorkflowEngine(verbose=not quiet)

    # Load workflow for visualization or validation/execution
    workflow = engine.load_workflow(workflow_file)

    # Handle visualization if requested
    if visualize:
        if not WORKFLOW_VISUALIZATION_AVAILABLE:
            console.print(
                "[bold red]Error:[/bold red] Workflow visualization requires additional dependencies."
            )
            console.print(
                "Please install with: pip install networkx graphviz matplotlib"
            )
            sys.exit(1)

        try:
            visualizer = WorkflowVisualizer()

            if visualize == "mermaid":
                # Generate Mermaid diagram
                mermaid_code = visualizer.export_to_mermaid(workflow)

                if viz_output:
                    with open(viz_output, "w") as f:
                        f.write(mermaid_code)
                    console.print(
                        f"[SUCCESS] [bold green]Mermaid diagram saved to:[/bold green] {viz_output}"
                    )
                else:
                    console.print("\n[MERMAID] Workflow DAG in Mermaid format:")
                    console.print(mermaid_code)

            elif visualize == "graphviz":
                # Generate Graphviz visualization
                output_path = visualizer.visualize_with_graphviz(
                    workflow, output_path=viz_output, format=viz_format
                )

                if output_path:
                    console.print(
                        f"[SUCCESS] [bold green]Graphviz visualization saved to:[/bold green] {output_path}"
                    )
                else:
                    console.print("\n[GRAPHVIZ] Workflow DAG source code:")
                    console.print(output_path)

            elif visualize == "networkx":
                # Generate NetworkX visualization
                output_path = visualizer.visualize_with_networkx(
                    workflow, output_path=viz_output or "workflow_dag.png"
                )

                if output_path:
                    console.print(
                        f"[SUCCESS] [bold green]NetworkX visualization saved to:[/bold green] {output_path}"
                    )
                else:
                    console.print("[INFO] NetworkX visualization displayed in window")

            # Show DAG statistics
            if not quiet:
                stats = visualizer.get_dag_statistics(workflow)
                console.print("\n[STATS] Workflow DAG Statistics:")
                console.print(f"  • Total Steps: {stats.get('total_steps', 0)}")
                console.print(f"  • Dependencies: {stats.get('total_dependencies', 0)}")
                console.print(f"  • Is Valid DAG: {stats.get('is_dag', False)}")
                console.print(f"  • Longest Path: {stats.get('longest_path', 0)}")
                if stats.get("potential_issues"):
                    console.print(f"  • Issues: {', '.join(stats['potential_issues'])}")

            return

        except Exception as e:
            console.print(f"[bold red]Visualization error:[/bold red] {e}")
            if not quiet:
                import traceback

                console.print(f"[dim]{traceback.format_exc()}[/dim]")
            sys.exit(1)

    try:
        if validate:
            # Validate workflow
            console.print(
                f"[VALIDATING] [bold blue]Validating workflow:[/bold blue] {workflow_file}"
            )
            errors = engine.validate_workflow(workflow)

            if errors:
                console.print("\n[FAILED] [bold red]Validation failed:[/bold red]")
                for error in errors:
                    console.print(f"  • {error}")
                sys.exit(1)
            else:
                console.print(
                    "\n[SUCCESS] [bold green]Workflow validation passed![/bold green]"
                )

                # Show workflow summary
                steps = workflow.get("steps", [])
                console.print("\n[SUMMARY] Workflow summary:")
                console.print(f"  • Name: {workflow.get('name', 'Unnamed workflow')}")
                console.print(
                    f"  • Description: {workflow.get('description', 'No description')}"
                )
                console.print(f"  • Steps: {len(steps)}")

                if workflow_variables:
                    console.print(f"  • Variables: {len(workflow_variables)}")

        else:
            # Execute workflow
            if not quiet:
                console.print(
                    f"[EXECUTING] [bold blue]Executing workflow:[/bold blue] {workflow_file}"
                )
                if workflow_variables:
                    console.print(f"[VARIABLES] Variables: {workflow_variables}")

            engine.run_workflow_file(workflow_file, variables=workflow_variables)

            if not quiet:
                console.print(
                    "\n[SUCCESS] [bold green]Workflow execution completed successfully![/bold green]"
                )

    except WorkflowError as e:
        console.print(f"[bold red]Workflow error:[/bold red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Workflow interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        if not quiet:
            import traceback

            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@main.command()
@click.argument("query", required=False)
@click.option(
    "--file",
    "-f",
    "main_file",
    type=click.Path(exists=True),
    help="Main parquet file to query (available as 'df' in SQL)",
)
@click.option(
    "--join",
    "-j",
    "join_files",
    multiple=True,
    help="Additional files for JOINs in format 'name=path' (e.g., 'customers=customers.parquet')",
)
@click.option(
    "--output", "-o", type=click.Path(), help="Save query results to output file"
)
@click.option("--interactive", "-i", is_flag=True, help="Start interactive SQL mode")
@click.option(
    "--explain", is_flag=True, help="Show query execution plan without running"
)
@click.option(
    "--validate", is_flag=True, help="Validate SQL query syntax without executing"
)
def sql(query, main_file, join_files, output, interactive, explain, validate):
    """
    Execute SQL queries on parquet files using DuckDB.

    The main file is available as 'df' in queries. Additional files can be
    joined using the --join option with name=path format.

    Examples:
        pframe sql "SELECT * FROM df WHERE age > 25" --file data.parquet
        pframe sql "SELECT * FROM df JOIN c ON df.id = c.id" -f orders.parquet -j "c=customers.parquet"
        pframe sql --interactive --file data.parquet
    """
    if not SQL_AVAILABLE:
        console.print("[bold red]Error:[/bold red] SQL functionality requires DuckDB.")
        console.print("Please install with: pip install parquetframe[sql]")
        sys.exit(1)

    # Interactive mode
    if interactive:
        if not main_file:
            console.print(
                "[bold red]Error:[/bold red] --file is required for interactive SQL mode"
            )
            sys.exit(1)

        try:
            # Load main file
            console.print(f"[LOADING] [bold blue]Loading file:[/bold blue] {main_file}")
            main_pf = ParquetFrame.read(main_file)

            # Load join files
            join_pfs = {}
            for join_spec in join_files:
                if "=" not in join_spec:
                    console.print(
                        f"[bold red]Error:[/bold red] Invalid join format: {join_spec}. Use 'name=path'"
                    )
                    sys.exit(1)
                name, path = join_spec.split("=", 1)
                console.print(f"[JOIN] Loading join file: {name} from {path}")
                join_pfs[name.strip()] = ParquetFrame.read(path.strip())

            # Interactive SQL REPL
            console.print(
                "\n[INTERACTIVE] [bold green]Interactive SQL Mode[/bold green]"
            )
            console.print("Available tables:")
            console.print("  • [cyan]df[/cyan] - Main dataset")
            for name in join_pfs.keys():
                console.print(f"  • [cyan]{name}[/cyan] - Join dataset")
            console.print("\nType 'exit' or press Ctrl+D to quit.\n")

            while True:
                try:
                    sql_query = input("SQL> ").strip()
                    if not sql_query:
                        continue
                    if sql_query.lower() in ("exit", "quit"):
                        break

                    # Execute query
                    result = main_pf.sql(sql_query, **join_pfs)
                    _display_dataframe_as_table(result._df, "Query Results")

                except (EOFError, KeyboardInterrupt):
                    console.print("\n[bold blue]Goodbye![/bold blue]")
                    break
                except Exception as e:
                    console.print(f"[bold red]SQL Error:[/bold red] {e}")

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)
        return

    # Non-interactive mode - query is required
    if not query:
        console.print(
            "[bold red]Error:[/bold red] SQL query is required (or use --interactive)"
        )
        console.print("\n[EXAMPLES] Examples:")
        console.print('  pframe sql "SELECT * FROM df LIMIT 10" --file data.parquet')
        console.print("  pframe sql --interactive --file data.parquet")
        sys.exit(1)

    if not main_file:
        console.print("[bold red]Error:[/bold red] --file is required")
        sys.exit(1)

    # Validate query if requested
    if validate:
        if not validate_sql_query(query):
            console.print("[bold red]SQL Validation:[/bold red] Query appears invalid")
            sys.exit(1)
        else:
            console.print(
                "[bold green][SUCCESS] SQL query validation passed[/bold green]"
            )
            return

    try:
        # Load main file
        console.print(
            f"[LOADING] [bold blue]Loading main file:[/bold blue] {main_file}"
        )
        main_pf = ParquetFrame.read(main_file)

        # Load join files
        join_pfs = {}
        for join_spec in join_files:
            if "=" not in join_spec:
                console.print(
                    f"[bold red]Error:[/bold red] Invalid join format: {join_spec}. Use 'name=path'"
                )
                sys.exit(1)
            name, path = join_spec.split("=", 1)
            console.print(
                f"[JOIN] Loading join file: {name.strip()} from {path.strip()}"
            )
            join_pfs[name.strip()] = ParquetFrame.read(path.strip())

        # Show query execution plan if requested
        if explain:
            from .sql import explain_query

            other_dfs = {name: pf._df for name, pf in join_pfs.items()}
            plan = explain_query(main_pf._df, query, other_dfs)
            console.print("\n[bold green]Query Execution Plan:[/bold green]")
            console.print(plan)
            return

        # Execute SQL query
        console.print("\n[EXECUTING] [bold blue]Executing query:[/bold blue]")
        console.print(f"[dim]{query}[/dim]")

        result = main_pf.sql(query, **join_pfs)

        # Display results
        console.print(
            f"\n[RESULTS] [bold green]Query Results:[/bold green] {len(result)} rows"
        )
        _display_dataframe_as_table(result._df, "SQL Results")

        # Save results if requested
        if output:
            console.print(f"\n[SAVING] Saving results to: {output}")
            result.save(output)
            console.print(
                "[bold green][SUCCESS] Results saved successfully![/bold green]"
            )

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        import traceback

        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@main.command()
@click.option("--workflow-name", "-w", help="Filter history by specific workflow name")
@click.option(
    "--limit",
    "-l",
    type=int,
    default=10,
    help="Limit number of records to show (default: 10)",
)
@click.option(
    "--status",
    "-s",
    type=click.Choice(["completed", "failed", "running"]),
    help="Filter by execution status",
)
@click.option(
    "--details", "-d", is_flag=True, help="Show detailed execution information"
)
@click.option("--cleanup", type=int, help="Clean up history files older than N days")
@click.option("--stats", is_flag=True, help="Show aggregate statistics")
def workflow_history(workflow_name, limit, status, details, cleanup, stats):
    """
    View and manage workflow execution history.

    This command allows you to explore .hist files generated by workflow executions,
    view statistics, and manage historical data.

    Examples:
        pframe workflow-history                          # Show recent executions
        pframe workflow-history --workflow-name my_flow # Filter by workflow
        pframe workflow-history --details               # Show detailed info
        pframe workflow-history --stats                 # Show aggregate stats
        pframe workflow-history --cleanup 30            # Clean up old files
    """
    if not WORKFLOW_HISTORY_AVAILABLE:
        console.print(
            "[bold red]Error:[/bold red] Workflow history functionality requires additional dependencies."
        )
        console.print("Please ensure the workflow_history module is available.")
        sys.exit(1)

    try:
        history_manager = WorkflowHistoryManager()

        # Handle cleanup operation
        if cleanup:
            removed_count = history_manager.cleanup_old_records(cleanup)
            console.print(
                f"[SUCCESS] [bold green]Cleaned up {removed_count} history files older than {cleanup} days[/bold green]"
            )
            return

        # Handle stats request
        if stats:
            statistics = history_manager.get_workflow_statistics(workflow_name)

            if "message" in statistics:
                console.print(f"[yellow]{statistics['message']}[/yellow]")
                return

            # Display statistics table
            stats_table = Table(
                title=f"Workflow Statistics{f' - {workflow_name}' if workflow_name else ''}"
            )
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="white")

            stats_table.add_row("Total Executions", str(statistics["total_executions"]))
            stats_table.add_row("Successful", str(statistics["successful_executions"]))
            stats_table.add_row("Failed", str(statistics["failed_executions"]))
            stats_table.add_row("Success Rate", f"{statistics['success_rate']:.1%}")
            stats_table.add_row(
                "Avg Duration", f"{statistics['average_duration_seconds']:.2f}s"
            )
            stats_table.add_row(
                "Total Duration", f"{statistics['total_duration_seconds']:.2f}s"
            )

            console.print(stats_table)
            return

        # Get execution records
        hist_files = history_manager.list_execution_records(workflow_name)[:limit]

        if not hist_files:
            console.print(
                f"[yellow]No execution records found{f' for workflow {workflow_name}' if workflow_name else ''}[/yellow]"
            )
            return

        console.print(
            f"\n[HISTORY] [bold blue]Workflow Execution History{f' - {workflow_name}' if workflow_name else ''}[/bold blue]"
        )

        if details:
            # Show detailed information for each execution
            for hist_file in hist_files:
                try:
                    execution = history_manager.load_execution_record(hist_file)

                    # Skip if status filter doesn't match
                    if status and execution.status != status:
                        continue

                    console.print(f"\n{'=' * 50}")
                    console.print(
                        f"[bold]Execution ID:[/bold] {execution.execution_id}"
                    )
                    console.print(f"[bold]Workflow:[/bold] {execution.workflow_name}")
                    console.print(f"[bold]Status:[/bold] {execution.status}")
                    console.print(f"[bold]Started:[/bold] {execution.start_time}")
                    if execution.duration_seconds:
                        console.print(
                            f"[bold]Duration:[/bold] {execution.duration_seconds:.2f}s"
                        )
                    if execution.peak_memory_usage_mb:
                        console.print(
                            f"[bold]Peak Memory:[/bold] {execution.peak_memory_usage_mb:.1f}MB"
                        )

                    # Show step details
                    if execution.steps:
                        console.print(f"\n[bold]Steps ({len(execution.steps)}):[/bold]")

                        steps_table = Table()
                        steps_table.add_column("Step", style="cyan")
                        steps_table.add_column("Type", style="yellow")
                        steps_table.add_column("Status", style="magenta")
                        steps_table.add_column("Duration", style="green")

                        for step in execution.steps:
                            duration_str = (
                                f"{step.duration_seconds:.2f}s"
                                if step.duration_seconds
                                else "N/A"
                            )
                            steps_table.add_row(
                                step.name, step.step_type, step.status, duration_str
                            )

                        console.print(steps_table)

                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Could not load {hist_file}: {e}[/yellow]"
                    )
                    continue
        else:
            # Show summary table
            history_table = Table(title="Recent Workflow Executions")
            history_table.add_column("Execution ID", style="cyan")
            history_table.add_column("Workflow", style="yellow")
            history_table.add_column("Status", style="magenta")
            history_table.add_column("Started", style="white")
            history_table.add_column("Duration", style="green")
            history_table.add_column("Steps", style="blue")

            for hist_file in hist_files:
                try:
                    summary = history_manager.get_execution_summary(hist_file)

                    # Skip if status filter doesn't match
                    if status and summary["status"] != status:
                        continue

                    duration_str = (
                        f"{summary['duration_seconds']:.2f}s"
                        if summary["duration_seconds"]
                        else "N/A"
                    )
                    started_str = (
                        summary["start_time"].strftime("%Y-%m-%d %H:%M:%S")
                        if summary["start_time"]
                        else "N/A"
                    )

                    history_table.add_row(
                        summary["execution_id"],
                        summary["workflow_name"],
                        summary["status"],
                        started_str,
                        duration_str,
                        str(summary["stats"]["total_steps"]),
                    )

                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Could not load {hist_file}: {e}[/yellow]"
                    )
                    continue

            console.print(history_table)

            if len(hist_files) == limit:
                console.print(
                    f"\n[dim]Showing latest {limit} records. Use --limit to see more.[/dim]"
                )

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        import traceback

        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


@main.command()
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to directory containing parquet files",
)
@click.option(
    "--db-uri",
    "--database",
    "-d",
    help="Database connection URI (e.g., 'postgresql://user:pass@host/db')",
)
@click.option("--no-ai", is_flag=True, help="Disable AI/LLM functionality")
def interactive(path, db_uri, no_ai):
    """
    Start an interactive ParquetFrame session.

    This launches a powerful REPL interface that can connect to either
    parquet file collections or relational databases, with optional
    AI-powered natural language query capabilities.

    Examples:
        pframe interactive --path ./data/parquets/
        pframe interactive --db-uri "postgresql://user:pass@localhost/mydb"
        pframe interactive --path ./sales_data/ --no-ai
    """
    if not INTERACTIVE_AVAILABLE:
        console.print(
            "[bold red]Error:[/bold red] Interactive mode requires additional dependencies."
        )
        console.print("Please install with: pip install parquetframe[ai,cli]")
        sys.exit(1)

    # Validate arguments
    if not path and not db_uri:
        console.print(
            "[bold red]Error:[/bold red] Must specify either --path or --db-uri"
        )
        console.print("\n[EXAMPLES]")
        console.print("  pframe interactive --path ./my_parquet_files/")
        console.print("  pframe interactive --db-uri 'sqlite:///my_database.db'")
        sys.exit(1)

    if path and db_uri:
        console.print(
            "[bold red]Error:[/bold red] Cannot specify both --path and --db-uri"
        )
        sys.exit(1)

    # Start interactive session
    import asyncio

    try:
        asyncio.run(
            start_interactive_session(path=path, db_uri=db_uri, enable_ai=not no_ai)
        )
    except KeyboardInterrupt:
        console.print("\n[bold blue]Interactive session cancelled.[/bold blue]")
    except Exception as e:
        console.print(f"[bold red]Failed to start interactive session:[/bold red] {e}")
        sys.exit(1)


@main.command()
def deps():
    """
    Check dependency status and show installation commands.

    This command shows which optional dependencies are available
    and provides installation commands for missing ones.

    Examples:
        pframe deps
    """
    try:
        # Show dependency status
        status = format_dependency_status()
        console.print(status)

        # Show installation commands for missing dependencies
        deps = check_dependencies()
        missing_deps = [dep for dep, available in deps.items() if not available]

        if missing_deps:
            install_commands = suggest_installation_commands()
            console.print(
                "\n🔧 [bold yellow]Installation Commands for Missing Dependencies:[/bold yellow]"
            )
            for dep in missing_deps:
                if dep in install_commands:
                    console.print(f"  • {dep}: [cyan]{install_commands[dep]}[/cyan]")
        else:
            console.print(
                "\n✅ [bold green]All dependencies are available![/bold green]"
            )

    except Exception as e:
        console.print(f"[bold red]Error checking dependencies:[/bold red] {e}")
        sys.exit(1)


def _display_dataframe_as_table(df: Any, title: str = "DataFrame") -> None:
    """Display a pandas DataFrame as a rich table."""
    if df.empty:
        console.print(f"[yellow]{title} is empty[/yellow]")
        return

    # Limit display size for readability
    display_df = df.head(20) if len(df) > 20 else df

    table = Table(title=title, show_header=True, header_style="bold blue")

    # Add index column if it's not the default range index
    if not isinstance(df.index, __import__("pandas").RangeIndex) or df.index.name:
        table.add_column("Index", style="dim")

    # Add data columns
    for col in display_df.columns:
        table.add_column(str(col), overflow="fold")

    # Add rows
    for idx, row in display_df.iterrows():
        row_data = []

        # Add index value if needed
        if not isinstance(df.index, __import__("pandas").RangeIndex) or df.index.name:
            row_data.append(str(idx))

        # Add column values
        for val in row:
            if __import__("pandas").isna(val):
                row_data.append("[dim]null[/dim]")
            else:
                # Truncate long values
                str_val = str(val)
                if len(str_val) > 50:
                    str_val = str_val[:47] + "..."
                row_data.append(str_val)

        table.add_row(*row_data)

    console.print(table)

    if len(df) > 20:
        console.print(f"[dim]... showing first 20 of {len(df)} rows[/dim]")


if __name__ == "__main__":
    main()
