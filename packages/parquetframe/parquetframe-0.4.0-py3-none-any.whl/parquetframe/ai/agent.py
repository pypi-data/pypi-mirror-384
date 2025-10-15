"""
LLM Agent for natural language to SQL conversion.

This module provides the main LLMAgent class that integrates with ollama
for local LLM inference, with self-correction capabilities and integration
with DataContext for query validation and execution.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .prompts import (
    MultiStepQueryPromptBuilder,
    QueryPromptBuilder,
    SelfCorrectionPromptBuilder,
)

if TYPE_CHECKING:
    from ..datacontext import DataContext

from ..exceptions import DependencyError

logger = logging.getLogger(__name__)

# Optional dependency for ollama
try:
    import ollama

    OLLAMA_AVAILABLE = True
except ImportError:
    ollama = None  # type: ignore
    OLLAMA_AVAILABLE = False


class LLMError(Exception):
    """Base exception for LLM-related errors."""

    pass


@dataclass
class QueryResult:
    """Result of an LLM query generation and execution attempt."""

    success: bool
    query: str | None
    result: Any | None
    error: str | None
    attempts: int
    execution_time_ms: float | None = None

    @property
    def failed(self) -> bool:
        """Check if the query generation/execution failed."""
        return not self.success


class LLMAgent:
    """
    LLM Agent for natural language to SQL conversion.

    This agent uses ollama for local LLM inference, with sophisticated prompt
    engineering, self-correction capabilities, and integration with DataContext
    for query validation and execution.
    """

    def __init__(
        self,
        model_name: str = "llama3.2",
        max_retries: int = 2,
        use_multi_step: bool = False,
        temperature: float = 0.1,
    ):
        """
        Initialize the LLM Agent.

        Args:
            model_name: Ollama model to use (e.g., 'llama3.2', 'codellama')
            max_retries: Maximum number of self-correction attempts
            use_multi_step: Whether to use multi-step reasoning for complex queries
            temperature: LLM temperature for query generation (lower = more deterministic)
        """
        if not OLLAMA_AVAILABLE:
            raise DependencyError(
                missing_package="ollama",
                feature="AI-powered query generation",
                install_command="pip install ollama && ollama pull llama3.2",
            )

        self.model_name = model_name
        self.max_retries = max_retries
        self.use_multi_step = use_multi_step
        self.temperature = temperature

        # Prompt builders
        self.query_builder = QueryPromptBuilder()
        self.multi_step_builder = MultiStepQueryPromptBuilder()
        self.correction_builder = SelfCorrectionPromptBuilder()

        # Verify model availability
        self._verify_model_available()

    def _get_ollama_module(self):
        """Get ollama module, handling dynamic imports for testing."""
        # This allows tests to mock ollama even when not installed
        if not OLLAMA_AVAILABLE and ollama is None:
            try:
                import ollama as _ollama

                return _ollama
            except ImportError:
                return None
        return ollama

    def _verify_model_available(self) -> None:
        """Verify that the specified model is available in ollama."""
        try:
            _ollama = self._get_ollama_module()
            if _ollama is None:
                return

            models = _ollama.list()
            available_models = []
            for model in models.get("models", []):
                if isinstance(model, dict) and "name" in model:
                    available_models.append(model["name"])
                elif hasattr(model, "name"):
                    available_models.append(model.name)

            # Check if exact model name or model name with :latest tag matches
            model_matches = [
                model_name
                for model_name in available_models
                if model_name == self.model_name
                or model_name.startswith(f"{self.model_name}:")
                or f"{self.model_name}:latest" == model_name
            ]

            if not model_matches:
                logger.warning(
                    f"Model '{self.model_name}' not found in ollama. "
                    f"Available models: {available_models}. "
                    f"Consider running: ollama pull {self.model_name}"
                )
        except Exception as e:
            logger.warning(f"Could not verify model availability: {e}")

    async def generate_query(
        self, natural_language_query: str, data_context: DataContext
    ) -> QueryResult:
        """
        Generate and optionally execute a SQL query from natural language.

        Args:
            natural_language_query: User's question in natural language
            data_context: DataContext containing schema and query execution capabilities

        Returns:
            QueryResult with the generated query and execution results
        """
        logger.info(f"Processing query: {natural_language_query[:100]}...")

        if not data_context.is_initialized:
            await data_context.initialize()

        try:
            # Step 1: Generate initial query
            if self.use_multi_step and len(data_context.get_table_names()) > 3:
                query = await self._generate_query_multi_step(
                    natural_language_query, data_context
                )
            else:
                query = await self._generate_query_single_step(
                    natural_language_query, data_context
                )

            if not query:
                return QueryResult(
                    success=False,
                    query=None,
                    result=None,
                    error="Failed to generate query from LLM",
                    attempts=1,
                )

            # Step 2: Attempt execution with self-correction
            return await self._execute_with_correction(
                query, natural_language_query, data_context
            )

        except Exception as e:
            logger.error(f"Query generation failed: {e}")
            return QueryResult(
                success=False,
                query=None,
                result=None,
                error=str(e),
                attempts=1,
            )

    async def _generate_query_single_step(
        self, natural_language_query: str, data_context: DataContext
    ) -> str | None:
        """Generate query using single-step approach."""
        schema_context = data_context.get_schema_as_text()
        table_names = data_context.get_table_names()
        main_table = table_names[0] if table_names else None

        prompt = self.query_builder.build_for_context(schema_context, main_table)
        full_prompt = f'{prompt}\n\nQuestion: "{natural_language_query}"'

        logger.debug(f"Single-step prompt: {full_prompt[:200]}...")

        try:
            _ollama = self._get_ollama_module()
            if _ollama is None:
                logger.error("Ollama module not available")
                return None

            response = _ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": full_prompt}],
                options={"temperature": self.temperature},
            )

            return self._extract_sql_from_response(response["message"]["content"])

        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            return None

    async def _generate_query_multi_step(
        self, natural_language_query: str, data_context: DataContext
    ) -> str | None:
        """Generate query using multi-step reasoning approach."""
        logger.info("Using multi-step reasoning for complex query")

        # Step 1: Select relevant tables
        table_names = data_context.get_table_names()
        table_selection_prompt = self.multi_step_builder.build_table_selection_prompt(
            table_names
        )

        full_selection_prompt = (
            f'{table_selection_prompt}\n\nUser Question: "{natural_language_query}"'
        )

        try:
            _ollama = self._get_ollama_module()
            if _ollama is None:
                logger.error("Ollama module not available")
                return None

            response = _ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": full_selection_prompt}],
                options={"temperature": self.temperature},
            )

            selected_tables_text = response["message"]["content"].strip()
            selected_tables = [
                table.strip()
                for table in selected_tables_text.split(",")
                if table.strip()
            ]

            logger.debug(f"Selected tables: {selected_tables}")

            # Step 2: Generate focused schema for selected tables
            focused_schema_parts = []
            for table_name in selected_tables:
                if table_name in table_names:
                    try:
                        data_context.get_table_schema(table_name)
                        # Convert to CREATE TABLE format (simplified)
                        focused_schema_parts.append(f"-- Table: {table_name}")
                    except Exception as e:
                        logger.warning(f"Could not get schema for {table_name}: {e}")

            if not focused_schema_parts:
                # Fallback to full schema
                logger.info("Falling back to single-step approach")
                return await self._generate_query_single_step(
                    natural_language_query, data_context
                )

            # Get detailed schema for selected tables only
            focused_schema = self._build_focused_schema(selected_tables, data_context)

            # Step 3: Generate query with focused context
            focused_prompt = self.multi_step_builder.build_focused_query_prompt(
                focused_schema
            )
            full_query_prompt = (
                f'{focused_prompt}\n\nQuestion: "{natural_language_query}"'
            )

            _ollama = self._get_ollama_module()
            if _ollama is None:
                logger.error("Ollama module not available for second call")
                return None

            response = _ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": full_query_prompt}],
                options={"temperature": self.temperature},
            )

            return self._extract_sql_from_response(response["message"]["content"])

        except Exception as e:
            logger.error(f"Multi-step query generation failed: {e}")
            return None

    def _build_focused_schema(
        self, table_names: list[str], data_context: DataContext
    ) -> str:
        """Build schema context for only the selected tables."""
        schema_parts = []

        for table_name in table_names:
            try:
                table_info = data_context.get_table_schema(table_name)
                if "columns" in table_info:
                    columns_info = []
                    for col in table_info["columns"]:
                        col_def = f"  {col['name']} {col.get('sql_type', 'VARCHAR')}"
                        if not col.get("nullable", True):
                            col_def += " NOT NULL"
                        columns_info.append(col_def)

                    create_statement = (
                        f"CREATE TABLE {table_name} (\n"
                        + ",\n".join(columns_info)
                        + "\n);"
                    )
                    schema_parts.append(create_statement)
            except Exception as e:
                logger.warning(f"Could not build schema for {table_name}: {e}")

        return "\n\n".join(schema_parts)

    async def _execute_with_correction(
        self,
        initial_query: str,
        original_question: str,
        data_context: DataContext,
    ) -> QueryResult:
        """Execute query with self-correction on errors."""
        current_query = initial_query
        attempts = 1

        for attempt in range(self.max_retries + 1):
            try:
                # Validate query syntax first
                is_valid = await data_context.validate_query(current_query)
                if not is_valid and attempt == 0:
                    logger.info(
                        "Initial query validation failed, attempting correction"
                    )

                # Execute the query
                import time

                start_time = time.time()
                result = await data_context.execute(current_query)
                execution_time = (time.time() - start_time) * 1000

                logger.info(f"Query executed successfully in {execution_time:.2f}ms")
                return QueryResult(
                    success=True,
                    query=current_query,
                    result=result,
                    error=None,
                    attempts=attempts,
                    execution_time_ms=execution_time,
                )

            except Exception as e:
                error_message = str(e)
                logger.warning(
                    f"Query execution failed (attempt {attempt + 1}): {error_message}"
                )

                # If we've exhausted retries, return failure
                if attempt >= self.max_retries:
                    return QueryResult(
                        success=False,
                        query=current_query,
                        result=None,
                        error=error_message,
                        attempts=attempts,
                    )

                # Attempt self-correction
                logger.info(f"Attempting self-correction (attempt {attempt + 1})")
                corrected_query = await self._self_correct_query(
                    current_query, error_message, data_context
                )

                if corrected_query and corrected_query != current_query:
                    current_query = corrected_query
                    attempts += 1
                    logger.info(f"Generated corrected query: {current_query[:100]}...")
                else:
                    logger.warning("Self-correction failed to generate new query")
                    return QueryResult(
                        success=False,
                        query=current_query,
                        result=None,
                        error=f"Self-correction failed after {attempts} attempts: {error_message}",
                        attempts=attempts,
                    )

        # This should not be reached
        return QueryResult(
            success=False,
            query=current_query,
            result=None,
            error="Unexpected error in execution loop",
            attempts=attempts,
        )

    async def _self_correct_query(
        self, failed_query: str, error_message: str, data_context: DataContext
    ) -> str | None:
        """Attempt to correct a failed query using LLM."""
        schema_context = data_context.get_schema_as_text()

        correction_prompt = self.correction_builder.build_correction_prompt(
            failed_query, error_message, schema_context
        )

        try:
            _ollama = self._get_ollama_module()
            if _ollama is None:
                logger.error("Ollama module not available for correction")
                return None

            response = _ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": correction_prompt}],
                options={
                    "temperature": self.temperature * 0.8
                },  # Slightly lower temperature
            )

            corrected_query = self._extract_sql_from_response(
                response["message"]["content"]
            )
            return corrected_query

        except Exception as e:
            logger.error(f"Self-correction API call failed: {e}")
            return None

    def _extract_sql_from_response(self, response_text: str) -> str | None:
        """Extract SQL query from LLM response (handles markdown code blocks)."""
        # Look for SQL code blocks
        sql_pattern = r"```sql\s*\n(.*?)\n\s*```"
        matches = re.findall(sql_pattern, response_text, re.DOTALL | re.IGNORECASE)

        if matches:
            # Get the first SQL block and clean it up
            sql = matches[0].strip()
            # Remove any comment lines at the start
            lines = sql.split("\n")
            cleaned_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith("--"):
                    cleaned_lines.append(line)
                elif cleaned_lines:  # Keep comments if they're in the middle
                    cleaned_lines.append(line)

            return "\n".join(cleaned_lines) if cleaned_lines else None

        # Fallback: look for any SQL-like content
        # This is a simple heuristic for SQL detection
        if any(
            keyword in response_text.upper()
            for keyword in ["SELECT", "INSERT", "UPDATE", "DELETE", "WITH"]
        ):
            # Try to extract everything that looks like SQL
            lines = response_text.strip().split("\n")
            sql_lines = []
            in_sql = False

            for line in lines:
                stripped = line.strip().upper()
                if any(
                    keyword in stripped
                    for keyword in ["SELECT", "INSERT", "UPDATE", "DELETE", "WITH"]
                ):
                    in_sql = True

                if in_sql:
                    sql_lines.append(line)
                    if line.strip().endswith(";"):
                        break

            if sql_lines:
                return "\n".join(sql_lines).strip()

        logger.warning(f"Could not extract SQL from response: {response_text[:200]}...")
        return None

    def set_model(self, model_name: str) -> None:
        """Change the LLM model."""
        self.model_name = model_name
        self._verify_model_available()

    def add_custom_example(self, question: str, sql: str) -> None:
        """Add a custom few-shot example to improve query generation."""
        self.query_builder.add_example(question, sql)

    def clear_examples(self) -> None:
        """Clear all few-shot examples."""
        self.query_builder.clear_examples()

    def get_available_models(self) -> list[str]:
        """Get list of available ollama models."""
        try:
            _ollama = self._get_ollama_module()
            if _ollama is None:
                return []

            models = _ollama.list()
            return [model["name"] for model in models.get("models", [])]
        except Exception as e:
            logger.error(f"Could not list models: {e}")
            return []
