"""Tests for CodeAnalyzer class."""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from safeai.analyzer import CodeAnalyzer


class TestCodeAnalyzer:
    """Test cases for CodeAnalyzer class."""

    def test_init(self):
        """Test analyzer initialization."""
        analyzer = CodeAnalyzer()
        assert analyzer.language == "python"
        assert len(analyzer.rules) > 0

    def test_init_with_language(self):
        """Test analyzer initialization with specific language."""
        analyzer = CodeAnalyzer(language="python")
        assert analyzer.language == "python"

    def test_analyze_code_empty(self):
        """Test analyzing empty code."""
        analyzer = CodeAnalyzer()
        issues = analyzer.analyze_code("")
        assert issues == []

    def test_analyze_code_with_eval(self):
        """Test analyzing code with eval() usage."""
        analyzer = CodeAnalyzer()
        code = "result = eval('1 + 1')"
        issues = analyzer.analyze_code(code)
        
        assert len(issues) > 0
        assert any(issue["id"] == "PY001" for issue in issues)

    def test_analyze_code_with_hardcoded_secret(self):
        """Test analyzing code with hardcoded secret."""
        analyzer = CodeAnalyzer()
        code = "api_key = 'sk-1234567890abcdef'"
        issues = analyzer.analyze_code(code)
        
        assert len(issues) > 0
        assert any(issue["id"] == "PY002" for issue in issues)

    def test_analyze_code_with_sql_injection(self):
        """Test analyzing code with SQL injection."""
        analyzer = CodeAnalyzer()
        code = """
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)
"""
        issues = analyzer.analyze_code(code)
        
        assert len(issues) > 0
        assert any(issue["id"] == "PY003" for issue in issues)

    def test_analyze_code_with_command_injection(self):
        """Test analyzing code with command injection."""
        analyzer = CodeAnalyzer()
        code = "import os; os.system('ls -la')"
        issues = analyzer.analyze_code(code)
        
        assert len(issues) > 0
        assert any(issue["id"] == "PY004" for issue in issues)

    def test_analyze_code_with_unsafe_deserialization(self):
        """Test analyzing code with unsafe deserialization."""
        analyzer = CodeAnalyzer()
        code = "import pickle; data = pickle.loads(user_input)"
        issues = analyzer.analyze_code(code)
        
        assert len(issues) > 0
        assert any(issue["id"] == "PY005" for issue in issues)

    def test_analyze_code_with_path_traversal(self):
        """Test analyzing code with path traversal."""
        analyzer = CodeAnalyzer()
        code = "with open('../etc/passwd', 'r') as f: pass"
        issues = analyzer.analyze_code(code)
        
        assert len(issues) > 0
        assert any(issue["id"] == "PY006" for issue in issues)

    def test_analyze_code_with_assert_security(self):
        """Test analyzing code with assert for security."""
        analyzer = CodeAnalyzer()
        code = "assert user.is_authenticated, 'Access denied'"
        issues = analyzer.analyze_code(code)
        
        assert len(issues) > 0
        assert any(issue["id"] == "PY008" for issue in issues)

    def test_analyze_code_with_insecure_http(self):
        """Test analyzing code with insecure HTTP."""
        analyzer = CodeAnalyzer()
        code = "import requests; requests.get('https://api.example.com', verify=False)"
        issues = analyzer.analyze_code(code)
        
        assert len(issues) > 0
        assert any(issue["id"] == "PY009" for issue in issues)

    def test_analyze_code_with_weak_cryptography(self):
        """Test analyzing code with weak cryptography."""
        analyzer = CodeAnalyzer()
        code = "import hashlib; hash = hashlib.md5(data).hexdigest()"
        issues = analyzer.analyze_code(code)
        
        assert len(issues) > 0
        assert any(issue["id"] == "PY010" for issue in issues)

    def test_analyze_file_nonexistent(self):
        """Test analyzing non-existent file."""
        analyzer = CodeAnalyzer()
        issues = analyzer.analyze_file(Path("nonexistent.py"))
        assert issues == []

    def test_analyze_file_non_python(self):
        """Test analyzing non-Python file."""
        analyzer = CodeAnalyzer()
        with patch("builtins.open", mock_open(read_data="console.log('test')")):
            issues = analyzer.analyze_file(Path("test.js"))
            assert issues == []

    def test_analyze_directory_nonexistent(self):
        """Test analyzing non-existent directory."""
        analyzer = CodeAnalyzer()
        with pytest.raises(FileNotFoundError):
            analyzer.analyze_directory(Path("nonexistent"))

    def test_analyze_path_file(self):
        """Test analyzing file path."""
        analyzer = CodeAnalyzer()
        code = "result = eval('1 + 1')"
        
        with patch("builtins.open", mock_open(read_data=code)):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    results = analyzer.analyze_path("test.py")
                    
                    assert results["files_analyzed"] == 1
                    assert results["total_issues"] > 0
                    assert "issues" in results
                    assert "severity_counts" in results

    def test_analyze_path_directory(self):
        """Test analyzing directory path."""
        analyzer = CodeAnalyzer()
        
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_file", return_value=False):
                with patch.object(analyzer, "analyze_directory") as mock_analyze:
                    mock_analyze.return_value = {
                        "files_analyzed": 2,
                        "total_issues": 3,
                        "issues": [],
                        "severity_counts": {"HIGH": 1, "MEDIUM": 1, "LOW": 1}
                    }
                    
                    results = analyzer.analyze_path("test_dir")
                    assert results["files_analyzed"] == 2
                    assert results["total_issues"] == 3

    def test_get_rules_info(self):
        """Test getting rules information."""
        analyzer = CodeAnalyzer()
        rules_info = analyzer.get_rules_info()
        
        assert len(rules_info) > 0
        for rule in rules_info:
            assert "id" in rule
            assert "description" in rule
            assert "severity" in rule
            assert "recommendation" in rule

    def test_severity_filtering(self):
        """Test severity filtering."""
        analyzer = CodeAnalyzer()
        code = """
result = eval('1 + 1')  # HIGH severity
api_key = 'sk-test'     # HIGH severity  
hash = hashlib.md5(data).hexdigest()  # LOW severity
"""
        
        # Test HIGH severity only
        issues_high = analyzer.analyze_code(code)
        high_issues = [issue for issue in issues_high if issue["severity"] == "HIGH"]
        
        assert len(high_issues) >= 2  # eval and hardcoded secret

    def test_rule_exception_handling(self):
        """Test that rule exceptions don't crash analyzer."""
        analyzer = CodeAnalyzer()
        
        # Mock a rule to raise exception
        with patch.object(analyzer.rules[0], 'check', side_effect=Exception("Test error")):
            issues = analyzer.analyze_code("print('hello')")
            # Should not crash and return empty list or other issues
            assert isinstance(issues, list)
