"""
Table Categorization Agent

An LLM-driven agent that analyzes data tables and categorizes them based on
domain schemas. This agent identifies entities, attributes, and relationships
from data and maps them to domain concepts.
"""

__version__ = "0.1.0"
__author__ = "StepFn AI"
__email__ = "rajesh@stepfunction.ai"

from .agent import TableCategorizationAgent
from .models import TableCategory, CategorizationResult

__all__ = [
    "TableCategorizationAgent",
    "TableCategory", 
    "CategorizationResult"
]
