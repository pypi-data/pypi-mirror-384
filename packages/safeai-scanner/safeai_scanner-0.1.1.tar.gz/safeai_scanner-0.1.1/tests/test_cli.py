"""Tests for CLI interface."""

import pytest
import sys
from unittest.mock import patch, mock_open
from pathlib import Path

from safeai.cli import (
    create_parser,
    parse_severity_filter,
    parse_ignore_patterns,
    print_rules,
    print_version,
    scan_command,
    list_rules_command,
    version_command,
    main
)


class TestCLIParser:
    """Test cases for CLI argument parser."""

    def test_create_parser(self):
        """Test parser creation."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "safeai"

    def test_scan_command_args(self):
        """Test scan command arguments."""
        parser = create_parser()
        args = parser.parse_args(["scan", "test.py"])
        
        assert args.command == "scan"
        assert args.path == "test.py"
        assert args.format == "text"
        assert args.lang == "python"

    def test_scan_command_with_options(self):
        """Test scan command with options."""
        parser = create_parser()
        args = parser.parse_args([
            "scan", "test.py", 
            "--format", "json",
            "--output", "report.json",
            "--severity", "HIGH,MEDIUM",
            "--ignore", "tests,docs",
            "--fail-on-error"
        ])
        
        assert args.command == "scan"
        assert args.path == "test.py"
        assert args.format == "json"
        assert args.output == "report.json"
        assert args.severity == "HIGH,MEDIUM"
        assert args.ignore == "tests,docs"
        assert args.fail_on_error is True

    def test_list_rules_command(self):
        """Test list-rules command."""
        parser = create_parser()
        args = parser.parse_args(["list-rules", "--format", "table"])
        
        assert args.command == "list-rules"
        assert args.format == "table"

    def test_version_command(self):
        """Test version command."""
        parser = create_parser()
        args = parser.parse_args(["version"])
        
        assert args.command == "version"

    def test_no_command(self):
        """Test parser with no command."""
        parser = create_parser()
        args = parser.parse_args([])
        
        assert args.command is None


class TestCLIUtils:
    """Test cases for CLI utility functions."""

    def test_parse_severity_filter_valid(self):
        """Test parsing valid severity filter."""
        result = parse_severity_filter("HIGH,MEDIUM")
        assert result == {"HIGH", "MEDIUM"}

    def test_parse_severity_filter_single(self):
        """Test parsing single severity."""
        result = parse_severity_filter("HIGH")
        assert result == {"HIGH"}

    def test_parse_severity_filter_none(self):
        """Test parsing None severity filter."""
        result = parse_severity_filter(None)
        assert result is None

    def test_parse_severity_filter_empty(self):
        """Test parsing empty severity filter."""
        result = parse_severity_filter("")
        assert result is None

    def test_parse_severity_filter_invalid(self):
        """Test parsing invalid severity filter."""
        with pytest.raises(ValueError):
            parse_severity_filter("INVALID")

    def test_parse_ignore_patterns(self):
        """Test parsing ignore patterns."""
        result = parse_ignore_patterns("tests,docs,venv")
        assert result == ["tests", "docs", "venv"]

    def test_parse_ignore_patterns_none(self):
        """Test parsing None ignore patterns."""
        result = parse_ignore_patterns(None)
        assert result is None

    def test_parse_ignore_patterns_empty(self):
        """Test parsing empty ignore patterns."""
        result = parse_ignore_patterns("")
        assert result is None


class TestCLICommands:
    """Test cases for CLI commands."""

    def test_print_version(self, capsys):
        """Test print_version function."""
        print_version()
        captured = capsys.readouterr()
        assert "SafeAI" in captured.out
        assert "0.1.0" in captured.out

    def test_scan_command_success(self):
        """Test successful scan command."""
        args = type('Args', (), {
            'path': 'test.py',
            'format': 'text',
            'output': None,
            'severity': None,
            'ignore': None,
            'fail_on_error': False,
            'lang': 'python'
        })()
        
        with patch('safeai.cli.CodeAnalyzer') as mock_analyzer_class:
            mock_analyzer = mock_analyzer_class.return_value
            mock_analyzer.analyze_path.return_value = {
                'files_analyzed': 1,
                'total_issues': 0,
                'issues': [],
                'severity_counts': {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
            }
            mock_analyzer.print_results.return_value = None
            
            with patch('pathlib.Path.exists', return_value=True):
                result = scan_command(args)
                assert result == 0

    def test_scan_command_file_not_found(self):
        """Test scan command with non-existent file."""
        args = type('Args', (), {
            'path': 'nonexistent.py',
            'format': 'text',
            'output': None,
            'severity': None,
            'ignore': None,
            'fail_on_error': False,
            'lang': 'python'
        })()
        
        with patch('safeai.cli.CodeAnalyzer') as mock_analyzer_class:
            with patch('pathlib.Path.exists', return_value=False):
                result = scan_command(args)
                assert result == 1

    def test_scan_command_with_issues_fail_on_error(self):
        """Test scan command with issues and fail-on-error."""
        args = type('Args', (), {
            'path': 'test.py',
            'format': 'text',
            'output': None,
            'severity': None,
            'ignore': None,
            'fail_on_error': True,
            'lang': 'python'
        })()
        
        with patch('safeai.cli.CodeAnalyzer') as mock_analyzer_class:
            mock_analyzer = mock_analyzer_class.return_value
            mock_analyzer.analyze_path.return_value = {
                'files_analyzed': 1,
                'total_issues': 1,
                'issues': [{'id': 'PY001', 'severity': 'HIGH'}],
                'severity_counts': {'HIGH': 1, 'MEDIUM': 0, 'LOW': 0}
            }
            mock_analyzer.print_results.return_value = None
            
            with patch('pathlib.Path.exists', return_value=True):
                result = scan_command(args)
                assert result == 1

    def test_list_rules_command(self):
        """Test list-rules command."""
        args = type('Args', (), {'format': 'table'})()
        
        with patch('safeai.cli.CodeAnalyzer') as mock_analyzer_class:
            mock_analyzer = mock_analyzer_class.return_value
            mock_analyzer.get_rules_info.return_value = [
                {'id': 'PY001', 'description': 'Test rule', 'severity': 'HIGH', 'recommendation': 'Fix it'}
            ]
            
            result = list_rules_command(args)
            assert result == 0

    def test_version_command(self):
        """Test version command."""
        args = type('Args', (), {})()
        result = version_command(args)
        assert result == 0


class TestCLIMain:
    """Test cases for main CLI function."""

    def test_main_scan_command(self):
        """Test main function with scan command."""
        with patch('sys.argv', ['safeai', 'scan', 'test.py']):
            with patch('safeai.cli.scan_command', return_value=0) as mock_scan:
                result = main()
                assert result == 0
                mock_scan.assert_called_once()

    def test_main_list_rules_command(self):
        """Test main function with list-rules command."""
        with patch('sys.argv', ['safeai', 'list-rules']):
            with patch('safeai.cli.list_rules_command', return_value=0) as mock_list:
                result = main()
                assert result == 0
                mock_list.assert_called_once()

    def test_main_version_command(self):
        """Test main function with version command."""
        with patch('sys.argv', ['safeai', 'version']):
            with patch('safeai.cli.version_command', return_value=0) as mock_version:
                result = main()
                assert result == 0
                mock_version.assert_called_once()

    def test_main_no_command(self):
        """Test main function with no command."""
        with patch('sys.argv', ['safeai']):
            result = main()
            assert result == 1

    def test_main_invalid_command(self):
        """Test main function with invalid command."""
        with patch('sys.argv', ['safeai', 'invalid']):
            result = main()
            assert result == 1
