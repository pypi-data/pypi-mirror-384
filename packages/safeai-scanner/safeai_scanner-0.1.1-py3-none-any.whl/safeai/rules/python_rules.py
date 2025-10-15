"""Python-specific security rules for SafeAI."""

import ast
import re
from typing import Any, Dict, List, Optional, Set

from .base import BaseRule


class EvalRule(BaseRule):
    """Rule PY001: Detect usage of eval() and exec()."""

    id = "PY001"
    description = "Использование eval() или exec() может быть небезопасным"
    severity = "HIGH"
    recommendation = "Избегайте использования eval() и exec(). Используйте безопасные альтернативы или тщательно валидируйте входные данные."

    def check(self, code: str, ast_tree: Optional[ast.AST] = None) -> Optional[Dict[str, Any]]:
        """Check for eval() and exec() usage."""
        if ast_tree is None:
            ast_tree = self._parse_ast(code)
            if ast_tree is None:
                return None

        dangerous_functions = {"eval", "exec"}
        calls = []

        class DangerousCallVisitor(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> Any:
                if isinstance(node.func, ast.Name) and node.func.id in dangerous_functions:
                    calls.append({
                        "function": node.func.id,
                        "line": node.lineno,
                        "col": node.col_offset
                    })
                self.generic_visit(node)

        visitor = DangerousCallVisitor()
        visitor.visit(ast_tree)

        if calls:
            call = calls[0]  # Return first occurrence
            return self._create_issue(
                line=call["line"],
                column=call["col"],
                code_snippet=f"Found {call['function']}() usage",
                details=f"Dangerous function {call['function']}() detected"
            )
        return None


class HardcodedSecretsRule(BaseRule):
    """Rule PY002: Detect hardcoded secrets, API keys, tokens."""

    id = "PY002"
    description = "В коде обнаружены хардкодные секреты или токены"
    severity = "HIGH"
    recommendation = "Используйте переменные окружения или конфигурационные файлы для хранения секретов. Никогда не коммитьте секреты в код."

    def check(self, code: str, ast_tree: Optional[ast.AST] = None) -> Optional[Dict[str, Any]]:
        """Check for hardcoded secrets."""
        # Patterns for common secret types
        secret_patterns = [
            r'(api_key|apikey|api-key)\s*=\s*["\'][A-Za-z0-9\-_]{20,}["\']',
            r'(secret|secret_key|secretkey)\s*=\s*["\'][A-Za-z0-9\-_]{20,}["\']',
            r'(token|access_token|access-token)\s*=\s*["\'][A-Za-z0-9\-_]{20,}["\']',
            r'(password|passwd|pwd)\s*=\s*["\'][^"\']{8,}["\']',
            r'(private_key|privatekey)\s*=\s*["\'][A-Za-z0-9\-_]{40,}["\']',
            r'(client_secret|client-secret)\s*=\s*["\'][A-Za-z0-9\-_]{20,}["\']',
        ]

        for pattern in secret_patterns:
            match = re.search(pattern, code, re.IGNORECASE)
            if match:
                line = self._get_line_number(code, match.start())
                return self._create_issue(
                    line=line,
                    column=match.start(),
                    code_snippet=match.group(0),
                    details=f"Hardcoded secret detected: {match.group(1)}"
                )
        return None


class SQLInjectionRule(BaseRule):
    """Rule PY003: Detect potential SQL injection vulnerabilities."""

    id = "PY003"
    description = "Потенциальная уязвимость SQL injection из-за конкатенации строк"
    severity = "HIGH"
    recommendation = "Используйте параметризованные запросы или ORM вместо конкатенации строк в SQL запросах."

    def check(self, code: str, ast_tree: Optional[ast.AST] = None) -> Optional[Dict[str, Any]]:
        """Check for SQL injection patterns."""
        if ast_tree is None:
            ast_tree = self._parse_ast(code)
            if ast_tree is None:
                return None

        # Look for string concatenation in SQL contexts
        sql_functions = {"execute", "executemany", "query"}
        dangerous_patterns = []

        class SQLInjectionVisitor(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> Any:
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in sql_functions:
                        # Check if any argument contains string concatenation
                        for arg in node.args:
                            if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                                dangerous_patterns.append({
                                    "line": node.lineno,
                                    "col": node.col_offset,
                                    "function": node.func.attr
                                })
                self.generic_visit(node)

        visitor = SQLInjectionVisitor()
        visitor.visit(ast_tree)

        if dangerous_patterns:
            pattern = dangerous_patterns[0]
            return self._create_issue(
                line=pattern["line"],
                column=pattern["col"],
                code_snippet=f"String concatenation in {pattern['function']}()",
                details="SQL query constructed with string concatenation"
            )
        return None


class CommandInjectionRule(BaseRule):
    """Rule PY004: Detect command injection vulnerabilities."""

    id = "PY004"
    description = "Потенциальная уязвимость command injection"
    severity = "HIGH"
    recommendation = "Избегайте использования os.system() и subprocess с shell=True. Используйте subprocess.run() с shell=False и списком аргументов."

    def check(self, code: str, ast_tree: Optional[ast.AST] = None) -> Optional[Dict[str, Any]]:
        """Check for command injection patterns."""
        if ast_tree is None:
            ast_tree = self._parse_ast(code)
            if ast_tree is None:
                return None

        dangerous_calls = []

        class CommandInjectionVisitor(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> Any:
                # Check for os.system()
                if isinstance(node.func, ast.Attribute):
                    if (isinstance(node.func.value, ast.Name) and 
                        node.func.value.id == "os" and 
                        node.func.attr == "system"):
                        dangerous_calls.append({
                            "type": "os.system",
                            "line": node.lineno,
                            "col": node.col_offset
                        })
                
                # Check for subprocess with shell=True
                elif isinstance(node.func, ast.Name):
                    if node.func.id in ["call", "check_call", "check_output", "run"]:
                        # Check for shell=True keyword argument
                        for keyword in node.keywords:
                            if (keyword.arg == "shell" and 
                                isinstance(keyword.value, ast.Constant) and 
                                keyword.value.value is True):
                                dangerous_calls.append({
                                    "type": f"subprocess.{node.func.id}",
                                    "line": node.lineno,
                                    "col": node.col_offset
                                })
                self.generic_visit(node)

        visitor = CommandInjectionVisitor()
        visitor.visit(ast_tree)

        if dangerous_calls:
            call = dangerous_calls[0]
            return self._create_issue(
                line=call["line"],
                column=call["col"],
                code_snippet=f"Dangerous call: {call['type']}",
                details=f"Command injection risk: {call['type']}"
            )
        return None


class UnsafeDeserializationRule(BaseRule):
    """Rule PY005: Detect unsafe deserialization."""

    id = "PY005"
    description = "Небезопасная десериализация данных"
    severity = "HIGH"
    recommendation = "Избегайте pickle.loads() и yaml.load() без безопасного Loader. Используйте json.loads() или yaml.safe_load()."

    def check(self, code: str, ast_tree: Optional[ast.AST] = None) -> Optional[Dict[str, Any]]:
        """Check for unsafe deserialization."""
        if ast_tree is None:
            ast_tree = self._parse_ast(code)
            if ast_tree is None:
                return None

        dangerous_calls = []

        class DeserializationVisitor(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> Any:
                if isinstance(node.func, ast.Attribute):
                    # Check for pickle.loads()
                    if (node.func.attr == "loads" and 
                        isinstance(node.func.value, ast.Name) and 
                        node.func.value.id == "pickle"):
                        dangerous_calls.append({
                            "type": "pickle.loads",
                            "line": node.lineno,
                            "col": node.col_offset
                        })
                    
                    # Check for yaml.load() without Loader
                    elif (node.func.attr == "load" and 
                          isinstance(node.func.value, ast.Name) and 
                          node.func.value.id == "yaml"):
                        # Check if Loader is specified
                        has_loader = any(
                            kw.arg == "Loader" for kw in node.keywords
                        )
                        if not has_loader:
                            dangerous_calls.append({
                                "type": "yaml.load",
                                "line": node.lineno,
                                "col": node.col_offset
                            })
                self.generic_visit(node)

        visitor = DeserializationVisitor()
        visitor.visit(ast_tree)

        if dangerous_calls:
            call = dangerous_calls[0]
            return self._create_issue(
                line=call["line"],
                column=call["col"],
                code_snippet=f"Unsafe deserialization: {call['type']}",
                details=f"Unsafe deserialization detected: {call['type']}"
            )
        return None


class PathTraversalRule(BaseRule):
    """Rule PY006: Detect path traversal vulnerabilities."""

    id = "PY006"
    description = "Потенциальная уязвимость path traversal"
    severity = "MEDIUM"
    recommendation = "Валидируйте и санитизируйте пути к файлам. Используйте os.path.abspath() и проверяйте, что путь находится в разрешенной директории."

    def check(self, code: str, ast_tree: Optional[ast.AST] = None) -> Optional[Dict[str, Any]]:
        """Check for path traversal patterns."""
        # Look for file operations with user input
        path_traversal_patterns = [
            r'open\s*\(\s*[^)]*\.\.',
            r'file\s*\(\s*[^)]*\.\.',
            r'os\.path\.join\s*\(\s*[^)]*\.\.',
        ]

        for pattern in path_traversal_patterns:
            match = re.search(pattern, code)
            if match:
                line = self._get_line_number(code, match.start())
                return self._create_issue(
                    line=line,
                    column=match.start(),
                    code_snippet=match.group(0),
                    details="Path traversal pattern detected"
                )
        return None


class MissingInputValidationRule(BaseRule):
    """Rule PY007: Detect missing input validation."""

    id = "PY007"
    description = "Отсутствует валидация входных данных"
    severity = "MEDIUM"
    recommendation = "Добавьте валидацию входных данных: проверяйте типы, диапазоны значений и формат данных."

    def check(self, code: str, ast_tree: Optional[ast.AST] = None) -> Optional[Dict[str, Any]]:
        """Check for missing input validation."""
        if ast_tree is None:
            ast_tree = self._parse_ast(code)
            if ast_tree is None:
                return None

        # Look for functions that accept user input without validation
        suspicious_patterns = []

        class InputValidationVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
                # Check if function has parameters but no validation
                if node.args.args:
                    has_validation = False
                    for stmt in node.body:
                        if isinstance(stmt, ast.If):
                            # Simple check for validation patterns
                            if self._has_validation_pattern(stmt):
                                has_validation = True
                                break
                    
                    if not has_validation:
                        suspicious_patterns.append({
                            "line": node.lineno,
                            "col": node.col_offset,
                            "function": node.name
                        })
                self.generic_visit(node)

            def _has_validation_pattern(self, node: ast.If) -> bool:
                """Check if if statement contains validation logic."""
                # Look for common validation patterns
                validation_keywords = ["isinstance", "len", "range", "validate", "check"]
                for child in ast.walk(node):
                    if isinstance(child, ast.Name) and child.id in validation_keywords:
                        return True
                return False

        visitor = InputValidationVisitor()
        visitor.visit(ast_tree)

        if suspicious_patterns:
            pattern = suspicious_patterns[0]
            return self._create_issue(
                line=pattern["line"],
                column=pattern["col"],
                code_snippet=f"Function '{pattern['function']}' without input validation",
                details="Function accepts parameters without validation"
            )
        return None


class AssertSecurityRule(BaseRule):
    """Rule PY008: Detect use of assert for security checks."""

    id = "PY008"
    description = "Использование assert для проверки безопасности"
    severity = "MEDIUM"
    recommendation = "Не используйте assert для проверки безопасности. Assert может быть отключен с флагом -O. Используйте явные проверки с исключениями."

    def check(self, code: str, ast_tree: Optional[ast.AST] = None) -> Optional[Dict[str, Any]]:
        """Check for assert statements used for security."""
        if ast_tree is None:
            ast_tree = self._parse_ast(code)
            if ast_tree is None:
                return None

        security_asserts = []

        class AssertVisitor(ast.NodeVisitor):
            def visit_Assert(self, node: ast.Assert) -> Any:
                # Check if assert contains security-related keywords
                security_keywords = ["password", "token", "secret", "auth", "permission", "access"]
                test_str = ast.unparse(node.test) if hasattr(ast, 'unparse') else str(node.test)
                
                if any(keyword in test_str.lower() for keyword in security_keywords):
                    security_asserts.append({
                        "line": node.lineno,
                        "col": node.col_offset,
                        "test": test_str
                    })
                self.generic_visit(node)

        visitor = AssertVisitor()
        visitor.visit(ast_tree)

        if security_asserts:
            assert_info = security_asserts[0]
            return self._create_issue(
                line=assert_info["line"],
                column=assert_info["col"],
                code_snippet=f"assert {assert_info['test']}",
                details="Assert statement used for security check"
            )
        return None


class InsecureHTTPRule(BaseRule):
    """Rule PY009: Detect insecure HTTP requests."""

    id = "PY009"
    description = "Небезопасные HTTP запросы"
    severity = "MEDIUM"
    recommendation = "Используйте HTTPS вместо HTTP. Если необходимо отключить проверку SSL, убедитесь, что это временно и в безопасной среде."

    def check(self, code: str, ast_tree: Optional[ast.AST] = None) -> Optional[Dict[str, Any]]:
        """Check for insecure HTTP patterns."""
        if ast_tree is None:
            ast_tree = self._parse_ast(code)
            if ast_tree is None:
                return None

        insecure_patterns = []

        class HTTPVisitor(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> Any:
                # Check for requests with verify=False
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ["get", "post", "put", "delete", "patch"]:
                        for keyword in node.keywords:
                            if (keyword.arg == "verify" and 
                                isinstance(keyword.value, ast.Constant) and 
                                keyword.value.value is False):
                                insecure_patterns.append({
                                    "line": node.lineno,
                                    "col": node.col_offset,
                                    "method": node.func.attr
                                })
                self.generic_visit(node)

        visitor = HTTPVisitor()
        visitor.visit(ast_tree)

        if insecure_patterns:
            pattern = insecure_patterns[0]
            return self._create_issue(
                line=pattern["line"],
                column=pattern["col"],
                code_snippet=f"requests.{pattern['method']}(verify=False)",
                details="SSL verification disabled in HTTP request"
            )
        return None


class WeakCryptographyRule(BaseRule):
    """Rule PY010: Detect weak cryptographic algorithms."""

    id = "PY010"
    description = "Использование слабых криптографических алгоритмов"
    severity = "LOW"
    recommendation = "Используйте современные криптографические алгоритмы: SHA-256 вместо MD5/SHA1, AES вместо DES."

    def check(self, code: str, ast_tree: Optional[ast.AST] = None) -> Optional[Dict[str, Any]]:
        """Check for weak cryptographic algorithms."""
        weak_algorithms = ["md5", "sha1", "des", "rc4"]
        
        for algorithm in weak_algorithms:
            pattern = rf'\b{algorithm}\b'
            match = re.search(pattern, code, re.IGNORECASE)
            if match:
                line = self._get_line_number(code, match.start())
                return self._create_issue(
                    line=line,
                    column=match.start(),
                    code_snippet=match.group(0),
                    details=f"Weak cryptographic algorithm: {algorithm}"
                )
        return None


class MissingExceptionHandlingRule(BaseRule):
    """Rule PY011: Detect missing exception handling in critical sections."""

    id = "PY011"
    description = "Отсутствует обработка исключений в критических секциях"
    severity = "LOW"
    recommendation = "Добавьте обработку исключений для критических операций: работа с файлами, сетевые запросы, операции с базой данных."

    def check(self, code: str, ast_tree: Optional[ast.AST] = None) -> Optional[Dict[str, Any]]:
        """Check for missing exception handling."""
        if ast_tree is None:
            ast_tree = self._parse_ast(code)
            if ast_tree is None:
                return None

        critical_operations = []
        critical_functions = {"open", "file", "connect", "execute", "request", "send"}

        class ExceptionHandlingVisitor(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> Any:
                if isinstance(node.func, ast.Name) and node.func.id in critical_functions:
                    # Check if this call is inside a try block
                    if not self._is_in_try_block(node):
                        critical_operations.append({
                            "line": node.lineno,
                            "col": node.col_offset,
                            "function": node.func.id
                        })
                self.generic_visit(node)

            def _is_in_try_block(self, node: ast.AST) -> bool:
                """Check if node is inside a try block."""
                for parent in ast.walk(self):
                    if isinstance(parent, ast.Try):
                        for stmt in parent.body:
                            if ast.walk(stmt) and node in ast.walk(stmt):
                                return True
                return False

        visitor = ExceptionHandlingVisitor()
        visitor.visit(ast_tree)

        if critical_operations:
            operation = critical_operations[0]
            return self._create_issue(
                line=operation["line"],
                column=operation["col"],
                code_snippet=f"{operation['function']}() without exception handling",
                details=f"Critical operation {operation['function']}() lacks exception handling"
            )
        return None


def get_rules() -> List[BaseRule]:
    """Get all Python security rules."""
    return [
        EvalRule(),
        HardcodedSecretsRule(),
        SQLInjectionRule(),
        CommandInjectionRule(),
        UnsafeDeserializationRule(),
        PathTraversalRule(),
        MissingInputValidationRule(),
        AssertSecurityRule(),
        InsecureHTTPRule(),
        WeakCryptographyRule(),
        MissingExceptionHandlingRule(),
    ]
