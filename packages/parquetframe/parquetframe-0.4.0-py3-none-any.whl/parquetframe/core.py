"""
Core ParquetFrame implementation.

This module contains the main ParquetFrame class that wraps pandas and Dask
DataFrames for seamless operation.
"""

import os
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

import dask.dataframe as dd
import pandas as pd

if TYPE_CHECKING:
    from .sql import QueryResult, SQLBuilder


class FileFormat(Enum):
    """Supported file formats for ParquetFrame."""

    PARQUET = "parquet"
    CSV = "csv"
    JSON = "json"
    ORC = "orc"


def detect_format(
    file_path: Union[str, Path], explicit_format: Optional[str] = None
) -> FileFormat:
    """
    Detect file format based on extension or explicit format specification.

    Args:
        file_path: Path to the file
        explicit_format: Explicitly specified format (overrides detection)

    Returns:
        FileFormat enum value

    Raises:
        ValueError: If format cannot be determined or is not supported

    Examples:
        >>> detect_format("data.csv")
        <FileFormat.CSV: 'csv'>
        >>> detect_format("data.unknown", explicit_format="json")
        <FileFormat.JSON: 'json'>
    """
    if explicit_format:
        try:
            return FileFormat(explicit_format.lower())
        except ValueError:
            raise ValueError(f"Unsupported format: {explicit_format}") from None

    path = Path(file_path)

    # Map extensions to formats
    extension_map = {
        ".parquet": FileFormat.PARQUET,
        ".pqt": FileFormat.PARQUET,
        ".csv": FileFormat.CSV,
        ".tsv": FileFormat.CSV,  # TSV treated as CSV with different delimiter
        ".json": FileFormat.JSON,
        ".jsonl": FileFormat.JSON,  # JSON lines
        ".ndjson": FileFormat.JSON,  # Newline delimited JSON
        ".orc": FileFormat.ORC,
    }

    suffix = path.suffix.lower()
    if suffix in extension_map:
        return extension_map[suffix]

    # Try to auto-detect for files without clear extensions
    # For now, default to parquet for backwards compatibility
    # This matches the original _resolve_file_path behavior
    return FileFormat.PARQUET


class IOHandler(ABC):
    """Abstract base class for file format handlers."""

    @abstractmethod
    def read(
        self, file_path: Union[str, Path], use_dask: bool = False, **kwargs
    ) -> Union[pd.DataFrame, dd.DataFrame]:
        """
        Read a file into a DataFrame.

        Args:
            file_path: Path to the file to read
            use_dask: Whether to use Dask backend
            **kwargs: Additional arguments specific to the format

        Returns:
            pandas or Dask DataFrame
        """
        pass

    @abstractmethod
    def write(
        self,
        df: Union[pd.DataFrame, dd.DataFrame],
        file_path: Union[str, Path],
        **kwargs,
    ) -> None:
        """
        Write a DataFrame to a file.

        Args:
            df: DataFrame to write
            file_path: Path to write the file to
            **kwargs: Additional arguments specific to the format
        """
        pass

    @abstractmethod
    def resolve_file_path(self, file: Union[str, Path]) -> Path:
        """
        Resolve file path and handle extension detection for this format.

        Args:
            file: Input file path

        Returns:
            Resolved Path object

        Raises:
            FileNotFoundError: If no file variant is found
        """
        pass


class ParquetHandler(IOHandler):
    """Handler for Parquet files (.parquet, .pqt)."""

    def _is_valid_parquet_directory(self, dir_path: Path) -> bool:
        """Check if directory contains valid parquet files."""
        try:
            # Check if directory contains parquet files or has _metadata file
            parquet_files = list(dir_path.glob("*.parquet"))
            has_metadata = (dir_path / "_metadata").exists()
            has_common_metadata = (dir_path / "_common_metadata").exists()

            return len(parquet_files) > 0 or has_metadata or has_common_metadata
        except (OSError, PermissionError):
            return False

    def read(
        self, file_path: Union[str, Path], use_dask: bool = False, **kwargs
    ) -> Union[pd.DataFrame, dd.DataFrame]:
        """Read a Parquet file."""
        if use_dask:
            return dd.read_parquet(file_path, **kwargs)
        else:
            return pd.read_parquet(file_path, **kwargs)

    def write(
        self,
        df: Union[pd.DataFrame, dd.DataFrame],
        file_path: Union[str, Path],
        **kwargs,
    ) -> None:
        """Write a DataFrame to a Parquet file."""
        if isinstance(df, dd.DataFrame):
            df.to_parquet(file_path, **kwargs)
        else:
            df.to_parquet(file_path, **kwargs)

    def resolve_file_path(self, file: Union[str, Path]) -> Path:
        """Resolve Parquet file path with extension detection."""
        file_path = Path(file)

        # First, check if the file/directory exists exactly as specified
        if file_path.exists():
            if file_path.is_file():
                return file_path
            elif file_path.is_dir() and self._is_valid_parquet_directory(file_path):
                return file_path

        # If extension is already present and matches our format, check existence
        if file_path.suffix in (".parquet", ".pqt"):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Try different extensions
        for ext in [".parquet", ".pqt"]:
            candidate = file_path.with_suffix(ext)
            if candidate.exists():
                if candidate.is_file():
                    return candidate
                elif candidate.is_dir() and self._is_valid_parquet_directory(candidate):
                    return candidate

        raise FileNotFoundError(
            f"No parquet file found for '{file}' (tried .parquet, .pqt)"
        )


class CsvHandler(IOHandler):
    """Handler for CSV files (.csv, .tsv)."""

    def read(
        self, file_path: Union[str, Path], use_dask: bool = False, **kwargs
    ) -> Union[pd.DataFrame, dd.DataFrame]:
        """Read a CSV file."""
        # Handle TSV files by setting delimiter
        path = Path(file_path)
        if (
            path.suffix.lower() in [".tsv"]
            and "sep" not in kwargs
            and "delimiter" not in kwargs
        ):
            kwargs["sep"] = "\t"

        if use_dask:
            return dd.read_csv(file_path, **kwargs)
        else:
            return pd.read_csv(file_path, **kwargs)

    def write(
        self,
        df: Union[pd.DataFrame, dd.DataFrame],
        file_path: Union[str, Path],
        **kwargs,
    ) -> None:
        """Write a DataFrame to a CSV file."""
        # Handle TSV files by setting delimiter
        path = Path(file_path)
        if path.suffix.lower() in [".tsv"] and "sep" not in kwargs:
            kwargs["sep"] = "\t"

        # Default to not including index unless explicitly specified
        kwargs.setdefault("index", False)

        if isinstance(df, dd.DataFrame):
            df.to_csv(file_path, **kwargs)
        else:
            df.to_csv(file_path, **kwargs)

    def resolve_file_path(self, file: Union[str, Path]) -> Path:
        """Resolve CSV file path with extension detection."""
        file_path = Path(file)

        # First, check if the file exists exactly as specified and is a file
        if file_path.exists() and file_path.is_file():
            return file_path

        # If extension is already present and matches our format, check existence
        if file_path.suffix.lower() in (".csv", ".tsv"):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Try different extensions
        for ext in [".csv", ".tsv"]:
            candidate = file_path.with_suffix(ext)
            if candidate.exists() and candidate.is_file():
                return candidate

        raise FileNotFoundError(f"No CSV file found for '{file}' (tried .csv, .tsv)")


class JsonHandler(IOHandler):
    """Handler for JSON files (.json, .jsonl, .ndjson)."""

    def read(
        self, file_path: Union[str, Path], use_dask: bool = False, **kwargs
    ) -> Union[pd.DataFrame, dd.DataFrame]:
        """Read a JSON file."""
        path = Path(file_path)

        # Handle different JSON formats
        is_lines_format = path.suffix.lower() in [".jsonl", ".ndjson"]

        if is_lines_format:
            kwargs.setdefault("lines", True)

        if use_dask:
            if is_lines_format:
                return dd.read_json(file_path, **kwargs)
            else:
                # For regular JSON, read with pandas and convert to dask
                df = pd.read_json(file_path, **kwargs)
                return dd.from_pandas(df, npartitions=1)
        else:
            return pd.read_json(file_path, **kwargs)

    def write(
        self,
        df: Union[pd.DataFrame, dd.DataFrame],
        file_path: Union[str, Path],
        **kwargs,
    ) -> None:
        """Write a DataFrame to a JSON file."""
        path = Path(file_path)

        # Handle format based on file extension
        is_lines_format = path.suffix.lower() in [".jsonl", ".ndjson"]
        if is_lines_format:
            # For JSON Lines format
            kwargs.setdefault("orient", "records")
            kwargs.setdefault("lines", True)
        else:
            # For regular JSON, default to records format but not lines
            kwargs.setdefault("orient", "records")
            # Don't set lines=True for regular JSON files

        if isinstance(df, dd.DataFrame):
            # Dask doesn't have to_json, compute first
            df.compute().to_json(file_path, **kwargs)
        else:
            df.to_json(file_path, **kwargs)

    def resolve_file_path(self, file: Union[str, Path]) -> Path:
        """Resolve JSON file path with extension detection."""
        file_path = Path(file)

        # First, check if the file exists exactly as specified and is a file
        if file_path.exists() and file_path.is_file():
            return file_path

        # If extension is already present and matches our format, check existence
        if file_path.suffix.lower() in (".json", ".jsonl", ".ndjson"):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Try different extensions
        for ext in [".json", ".jsonl", ".ndjson"]:
            candidate = file_path.with_suffix(ext)
            if candidate.exists() and candidate.is_file():
                return candidate

        raise FileNotFoundError(
            f"No JSON file found for '{file}' (tried .json, .jsonl, .ndjson)"
        )


class OrcHandler(IOHandler):
    """Handler for ORC files (.orc) - requires pyarrow with ORC support."""

    def read(
        self, file_path: Union[str, Path], use_dask: bool = False, **kwargs
    ) -> Union[pd.DataFrame, dd.DataFrame]:
        """Read an ORC file."""
        try:
            import pyarrow.orc as orc
        except ImportError:
            raise ImportError(
                "ORC support requires pyarrow with ORC functionality. "
                "Install with: pip install pyarrow"
            ) from None

        # Read ORC file using pyarrow
        table = orc.read_table(file_path)
        df = table.to_pandas()

        if use_dask:
            return dd.from_pandas(df, npartitions=1)
        else:
            return df

    def write(
        self,
        df: Union[pd.DataFrame, dd.DataFrame],
        file_path: Union[str, Path],
        **kwargs,
    ) -> None:
        """Write a DataFrame to an ORC file."""
        try:
            import pyarrow as pa
            import pyarrow.orc as orc
        except ImportError:
            raise ImportError(
                "ORC support requires pyarrow with ORC functionality. "
                "Install with: pip install pyarrow"
            ) from None

        # Convert to pandas if Dask
        if isinstance(df, dd.DataFrame):
            df = df.compute()

        # Convert to Arrow table and write as ORC
        table = pa.Table.from_pandas(df)
        orc.write_table(table, file_path)

    def resolve_file_path(self, file: Union[str, Path]) -> Path:
        """Resolve ORC file path with extension detection."""
        file_path = Path(file)

        # First, check if the file exists exactly as specified and is a file
        if file_path.exists() and file_path.is_file():
            return file_path

        # If extension is already present and matches our format, check existence
        if file_path.suffix.lower() == ".orc":
            raise FileNotFoundError(f"File not found: {file_path}")

        # Try ORC extension
        candidate = file_path.with_suffix(".orc")
        if candidate.exists() and candidate.is_file():
            return candidate

        raise FileNotFoundError(f"No ORC file found for '{file}' (tried .orc)")


# Format handler registry
FORMAT_HANDLERS: dict[FileFormat, IOHandler] = {
    FileFormat.PARQUET: ParquetHandler(),
    FileFormat.CSV: CsvHandler(),
    FileFormat.JSON: JsonHandler(),
    FileFormat.ORC: OrcHandler(),
}


class ParquetFrame:
    """
    A universal wrapper for pandas and Dask DataFrames supporting multiple file formats.

    Supports reading and writing parquet, CSV, JSON, and ORC files with automatic
    format detection. The class automatically switches between pandas and Dask based
    on file size or manual control. It delegates all standard DataFrame methods to
    the active internal dataframe.

    Supported Formats:
        - Parquet (.parquet, .pqt)
        - CSV (.csv, .tsv)
        - JSON (.json, .jsonl, .ndjson)
        - ORC (.orc) - requires pyarrow

    Examples:
        >>> import parquetframe as pqf
        >>> # Read files with automatic format detection
        >>> pf = pqf.pf.read("data.csv")      # Auto-detects CSV
        >>> pf = pqf.pf.read("data.json")     # Auto-detects JSON
        >>> pf = pqf.pf.read("data.parquet")  # Auto-detects Parquet
        >>> # Manual backend control
        >>> pf = pqf.pf.read("data.csv", islazy=True)  # Force Dask
        >>> # Standard DataFrame operations work transparently
        >>> result = pf.groupby("column").sum()
        >>> # Save in different formats
        >>> pf.save("output.csv")     # Saves as CSV
        >>> pf.save("output.json")    # Saves as JSON
    """

    def __init__(
        self,
        df: Optional[Union[pd.DataFrame, dd.DataFrame]] = None,
        islazy: bool = False,
        track_history: bool = False,
    ) -> None:
        """
        Initialize the ParquetFrame.

        Args:
            df: An initial dataframe (pandas or Dask).
            islazy: If True, forces a Dask DataFrame.
            track_history: If True, enables history tracking for CLI sessions.
        """
        self._df = df
        self._islazy = islazy
        self.DEFAULT_THRESHOLD_MB = 10
        self._track_history = track_history
        self._history = [] if track_history else None

    @property
    def islazy(self) -> bool:
        """Get the current backend type (True for Dask, False for pandas)."""
        return self._islazy

    @property
    def pandas_df(self) -> pd.DataFrame:
        """Get the underlying pandas DataFrame.

        If the current backend is Dask, it will be computed to pandas.

        Returns:
            The raw pandas DataFrame
        """
        if self._df is None:
            raise ValueError("No dataframe loaded")

        if self._islazy and isinstance(self._df, dd.DataFrame):
            return self._df.compute()
        elif isinstance(self._df, pd.DataFrame):
            return self._df
        else:
            raise TypeError(f"Unexpected dataframe type: {type(self._df)}")

    @islazy.setter
    def islazy(self, value: bool) -> None:
        """Set the backend type and convert the dataframe if necessary."""
        if not isinstance(value, bool):
            raise TypeError("islazy must be a boolean")
        if value != self._islazy:
            if value:
                self.to_dask()
            else:
                self.to_pandas()

    def __repr__(self) -> str:
        """String representation of the object."""
        df_type = "Dask" if self.islazy else "pandas"
        if self._df is None:
            return f"ParquetFrame(type={df_type}, df=None)"
        return f"ParquetFrame(type={df_type}, df={self._df.__repr__()})"

    def __getitem__(self, key):
        """
        Support indexing operations (df[column] or df[columns]).
        """
        if self._df is None:
            raise ValueError("No dataframe loaded")

        result = self._df[key]

        # Track operation in history if enabled
        if self._track_history:
            if isinstance(key, list):
                key_repr = repr(key)
            else:
                key_repr = repr(key)
            self._history.append(f"pf = pf[{key_repr}]")

        # If result is a dataframe, wrap it
        if isinstance(result, (pd.DataFrame, dd.DataFrame)):
            new_pf = ParquetFrame(
                result,
                isinstance(result, dd.DataFrame),
                track_history=self._track_history,
            )
            # Inherit history from parent if tracking
            if self._track_history:
                new_pf._history = self._history.copy()
            return new_pf
        return result

    def __len__(self) -> int:
        """
        Return the length of the dataframe.
        """
        if self._df is None:
            return 0
        return len(self._df)

    def __getattr__(self, name: str) -> Any:
        """
        Delegate attribute access to the underlying dataframe.

        This method is called for attributes not found in the ParquetFrame instance.
        It forwards the call to the internal dataframe (_df).
        """
        if self._df is not None:
            attr = getattr(self._df, name)
            if callable(attr):

                def wrapper(*args, **kwargs):
                    # Track operation in history if enabled
                    if self._track_history:
                        args_repr = [repr(arg) for arg in args]
                        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
                        call_repr = f".{name}({', '.join(args_repr + kwargs_repr)})"
                        self._history.append(f"pf = pf{call_repr}")

                    result = attr(*args, **kwargs)
                    # If the result is a dataframe, wrap it in a new ParquetFrame
                    if isinstance(result, (pd.DataFrame, dd.DataFrame)):
                        new_pf = ParquetFrame(
                            result,
                            isinstance(result, dd.DataFrame),
                            track_history=self._track_history,
                        )
                        # Inherit history from parent if tracking
                        if self._track_history:
                            new_pf._history = self._history.copy()
                        return new_pf
                    return result

                return wrapper
            return attr
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    @classmethod
    def _estimate_memory_usage(cls, file_path: Path) -> float:
        """Estimate memory usage for loading file based on file size and compression."""
        try:
            import pyarrow.parquet as pq

            # Get file metadata without loading full file
            _ = pq.ParquetFile(file_path).metadata

            # Estimate memory usage based on:
            # 1. Uncompressed size (compressed size * expansion factor)
            # 2. Data types (strings use more memory than numbers)
            # 3. Null values (can reduce memory usage)

            compressed_size = file_path.stat().st_size / 1024 / 1024  # MB

            # Estimate compression ratio (typical parquet compression is 3-10x)
            # Use conservative estimate of 4x expansion
            expansion_factor = 4.0

            # Additional overhead for pandas DataFrame structure
            pandas_overhead = 1.5

            estimated_memory = compressed_size * expansion_factor * pandas_overhead

            return estimated_memory

        except Exception:
            # Fallback to simple file size estimation
            file_size_mb = file_path.stat().st_size / 1024 / 1024
            return file_size_mb * 5  # Conservative estimate

    @classmethod
    def _get_system_memory(cls) -> float:
        """Get available system memory in MB."""
        try:
            import psutil

            # Get available memory (not just free, but actually available)
            available_mb = psutil.virtual_memory().available / 1024 / 1024
            return available_mb
        except (ImportError, Exception):
            # Conservative fallback if psutil not available or fails
            return 2048  # Assume 2GB available

    @classmethod
    def _should_use_dask(
        cls, file_path: Path, threshold_mb: float, islazy: Optional[bool] = None
    ) -> bool:
        """Intelligently determine whether to use Dask based on multiple factors."""
        if islazy is not None:
            return islazy

        file_size_mb = file_path.stat().st_size / 1024 / 1024

        # Basic threshold check
        if file_size_mb >= threshold_mb:
            return True

        # Advanced checks if file is close to threshold
        if file_size_mb >= threshold_mb * 0.7:  # Within 70% of threshold
            estimated_memory = cls._estimate_memory_usage(file_path)
            available_memory = cls._get_system_memory()

            # Use Dask if estimated memory usage > 50% of available memory
            if estimated_memory > available_memory * 0.5:
                return True

            # Use Dask if file has many partitions (suggests it's meant for parallel processing)
            try:
                import pyarrow.parquet as pq

                metadata = pq.ParquetFile(file_path).metadata
                if metadata.num_row_groups > 10:  # Many row groups suggest chunked data
                    return True
            except Exception:  # nosec B110
                # Intentional broad exception handling for metadata parsing robustness
                # Failure to determine row groups should not crash file read operation
                pass

        return False

    @classmethod
    def read(
        cls,
        file: Union[str, Path],
        threshold_mb: Optional[float] = None,
        islazy: Optional[bool] = None,
        format: Optional[str] = None,
        **kwargs,
    ) -> "ParquetFrame":
        """
        Read a file into a ParquetFrame with automatic format detection.

        Supports parquet, CSV, JSON, and ORC files. Automatically selects pandas
        or Dask based on file size, unless overridden. Handles file extension
        detection automatically.

        Args:
            file: Path to the file (extension used for format detection if format not specified).
            threshold_mb: Size threshold in MB for backend selection. Defaults to 10MB.
            islazy: Force backend selection (True=Dask, False=pandas, None=auto).
            format: Explicitly specify format ('parquet', 'csv', 'json', 'orc').
                   If None, auto-detects from file extension.
            **kwargs: Additional keyword arguments passed to the format-specific reader.

        Returns:
            ParquetFrame instance with loaded data.

        Raises:
            FileNotFoundError: If no file is found.
            ValueError: If format is unsupported.
            ImportError: If required dependencies for format are missing.

        Examples:
            >>> pf = ParquetFrame.read("data.csv")           # Auto-detects CSV
            >>> pf = ParquetFrame.read("data.json")          # Auto-detects JSON
            >>> pf = ParquetFrame.read("data")               # Auto-detects .parquet/.pqt
            >>> pf = ParquetFrame.read("data.txt", format="csv")  # Force CSV format
            >>> pf = ParquetFrame.read("data.csv", threshold_mb=50, islazy=True)  # Force Dask
        """
        # Support URLs and fsspec-based paths without local existence checks
        file_str = str(file)
        is_url = file_str.startswith(("http://", "https://", "s3://", "gs://"))

        # Detect format
        file_format = detect_format(file_str, format)
        handler = FORMAT_HANDLERS[file_format]

        if is_url:
            file_path = file_str  # pass through to reader
            file_size_mb = 0.0
        else:
            # Use format-specific path resolution
            file_path = handler.resolve_file_path(file)
            file_size_mb = file_path.stat().st_size / (1024 * 1024)

        # Validate islazy parameter
        if islazy is not None and not isinstance(islazy, bool):
            raise TypeError("islazy parameter must be a boolean or None")

        # Determine backend using explicit override first
        threshold = threshold_mb if threshold_mb is not None else 10
        if islazy is not None:
            use_dask = bool(islazy)
        else:
            # Intelligent switching when not explicitly specified
            if not is_url and file_format == FileFormat.PARQUET:
                # Only use advanced heuristics for parquet files
                use_dask = cls._should_use_dask(file_path, threshold, None)
            else:
                # Simple size-based decision for other formats
                use_dask = file_size_mb >= threshold

        # Read the file using format-specific handler
        df = handler.read(file_path, use_dask=use_dask, **kwargs)

        backend_type = "Dask" if use_dask else "pandas"
        print(
            f"Reading '{file_path}' as {backend_type} DataFrame "
            f"(format: {file_format.value}, size: {file_size_mb:.2f} MB)"
        )

        instance = cls(df, use_dask)
        # Track read operation in history if needed
        if hasattr(cls, "_current_session_tracking") and cls._current_session_tracking:
            instance._track_history = True
            instance._history = [
                f"pf = ParquetFrame.read('{file}', threshold_mb={threshold_mb}, "
                f"islazy={islazy}, format={format!r})"
            ]
        return instance

    def save(
        self, file: Union[str, Path], save_script: Optional[str] = None, **kwargs
    ) -> "ParquetFrame":
        """
        Save the dataframe to a parquet file.

        Automatically adds .parquet extension if not present.
        Works with both pandas and Dask dataframes.

        Args:
            file: Base name for the output file.
            save_script: If provided, saves session history to this Python script.
            **kwargs: Additional keyword arguments for to_parquet methods.

        Returns:
            Self for method chaining.

        Raises:
            TypeError: If no dataframe is loaded.

        Examples:
            >>> pf.save("output")  # Saves as output.parquet
            >>> pf.save("data.parquet", compression='snappy')
            >>> pf.save("output", save_script="session.py")  # Also saves session history
        """
        if self._df is None:
            raise TypeError("No dataframe loaded to save.")

        file_path = self._ensure_parquet_extension(file)

        # Track save operation in history
        if self._track_history:
            save_args = [f"'{file}'"] + [f"{k}={v!r}" for k, v in kwargs.items()]
            if save_script:
                save_args.append(f"save_script='{save_script}'")
            self._history.append(f"pf.save({', '.join(save_args)})")

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(self._df, dd.DataFrame):
            self._df.to_parquet(file_path, **kwargs)
            print(f"Dask DataFrame saved to '{file_path}'.")
        elif isinstance(self._df, pd.DataFrame):
            self._df.to_parquet(file_path, **kwargs)
            print(f"pandas DataFrame saved to '{file_path}'.")

        # Save script if requested
        if save_script and self._track_history:
            self._save_history_script(save_script)

        return self

    def to_pandas(self) -> "ParquetFrame":
        """
        Convert the internal Dask dataframe to a pandas dataframe.

        Returns:
            Self for method chaining.
        """
        if self.islazy and isinstance(self._df, dd.DataFrame):
            self._df = self._df.compute()
            # Normalize string dtype back to object for consistency with tests
            try:
                string_cols = list(self._df.select_dtypes(include="string").columns)
                if string_cols:
                    self._df[string_cols] = self._df[string_cols].astype("object")
            except Exception:  # nosec B110
                # Intentional broad exception handling for dtype conversion robustness
                # Failure to normalize string dtypes should not crash pandas conversion
                pass
            self._islazy = False
            print("Converted to pandas DataFrame.")
        else:
            print("Already a pandas DataFrame.")
        return self

    def to_dask(self, npartitions: Optional[int] = None) -> "ParquetFrame":
        """
        Convert the internal pandas dataframe to a Dask dataframe.

        Args:
            npartitions: Number of partitions for the Dask dataframe.
                       Defaults to the number of CPU cores.

        Returns:
            Self for method chaining.
        """
        if npartitions is not None and npartitions <= 0:
            raise ValueError("npartitions must be a positive integer")
        if not self.islazy and isinstance(self._df, pd.DataFrame):
            npart = npartitions if npartitions is not None else os.cpu_count() or 1
            self._df = dd.from_pandas(self._df, npartitions=npart)
            self._islazy = True
            print("Converted to Dask DataFrame.")
        else:
            print("Already a Dask DataFrame.")
        return self

    def sql(
        self,
        query: str,
        profile: bool = False,
        use_cache: bool = True,
        **other_frames: "ParquetFrame",
    ) -> Union["ParquetFrame", "QueryResult"]:
        """
        Execute a SQL query on this ParquetFrame using DuckDB with optional profiling.

        The current ParquetFrame is available as 'df' in the query.
        Additional ParquetFrames can be passed as keyword arguments.

        Args:
            query: SQL query string to execute.
            profile: If True, return QueryResult with execution metadata instead of ParquetFrame.
            use_cache: If True, use cached results for identical queries.
            **other_frames: Additional ParquetFrames to use in JOINs.

        Returns:
            New ParquetFrame with query results (always pandas backend),
            or QueryResult with profiling info if profile=True.

        Raises:
            ImportError: If DuckDB is not installed.
            ValueError: If query execution fails.

        Examples:
            >>> # Simple query
            >>> result = pf.sql("SELECT * FROM df WHERE age > 25")
            >>>
            >>> # With profiling
            >>> result = pf.sql("SELECT COUNT(*) FROM df", profile=True)
            >>> print(result.summary())  # Shows execution time and metadata
            >>>
            >>> # JOIN with another ParquetFrame
            >>> orders = pf.sql(
            ...     "SELECT * FROM df JOIN customers ON df.cust_id = customers.id",
            ...     customers=customers_pf
            ... )
        """
        if self._df is None:
            raise ValueError("No dataframe loaded for SQL query")

        from .sql import query_dataframes

        # Convert other ParquetFrames to their underlying DataFrames
        other_dfs = {name: pf._df for name, pf in other_frames.items()}

        # Execute SQL query with profiling support
        result = query_dataframes(
            self._df, query, other_dfs, profile=profile, use_cache=use_cache
        )

        # Return QueryResult directly if profiling is enabled
        if profile:
            return result

        # Otherwise return as pandas-backed ParquetFrame (SQL results are always pandas)
        return self.__class__(result, islazy=False)

    def sql_with_params(
        self,
        query_template: str,
        profile: bool = False,
        use_cache: bool = True,
        **params: Any,
    ) -> Union["ParquetFrame", "QueryResult"]:
        """
        Execute a parameterized SQL query on this ParquetFrame.

        Args:
            query_template: SQL query string with {param_name} placeholders
            profile: If True, return QueryResult with execution metadata
            use_cache: If True, use cached results for identical queries
            **params: Named parameters to substitute in the query

        Returns:
            New ParquetFrame with query results or QueryResult if profile=True

        Examples:
            >>> result = pf.sql_with_params(
            ...     "SELECT * FROM df WHERE age > {min_age} AND salary < {max_salary}",
            ...     min_age=25, max_salary=100000
            ... )
        """
        from .sql import parameterize_query

        # Substitute parameters
        query = parameterize_query(query_template, **params)

        # Execute the parameterized query
        return self.sql(query, profile=profile, use_cache=use_cache)

    def select(self, *columns: str) -> "SQLBuilder":
        """
        Start building a fluent SQL query with SELECT.

        Args:
            *columns: Column names to select

        Returns:
            SQLBuilder instance for method chaining

        Examples:
            >>> # Fluent SQL API
            >>> result = (pf.select("name", "age")
            ...             .where("age > 25")
            ...             .order_by("name")
            ...             .execute())
            >>>
            >>> # Aggregation with grouping
            >>> summary = (pf.select("category", "COUNT(*) as count", "AVG(value) as avg_val")
            ...              .group_by("category")
            ...              .having("count > 10")
            ...              .order_by("avg_val", "DESC")
            ...              .execute())
        """
        from .sql import SQLBuilder

        return SQLBuilder(self).select(*columns)

    def where(self, condition: str) -> "SQLBuilder":
        """
        Start building a fluent SQL query with WHERE.

        Args:
            condition: SQL WHERE condition

        Returns:
            SQLBuilder instance for method chaining

        Examples:
            >>> result = pf.where("age > 30").select("name", "salary").execute()
        """
        from .sql import SQLBuilder

        return SQLBuilder(self).where(condition)

    def group_by(self, *columns: str) -> "SQLBuilder":
        """
        Start building a fluent SQL query with GROUP BY.

        Args:
            *columns: Column names to group by

        Returns:
            SQLBuilder instance for method chaining

        Examples:
            >>> # Aggregation query starting with GROUP BY
            >>> result = (pf.group_by("category")
            ...             .select("category", "COUNT(*) as count", "AVG(price) as avg_price")
            ...             .having("count > 5")
            ...             .execute())
        """
        from .sql import SQLBuilder

        return SQLBuilder(self).group_by(*columns)

    def order_by(self, *columns: str) -> "SQLBuilder":
        """
        Start building a fluent SQL query with ORDER BY.

        Args:
            *columns: Column names/expressions to order by

        Returns:
            SQLBuilder instance for method chaining

        Examples:
            >>> # Simple ordering
            >>> result = pf.order_by("name").select("*").execute()
            >>>
            >>> # Multiple columns with explicit direction
            >>> result = pf.order_by("age DESC", "name").select("*").execute()
        """
        from .sql import SQLBuilder

        return SQLBuilder(self).order_by(*columns)

    @property
    def bio(self):
        """
        Access bioframe functions with intelligent parallel dispatching.

        Returns BioAccessor that automatically chooses between pandas (eager)
        and Dask (parallel) implementations based on the current backend.

        Returns:
            BioAccessor instance for genomic operations.

        Raises:
            ImportError: If bioframe is not installed.

        Examples:
            >>> # Cluster genomic intervals
            >>> clustered = pf.bio.cluster(min_dist=1000)
            >>>
            >>> # Find overlaps with another ParquetFrame
            >>> overlaps = pf.bio.overlap(other_pf, broadcast=True)
        """
        from .bio import BioAccessor

        return BioAccessor(self)

    @staticmethod
    def _resolve_file_path(file: Union[str, Path]) -> Path:
        """
        Resolve file path and handle extension detection.

        Args:
            file: Input file path.

        Returns:
            Resolved Path object.

        Raises:
            FileNotFoundError: If no parquet file variant is found.
        """
        file_path = Path(file)

        # If extension is already present, use as-is
        if file_path.suffix in (".parquet", ".pqt"):
            if file_path.exists():
                return file_path
            else:
                raise FileNotFoundError(f"File not found: {file_path}")

        # Try different extensions
        for ext in [".parquet", ".pqt"]:
            candidate = file_path.with_suffix(ext)
            if candidate.exists():
                return candidate

        raise FileNotFoundError(
            f"No parquet file found for '{file}' (tried .parquet, .pqt)"
        )

    def _save_history_script(self, script_path: Union[str, Path]) -> None:
        """
        Save the session history to a Python script.

        Args:
            script_path: Path to save the script to.
        """
        if not self._track_history or not self._history:
            print("No history to save (history tracking not enabled or empty).")
            return

        script_path = Path(script_path)
        if script_path.suffix != ".py":
            script_path = script_path.with_suffix(".py")

        header = "# Auto-generated script from ParquetFrame CLI session\n"
        header += (
            "from parquetframe import ParquetFrame\nimport parquetframe as pqf\n\n"
        )

        with open(script_path, "w") as f:
            f.write(header)
            for line in self._history:
                f.write(line + "\n")

        print(f"Session history saved to '{script_path}'")

    def get_history(self) -> Optional[list]:
        """
        Get the current session history.

        Returns:
            List of command strings if history tracking is enabled, None otherwise.
        """
        return self._history.copy() if self._track_history else None

    def clear_history(self) -> None:
        """
        Clear the session history.
        """
        if self._track_history:
            self._history.clear()
            print("Session history cleared.")
        else:
            print("History tracking not enabled.")

    @staticmethod
    def _ensure_parquet_extension(file: Union[str, Path]) -> Path:
        """
        Ensure the file path has a parquet extension.

        Args:
            file: Input file path.

        Returns:
            Path with appropriate parquet extension.
        """
        file_path = Path(file)
        if file_path.suffix not in (".parquet", ".pqt"):
            return file_path.with_suffix(".parquet")
        return file_path
