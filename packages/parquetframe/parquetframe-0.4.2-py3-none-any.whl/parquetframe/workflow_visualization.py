"""
Workflow DAG visualization for ParquetFrame workflows.

This module provides functionality to create visual representations of workflow
dependencies and execution flow using graphviz and networkx.
"""

import warnings
from pathlib import Path
from typing import Any

try:
    import networkx as nx

    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

try:
    import graphviz

    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False

from .workflow_history import WorkflowExecution


class WorkflowVisualizer:
    """Create visual representations of workflow DAGs."""

    def __init__(self):
        """Initialize the workflow visualizer."""
        if not NETWORKX_AVAILABLE and not GRAPHVIZ_AVAILABLE:
            raise ImportError(
                "Workflow visualization requires either networkx or graphviz. "
                "Install with: pip install networkx or pip install graphviz"
            )

    def create_dag_from_workflow(
        self,
        workflow: dict[str, Any],
        execution_data: WorkflowExecution | None = None,
    ) -> "nx.DiGraph":
        """Create a NetworkX directed graph from workflow definition.

        Args:
            workflow: Workflow definition dictionary
            execution_data: Optional execution data for status coloring

        Returns:
            NetworkX directed graph representing the workflow
        """
        if not NETWORKX_AVAILABLE:
            raise ImportError("NetworkX is required for DAG creation")

        G = nx.DiGraph()

        # Add workflow metadata
        workflow_name = workflow.get("name", "Unnamed Workflow")
        G.graph["name"] = workflow_name
        G.graph["description"] = workflow.get("description", "")

        steps = workflow.get("steps", [])

        # Add nodes for each step
        for i, step_config in enumerate(steps):
            step_name = step_config.get("name", f"step_{i}")
            step_type = step_config["type"]

            # Get execution status if available
            status = "pending"
            duration = None
            if execution_data:
                for step_exec in execution_data.steps:
                    if step_exec.name == step_name:
                        status = step_exec.status
                        duration = step_exec.duration_seconds
                        break

            G.add_node(
                step_name,
                type=step_type,
                config=step_config,
                status=status,
                duration=duration,
                index=i,
            )

        # Add edges based on data dependencies
        for i, step_config in enumerate(steps):
            step_name = step_config.get("name", f"step_{i}")

            # Check for input dependencies
            input_name = step_config.get("input")
            if input_name and input_name != "data":
                # Find the step that produces this output
                for j, prev_step_config in enumerate(steps[:i]):
                    prev_step_name = prev_step_config.get("name", f"step_{j}")
                    prev_output = prev_step_config.get("output", prev_step_name)
                    if prev_output == input_name:
                        G.add_edge(prev_step_name, step_name, type="data_dependency")
                        break

            # Add sequential dependencies for steps without explicit input
            if not input_name and i > 0:
                prev_step_config = steps[i - 1]
                prev_step_name = prev_step_config.get("name", f"step_{i - 1}")
                G.add_edge(prev_step_name, step_name, type="sequence")

        return G

    def visualize_with_graphviz(
        self,
        workflow: dict[str, Any],
        output_path: str | Path | None = None,
        format: str = "svg",
        execution_data: WorkflowExecution | None = None,
    ) -> str | None:
        """Create a Graphviz visualization of the workflow.

        Args:
            workflow: Workflow definition dictionary
            output_path: Optional path to save the visualization
            format: Output format (svg, png, pdf, etc.)
            execution_data: Optional execution data for status coloring

        Returns:
            Path to the generated file or None if not saved
        """
        if not GRAPHVIZ_AVAILABLE:
            raise ImportError(
                "Graphviz is required for visualization. Install with: pip install graphviz"
            )

        # Create a new Digraph
        dot = graphviz.Digraph(comment=workflow.get("name", "Workflow"))
        dot.attr(rankdir="TB", size="8,6")
        dot.attr("node", shape="box", style="rounded,filled")

        # Define colors for different statuses
        status_colors = {
            "completed": "#90EE90",  # Light green
            "failed": "#FFB6C1",  # Light red
            "running": "#87CEEB",  # Sky blue
            "pending": "#F0F0F0",  # Light gray
            "skipped": "#DDA0DD",  # Plum
        }

        # Define colors for different step types
        type_colors = {
            "read": "#E6F3FF",  # Light blue
            "filter": "#FFE6E6",  # Light red
            "select": "#E6FFE6",  # Light green
            "groupby": "#FFFFE6",  # Light yellow
            "save": "#F0E6FF",  # Light purple
            "transform": "#FFE6F0",  # Light pink
        }

        steps = workflow.get("steps", [])

        # Add nodes
        for i, step_config in enumerate(steps):
            step_name = step_config.get("name", f"step_{i}")
            step_type = step_config["type"]

            # Get execution status
            status = "pending"
            duration_str = ""
            if execution_data:
                for step_exec in execution_data.steps:
                    if step_exec.name == step_name:
                        status = step_exec.status
                        if step_exec.duration_seconds:
                            duration_str = f"\\n({step_exec.duration_seconds:.2f}s)"
                        break

            # Choose color based on status, fallback to type
            color = status_colors.get(status, type_colors.get(step_type, "#F0F0F0"))

            # Create label with step info
            label = f"{step_name}\\n[{step_type}]{duration_str}"

            dot.node(step_name, label=label, fillcolor=color)

        # Add edges
        G = self.create_dag_from_workflow(workflow, execution_data)
        for source, target, edge_data in G.edges(data=True):
            edge_type = edge_data.get("type", "sequence")
            if edge_type == "data_dependency":
                dot.edge(source, target, style="solid", color="blue")
            else:
                dot.edge(source, target, style="solid", color="black")

        # Add legend
        with dot.subgraph(name="cluster_legend") as legend:
            legend.attr(label="Legend", style="dashed")
            legend.node("legend_completed", "Completed", fillcolor="#90EE90")
            legend.node("legend_failed", "Failed", fillcolor="#FFB6C1")
            legend.node("legend_running", "Running", fillcolor="#87CEEB")
            legend.node("legend_pending", "Pending", fillcolor="#F0F0F0")

        if output_path:
            output_path = Path(output_path)
            if output_path.suffix:
                # Remove extension as graphviz adds it
                output_path = output_path.with_suffix("")

            dot.render(str(output_path), format=format, cleanup=True)
            return str(output_path.with_suffix(f".{format}"))
        else:
            return dot.source

    def visualize_with_networkx(
        self,
        workflow: dict[str, Any],
        output_path: str | Path | None = None,
        execution_data: WorkflowExecution | None = None,
    ) -> str | None:
        """Create a NetworkX visualization of the workflow.

        Args:
            workflow: Workflow definition dictionary
            output_path: Optional path to save the visualization
            execution_data: Optional execution data for status coloring

        Returns:
            Path to the generated file or None if not saved
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            warnings.warn(
                "matplotlib is required for NetworkX visualization. Install with: pip install matplotlib",
                stacklevel=2,
            )
            return None

        if not NETWORKX_AVAILABLE:
            raise ImportError(
                "NetworkX is required for visualization. Install with: pip install networkx"
            )

        G = self.create_dag_from_workflow(workflow, execution_data)

        # Create the plot
        plt.figure(figsize=(12, 8))
        plt.title(workflow.get("name", "Workflow DAG"), size=16)

        # Use hierarchical layout
        try:
            pos = nx.spring_layout(G, k=3, iterations=50)
        except Exception:
            # Fallback to shell layout
            pos = nx.shell_layout(G)

        # Define colors for different statuses
        status_colors = {
            "completed": "lightgreen",
            "failed": "lightcoral",
            "running": "lightblue",
            "pending": "lightgray",
            "skipped": "plum",
        }

        # Get node colors based on status
        node_colors = []
        for node in G.nodes():
            status = G.nodes[node].get("status", "pending")
            node_colors.append(status_colors.get(status, "lightgray"))

        # Draw the graph
        nx.draw(
            G,
            pos,
            with_labels=True,
            node_color=node_colors,
            node_size=3000,
            font_size=8,
            font_weight="bold",
            arrows=True,
            arrowsize=20,
            edge_color="gray",
            arrowstyle="->",
        )

        # Add step types as labels
        step_labels = {}
        for node in G.nodes():
            step_type = G.nodes[node].get("type", "")
            duration = G.nodes[node].get("duration")
            if duration:
                step_labels[node] = f"{node}\n[{step_type}]\n({duration:.2f}s)"
            else:
                step_labels[node] = f"{node}\n[{step_type}]"

        nx.draw_networkx_labels(G, pos, step_labels, font_size=6)

        plt.tight_layout()

        if output_path:
            plt.savefig(str(output_path), dpi=300, bbox_inches="tight")
            plt.close()
            return str(output_path)
        else:
            plt.show()
            return None

    def get_dag_statistics(self, workflow: dict[str, Any]) -> dict[str, Any]:
        """Get statistics about the workflow DAG structure.

        Args:
            workflow: Workflow definition dictionary

        Returns:
            Dictionary containing DAG statistics
        """
        if not NETWORKX_AVAILABLE:
            warnings.warn("NetworkX is required for DAG statistics", stacklevel=2)
            return {"error": "NetworkX not available"}

        G = self.create_dag_from_workflow(workflow)

        stats = {
            "total_steps": G.number_of_nodes(),
            "total_dependencies": G.number_of_edges(),
            "is_dag": nx.is_directed_acyclic_graph(G),
            "longest_path": (
                len(nx.dag_longest_path(G)) if nx.is_directed_acyclic_graph(G) else 0
            ),
            "complexity": (
                G.number_of_edges() / G.number_of_nodes()
                if G.number_of_nodes() > 0
                else 0
            ),
        }

        # Get step type distribution
        step_types = {}
        for node in G.nodes():
            step_type = G.nodes[node].get("type", "unknown")
            step_types[step_type] = step_types.get(step_type, 0) + 1

        stats["step_types"] = step_types

        # Check for potential issues
        issues = []
        if not nx.is_directed_acyclic_graph(G):
            issues.append("Workflow contains cycles")

        isolated_nodes = list(nx.isolates(G))
        if isolated_nodes:
            issues.append(f"Isolated steps: {isolated_nodes}")

        stats["potential_issues"] = issues

        return stats

    def export_to_mermaid(
        self,
        workflow: dict[str, Any],
        execution_data: WorkflowExecution | None = None,
    ) -> str:
        """Export workflow as Mermaid diagram syntax.

        Args:
            workflow: Workflow definition dictionary
            execution_data: Optional execution data for status coloring

        Returns:
            Mermaid diagram syntax string
        """
        lines = ["graph TD"]

        steps = workflow.get("steps", [])

        # Add nodes with styling
        for i, step_config in enumerate(steps):
            step_name = step_config.get("name", f"step_{i}")
            step_type = step_config["type"]

            # Get execution status
            status = "pending"
            if execution_data:
                for step_exec in execution_data.steps:
                    if step_exec.name == step_name:
                        status = step_exec.status
                        break

            # Clean step name for mermaid (no spaces or special chars)
            safe_name = step_name.replace(" ", "_").replace("-", "_")
            label = f"{step_name}<br/>[{step_type}]"

            lines.append(f'    {safe_name}["{label}"]')

            # Add styling based on status
            if status == "completed":
                lines.append(f"    style {safe_name} fill:#90EE90")
            elif status == "failed":
                lines.append(f"    style {safe_name} fill:#FFB6C1")
            elif status == "running":
                lines.append(f"    style {safe_name} fill:#87CEEB")

        # Add edges
        if NETWORKX_AVAILABLE:
            G = self.create_dag_from_workflow(workflow, execution_data)
            for source, target in G.edges():
                safe_source = source.replace(" ", "_").replace("-", "_")
                safe_target = target.replace(" ", "_").replace("-", "_")
                lines.append(f"    {safe_source} --> {safe_target}")

        return "\n".join(lines)
