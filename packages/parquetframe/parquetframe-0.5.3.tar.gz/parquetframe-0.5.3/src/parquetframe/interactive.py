"""
Interactive CLI session for parquetframe.

This module provides an interactive REPL interface that integrates DataContext
for data source management and LLM for natural language queries.
"""

from __future__ import annotations

import asyncio
import logging
import pickle
import sys
import time
from pathlib import Path
from typing import Any

from .ai import LLMAgent, LLMError
from .datacontext import DataContext, DataContextFactory
from .exceptions import DependencyError, check_dependencies, format_dependency_status
from .history import HistoryManager

logger = logging.getLogger(__name__)

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.shortcuts import confirm
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    INTERACTIVE_AVAILABLE = True
except ImportError:
    # Define fallback classes for testing when dependencies are not available
    class Console:
        def print(self, *args, **kwargs):
            pass

    class Panel:
        @staticmethod
        def fit(*args, **kwargs):
            return "Panel"

    class Table:
        def add_column(self, *args, **kwargs):
            pass

        def add_row(self, *args, **kwargs):
            pass

    class HTML:
        def __init__(self, text):
            self.text = text

    class PromptSession:
        def __init__(self, *args, **kwargs):
            pass

        def prompt(self, *args, **kwargs):
            return ""

    class WordCompleter:
        def __init__(self, *args, **kwargs):
            pass

    class InMemoryHistory:
        def __init__(self, *args, **kwargs):
            pass

    def confirm(*args, **kwargs):
        return True

    INTERACTIVE_AVAILABLE = False


class InteractiveSession:
    """
    Interactive CLI session for parquetframe.

    Provides a REPL interface with meta-commands for exploring data sources,
    executing queries, and using LLM-powered natural language queries.
    """

    def __init__(self, data_context: DataContext, enable_ai: bool = True):
        """
        Initialize interactive session.

        Args:
            data_context: DataContext for data source interaction
            enable_ai: Whether to enable LLM functionality
        """
        if not INTERACTIVE_AVAILABLE:
            raise DependencyError(
                missing_package="prompt_toolkit or rich",
                feature="interactive CLI mode",
                install_command="pip install parquetframe[ai,cli]",
            )

        self.data_context = data_context
        self.console = Console()
        self.history = InMemoryHistory()

        # Initialize LLM agent if available
        self.llm_agent: LLMAgent | None = None
        self.ai_enabled = False

        if enable_ai:
            try:
                self.llm_agent = LLMAgent()
                self.ai_enabled = True
                logger.info("AI functionality enabled")
            except (LLMError, Exception) as e:
                logger.warning(f"AI functionality disabled: {e}")
                self.ai_enabled = False

        # Session state and history management
        self.history_manager = HistoryManager()
        self.session_id = self.history_manager.create_session(
            data_source=str(data_context.source_location),
            data_source_type=data_context.source_type.value,
            ai_enabled=enable_ai,
        )
        self.query_history: list[dict[str, Any]] = []

        # Setup command completions
        meta_commands = [
            "\\help",
            "\\h",
            "\\?",
            "\\list",
            "\\l",
            "\\tables",
            "\\describe",
            "\\d",
            "\\ai",
            "\\llm",
            "\\history",
            "\\hist",
            "\\save-session",
            "\\load-session",
            "\\quit",
            "\\q",
            "\\exit",
        ]

        self.completer = WordCompleter(meta_commands, ignore_case=True)
        self.session = PromptSession(history=self.history, completer=self.completer)

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"session_{int(time.time())}"

    async def start(self) -> None:
        """Start the interactive session."""
        self.console.print()
        self.console.print(
            Panel.fit(
                "[bold blue]ParquetFrame Interactive Mode[/bold blue]\n"
                f"Data source: [green]{self.data_context.source_location}[/green]\n"
                f"Type: [yellow]{self.data_context.source_type.value}[/yellow]\n"
                f"AI enabled: [{'green' if self.ai_enabled else 'red'}]"
                f"{'Yes' if self.ai_enabled else 'No'}[/]\n\n"
                "Type [cyan]\\help[/cyan] for available commands",
                title="🚀 Welcome",
                border_style="blue",
            )
        )

        # Initialize data context
        try:
            await self.data_context.initialize()
            table_count = len(self.data_context.get_table_names())
            self.console.print(
                f"✅ Connected! Found [bold]{table_count}[/bold] table(s)"
            )
        except Exception as e:
            self.console.print(f"❌ Connection failed: {e}", style="red")
            return

        # Main REPL loop
        while True:
            try:
                # Create prompt with context info
                prompt_text = self._create_prompt()

                # Get user input
                user_input = await asyncio.to_thread(self.session.prompt, prompt_text)

                if not user_input.strip():
                    continue

                # Handle meta-commands vs SQL queries
                if user_input.strip().startswith("\\"):
                    should_continue = await self._handle_meta_command(
                        user_input.strip()
                    )
                    if not should_continue:
                        break
                else:
                    await self._handle_query(user_input.strip())

            except (EOFError, KeyboardInterrupt):
                self.console.print("\n👋 Goodbye!")
                # End session in history
                self.history_manager.end_session(self.session_id)
                break
            except Exception as e:
                self.console.print(f"❌ Error: {e}", style="red")
                logger.exception("Unexpected error in interactive session")

    def _create_prompt(self) -> HTML:
        """Create the interactive prompt."""
        source_type = self.data_context.source_type.value
        ai_indicator = "🤖" if self.ai_enabled else ""

        return HTML(
            f"<ansigreen>pframe</ansigreen>:"
            f"<ansiblue>{source_type}</ansiblue>"
            f"{ai_indicator}> "
        )

    async def _handle_meta_command(self, command: str) -> bool:
        """
        Handle meta-commands (starting with \\).

        Returns:
            True to continue session, False to exit
        """
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if cmd in ["\\help", "\\h", "\\?"]:
            await self._show_help()

        elif cmd in ["\\list", "\\l", "\\tables"]:
            await self._list_tables()

        elif cmd in ["\\describe", "\\d"]:
            if args:
                await self._describe_table(args[0])
            else:
                self.console.print("Usage: \\describe <table_name>", style="yellow")

        elif cmd in ["\\ai", "\\llm"]:
            await self._handle_ai_command(args)

        elif cmd in ["\\history", "\\hist"]:
            await self._show_history()

        elif cmd == "\\save-session":
            if args:
                await self._save_session(args[0])
            else:
                self.console.print("Usage: \\save-session <filename>", style="yellow")

        elif cmd == "\\load-session":
            if args:
                await self._load_session(args[0])
            else:
                self.console.print("Usage: \\load-session <filename>", style="yellow")

        elif cmd in ["\\save-script", "\\export-script"]:
            if args:
                await self._save_script(args[0])
            else:
                self.console.print("Usage: \\save-script <filename>", style="yellow")

        elif cmd in ["\\stats", "\\statistics"]:
            await self._show_statistics()

        elif cmd in ["\\deps", "\\dependencies"]:
            await self._show_dependencies()

        elif cmd in ["\\quit", "\\q", "\\exit"]:
            return False

        else:
            self.console.print(
                f"Unknown command: {cmd}. Type \\help for help.", style="yellow"
            )

        return True

    async def _handle_query(self, query: str) -> None:
        """Handle SQL query execution."""
        try:
            # Execute the query
            start_time = time.time()

            result = await self.data_context.execute(query)
            execution_time = (time.time() - start_time) * 1000

            # Display results
            self._display_query_result(result, execution_time)

            # Log to both in-memory and persistent history
            result_rows = len(result) if hasattr(result, "__len__") else None

            self.history_manager.log_query(
                session_id=self.session_id,
                query_text=query,
                query_type="sql",
                execution_time_ms=execution_time,
                success=True,
                result_rows=result_rows,
            )

            self.query_history.append(
                {
                    "query": query,
                    "timestamp": time.time(),
                    "execution_time_ms": execution_time,
                    "success": True,
                    "error": None,
                }
            )

        except Exception as e:
            self.console.print(f"❌ Query failed: {e}", style="red")

            # Log failed query to both histories
            self.history_manager.log_query(
                session_id=self.session_id,
                query_text=query,
                query_type="sql",
                success=False,
                error_message=str(e),
            )

            self.query_history.append(
                {
                    "query": query,
                    "timestamp": time.time(),
                    "execution_time_ms": None,
                    "success": False,
                    "error": str(e),
                }
            )

    async def _handle_ai_command(self, args: list[str]) -> None:
        """Handle AI/LLM commands."""
        if not self.ai_enabled:
            self.console.print("❌ AI functionality not available", style="red")
            return

        if not args:
            self.console.print(
                "Usage: \\ai <natural language question>", style="yellow"
            )
            return

        natural_query = " ".join(args)

        try:
            self.console.print(f"🤖 Processing: [italic]{natural_query}[/italic]")

            with self.console.status("[bold green]Thinking..."):
                result = await self.llm_agent.generate_query(
                    natural_query, self.data_context
                )

            if result.success:
                # Show generated query and ask for approval
                self.console.print("\n📝 Generated Query:", style="bold")
                self.console.print(
                    Panel(result.query, expand=False, border_style="green")
                )

                # Ask for approval (run confirm in thread to avoid event loop conflict)
                user_confirmed = await asyncio.to_thread(
                    confirm, "\n🚀 Execute this query? [Y/n]"
                )
                if user_confirmed:
                    self._display_query_result(result.result, result.execution_time_ms)

                    # Log to persistent history
                    result_rows = (
                        len(result.result)
                        if hasattr(result.result, "__len__")
                        else None
                    )

                    self.history_manager.log_query(
                        session_id=self.session_id,
                        query_text=result.query,
                        query_type="natural_language",
                        execution_time_ms=result.execution_time_ms,
                        success=True,
                        result_rows=result_rows,
                        ai_generated=True,
                        natural_language_input=natural_query,
                        ai_attempts=result.attempts,
                    )

                    # Also log the AI interaction
                    self.history_manager.log_ai_message(
                        session_id=self.session_id,
                        natural_language_input=natural_query,
                        generated_sql=result.query,
                        success=True,
                        attempts=result.attempts,
                        final_result=(
                            f"Returned {result_rows} rows"
                            if result_rows
                            else "Query executed successfully"
                        ),
                    )

                    # Log to in-memory history
                    self.query_history.append(
                        {
                            "query": result.query,
                            "natural_language": natural_query,
                            "timestamp": time.time(),
                            "execution_time_ms": result.execution_time_ms,
                            "success": True,
                            "ai_generated": True,
                            "attempts": result.attempts,
                        }
                    )
                else:
                    self.console.print("❌ Query cancelled", style="yellow")
            else:
                self.console.print(
                    f"❌ Failed to generate query: {result.error}", style="red"
                )
                if result.query:
                    self.console.print(f"Last attempted query: {result.query}")

        except Exception as e:
            self.console.print(f"❌ AI error: {e}", style="red")
            logger.exception("AI command failed")

    def _display_query_result(
        self, result: Any, execution_time_ms: float | None
    ) -> None:
        """Display query results in a formatted table."""
        try:
            # Handle pandas DataFrame
            if hasattr(result, "head"):
                df = result

                # Limit display rows
                display_rows = min(20, len(df))
                display_df = df.head(display_rows)

                # Create Rich table
                table = Table(show_header=True, header_style="bold blue")

                # Add columns
                for col in display_df.columns:
                    table.add_column(str(col))

                # Add rows
                for _, row in display_df.iterrows():
                    table.add_row(*[str(val) for val in row])

                self.console.print()
                self.console.print(table)

                # Show summary
                time_info = (
                    f" in {execution_time_ms:.2f}ms" if execution_time_ms else ""
                )
                if len(df) > display_rows:
                    self.console.print(
                        f"📊 Showing {display_rows} of {len(df)} rows{time_info}",
                        style="dim",
                    )
                else:
                    self.console.print(f"📊 {len(df)} rows{time_info}", style="dim")

            else:
                # Handle other result types
                self.console.print(f"Result: {result}")
                if execution_time_ms:
                    self.console.print(
                        f"Execution time: {execution_time_ms:.2f}ms", style="dim"
                    )

        except Exception as e:
            self.console.print(f"Error displaying results: {e}", style="red")
            self.console.print(f"Raw result: {result}")

    async def _show_help(self) -> None:
        """Show help information."""
        help_text = """
[bold blue]ParquetFrame Interactive Commands[/bold blue]

[bold]Data Exploration:[/bold]
  \\list, \\l, \\tables     List all available tables
  \\describe <table>       Show detailed table schema

[bold]Querying:[/bold]
  <SQL query>             Execute SQL query directly
  \\ai <question>          Ask question in natural language 🤖

[bold]Session Management:[/bold]
  \\history                Show query history
  \\save-session <file>    Save current session
  \\load-session <file>    Load saved session

[bold]Other:[/bold]
  \\help, \\h, \\?           Show this help
  \\quit, \\q, \\exit        Exit interactive mode

[bold]Examples:[/bold]
  SELECT * FROM users LIMIT 10;
  \\ai how many users are there?
  \\describe users
"""
        self.console.print(Panel(help_text, title="📚 Help", border_style="blue"))

    async def _list_tables(self) -> None:
        """List all available tables."""
        try:
            table_names = self.data_context.get_table_names()

            if not table_names:
                self.console.print("No tables found", style="yellow")
                return

            # Create table listing
            table = Table(
                title="📋 Available Tables", show_header=True, header_style="bold blue"
            )
            table.add_column("Table Name")
            table.add_column("Type")

            for name in table_names:
                source_type = (
                    "Virtual"
                    if self.data_context.source_type.value == "parquet"
                    else "Database"
                )
                table.add_row(name, source_type)

            self.console.print(table)

        except Exception as e:
            self.console.print(f"❌ Error listing tables: {e}", style="red")

    async def _describe_table(self, table_name: str) -> None:
        """Describe a specific table."""
        try:
            schema_info = self.data_context.get_table_schema(table_name)

            # Create schema table
            table = Table(
                title=f"🔍 Table Schema: {table_name}",
                show_header=True,
                header_style="bold blue",
            )
            table.add_column("Column")
            table.add_column("Type")
            table.add_column("Nullable")

            if "columns" in schema_info:
                for col in schema_info["columns"]:
                    nullable = "✓" if col.get("nullable", True) else "✗"
                    table.add_row(
                        col["name"],
                        col.get("sql_type", col.get("type", "UNKNOWN")),
                        nullable,
                    )

            self.console.print(table)

            # Show additional info
            if "file_count" in schema_info:
                self.console.print(
                    f"📁 Files: {schema_info['file_count']}", style="dim"
                )
            if "source_location" in schema_info:
                self.console.print(
                    f"📍 Source: {schema_info['source_location']}", style="dim"
                )

        except Exception as e:
            self.console.print(
                f"❌ Error describing table '{table_name}': {e}", style="red"
            )

    async def _show_history(self) -> None:
        """Show query history."""
        if not self.query_history:
            self.console.print("No query history", style="yellow")
            return

        table = Table(
            title="📚 Query History", show_header=True, header_style="bold blue"
        )
        table.add_column("#", justify="right", style="dim")
        table.add_column("Query")
        table.add_column("Status")
        table.add_column("Time (ms)", justify="right")

        for i, entry in enumerate(self.query_history[-10:], 1):  # Show last 10
            query = (
                entry["query"][:60] + "..."
                if len(entry["query"]) > 60
                else entry["query"]
            )
            status = "✅" if entry["success"] else "❌"
            time_str = (
                f"{entry['execution_time_ms']:.1f}"
                if entry.get("execution_time_ms")
                else "N/A"
            )

            style = None if entry["success"] else "red"
            table.add_row(str(i), query, status, time_str, style=style)

        self.console.print(table)

    async def _save_session(self, filename: str) -> None:
        """Save current session to file."""
        try:
            session_data = {
                "session_id": self.session_id,
                "data_context_config": {
                    "source_location": self.data_context.source_location,
                    "source_type": self.data_context.source_type.value,
                },
                "query_history": self.query_history,
                "ai_enabled": self.ai_enabled,
            }

            # Ensure sessions directory exists
            sessions_dir = Path.home() / ".parquetframe" / "sessions"
            sessions_dir.mkdir(parents=True, exist_ok=True)

            session_file = sessions_dir / f"{filename}.pkl"

            with open(session_file, "wb") as f:
                pickle.dump(session_data, f)

            self.console.print(f"💾 Session saved to: {session_file}", style="green")

        except Exception as e:
            self.console.print(f"❌ Error saving session: {e}", style="red")

    async def _load_session(self, filename: str) -> None:
        """Load session from file."""
        try:
            sessions_dir = Path.home() / ".parquetframe" / "sessions"
            session_file = sessions_dir / f"{filename}.pkl"

            if not session_file.exists():
                self.console.print(
                    f"❌ Session file not found: {session_file}", style="red"
                )
                return

            with open(session_file, "rb") as f:
                session_data = pickle.load(f)

            # Restore query history
            self.query_history = session_data.get("query_history", [])

            self.console.print(
                f"📂 Loaded session: {len(self.query_history)} queries in history",
                style="green",
            )

        except Exception as e:
            self.console.print(f"❌ Error loading session: {e}", style="red")

    async def _save_script(self, filename: str) -> None:
        """Export session queries as SQL script."""
        try:
            # Determine output path
            if not filename.endswith(".sql"):
                filename += ".sql"

            output_path = Path(filename)
            if not output_path.is_absolute():
                output_path = Path.cwd() / filename

            # Export using history manager
            self.history_manager.export_session_script(
                session_id=self.session_id,
                output_path=output_path,
                include_ai_queries=True,
                include_failed_queries=False,
            )

            self.console.print(
                f"📝 Session script exported to: {output_path}", style="green"
            )

        except Exception as e:
            self.console.print(f"❌ Error exporting script: {e}", style="red")

    async def _show_statistics(self) -> None:
        """Show session and overall usage statistics."""
        try:
            # Get overall statistics
            stats = self.history_manager.get_statistics()

            # Create statistics table
            table = Table(
                title="📊 ParquetFrame Usage Statistics",
                show_header=True,
                header_style="bold blue",
            )
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white", justify="right")

            # Add overall statistics
            table.add_row("Total Sessions", str(stats["total_sessions"]))
            table.add_row("Total Queries", str(stats["total_queries"]))
            table.add_row("Successful Queries", str(stats["successful_queries"]))
            table.add_row("Query Success Rate", f"{stats['query_success_rate']:.1%}")

            if stats["total_ai_messages"] > 0:
                table.add_row("AI Messages", str(stats["total_ai_messages"]))
                table.add_row("AI Success Rate", f"{stats['ai_success_rate']:.1%}")

            table.add_row("Recent Sessions (7d)", str(stats["recent_sessions_7d"]))

            self.console.print(table)

            # Current session info
            current_queries = len(self.query_history)
            successful_current = len(
                [q for q in self.query_history if q.get("success", False)]
            )

            self.console.print("\n[bold]Current Session:[/bold]")
            self.console.print(f"  • Session ID: [dim]{self.session_id[:8]}...[/dim]")
            self.console.print(
                f"  • Queries executed: [green]{current_queries}[/green]"
            )
            if current_queries > 0:
                self.console.print(
                    f"  • Success rate: [green]{successful_current / current_queries:.1%}[/green]"
                )
            self.console.print(
                f"  • AI enabled: [{'green' if self.ai_enabled else 'red'}]{'Yes' if self.ai_enabled else 'No'}[/]"
            )

        except Exception as e:
            self.console.print(f"❌ Error showing statistics: {e}", style="red")

    async def _show_dependencies(self) -> None:
        """Show dependency status and installation guidance."""
        try:
            # Format and display dependency status
            status_text = format_dependency_status()
            self.console.print(status_text)

            # Show missing dependencies with installation commands
            deps = check_dependencies()
            missing_deps = [dep for dep, available in deps.items() if not available]

            if missing_deps:
                from .exceptions import suggest_installation_commands

                install_commands = suggest_installation_commands()

                self.console.print(
                    "\n🔧 [bold yellow]Installation Commands for Missing Dependencies:[/bold yellow]"
                )
                for dep in missing_deps:
                    if dep in install_commands:
                        self.console.print(
                            f"  • {dep}: [cyan]{install_commands[dep]}[/cyan]"
                        )
            else:
                self.console.print(
                    "\n✅ [bold green]All dependencies are available![/bold green]"
                )

        except Exception as e:
            self.console.print(f"❌ Error checking dependencies: {e}", style="red")

    async def _show_help(self) -> None:
        """Show enhanced help information."""
        help_text = """
[bold blue]ParquetFrame Interactive Commands[/bold blue]

[bold]Data Exploration:[/bold]
  \\list, \\l, \\tables     List all available tables
  \\describe <table>       Show detailed table schema

[bold]Querying:[/bold]
  <SQL query>             Execute SQL query directly
  \\ai <question>          Ask question in natural language 🤖

[bold]Session Management:[/bold]
  \\history                Show query history
  \\save-session <file>    Save current session
  \\load-session <file>    Load saved session
  \\save-script <file>     Export queries as SQL script
  \\stats                  Show usage statistics
  \\deps                   Show dependency status

[bold]Other:[/bold]
  \\help, \\h, \\?           Show this help
  \\quit, \\q, \\exit        Exit interactive mode

[bold]Examples:[/bold]
  SELECT * FROM users LIMIT 10;
  \\ai show me top 10 customers by revenue
  \\describe customers
  \\save-script my_analysis.sql
        """

        self.console.print(
            Panel(help_text, title="Help", border_style="blue", expand=False)
        )


async def start_interactive_session(
    path: str | None = None, db_uri: str | None = None, enable_ai: bool = True
) -> None:
    """
    Start an interactive parquetframe session.

    Args:
        path: Path to parquet directory
        db_uri: Database connection URI
        enable_ai: Whether to enable AI functionality
    """
    try:
        # Create DataContext
        data_context = DataContextFactory.create_context(path=path, db_uri=db_uri)

        # Create and start interactive session
        session = InteractiveSession(data_context, enable_ai=enable_ai)
        await session.start()

    except Exception as e:
        from rich.console import Console

        console = Console()
        console.print(f"❌ Failed to start interactive session: {e}", style="red")
        sys.exit(1)
    finally:
        # Clean up DataContext
        if "data_context" in locals():
            data_context.close()
