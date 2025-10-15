"""Command-line interface for SafeAI."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Set

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .analyzer import CodeAnalyzer
from .utils.formatter import Formatter


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="SafeAI - Security analyzer for AI-generated code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  safeai scan ./myproject
  safeai scan main.py --format json --output report.json
  safeai scan ./src --severity HIGH,MEDIUM --ignore tests,docs
  safeai list-rules
  safeai version
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan code for security vulnerabilities")
    scan_parser.add_argument(
        "path",
        help="Path to file or directory to scan"
    )
    scan_parser.add_argument(
        "--format",
        choices=["text", "json", "table"],
        default="text",
        help="Output format (default: text)"
    )
    scan_parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: stdout)"
    )
    scan_parser.add_argument(
        "--severity",
        help="Comma-separated list of severity levels to include (HIGH,MEDIUM,LOW)"
    )
    scan_parser.add_argument(
        "--ignore",
        help="Comma-separated list of directories to ignore"
    )
    scan_parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit with non-zero code if issues are found"
    )
    scan_parser.add_argument(
        "--lang",
        default="python",
        help="Programming language (default: python)"
    )

    # List rules command
    rules_parser = subparsers.add_parser("list-rules", help="List all available security rules")
    rules_parser.add_argument(
        "--format",
        choices=["text", "table"],
        default="table",
        help="Output format (default: table)"
    )

    # Version command
    subparsers.add_parser("version", help="Show version information")

    return parser


def parse_severity_filter(severity_str: Optional[str]) -> Optional[Set[str]]:
    """Parse severity filter string."""
    if not severity_str:
        return None
    
    severities = {s.strip().upper() for s in severity_str.split(",")}
    valid_severities = {"HIGH", "MEDIUM", "LOW"}
    
    if not severities.issubset(valid_severities):
        invalid = severities - valid_severities
        raise ValueError(f"Invalid severity levels: {', '.join(invalid)}")
    
    return severities


def parse_ignore_patterns(ignore_str: Optional[str]) -> Optional[List[str]]:
    """Parse ignore patterns string."""
    if not ignore_str:
        return None
    
    return [pattern.strip() for pattern in ignore_str.split(",")]


def print_rules(analyzer: CodeAnalyzer, format_type: str = "table") -> None:
    """Print available security rules."""
    console = Console()
    rules = analyzer.get_rules_info()
    
    if format_type == "table":
        table = Table(title="Available Security Rules", box=None)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Severity", style="bold")
        table.add_column("Description", style="white")
        
        for rule in rules:
            severity_color = {
                "HIGH": "bold red",
                "MEDIUM": "bold yellow", 
                "LOW": "bold blue"
            }.get(rule["severity"], "white")
            
            table.add_row(
                rule["id"],
                Text(rule["severity"], style=severity_color),
                rule["description"]
            )
        
        console.print(table)
    else:
        # Text format
        for rule in rules:
            severity_icon = {
                "HIGH": "🔴",
                "MEDIUM": "🟡",
                "LOW": "🔵"
            }.get(rule["severity"], "⚪")
            
            console.print(f"{severity_icon} [{rule['id']}] {rule['description']}")
            console.print(f"   Severity: {rule['severity']}")
            console.print(f"   Recommendation: {rule['recommendation']}")
            console.print()


def print_version() -> None:
    """Print version information."""
    console = Console()
    
    version_info = f"""
SafeAI Security Analyzer
Version: 0.1.0
Author: SafeAI Team
License: MIT

A Python library for analyzing AI-generated code for security vulnerabilities.
    """.strip()
    
    panel = Panel(
        version_info,
        title="SafeAI",
        border_style="green"
    )
    console.print(panel)


def scan_command(args: argparse.Namespace) -> int:
    """Execute scan command."""
    console = Console()
    
    try:
        # Parse arguments
        severity_filter = parse_severity_filter(args.severity)
        ignore_patterns = parse_ignore_patterns(args.ignore)
        
        # Initialize analyzer
        analyzer = CodeAnalyzer(language=args.lang)
        
        # Check if path exists
        target_path = Path(args.path)
        if not target_path.exists():
            console.print(f"[red]Error: Path '{args.path}' does not exist[/red]")
            return 1
        
        # Perform analysis
        console.print(f"[blue]Scanning: {args.path}[/blue]")
        results = analyzer.analyze_path(
            args.path,
            ignore_patterns=ignore_patterns,
            severity_filter=severity_filter
        )
        
        # Print results
        analyzer.print_results(
            results,
            output_format=args.format,
            output_file=args.output
        )
        
        # Return appropriate exit code
        if args.fail_on_error and results["total_issues"] > 0:
            return 1
        
        return 0
        
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        return 1


def list_rules_command(args: argparse.Namespace) -> int:
    """Execute list-rules command."""
    analyzer = CodeAnalyzer()
    print_rules(analyzer, args.format)
    return 0


def version_command(args: argparse.Namespace) -> int:
    """Execute version command."""
    print_version()
    return 0


def main() -> int:
    """Main entry point for CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate command handler
    if args.command == "scan":
        return scan_command(args)
    elif args.command == "list-rules":
        return list_rules_command(args)
    elif args.command == "version":
        return version_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
