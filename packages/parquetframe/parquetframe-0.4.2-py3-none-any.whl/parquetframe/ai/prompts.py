"""
Prompt template system for LLM-powered SQL generation.

This module provides structured prompt templates that inject schema context
and examples to improve LLM query generation accuracy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PromptTemplate:
    """A template for constructing LLM prompts with dynamic content."""

    system_message: str
    few_shot_examples: list[dict[str, str]]
    output_format_instructions: str

    def format(self, **kwargs: Any) -> str:
        """Format the template with provided variables."""
        formatted_system = self.system_message.format(**kwargs)

        examples_text = ""
        if self.few_shot_examples:
            examples_text = "\n--- Examples ---\n"
            for example in self.few_shot_examples:
                examples_text += f'Question: "{example["question"]}"\n'
                examples_text += f"SQL: {example['sql']}\n\n"

        return f"{formatted_system}\n\n{examples_text}{self.output_format_instructions}"


class QueryPromptBuilder:
    """Builder for creating SQL query generation prompts."""

    # Default system message template
    DEFAULT_SYSTEM_MESSAGE = """You are an expert SQL analyst. Your task is to translate the user's question into a single, valid SQL query.

The following tables are available:

{schema_context}

Guidelines:
- Generate only valid SQL syntax
- Use appropriate JOINs when querying multiple tables
- Apply reasonable LIMIT clauses for exploratory queries
- Use proper column names exactly as shown in the schema
- Consider data types when applying filters and functions"""

    # Default few-shot examples for common query patterns
    DEFAULT_EXAMPLES = [
        {
            "question": "how many rows are there",
            "sql": "SELECT COUNT(*) as row_count FROM {main_table};",
        },
        {
            "question": "show me the first 10 rows",
            "sql": "SELECT * FROM {main_table} LIMIT 10;",
        },
        {
            "question": "what are the unique values in the status column",
            "sql": "SELECT DISTINCT status FROM {main_table};",
        },
    ]

    # Default output format instructions
    DEFAULT_OUTPUT_FORMAT = """Provide ONLY the SQL query. Do not include any explanation or introductory text.
Enclose the query in a single markdown code block like this:

```sql
SELECT * FROM table_name;
```"""

    def __init__(self):
        self.system_message = self.DEFAULT_SYSTEM_MESSAGE
        self.examples = self.DEFAULT_EXAMPLES.copy()
        self.output_format = self.DEFAULT_OUTPUT_FORMAT

    def with_system_message(self, message: str) -> QueryPromptBuilder:
        """Set custom system message."""
        self.system_message = message
        return self

    def add_example(self, question: str, sql: str) -> QueryPromptBuilder:
        """Add a few-shot example."""
        self.examples.append({"question": question, "sql": sql})
        return self

    def clear_examples(self) -> QueryPromptBuilder:
        """Clear all examples."""
        self.examples = []
        return self

    def with_output_format(self, format_instructions: str) -> QueryPromptBuilder:
        """Set custom output format instructions."""
        self.output_format = format_instructions
        return self

    def build(self) -> PromptTemplate:
        """Build the final prompt template."""
        return PromptTemplate(
            system_message=self.system_message,
            few_shot_examples=self.examples,
            output_format_instructions=self.output_format,
        )

    def build_for_context(
        self, schema_context: str, main_table: str | None = None
    ) -> str:
        """Build a complete prompt for a specific schema context."""
        template = self.build()

        # Format examples with main table if provided
        formatted_examples = []
        for example in self.examples:
            formatted_sql = example["sql"]
            if main_table and "{main_table}" in formatted_sql:
                formatted_sql = formatted_sql.format(main_table=main_table)
            formatted_examples.append(
                {"question": example["question"], "sql": formatted_sql}
            )

        # Create template with formatted examples
        formatted_template = PromptTemplate(
            system_message=template.system_message,
            few_shot_examples=formatted_examples,
            output_format_instructions=template.output_format_instructions,
        )

        return formatted_template.format(schema_context=schema_context)


class MultiStepQueryPromptBuilder:
    """Builder for multi-step reasoning prompts (table selection then query generation)."""

    TABLE_SELECTION_SYSTEM = """You are a database expert. Given a user's question and a list of available tables, determine which tables are necessary to answer the question.

Available tables:
{table_list}

Instructions:
- Analyze the user's question carefully
- Consider which tables contain the relevant data
- Think about necessary JOINs between tables
- Respond with ONLY a comma-separated list of table names
- Do not include any explanation"""

    def build_table_selection_prompt(self, table_names: list[str]) -> str:
        """Build a prompt for selecting relevant tables."""
        table_list = "\n".join(f"- {name}" for name in table_names)
        return self.TABLE_SELECTION_SYSTEM.format(table_list=table_list)

    def build_focused_query_prompt(self, selected_schema: str) -> str:
        """Build a query generation prompt with only selected tables."""
        builder = QueryPromptBuilder()
        return builder.build_for_context(selected_schema)


class SelfCorrectionPromptBuilder:
    """Builder for self-correction prompts when queries fail."""

    CORRECTION_SYSTEM = """The previously generated query failed with an error. Please analyze the error and provide a corrected SQL query.

Original Query:
{original_query}

Error Message:
{error_message}

Schema Context:
{schema_context}

Instructions:
- Carefully analyze the error message
- Identify the specific issue (syntax, column names, table names, etc.)
- Generate a corrected SQL query that resolves the error
- Ensure the corrected query still answers the original user question

Provide ONLY the corrected SQL query in a markdown code block:

```sql
-- corrected query here
```"""

    def build_correction_prompt(
        self, original_query: str, error_message: str, schema_context: str
    ) -> str:
        """Build a self-correction prompt."""
        return self.CORRECTION_SYSTEM.format(
            original_query=original_query,
            error_message=error_message,
            schema_context=schema_context,
        )
