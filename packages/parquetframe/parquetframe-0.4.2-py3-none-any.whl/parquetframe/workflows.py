"""
YAML Workflow Engine for ParquetFrame

This module provides a declarative way to define and execute data processing workflows
using YAML configuration files. Workflows can include multiple steps with data
transformations, filtering, aggregations, and output operations.
"""

import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    from rich.console import Console
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
    )
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from .core import ParquetFrame
from .exceptions import ParquetFrameError
from .workflow_history import StepExecution, WorkflowHistoryManager


class WorkflowError(ParquetFrameError):
    """Base exception for workflow-related errors."""

    pass


class WorkflowValidationError(WorkflowError):
    """Exception raised when workflow validation fails."""

    pass


class WorkflowExecutionError(WorkflowError):
    """Exception raised when workflow execution fails."""

    pass


@dataclass
class WorkflowContext:
    """Context for workflow execution containing variables and intermediate results."""

    variables: dict[str, Any] = field(default_factory=dict)
    datasets: dict[str, ParquetFrame] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    working_dir: Path = field(default_factory=lambda: Path.cwd())

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a variable from the context."""
        return self.variables.get(name, default)

    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable in the context."""
        self.variables[name] = value

    def get_dataset(self, name: str) -> ParquetFrame | None:
        """Get a dataset from the context."""
        return self.datasets.get(name)

    def set_dataset(self, name: str, dataset: ParquetFrame) -> None:
        """Set a dataset in the context."""
        self.datasets[name] = dataset

    def resolve_path(self, path: str) -> Path:
        """Resolve a path relative to the working directory."""
        path_obj = Path(path)
        if path_obj.is_absolute():
            return path_obj
        return self.working_dir / path_obj


class WorkflowStep(ABC):
    """Abstract base class for workflow steps."""

    def __init__(self, name: str, config: dict[str, Any]):
        self.name = name
        self.config = config

    @abstractmethod
    def execute(self, context: WorkflowContext) -> Any:
        """Execute the workflow step."""
        pass

    @abstractmethod
    def validate(self) -> list[str]:
        """Validate the step configuration. Returns list of error messages."""
        pass

    def interpolate_variables(self, value: Any, context: WorkflowContext) -> Any:
        """Interpolate variables in string values using ${var} syntax."""
        if not isinstance(value, str):
            return value

        # Simple variable interpolation
        result = value
        for var_name, var_value in context.variables.items():
            result = result.replace(f"${{{var_name}}}", str(var_value))
            result = result.replace(
                f"${var_name}", str(var_value)
            )  # Support both ${var} and $var

        return result


class ReadStep(WorkflowStep):
    """Step to read data from parquet files."""

    def execute(self, context: WorkflowContext) -> ParquetFrame:
        input_path = self.interpolate_variables(self.config["input"], context)
        full_path = context.resolve_path(input_path)

        # Optional parameters
        threshold_mb = self.config.get("threshold_mb")
        islazy = self.config.get("islazy")
        columns = self.config.get("columns")

        # Read the file
        pf = ParquetFrame.read(str(full_path), threshold_mb=threshold_mb, islazy=islazy)

        # Column selection
        if columns:
            pf = pf[columns]

        # Store in context if output name specified
        output_name = self.config.get("output", "data")
        context.set_dataset(output_name, pf)

        return pf

    def validate(self) -> list[str]:
        errors = []
        if "input" not in self.config:
            errors.append(f"Step '{self.name}': 'input' is required")
        return errors


class FilterStep(WorkflowStep):
    """Step to filter data using queries."""

    def execute(self, context: WorkflowContext) -> ParquetFrame:
        # Get input dataset
        input_name = self.config.get("input", "data")
        pf = context.get_dataset(input_name)
        if pf is None:
            raise WorkflowExecutionError(
                f"Step '{self.name}': Dataset '{input_name}' not found"
            )

        # Apply query
        query = self.interpolate_variables(self.config["query"], context)
        filtered_pf = pf.query(query)

        # Store result
        output_name = self.config.get("output", input_name)
        context.set_dataset(output_name, filtered_pf)

        return filtered_pf

    def validate(self) -> list[str]:
        errors = []
        if "query" not in self.config:
            errors.append(f"Step '{self.name}': 'query' is required")
        return errors


class SelectStep(WorkflowStep):
    """Step to select specific columns."""

    def execute(self, context: WorkflowContext) -> ParquetFrame:
        input_name = self.config.get("input", "data")
        pf = context.get_dataset(input_name)
        if pf is None:
            raise WorkflowExecutionError(
                f"Step '{self.name}': Dataset '{input_name}' not found"
            )

        columns = self.config["columns"]
        if isinstance(columns, str):
            columns = [col.strip() for col in columns.split(",")]

        selected_pf = pf[columns]

        output_name = self.config.get("output", input_name)
        context.set_dataset(output_name, selected_pf)

        return selected_pf

    def validate(self) -> list[str]:
        errors = []
        if "columns" not in self.config:
            errors.append(f"Step '{self.name}': 'columns' is required")
        return errors


class GroupByStep(WorkflowStep):
    """Step to perform group by operations."""

    def execute(self, context: WorkflowContext) -> ParquetFrame:
        input_name = self.config.get("input", "data")
        pf = context.get_dataset(input_name)
        if pf is None:
            raise WorkflowExecutionError(
                f"Step '{self.name}': Dataset '{input_name}' not found"
            )

        by_columns = self.config["by"]
        if isinstance(by_columns, str):
            by_columns = [col.strip() for col in by_columns.split(",")]

        # Perform groupby
        grouped = pf.groupby(by_columns)

        # Apply aggregation
        agg_config = self.config.get("agg", "count")
        if isinstance(agg_config, str):
            # Simple aggregation
            result = getattr(grouped, agg_config)()
        elif isinstance(agg_config, dict):
            # Complex aggregation
            result = grouped.agg(agg_config)
        else:
            raise WorkflowExecutionError(
                f"Step '{self.name}': Invalid aggregation configuration"
            )

        # Wrap result in ParquetFrame if it isn't already
        if not isinstance(result, ParquetFrame):
            # Create a new ParquetFrame from the result
            if hasattr(result, "compute"):
                # Dask result
                result_pf = ParquetFrame(result, islazy=True)
            else:
                # Pandas result
                result_pf = ParquetFrame(result, islazy=False)
        else:
            result_pf = result

        output_name = self.config.get("output", input_name)
        context.set_dataset(output_name, result_pf)

        return result_pf

    def validate(self) -> list[str]:
        errors = []
        if "by" not in self.config:
            errors.append(f"Step '{self.name}': 'by' is required")
        return errors


class SaveStep(WorkflowStep):
    """Step to save data to parquet files."""

    def execute(self, context: WorkflowContext) -> Path:
        input_name = self.config.get("input", "data")
        pf = context.get_dataset(input_name)
        if pf is None:
            raise WorkflowExecutionError(
                f"Step '{self.name}': Dataset '{input_name}' not found"
            )

        output_path = self.interpolate_variables(self.config["output"], context)
        full_path = context.resolve_path(output_path)

        # Ensure parent directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Save the data
        pf.save(str(full_path))

        return full_path

    def validate(self) -> list[str]:
        errors = []
        if "output" not in self.config:
            errors.append(f"Step '{self.name}': 'output' is required")
        return errors


class TransformStep(WorkflowStep):
    """Step to apply custom transformations."""

    def execute(self, context: WorkflowContext) -> ParquetFrame:
        input_name = self.config.get("input", "data")
        pf = context.get_dataset(input_name)
        if pf is None:
            raise WorkflowExecutionError(
                f"Step '{self.name}': Dataset '{input_name}' not found"
            )

        # Apply transformations
        transforms = self.config["transforms"]
        if not isinstance(transforms, list):
            transforms = [transforms]

        result_pf = pf
        for transform in transforms:
            if "column" in transform and "operation" in transform:
                # Column-specific transformation
                col_name = transform["column"]
                operation = transform["operation"]

                if operation == "rename":
                    new_name = transform["to"]
                    result_pf = result_pf.rename(columns={col_name: new_name})
                elif operation == "drop":
                    result_pf = result_pf.drop(columns=[col_name])
                else:
                    # For more complex operations, we'd need to access the underlying DataFrame
                    # This is a simplified implementation
                    warnings.warn(
                        f"Transform operation '{operation}' not fully supported yet",
                        stacklevel=2,
                    )

        output_name = self.config.get("output", input_name)
        context.set_dataset(output_name, result_pf)

        return result_pf

    def validate(self) -> list[str]:
        errors = []
        if "transforms" not in self.config:
            errors.append(f"Step '{self.name}': 'transforms' is required")
        return errors


# Registry of available step types
STEP_REGISTRY = {
    "read": ReadStep,
    "filter": FilterStep,
    "select": SelectStep,
    "groupby": GroupByStep,
    "save": SaveStep,
    "transform": TransformStep,
}


class WorkflowEngine:
    """Main workflow engine for executing YAML workflows."""

    def __init__(
        self,
        verbose: bool = True,
        enable_history: bool = True,
        history_dir: str | Path | None = None,
    ):
        self.verbose = verbose
        self.console = Console() if RICH_AVAILABLE and verbose else None
        self.enable_history = enable_history
        self.history_manager = (
            WorkflowHistoryManager(history_dir) if enable_history else None
        )

    def load_workflow(self, workflow_path: str | Path) -> dict[str, Any]:
        """Load a workflow from a YAML file."""
        if not YAML_AVAILABLE:
            raise WorkflowError(
                "PyYAML is required for workflow support. Install with: pip install pyyaml"
            )

        path = Path(workflow_path)
        if not path.exists():
            raise WorkflowError(f"Workflow file not found: {path}")

        try:
            with open(path) as f:
                workflow = yaml.safe_load(f)

            if not isinstance(workflow, dict):
                raise WorkflowValidationError("Workflow must be a YAML dictionary")

            return workflow
        except yaml.YAMLError as e:
            raise WorkflowValidationError(f"Invalid YAML in workflow file: {e}") from e

    def validate_workflow(self, workflow: dict[str, Any]) -> list[str]:
        """Validate a workflow configuration."""
        errors = []

        # Check required top-level fields
        if "steps" not in workflow:
            errors.append("Workflow must contain 'steps' section")
            return errors

        steps = workflow["steps"]
        if not isinstance(steps, list):
            errors.append("'steps' must be a list")
            return errors

        # Validate each step
        for i, step_config in enumerate(steps):
            if not isinstance(step_config, dict):
                errors.append(f"Step {i}: Must be a dictionary")
                continue

            if "type" not in step_config:
                errors.append(f"Step {i}: 'type' is required")
                continue

            step_type = step_config["type"]
            if step_type not in STEP_REGISTRY:
                errors.append(f"Step {i}: Unknown step type '{step_type}'")
                continue

            # Validate step-specific configuration
            step_name = step_config.get("name", f"step_{i}")
            step_class = STEP_REGISTRY[step_type]
            step = step_class(step_name, step_config)
            step_errors = step.validate()
            errors.extend(step_errors)

        return errors

    def execute_workflow(
        self,
        workflow: dict[str, Any],
        working_dir: Path | None = None,
        variables: dict[str, Any | None] = None,
        workflow_file: str | None = None,
    ) -> WorkflowContext:
        """Execute a workflow."""

        # Create execution context
        context = WorkflowContext(
            working_dir=working_dir or Path.cwd(), variables=variables or {}
        )

        # Add workflow-level variables
        if "variables" in workflow:
            context.variables.update(workflow["variables"])

        steps = workflow["steps"]
        workflow_name = workflow.get("name", "unnamed_workflow")

        # Initialize execution history tracking
        execution_record = None
        if self.enable_history and self.history_manager:
            execution_record = self.history_manager.create_execution_record(
                workflow_name=workflow_name,
                workflow_file=workflow_file or "<inline>",
                variables=context.variables,
            )

        if self.verbose and self.console:
            self.console.print(
                f"\n[EXECUTE] [bold blue]Executing workflow '{workflow_name}' with {len(steps)} steps[/bold blue]"
            )

        # Execute steps
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console if self.verbose else None,
            disable=not self.verbose,
        ) as progress:
            main_task = progress.add_task("Processing workflow...", total=len(steps))

            try:
                for i, step_config in enumerate(steps):
                    step_name = step_config.get("name", f"step_{i}")
                    step_type = step_config["type"]

                    # Create step execution record
                    step_execution = None
                    if execution_record:
                        input_datasets = (
                            [step_config.get("input", "data")]
                            if "input" in step_config or step_type == "read"
                            else []
                        )
                        step_execution = StepExecution(
                            name=step_name,
                            step_type=step_type,
                            status="running",
                            start_time=__import__("datetime").datetime.now(),
                            input_datasets=input_datasets,
                            config=step_config,
                        )
                        step_execution.start()

                    if self.verbose:
                        progress.update(
                            main_task,
                            description=f"Executing {step_name} ({step_type})",
                        )

                    try:
                        # Create and execute step
                        step_class = STEP_REGISTRY[step_type]
                        step = step_class(step_name, step_config)
                        result = step.execute(context)

                        # Store step result in context
                        context.outputs[step_name] = result

                        # Update step execution record
                        if step_execution:
                            output_datasets = (
                                [step_config.get("output", step_name)]
                                if "output" in step_config
                                else []
                            )
                            step_execution.complete(output_datasets)
                            execution_record.add_step(step_execution)

                        if self.verbose and self.console:
                            self.console.print(f"  [SUCCESS] {step_name} completed")

                    except Exception as e:
                        error_msg = f"Step '{step_name}' failed: {e}"

                        # Update step execution record with failure
                        if step_execution:
                            step_execution.fail(str(e))
                            execution_record.add_step(step_execution)

                        if self.verbose and self.console:
                            self.console.print(f"  [ERROR] {error_msg}")
                        raise WorkflowExecutionError(error_msg) from e

                    progress.update(main_task, advance=1)

                # Mark workflow as completed
                if execution_record:
                    execution_record.complete()

            except Exception as e:
                # Mark workflow as failed
                if execution_record:
                    execution_record.fail(str(e))
                raise
            finally:
                # Save execution record
                if execution_record and self.history_manager:
                    hist_file = self.history_manager.save_execution_record(
                        execution_record
                    )
                    if self.verbose and self.console:
                        self.console.print(
                            f"\n[HISTORY] Execution history saved to: {hist_file}"
                        )

        if self.verbose and self.console:
            self.console.print(
                "\n[SUCCESS] [bold green]Workflow completed successfully![/bold green]"
            )

            # Show summary
            if context.datasets:
                table = Table(title="Workflow Results")
                table.add_column("Dataset", style="cyan")
                table.add_column("Shape", style="yellow")
                table.add_column("Backend", style="magenta")

                for name, dataset in context.datasets.items():
                    backend = "Dask" if dataset.islazy else "pandas"
                    shape = (
                        str(dataset.shape) if hasattr(dataset, "shape") else "Unknown"
                    )
                    table.add_row(name, shape, backend)

                self.console.print(table)

        return context

    def run_workflow_file(
        self,
        workflow_path: str | Path,
        variables: dict[str, Any | None] = None,
    ) -> WorkflowContext:
        """Load and execute a workflow from a file."""

        # Load workflow
        workflow = self.load_workflow(workflow_path)

        # Validate workflow
        errors = self.validate_workflow(workflow)
        if errors:
            error_msg = "Workflow validation failed:\n" + "\n".join(
                f"  • {error}" for error in errors
            )
            raise WorkflowValidationError(error_msg)

        # Set working directory to the workflow file's directory
        working_dir = Path(workflow_path).parent

        # Execute workflow
        return self.execute_workflow(
            workflow,
            working_dir=working_dir,
            variables=variables,
            workflow_file=str(workflow_path),
        )


def create_example_workflow() -> dict[str, Any]:
    """Create an example workflow for documentation and testing."""
    return {
        "name": "Example Data Processing Workflow",
        "description": "A sample workflow demonstrating common data processing operations",
        "variables": {"input_dir": "data", "output_dir": "results", "min_age": 18},
        "steps": [
            {
                "name": "load_data",
                "type": "read",
                "input": "${input_dir}/users.parquet",
                "output": "users",
            },
            {
                "name": "filter_adults",
                "type": "filter",
                "input": "users",
                "query": "age >= ${min_age}",
                "output": "adults",
            },
            {
                "name": "select_columns",
                "type": "select",
                "input": "adults",
                "columns": ["name", "age", "city"],
                "output": "selected",
            },
            {
                "name": "group_by_city",
                "type": "groupby",
                "input": "selected",
                "by": "city",
                "agg": {"age": ["mean", "count"]},
                "output": "city_stats",
            },
            {
                "name": "save_results",
                "type": "save",
                "input": "city_stats",
                "output": "${output_dir}/city_statistics.parquet",
            },
        ],
    }
