"""Base rule class for SafeAI security analyzer."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import ast


class BaseRule(ABC):
    """Base class for all security rules."""

    # Rule metadata
    id: str = "GENERIC"
    description: str = "Base rule"
    severity: str = "LOW"
    recommendation: str = "Review the code for potential security issues"

    @abstractmethod
    def check(self, code: str, ast_tree: Optional[ast.AST] = None) -> Optional[Dict[str, Any]]:
        """
        Check code for security vulnerabilities.

        Args:
            code: Source code to analyze
            ast_tree: Parsed AST tree (optional, will be parsed if not provided)

        Returns:
            Dictionary with vulnerability details if found, None otherwise
        """
        pass

    def _parse_ast(self, code: str) -> Optional[ast.AST]:
        """Parse code into AST tree."""
        try:
            return ast.parse(code)
        except SyntaxError:
            return None

    def _get_line_number(self, code: str, position: int) -> int:
        """Get line number for a given position in code."""
        return code[:position].count('\n') + 1

    def _create_issue(
        self,
        line: int,
        column: int = 0,
        code_snippet: str = "",
        details: str = ""
    ) -> Dict[str, Any]:
        """Create a standardized issue dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "severity": self.severity,
            "recommendation": self.recommendation,
            "line": line,
            "column": column,
            "code_snippet": code_snippet,
            "details": details,
        }
