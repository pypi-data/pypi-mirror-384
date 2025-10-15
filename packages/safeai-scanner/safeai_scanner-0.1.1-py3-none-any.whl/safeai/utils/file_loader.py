"""File loading utilities for SafeAI."""

import os
from pathlib import Path
from typing import Generator, List, Tuple


class FileLoader:
    """Utility class for loading and processing files."""

    # Default ignore patterns
    DEFAULT_IGNORE_PATTERNS = {
        "__pycache__",
        ".git",
        ".pytest_cache",
        ".mypy_cache",
        ".coverage",
        "venv",
        "env",
        ".venv",
        ".env",
        "node_modules",
        ".tox",
        ".nox",
        "build",
        "dist",
        "*.egg-info",
    }

    @staticmethod
    def is_python_file(file_path: Path) -> bool:
        """Check if file is a Python file."""
        return file_path.suffix == ".py"

    @staticmethod
    def should_ignore(file_path: Path, ignore_patterns: List[str] = None) -> bool:
        """Check if file should be ignored based on patterns."""
        if ignore_patterns is None:
            ignore_patterns = list(FileLoader.DEFAULT_IGNORE_PATTERNS)

        # Check if any part of the path matches ignore patterns
        path_parts = file_path.parts
        for pattern in ignore_patterns:
            if pattern in path_parts:
                return True
            # Check for wildcard patterns
            if "*" in pattern:
                import fnmatch
                for part in path_parts:
                    if fnmatch.fnmatch(part, pattern):
                        return True
        return False

    @staticmethod
    def find_python_files(
        root_path: Path,
        ignore_patterns: List[str] = None
    ) -> Generator[Path, None, None]:
        """Find all Python files in directory tree."""
        if not root_path.exists():
            return

        if root_path.is_file():
            if FileLoader.is_python_file(root_path):
                yield root_path
            return

        for file_path in root_path.rglob("*.py"):
            if not FileLoader.should_ignore(file_path, ignore_patterns):
                yield file_path

    @staticmethod
    def read_file(file_path: Path) -> Tuple[str, str]:
        """
        Read file content with encoding detection.

        Returns:
            Tuple of (content, encoding)
        """
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        
        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                return content, encoding
            except UnicodeDecodeError:
                continue
        
        # Fallback to binary read with error handling
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return content, "utf-8"
        except Exception as e:
            raise IOError(f"Could not read file {file_path}: {e}")

    @staticmethod
    def get_file_info(file_path: Path) -> dict:
        """Get file metadata."""
        try:
            stat = file_path.stat()
            return {
                "path": str(file_path),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "is_file": file_path.is_file(),
                "is_dir": file_path.is_dir(),
            }
        except OSError:
            return {
                "path": str(file_path),
                "size": 0,
                "modified": 0,
                "is_file": False,
                "is_dir": False,
            }
