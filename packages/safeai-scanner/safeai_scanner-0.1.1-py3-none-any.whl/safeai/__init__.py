"""
SafeAI - Security analyzer for AI-generated code.

A Python library that analyzes source code for security vulnerabilities
commonly found in AI-generated code.
"""

from .analyzer import CodeAnalyzer
from .rules import get_all_rules

__version__ = "0.1.0"
__author__ = "SafeAI Team"
__email__ = "team@safeai.dev"

__all__ = [
    "CodeAnalyzer",
    "get_all_rules",
    "__version__",
    "__author__",
    "__email__",
]
