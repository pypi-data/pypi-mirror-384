"""AST parsing utilities for SafeAI."""

import ast
from typing import Any, Dict, List, Optional, Set, Tuple


class ASTHelper:
    """Utility class for AST analysis."""

    @staticmethod
    def parse_code(code: str) -> Optional[ast.AST]:
        """Parse Python code into AST."""
        try:
            return ast.parse(code)
        except SyntaxError:
            return None

    @staticmethod
    def find_function_calls(tree: ast.AST, function_names: Set[str]) -> List[Dict[str, Any]]:
        """Find calls to specific functions."""
        calls = []
        
        class CallVisitor(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> Any:
                if isinstance(node.func, ast.Name) and node.func.id in function_names:
                    calls.append({
                        "name": node.func.id,
                        "line": node.lineno,
                        "col": node.col_offset,
                        "args": len(node.args),
                        "keywords": len(node.keywords),
                    })
                self.generic_visit(node)

        visitor = CallVisitor()
        visitor.visit(tree)
        return calls

    @staticmethod
    def find_imports(tree: ast.AST) -> List[Dict[str, Any]]:
        """Find all import statements."""
        imports = []
        
        class ImportVisitor(ast.NodeVisitor):
            def visit_Import(self, node: ast.Import) -> Any:
                for alias in node.names:
                    imports.append({
                        "type": "import",
                        "module": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno,
                        "col": node.col_offset,
                    })
                self.generic_visit(node)

            def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
                module = node.module or ""
                for alias in node.names:
                    imports.append({
                        "type": "from_import",
                        "module": module,
                        "name": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno,
                        "col": node.col_offset,
                    })
                self.generic_visit(node)

        visitor = ImportVisitor()
        visitor.visit(tree)
        return imports

    @staticmethod
    def find_string_concatenations(tree: ast.AST) -> List[Dict[str, Any]]:
        """Find string concatenations that might be vulnerable."""
        concatenations = []
        
        class ConcatVisitor(ast.NodeVisitor):
            def visit_BinOp(self, node: ast.BinOp) -> Any:
                if isinstance(node.op, ast.Add):
                    # Check if it's string concatenation
                    if (isinstance(node.left, ast.Str) or isinstance(node.right, ast.Str) or
                        isinstance(node.left, ast.Constant) or isinstance(node.right, ast.Constant)):
                        concatenations.append({
                            "line": node.lineno,
                            "col": node.col_offset,
                            "left_type": type(node.left).__name__,
                            "right_type": type(node.right).__name__,
                        })
                self.generic_visit(node)

        visitor = ConcatVisitor()
        visitor.visit(tree)
        return concatenations

    @staticmethod
    def find_assignment_patterns(tree: ast.AST, patterns: List[str]) -> List[Dict[str, Any]]:
        """Find variable assignments matching patterns."""
        assignments = []
        
        class AssignVisitor(ast.NodeVisitor):
            def visit_Assign(self, node: ast.Assign) -> Any:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        for pattern in patterns:
                            if pattern.lower() in target.id.lower():
                                assignments.append({
                                    "variable": target.id,
                                    "line": node.lineno,
                                    "col": node.col_offset,
                                    "pattern": pattern,
                                })
                self.generic_visit(node)

        visitor = AssignVisitor()
        visitor.visit(tree)
        return assignments

    @staticmethod
    def find_file_operations(tree: ast.AST) -> List[Dict[str, Any]]:
        """Find file operations."""
        operations = []
        
        class FileOpVisitor(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> Any:
                if isinstance(node.func, ast.Name):
                    if node.func.id in ["open", "file"]:
                        operations.append({
                            "operation": node.func.id,
                            "line": node.lineno,
                            "col": node.col_offset,
                            "args": len(node.args),
                        })
                self.generic_visit(node)

        visitor = FileOpVisitor()
        visitor.visit(tree)
        return operations

    @staticmethod
    def get_code_snippet(code: str, line: int, context_lines: int = 3) -> str:
        """Get code snippet around a specific line."""
        lines = code.split('\n')
        start = max(0, line - context_lines - 1)
        end = min(len(lines), line + context_lines)
        return '\n'.join(lines[start:end])
