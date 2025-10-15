# SafeAI 🔒

**Security analyzer for AI-generated code**

SafeAI is a Python library that analyzes source code for security vulnerabilities commonly found in AI-generated code. It helps developers identify and fix security issues before they reach production.

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/safeai-scanner.svg)](https://badge.fury.io/py/safeai-scanner)
[![Downloads](https://static.pepy.tech/badge/safeai-scanner)](https://pepy.tech/project/safeai-scanner)
[![Downloads/Month](https://static.pepy.tech/badge/safeai-scanner/month)](https://pepy.tech/project/safeai-scanner)

## 🚀 Features

- **11 Security Rules**: Comprehensive detection of common vulnerabilities
- **AI-Focused**: Specifically designed for AI-generated code patterns
- **Multiple Output Formats**: Text, JSON, and table output
- **CLI Interface**: Easy-to-use command-line tool
- **Severity Levels**: HIGH, MEDIUM, LOW classification
- **Extensible**: Easy to add custom security rules

## 📦 Installation

```bash
pip install safeai-scanner
```

## 🎯 Quick Start

### Basic Usage

```bash
# Scan a single file
safeai scan main.py

# Scan a directory
safeai scan ./myproject

# Get detailed output
safeai scan ./myproject --format table

# Export results to JSON
safeai scan ./myproject --format json --output report.json
```

### Command Line Options

```bash
# Filter by severity
safeai scan ./myproject --severity HIGH,MEDIUM

# Ignore specific directories
safeai scan ./myproject --ignore tests,docs,venv

# Fail CI/CD pipeline if issues found
safeai scan ./myproject --fail-on-error

# List all available rules
safeai list-rules

# Show version
safeai version
```

## 🔍 Security Rules

SafeAI includes 11 security rules specifically designed for AI-generated code:

### Critical (HIGH) Severity

- **PY001**: `eval()`/`exec()` usage - Code injection risk
- **PY002**: Hardcoded secrets - API keys, tokens, passwords
- **PY003**: SQL injection - String concatenation in SQL queries
- **PY004**: Command injection - `os.system()`, `subprocess` with `shell=True`
- **PY005**: Unsafe deserialization - `pickle.loads()`, `yaml.load()` without Loader

### Medium (MEDIUM) Severity

- **PY006**: Path traversal - File operations without path validation
- **PY007**: Missing input validation - Functions without parameter validation
- **PY008**: Assert for security - Security checks using `assert` (can be disabled)
- **PY009**: Insecure HTTP - `requests` with `verify=False`

### Low (LOW) Severity

- **PY010**: Weak cryptography - MD5, SHA1, DES usage
- **PY011**: Missing exception handling - Critical operations without try/except

## 📋 Example Output

```bash
$ safeai scan vulnerable_code.py

⚠️  Found 3 security issues in vulnerable_code.py:

🔴 [PY001] Using eval() or exec() can be unsafe
   Line 3: result = eval(expr)
   Recommendation: Avoid using eval() and exec(). Use safe alternatives or thoroughly validate input data.

🔴 [PY002] Hardcoded secrets or tokens detected in code
   Line 6: api_key = "sk-1234567890abcdef"
   Recommendation: Use environment variables or configuration files to store secrets.

🟡 [PY010] Using weak cryptographic algorithms
   Line 15: hash_value = hashlib.md5(data).hexdigest()
   Recommendation: Use modern cryptographic algorithms: SHA-256 instead of MD5/SHA1.
```

## 🐍 Python API

```python
from safeai import CodeAnalyzer

# Initialize analyzer
analyzer = CodeAnalyzer()

# Analyze code string
code = "result = eval('1 + 1')"
issues = analyzer.analyze_code(code)

# Analyze file
issues = analyzer.analyze_file("main.py")

# Analyze directory
results = analyzer.analyze_directory("./myproject")

# Get rules information
rules = analyzer.get_rules_info()
```

## 🔧 Configuration

### Ignore Patterns

SafeAI automatically ignores common directories:

- `__pycache__`, `.git`, `.pytest_cache`
- `venv`, `env`, `.venv`, `.env`
- `node_modules`, `.tox`, `.nox`
- `build`, `dist`, `*.egg-info`

### Custom Ignore Patterns

```bash
safeai scan ./myproject --ignore custom_dir,another_dir
```

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/whickybravo388/safeai.git
cd safeai

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .

# Run type checking
mypy safeai/
```

### Adding Custom Rules

```python
from safeai.rules.base import BaseRule

class CustomRule(BaseRule):
    id = "CUSTOM001"
    description = "Custom security rule"
    severity = "MEDIUM"
    recommendation = "Fix this issue"

    def check(self, code: str, ast_tree=None):
        # Your detection logic here
        if "dangerous_pattern" in code:
            return self._create_issue(
                line=1,
                column=0,
                code_snippet="dangerous_pattern",
                details="Custom issue detected"
            )
        return None
```

## 📊 CI/CD Integration

### GitHub Actions

```yaml
name: Security Scan
on: [push, pull_request]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.9"
      - name: Install SafeAI
        run: pip install safeai
      - name: Run security scan
        run: safeai scan . --fail-on-error
```

### GitLab CI

```yaml
security-scan:
  stage: test
  image: python:3.9
  script:
    - pip install safeai
    - safeai scan . --fail-on-error
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by tools like [Bandit](https://bandit.readthedocs.io/) and [Safety](https://pyup.io/safety/)
- Built with [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- Uses Python's built-in `ast` module for code analysis

## 📞 Support

- 📧 Email: whickybravo388@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/whickybravo388/safeai/issues)

## 🔄 Changelog

### v0.1.0 (2024-01-XX)

- Initial release
- 11 security rules for Python
- CLI interface with multiple output formats
- Comprehensive test suite
- Full documentation

---

**Made with ❤️ by the SafeAI Team**
