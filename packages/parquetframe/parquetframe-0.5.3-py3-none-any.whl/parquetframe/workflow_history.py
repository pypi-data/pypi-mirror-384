"""
Workflow execution history tracking for ParquetFrame.

This module provides functionality to track workflow execution with .hist files
containing detailed execution metrics, timings, and status information.
"""

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class StepExecution:
    """Record of a single workflow step execution."""

    name: str
    step_type: str
    status: str  # "running", "completed", "failed", "skipped"
    start_time: datetime
    end_time: datetime | None = None
    duration_seconds: float | None = None
    memory_usage_mb: float | None = None
    cpu_percent: float | None = None
    input_datasets: list[str] = field(default_factory=list)
    output_datasets: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)

    def start(self) -> None:
        """Mark the step as started."""
        self.status = "running"
        self.start_time = datetime.now()
        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            self.memory_usage_mb = process.memory_info().rss / 1024 / 1024
            self.cpu_percent = process.cpu_percent()

    def complete(self, output_datasets: list[str | None] = None) -> None:
        """Mark the step as completed successfully."""
        self.status = "completed"
        self.end_time = datetime.now()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        if output_datasets:
            self.output_datasets = output_datasets

        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            memory_after = process.memory_info().rss / 1024 / 1024
            if self.memory_usage_mb:
                self.metrics["memory_delta_mb"] = memory_after - self.memory_usage_mb
            self.memory_usage_mb = memory_after

    def fail(self, error_message: str) -> None:
        """Mark the step as failed with error message."""
        self.status = "failed"
        self.end_time = datetime.now()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        self.error_message = error_message

    def skip(self, reason: str) -> None:
        """Mark the step as skipped."""
        self.status = "skipped"
        self.end_time = datetime.now()
        self.error_message = reason


@dataclass
class WorkflowExecution:
    """Complete record of a workflow execution."""

    workflow_name: str
    workflow_file: str
    execution_id: str
    start_time: datetime
    end_time: datetime | None = None
    duration_seconds: float | None = None
    status: str = "running"  # "running", "completed", "failed", "cancelled"
    steps: list[StepExecution] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    system_info: dict[str, Any] = field(default_factory=dict)
    working_directory: str = ""
    total_memory_usage_mb: float | None = None
    peak_memory_usage_mb: float | None = None
    success_count: int = 0
    failure_count: int = 0
    skip_count: int = 0

    def __post_init__(self):
        """Initialize system information."""
        if PSUTIL_AVAILABLE:
            self.system_info = {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
                "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}.{__import__('sys').version_info.micro}",
                "platform": __import__("platform").system(),
            }

    def add_step(self, step: StepExecution) -> None:
        """Add a step execution record."""
        self.steps.append(step)

        # Update counters
        if step.status == "completed":
            self.success_count += 1
        elif step.status == "failed":
            self.failure_count += 1
        elif step.status == "skipped":
            self.skip_count += 1

        # Update peak memory usage
        if step.memory_usage_mb and (
            not self.peak_memory_usage_mb
            or step.memory_usage_mb > self.peak_memory_usage_mb
        ):
            self.peak_memory_usage_mb = step.memory_usage_mb

    def complete(self) -> None:
        """Mark the workflow execution as completed."""
        self.end_time = datetime.now()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        self.status = "completed" if self.failure_count == 0 else "failed"

        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            self.total_memory_usage_mb = process.memory_info().rss / 1024 / 1024

    def fail(self, error_message: str) -> None:
        """Mark the workflow execution as failed."""
        self.end_time = datetime.now()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        self.status = "failed"

    def get_summary_stats(self) -> dict[str, Any]:
        """Get summary statistics for the workflow execution."""
        return {
            "total_steps": len(self.steps),
            "successful_steps": self.success_count,
            "failed_steps": self.failure_count,
            "skipped_steps": self.skip_count,
            "total_duration_seconds": self.duration_seconds,
            "average_step_duration": (
                sum(step.duration_seconds or 0 for step in self.steps) / len(self.steps)
                if self.steps
                else 0
            ),
            "peak_memory_mb": self.peak_memory_usage_mb,
            "success_rate": self.success_count / len(self.steps) if self.steps else 0,
        }


class WorkflowHistoryManager:
    """Manager for workflow execution history and .hist files."""

    def __init__(self, history_dir: str | Path | None = None):
        """Initialize the history manager.

        Args:
            history_dir: Directory to store .hist files. Defaults to .parquetframe/history
        """
        if history_dir:
            self.history_dir = Path(history_dir)
        else:
            self.history_dir = Path.home() / ".parquetframe" / "history"

        self.history_dir.mkdir(parents=True, exist_ok=True)

    def create_execution_record(
        self,
        workflow_name: str,
        workflow_file: str,
        variables: dict[str, Any | None] = None,
    ) -> WorkflowExecution:
        """Create a new workflow execution record."""
        execution_id = f"{workflow_name}_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        return WorkflowExecution(
            workflow_name=workflow_name,
            workflow_file=str(workflow_file),
            execution_id=execution_id,
            start_time=datetime.now(),
            variables=variables or {},
            working_directory=str(Path.cwd()),
        )

    def save_execution_record(self, execution: WorkflowExecution) -> Path:
        """Save a workflow execution record to a .hist file."""
        hist_file = self.history_dir / f"{execution.execution_id}.hist"

        # Convert to JSON-serializable format
        data = asdict(execution)

        # Convert datetime objects to ISO strings
        def convert_datetime(obj):
            if isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        data = convert_datetime(data)

        with open(hist_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return hist_file

    def load_execution_record(self, hist_file: str | Path) -> WorkflowExecution:
        """Load a workflow execution record from a .hist file."""
        with open(hist_file) as f:
            data = json.load(f)

        # Convert ISO strings back to datetime objects
        def convert_datetime(obj):
            if isinstance(obj, dict):
                converted = {}
                for k, v in obj.items():
                    if k in ["start_time", "end_time"] and v:
                        try:
                            converted[k] = datetime.fromisoformat(v)
                        except (ValueError, TypeError):
                            converted[k] = v
                    else:
                        converted[k] = convert_datetime(v)
                return converted
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            return obj

        data = convert_datetime(data)

        # Reconstruct StepExecution objects
        steps = []
        for step_data in data.get("steps", []):
            steps.append(StepExecution(**step_data))

        data["steps"] = steps

        return WorkflowExecution(**data)

    def list_execution_records(self, workflow_name: str | None = None) -> list[Path]:
        """List all .hist files, optionally filtered by workflow name."""
        pattern = f"{workflow_name}_*.hist" if workflow_name else "*.hist"
        return sorted(
            self.history_dir.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

    def get_execution_summary(self, hist_file: str | Path) -> dict[str, Any]:
        """Get a summary of a workflow execution from its .hist file."""
        execution = self.load_execution_record(hist_file)
        return {
            "execution_id": execution.execution_id,
            "workflow_name": execution.workflow_name,
            "start_time": execution.start_time,
            "duration_seconds": execution.duration_seconds,
            "status": execution.status,
            "stats": execution.get_summary_stats(),
            "file_path": str(hist_file),
        }

    def cleanup_old_records(self, keep_days: int = 30) -> int:
        """Remove .hist files older than specified days."""
        cutoff_time = time.time() - (keep_days * 24 * 60 * 60)
        removed_count = 0

        for hist_file in self.history_dir.glob("*.hist"):
            if hist_file.stat().st_mtime < cutoff_time:
                hist_file.unlink()
                removed_count += 1

        return removed_count

    def get_workflow_statistics(
        self, workflow_name: str | None = None
    ) -> dict[str, Any]:
        """Get aggregate statistics for workflow executions."""
        hist_files = self.list_execution_records(workflow_name)

        if not hist_files:
            return {"message": "No execution records found"}

        total_executions = len(hist_files)
        successful_executions = 0
        failed_executions = 0
        total_duration = 0.0

        for hist_file in hist_files:
            try:
                execution = self.load_execution_record(hist_file)
                if execution.status == "completed":
                    successful_executions += 1
                else:
                    failed_executions += 1

                if execution.duration_seconds:
                    total_duration += execution.duration_seconds
            except Exception:
                # Skip corrupted files
                continue

        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate": (
                successful_executions / total_executions if total_executions > 0 else 0
            ),
            "average_duration_seconds": (
                total_duration / total_executions if total_executions > 0 else 0
            ),
            "total_duration_seconds": total_duration,
        }
