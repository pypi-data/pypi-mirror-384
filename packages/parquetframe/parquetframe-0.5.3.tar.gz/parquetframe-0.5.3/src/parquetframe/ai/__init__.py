"""
AI module for parquetframe.

This module provides LLM-powered natural language to SQL conversion
with self-correction capabilities and integration with DataContext.
"""

from .agent import LLMAgent, LLMError, QueryResult
from .prompts import PromptTemplate, QueryPromptBuilder

__all__ = [
    "LLMAgent",
    "LLMError",
    "QueryResult",
    "PromptTemplate",
    "QueryPromptBuilder",
]
