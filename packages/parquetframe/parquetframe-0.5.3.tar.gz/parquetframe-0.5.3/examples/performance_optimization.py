#!/usr/bin/env python3
"""
Performance Optimization Example for ParquetFrame

This script demonstrates the enhanced performance features including:
1. Intelligent backend switching based on memory pressure and file characteristics
2. Performance benchmarking tools
3. Optimal threshold detection
4. Memory-aware processing
"""

import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# Try to import ParquetFrame components
try:
    from parquetframe import ParquetFrame
    from parquetframe.benchmark import PerformanceBenchmark
except ImportError:
    print("Please install parquetframe: pip install -e .")
    exit(1)


def create_sample_datasets() -> tuple[dict[str, Path], Path]:
    """Create sample datasets of different sizes for testing."""
    print("📊 Creating sample datasets for performance testing...")

    datasets = {}

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Small dataset - should use pandas
        small_data = pd.DataFrame(
            {
                "id": range(1000),
                "name": [f"user_{i}" for i in range(1000)],
                "value": np.random.randn(1000),
                "category": np.random.choice(["A", "B", "C"], 1000),
            }
        )
        small_file = temp_path / "small_dataset.parquet"
        small_data.to_parquet(small_file)
        datasets["small"] = small_file

        # Medium dataset - may use either backend
        medium_data = pd.DataFrame(
            {
                "id": range(50000),
                "name": [f"user_{i}" for i in range(50000)],
                "value": np.random.randn(50000),
                "category": np.random.choice(["A", "B", "C", "D", "E"], 50000),
                "timestamp": pd.date_range("2023-01-01", periods=50000, freq="1min"),
            }
        )
        medium_file = temp_path / "medium_dataset.parquet"
        medium_data.to_parquet(medium_file)
        datasets["medium"] = medium_file

        # Large dataset - should use Dask
        print("  Creating large dataset (this may take a moment)...")
        large_data = pd.DataFrame(
            {
                "id": range(200000),
                "name": [f"user_{i}" for i in range(200000)],
                "value": np.random.randn(200000),
                "category": np.random.choice(
                    ["A", "B", "C", "D", "E", "F", "G", "H"], 200000
                ),
                "timestamp": pd.date_range("2023-01-01", periods=200000, freq="30s"),
                "metadata": [f"meta_{i % 1000}" for i in range(200000)],
            }
        )
        large_file = temp_path / "large_dataset.parquet"
        large_data.to_parquet(large_file)
        datasets["large"] = large_file

        return datasets, temp_path


def demonstrate_intelligent_backend_switching(datasets: dict[str, Path]) -> None:
    """Demonstrate intelligent backend switching."""
    print("\n🧠 Intelligent Backend Switching Demonstration")
    print("=" * 60)

    # Test with different thresholds
    thresholds = [1, 5, 10, 20]  # MB

    for name, file_path in datasets.items():
        file_size_mb = file_path.stat().st_size / 1024 / 1024
        print(f"\n📁 Dataset: {name} ({file_size_mb:.2f} MB)")

        for threshold in thresholds:
            pf = ParquetFrame.read(str(file_path), threshold_mb=threshold)
            backend = "Dask" if pf.islazy else "pandas"
            print(f"  Threshold {threshold:2d}MB: {backend:6s} backend selected")

        # Test explicit backend selection
        _ = ParquetFrame.read(str(file_path), islazy=False)
        _ = ParquetFrame.read(str(file_path), islazy=True)
        print("  Explicit:      pandas (forced), Dask (forced)")


def demonstrate_performance_benchmarking(
    datasets: dict[str, Path], temp_path: Path
) -> Any:
    """Demonstrate performance benchmarking capabilities."""
    print("\n⚡ Performance Benchmarking Demonstration")
    print("=" * 60)

    # Run a quick benchmark with small datasets
    print("\n🔍 Running quick benchmark on small datasets...")

    benchmark = PerformanceBenchmark(verbose=True)

    # Test read operations
    file_sizes = [(1000, "1K rows"), (5000, "5K rows")]
    read_results = benchmark.benchmark_read_operations(file_sizes)

    print("\n📈 Read Performance Results:")
    for result in read_results:
        status = "✅" if result.success else "❌"
        print(
            f"  {status} {result.operation} ({result.backend}): "
            f"{result.execution_time:.3f}s, {result.memory_peak:.1f}MB peak"
        )

    # Test a few operations
    print("\n🔧 Testing operations performance...")
    operations = ["filter", "groupby"]
    op_results = benchmark.benchmark_operations(operations, data_size=5000)

    print("\n📊 Operations Performance Results:")
    for result in op_results:
        status = "✅" if result.success else "❌"
        print(
            f"  {status} {result.operation} ({result.backend}): "
            f"{result.execution_time:.3f}s, {result.memory_peak:.1f}MB peak"
        )

    # Generate recommendations
    benchmark.generate_report()

    return benchmark


def demonstrate_memory_aware_processing(datasets: dict[str, Path]) -> None:
    """Demonstrate memory-aware processing techniques."""
    print("\n💾 Memory-Aware Processing Demonstration")
    print("=" * 60)

    for name, file_path in datasets.items():
        print(f"\n📁 Processing {name} dataset...")

        # Load with automatic backend selection
        pf = ParquetFrame.read(str(file_path))
        backend = "Dask" if pf.islazy else "pandas"

        print(f"  Backend selected: {backend}")
        print(f"  Dataset shape: {pf.shape}")
        print(
            f"  Memory estimate: {ParquetFrame._estimate_memory_usage(file_path):.1f} MB"
        )

        # Demonstrate efficient operations
        try:
            # Count by category
            if pf.islazy:
                category_counts = pf.groupby("category").size().compute()
            else:
                category_counts = pf.groupby("category").size()
            print(f"  Category distribution: {dict(category_counts)}")

            # Sample some data
            sample = pf.head(3)
            if hasattr(sample, "_df") and hasattr(sample._df, "compute"):
                sample = sample._df.compute()
            elif hasattr(sample, "_df"):
                sample = sample._df
            print(f"  Sample rows: {len(sample)}")

        except Exception as e:
            print(f"  ⚠️  Processing error: {e}")


def demonstrate_advanced_usage(datasets: dict[str, Path]) -> None:
    """Demonstrate advanced usage patterns."""
    print("\n🚀 Advanced Usage Patterns")
    print("=" * 60)

    # Chain operations efficiently
    print("\n🔗 Efficient operation chaining:")

    for name, file_path in datasets.items():
        if name == "large":  # Skip large dataset for demo speed
            continue

        print(f"\n  Processing {name} dataset:")

        pf = ParquetFrame.read(str(file_path))

        # Chain multiple operations
        try:
            result = (
                pf.query("value > 0")  # Filter positive values
                .groupby("category")["value"]  # Group by category
                .mean()
            )  # Calculate mean

            if hasattr(result, "compute"):
                result = result.compute()

            print(f"    Mean values by category: {dict(result)}")

            # Convert backends when needed
            if pf.islazy:
                print("    Converting Dask → pandas for small result processing")
                _ = pf.head(10).to_pandas()
            else:
                print("    Using pandas for efficient small data operations")

        except Exception as e:
            print(f"    ⚠️  Operation error: {e}")


def save_benchmark_results(benchmark: Any, temp_path: Path) -> None:
    """Save benchmark results for analysis."""
    print("\n💾 Saving Performance Analysis")
    print("=" * 60)

    results_file = temp_path / "benchmark_results.json"

    # Compile results
    all_results = {
        "read_operations": [
            r.__dict__ for r in benchmark.results if "Read" in r.operation
        ],
        "data_operations": [
            r.__dict__ for r in benchmark.results if "Read" not in r.operation
        ],
        "summary": {
            "total_benchmarks": len(benchmark.results),
            "successful_benchmarks": sum(1 for r in benchmark.results if r.success),
            "average_execution_time": sum(r.execution_time for r in benchmark.results)
            / len(benchmark.results),
            "recommendations": benchmark._compare_backends(),
        },
    }

    import json

    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"📊 Results saved to: {results_file}")
    print("🔍 Summary:")
    print(f"  • Total benchmarks: {all_results['summary']['total_benchmarks']}")
    print(
        f"  • Success rate: {all_results['summary']['successful_benchmarks'] / all_results['summary']['total_benchmarks'] * 100:.1f}%"
    )
    print(f"  • Average time: {all_results['summary']['average_execution_time']:.3f}s")

    if all_results["summary"]["recommendations"]:
        print("💡 Recommendations:")
        for rec in all_results["summary"]["recommendations"]:
            print(f"  • {rec}")


def main() -> None:
    """Main demonstration function."""
    print("🔥 ParquetFrame Performance Optimization Demo")
    print("=" * 60)
    print()
    print("This demonstration showcases advanced performance features:")
    print("• Intelligent backend switching based on memory and file characteristics")
    print("• Performance benchmarking and analysis tools")
    print("• Memory-aware processing techniques")
    print("• Advanced usage patterns for optimal performance")

    try:
        # Create sample datasets
        datasets, temp_path = create_sample_datasets()

        # Run demonstrations
        demonstrate_intelligent_backend_switching(datasets)
        demonstrate_memory_aware_processing(datasets)

        # Run performance benchmark
        benchmark = demonstrate_performance_benchmarking(datasets, temp_path)

        demonstrate_advanced_usage(datasets)

        # Save results
        save_benchmark_results(benchmark, temp_path)

        print("\n" + "=" * 60)
        print("✨ Demo completed successfully!")
        print(f"📁 Temporary files created in: {temp_path}")
        print("🔧 Try the CLI commands:")
        print("   python -m parquetframe.cli benchmark --help")
        print("   python -m parquetframe.cli run data.parquet --info")

    except KeyboardInterrupt:
        print("\n❌ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
