"""
Enhanced exceptions and error handling for ParquetFrame.

This module provides structured exceptions with actionable error messages,
dependency checking, and graceful fallback suggestions.
"""

from typing import Any


class ParquetFrameError(Exception):
    """Base exception for ParquetFrame with enhanced error messages."""

    def __init__(
        self,
        message: str,
        suggestion: str | None = None,
        error_code: str | None = None,
        details: dict[str, Any | None] = None,
    ):
        self.message = message
        self.suggestion = suggestion
        self.error_code = error_code
        self.details = details or {}

        # Build full error message
        full_message = f"❌ {message}"
        if suggestion:
            full_message += f"\n💡 {suggestion}"
        if error_code:
            full_message += f" (Error: {error_code})"

        super().__init__(full_message)


class BackendError(ParquetFrameError):
    """Exception raised when backend operations fail."""

    def __init__(
        self,
        backend_type: str,
        operation: str,
        underlying_error: Exception | None = None,
    ):
        message = f"{backend_type} backend failed during {operation}"
        if underlying_error:
            message += f": {str(underlying_error)}"

        suggestions = [
            f"Verify {backend_type} is properly installed",
            "Check data format compatibility",
            "Try using a different backend if available",
        ]

        suggestion = "\n".join(f"• {s}" for s in suggestions)

        super().__init__(
            message=message, suggestion=suggestion, error_code="BACKEND_ERROR"
        )


class FileNotFoundError(ParquetFrameError):
    """Exception raised when a parquet file is not found."""

    def __init__(self, file_path: str, additional_context: str | None = None):
        message = f"Parquet file not found: {file_path}"
        if additional_context:
            message += f" ({additional_context})"

        suggestions = [
            "Check if the file path is correct",
            "Verify the file exists and has .parquet extension",
            "Ensure you have read permissions for the file",
        ]

        suggestion = "\n".join(f"• {s}" for s in suggestions)

        super().__init__(
            message=message, suggestion=suggestion, error_code="FILE_NOT_FOUND"
        )


class ValidationError(ParquetFrameError):
    """Exception raised when data validation fails."""

    def __init__(
        self,
        validation_type: str,
        failed_checks: list[str],
        data_info: dict[str, Any | None] = None,
    ):
        message = f"Data validation failed: {validation_type}"

        suggestion_parts = ["Validation failures:"]
        suggestion_parts.extend(f"  • {check}" for check in failed_checks)
        suggestion_parts.append("\nConsider:")
        suggestion_parts.extend(
            [
                "  • Checking data quality and format",
                "  • Using data cleaning operations",
                "  • Adjusting validation criteria",
            ]
        )

        suggestion = "\n".join(suggestion_parts)

        super().__init__(
            message=message,
            suggestion=suggestion,
            error_code="VALIDATION_ERROR",
            details=data_info or {},
        )


class DependencyError(ParquetFrameError):
    """Raised when required dependencies are missing."""

    def __init__(
        self,
        missing_package: str,
        feature: str,
        install_command: str | None = None,
        alternative: str | None = None,
    ):
        self.missing_package = missing_package
        self.feature = feature

        message = f"Missing dependency '{missing_package}' required for {feature}"

        if install_command:
            suggestion = f"Install with: {install_command}"
        else:
            suggestion = f"Install with: pip install {missing_package}"

        if alternative:
            suggestion += f"\nAlternatively: {alternative}"

        super().__init__(
            message=message, suggestion=suggestion, error_code="MISSING_DEPENDENCY"
        )


class DataSourceError(ParquetFrameError):
    """Raised when data source connection or access fails."""

    def __init__(
        self,
        source_type: str,
        source_location: str,
        underlying_error: Exception | None = None,
        troubleshooting_steps: list[str | None] = None,
    ):
        self.source_type = source_type
        self.source_location = source_location
        self.underlying_error = underlying_error

        message = f"Failed to connect to {source_type} at '{source_location}'"
        if underlying_error:
            message += f": {str(underlying_error)}"

        suggestion_parts = []

        if source_type == "parquet":
            suggestion_parts.extend(
                [
                    "Check if the directory exists and contains .parquet files",
                    "Verify read permissions for the directory",
                    "Ensure parquet files are not corrupted",
                ]
            )
        elif source_type == "database":
            suggestion_parts.extend(
                [
                    "Verify database connection string format",
                    "Check database server is running and accessible",
                    "Confirm authentication credentials are correct",
                ]
            )

        if troubleshooting_steps:
            suggestion_parts.extend(troubleshooting_steps)

        suggestion = "\n".join(f"• {step}" for step in suggestion_parts)

        super().__init__(
            message=message,
            suggestion=suggestion,
            error_code="DATA_SOURCE_ERROR",
            details={
                "source_type": source_type,
                "source_location": source_location,
                "underlying_error": str(underlying_error) if underlying_error else None,
            },
        )

        # Properly chain the exception
        if underlying_error:
            self.__cause__ = underlying_error


class QueryError(ParquetFrameError):
    """Raised when query execution fails with helpful debugging info."""

    def __init__(
        self,
        query: str,
        error_message: str,
        query_type: str = "SQL",
        suggestions: list[str | None] = None,
    ):
        self.query = query
        self.query_type = query_type

        message = f"{query_type} query failed: {error_message}"

        suggestion_parts = []
        if suggestions:
            suggestion_parts.extend(suggestions)
        else:
            # Default suggestions based on common errors
            if (
                "table" in error_message.lower()
                and "not found" in error_message.lower()
            ):
                suggestion_parts.append("Use \\list to see available tables")
                suggestion_parts.append(
                    "Check table name spelling and case sensitivity"
                )
            elif "column" in error_message.lower():
                suggestion_parts.append(
                    "Use \\describe <table> to see available columns"
                )
                suggestion_parts.append("Check column name spelling")
            elif "syntax" in error_message.lower():
                suggestion_parts.append("Verify SQL syntax is correct")
                suggestion_parts.append("Check for missing quotes around string values")

        if suggestion_parts:
            suggestion = "\n".join(f"• {step}" for step in suggestion_parts)
        else:
            suggestion = "Check query syntax and table/column names"

        super().__init__(
            message=message,
            suggestion=suggestion,
            error_code="QUERY_ERROR",
            details={"query": query, "query_type": query_type},
        )


class AIError(ParquetFrameError):
    """Raised when AI/LLM operations fail."""

    def __init__(
        self,
        operation: str,
        error_message: str,
        natural_language_input: str | None = None,
        attempts: int = 1,
    ):
        self.operation = operation
        self.natural_language_input = natural_language_input
        self.attempts = attempts

        message = f"AI {operation} failed: {error_message}"

        suggestion_parts = [
            "Check that Ollama is running: ollama serve",
            "Verify the AI model is available: ollama list",
        ]

        if operation == "query_generation":
            suggestion_parts.extend(
                [
                    "Try rephrasing your question more clearly",
                    "Be specific about table and column names",
                    "Break complex questions into simpler parts",
                ]
            )
        elif "connection" in error_message.lower():
            suggestion_parts.extend(
                [
                    "Ensure Ollama is installed and running",
                    "Check network connectivity to Ollama service",
                ]
            )

        suggestion = "\n".join(f"• {step}" for step in suggestion_parts)

        super().__init__(
            message=message,
            suggestion=suggestion,
            error_code="AI_ERROR",
            details={
                "operation": operation,
                "natural_language_input": natural_language_input,
                "attempts": attempts,
            },
        )


class ConfigurationError(ParquetFrameError):
    """Raised when configuration is invalid or missing."""

    def __init__(
        self, config_item: str, issue: str, expected_format: str | None = None
    ):
        self.config_item = config_item
        self.issue = issue

        message = f"Configuration error in '{config_item}': {issue}"

        suggestion_parts = []
        if expected_format:
            suggestion_parts.append(f"Expected format: {expected_format}")

        suggestion_parts.extend(
            [
                "Check configuration file syntax",
                "Refer to documentation for valid configuration options",
            ]
        )

        suggestion = "\n".join(f"• {step}" for step in suggestion_parts)

        super().__init__(
            message=message, suggestion=suggestion, error_code="CONFIG_ERROR"
        )


def check_dependencies() -> dict[str, bool]:
    """Check availability of optional dependencies."""
    dependencies = {}

    # Core dependencies
    try:
        import pandas  # noqa: F401

        dependencies["pandas"] = True
    except ImportError:
        dependencies["pandas"] = False

    try:
        import pyarrow  # noqa: F401

        dependencies["pyarrow"] = True
    except ImportError:
        dependencies["pyarrow"] = False

    # AI dependencies
    try:
        import ollama  # noqa: F401

        dependencies["ollama"] = True
    except ImportError:
        dependencies["ollama"] = False

    # Interactive dependencies
    try:
        from prompt_toolkit import PromptSession  # noqa: F401

        dependencies["prompt_toolkit"] = True
    except ImportError:
        dependencies["prompt_toolkit"] = False

    try:
        from rich.console import Console  # noqa: F401

        dependencies["rich"] = True
    except ImportError:
        dependencies["rich"] = False

    # Database dependencies
    try:
        import sqlalchemy  # noqa: F401

        dependencies["sqlalchemy"] = True
    except ImportError:
        dependencies["sqlalchemy"] = False

    # Query engines
    try:
        import duckdb  # noqa: F401

        dependencies["duckdb"] = True
    except ImportError:
        dependencies["duckdb"] = False

    try:
        import polars  # noqa: F401

        dependencies["polars"] = True
    except ImportError:
        dependencies["polars"] = False

    return dependencies


def format_dependency_status() -> str:
    """Format dependency status for display."""
    deps = check_dependencies()

    lines = ["📦 Dependency Status:"]

    # Group dependencies by category
    core_deps = ["pandas", "pyarrow"]
    ai_deps = ["ollama"]
    interactive_deps = ["prompt_toolkit", "rich"]
    db_deps = ["sqlalchemy"]
    query_deps = ["duckdb", "polars"]

    categories = [
        ("Core", core_deps),
        ("AI Features", ai_deps),
        ("Interactive CLI", interactive_deps),
        ("Database Support", db_deps),
        ("Query Engines", query_deps),
    ]

    for category, dep_list in categories:
        lines.append(f"\n{category}:")
        for dep in dep_list:
            if dep in deps:
                status = "✅ Available" if deps[dep] else "❌ Missing"
                lines.append(f"  • {dep}: {status}")

    return "\n".join(lines)


def suggest_installation_commands() -> dict[str, str]:
    """Get installation commands for missing dependencies."""
    return {
        "pandas": "pip install pandas",
        "pyarrow": "pip install pyarrow",
        "ollama": "pip install ollama && ollama pull llama3.2",
        "prompt_toolkit": "pip install prompt-toolkit",
        "rich": "pip install rich",
        "sqlalchemy": "pip install sqlalchemy",
        "duckdb": "pip install duckdb",
        "polars": "pip install polars",
    }


def create_progress_spinner():
    """Create a progress spinner context manager for long operations."""
    try:
        from rich.console import Console
        from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

        console = Console()

        class ProgressSpinner:
            def __init__(self):
                self.progress = Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    TimeElapsedColumn(),
                    console=console,
                )
                self.task_id = None

            def __enter__(self):
                self.progress.__enter__()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.progress.__exit__(exc_type, exc_val, exc_tb)

            def update(self, description: str):
                if self.task_id is None:
                    self.task_id = self.progress.add_task(description)
                else:
                    self.progress.update(self.task_id, description=description)

        return ProgressSpinner()

    except ImportError:
        # Fallback for when rich is not available
        import contextlib

        @contextlib.contextmanager
        def simple_spinner():
            class SimpleSpinner:
                def update(self, description: str):
                    print(f"⏳ {description}...")

            yield SimpleSpinner()

        return simple_spinner()
