"""Output formatting utilities for SafeAI."""

import json
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box


class Formatter:
    """Utility class for formatting analysis results."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def format_results(
        self,
        results: List[Dict[str, Any]],
        format_type: str = "text",
        file_path: str = ""
    ) -> str:
        """
        Format analysis results.

        Args:
            results: List of analysis results
            format_type: Output format ("text", "json", "table")
            file_path: Path to analyzed file

        Returns:
            Formatted string
        """
        if format_type == "json":
            return self._format_json(results, file_path)
        elif format_type == "table":
            return self._format_table(results, file_path)
        else:
            return self._format_text(results, file_path)

    def _format_json(self, results: List[Dict[str, Any]], file_path: str) -> str:
        """Format results as JSON."""
        output = {
            "file": file_path,
            "issues": results,
            "total_issues": len(results),
            "severity_counts": self._count_severities(results)
        }
        return json.dumps(output, indent=2, ensure_ascii=False)

    def _format_table(self, results: List[Dict[str, Any]], file_path: str) -> str:
        """Format results as a rich table."""
        if not results:
            return f"✅ No security issues found in {file_path}"

        table = Table(title=f"Security Analysis Results: {file_path}", box=box.ROUNDED)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Severity", style="bold")
        table.add_column("Line", justify="right", style="green")
        table.add_column("Description", style="white")
        table.add_column("Recommendation", style="dim")

        for result in results:
            severity_color = self._get_severity_color(result["severity"])
            table.add_row(
                result["id"],
                Text(result["severity"], style=severity_color),
                str(result["line"]),
                result["description"],
                result["recommendation"]
            )

        # Capture table output
        with self.console.capture() as capture:
            self.console.print(table)
        return capture.get()

    def _format_text(self, results: List[Dict[str, Any]], file_path: str) -> str:
        """Format results as plain text."""
        if not results:
            return f"✅ No security issues found in {file_path}"

        output = [f"⚠️  Found {len(results)} security issues in {file_path}:\n"]

        for result in results:
            severity_icon = self._get_severity_icon(result["severity"])
            output.append(
                f"{severity_icon} [{result['id']}] {result['description']}\n"
                f"   Line {result['line']}: {result['code_snippet']}\n"
                f"   Recommendation: {result['recommendation']}\n"
            )

        return "\n".join(output)

    def _count_severities(self, results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count issues by severity."""
        counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for result in results:
            severity = result.get("severity", "LOW")
            counts[severity] = counts.get(severity, 0) + 1
        return counts

    def _get_severity_color(self, severity: str) -> str:
        """Get color for severity level."""
        colors = {
            "HIGH": "bold red",
            "MEDIUM": "bold yellow",
            "LOW": "bold blue"
        }
        return colors.get(severity, "white")

    def _get_severity_icon(self, severity: str) -> str:
        """Get icon for severity level."""
        icons = {
            "HIGH": "🔴",
            "MEDIUM": "🟡",
            "LOW": "🔵"
        }
        return icons.get(severity, "⚪")

    def print_summary(self, total_files: int, total_issues: int, severity_counts: Dict[str, int]):
        """Print analysis summary."""
        summary_text = f"""
📊 Analysis Summary:
   Files scanned: {total_files}
   Total issues: {total_issues}
   
   Severity breakdown:
   🔴 High: {severity_counts.get('HIGH', 0)}
   🟡 Medium: {severity_counts.get('MEDIUM', 0)}
   🔵 Low: {severity_counts.get('LOW', 0)}
        """

        panel = Panel(
            summary_text.strip(),
            title="SafeAI Analysis Complete",
            border_style="green" if total_issues == 0 else "yellow"
        )
        self.console.print(panel)
