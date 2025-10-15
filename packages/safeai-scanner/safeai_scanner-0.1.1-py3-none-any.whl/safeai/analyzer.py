"""Main analyzer class for SafeAI."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .rules import get_all_rules
from .utils.file_loader import FileLoader
from .utils.ast_helper import ASTHelper
from .utils.formatter import Formatter


class CodeAnalyzer:
    """Main analyzer class for security vulnerability detection."""

    def __init__(self, language: str = "python"):
        """
        Initialize the analyzer.

        Args:
            language: Programming language to analyze (currently only "python")
        """
        self.language = language
        self.rules = get_all_rules()
        self.file_loader = FileLoader()
        self.ast_helper = ASTHelper()
        self.formatter = Formatter()

    def analyze_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Analyze a single file for security vulnerabilities.

        Args:
            file_path: Path to the file to analyze

        Returns:
            List of security issues found
        """
        if not self.file_loader.is_python_file(file_path):
            return []

        try:
            code, encoding = self.file_loader.read_file(file_path)
        except IOError:
            return []

        return self.analyze_code(code, str(file_path))

    def analyze_code(self, code: str, file_path: str = "") -> List[Dict[str, Any]]:
        """
        Analyze code string for security vulnerabilities.

        Args:
            code: Source code to analyze
            file_path: Optional file path for context

        Returns:
            List of security issues found
        """
        issues = []
        ast_tree = self.ast_helper.parse_code(code)

        for rule in self.rules:
            try:
                result = rule.check(code, ast_tree)
                if result:
                    # Add file path context
                    result["file_path"] = file_path
                    issues.append(result)
            except Exception as e:
                # Log rule execution error but continue
                print(f"Warning: Rule {rule.id} failed: {e}")

        return issues

    def analyze_directory(
        self,
        directory_path: Path,
        ignore_patterns: Optional[List[str]] = None,
        severity_filter: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze all Python files in a directory.

        Args:
            directory_path: Path to directory to analyze
            ignore_patterns: List of patterns to ignore
            severity_filter: Set of severity levels to include

        Returns:
            Dictionary with analysis results
        """
        all_issues = []
        files_analyzed = 0
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

        for file_path in self.file_loader.find_python_files(directory_path, ignore_patterns):
            file_issues = self.analyze_file(file_path)
            
            # Filter by severity if specified
            if severity_filter:
                file_issues = [
                    issue for issue in file_issues
                    if issue.get("severity") in severity_filter
                ]

            all_issues.extend(file_issues)
            files_analyzed += 1

            # Update severity counts
            for issue in file_issues:
                severity = issue.get("severity", "LOW")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "files_analyzed": files_analyzed,
            "total_issues": len(all_issues),
            "issues": all_issues,
            "severity_counts": severity_counts,
            "directory": str(directory_path)
        }

    def analyze_path(
        self,
        path: str,
        ignore_patterns: Optional[List[str]] = None,
        severity_filter: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a file or directory path.

        Args:
            path: File or directory path to analyze
            ignore_patterns: List of patterns to ignore
            severity_filter: Set of severity levels to include

        Returns:
            Dictionary with analysis results
        """
        target_path = Path(path)

        if not target_path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")

        if target_path.is_file():
            issues = self.analyze_file(target_path)
            
            # Filter by severity if specified
            if severity_filter:
                issues = [
                    issue for issue in issues
                    if issue.get("severity") in severity_filter
                ]

            severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
            for issue in issues:
                severity = issue.get("severity", "LOW")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

            return {
                "files_analyzed": 1,
                "total_issues": len(issues),
                "issues": issues,
                "severity_counts": severity_counts,
                "directory": str(target_path.parent)
            }
        else:
            return self.analyze_directory(target_path, ignore_patterns, severity_filter)

    def get_rules_info(self) -> List[Dict[str, str]]:
        """Get information about all available rules."""
        return [
            {
                "id": rule.id,
                "description": rule.description,
                "severity": rule.severity,
                "recommendation": rule.recommendation
            }
            for rule in self.rules
        ]

    def print_results(
        self,
        results: Dict[str, Any],
        output_format: str = "text",
        output_file: Optional[str] = None
    ) -> None:
        """
        Print analysis results.

        Args:
            results: Analysis results dictionary
            output_format: Output format ("text", "json", "table")
            output_file: Optional output file path
        """
        if output_format == "json":
            output = self.formatter.format_results(
                results["issues"], "json", results.get("directory", "")
            )
        else:
            # Group issues by file for better display
            issues_by_file = {}
            for issue in results["issues"]:
                file_path = issue.get("file_path", "unknown")
                if file_path not in issues_by_file:
                    issues_by_file[file_path] = []
                issues_by_file[file_path].append(issue)

            output_parts = []
            for file_path, file_issues in issues_by_file.items():
                file_output = self.formatter.format_results(
                    file_issues, output_format, file_path
                )
                output_parts.append(file_output)

            output = "\n".join(output_parts)

            # Add summary
            summary = self.formatter.print_summary(
                results["files_analyzed"],
                results["total_issues"],
                results["severity_counts"]
            )

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output)
        else:
            print(output)
