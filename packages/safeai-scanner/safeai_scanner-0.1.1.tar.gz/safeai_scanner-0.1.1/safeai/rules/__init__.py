"""Rules module for SafeAI security analyzer."""

from .base import BaseRule
from .python_rules import get_rules

__all__ = ["BaseRule", "get_rules"]


def get_all_rules() -> list[BaseRule]:
    """Get all available security rules."""
    return get_rules()
