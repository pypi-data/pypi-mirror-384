# Contributing to SafeAI

Thank you for your interest in contributing to SafeAI! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Basic knowledge of Python security concepts

### Development Setup

1. **Fork the repository**

   ```bash
   git clone https://github.com/whickybravo388/safeai.git
   cd safeai
   ```

2. **Install in development mode**

   ```bash
   pip install -e .
   pip install -e ".[dev]"
   ```

3. **Run tests to ensure everything works**
   ```bash
   pytest
   ```

## 📝 Types of Contributions

### 🐛 Bug Reports

When reporting bugs, please include:

- **Description**: Clear description of the bug
- **Steps to reproduce**: Minimal code example
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: Python version, OS, etc.

### ✨ Feature Requests

For new features, please provide:

- **Use case**: Why is this feature needed?
- **Proposed solution**: How should it work?
- **Alternatives**: Other approaches considered
- **Additional context**: Any other relevant information

### 🔒 Security Rules

We welcome new security rules! When proposing a rule:

- **Vulnerability**: What security issue does it detect?
- **Severity**: HIGH, MEDIUM, or LOW?
- **Examples**: Vulnerable and safe code examples
- **Detection method**: How should it be detected?
- **False positives**: Potential false positive scenarios

## 🛠️ Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clean, readable code
- Add docstrings in Google style
- Follow existing code style
- Add tests for new functionality

### 3. Run Tests and Linting

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=safeai --cov-report=html

# Run linting
ruff check .

# Run type checking
mypy safeai/
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add new security rule for XSS detection"
```

Use conventional commit messages:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `test:` for tests
- `refactor:` for code refactoring

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## 📋 Code Style Guidelines

### Python Code Style

- Follow PEP 8
- Use type hints
- Write descriptive variable names
- Keep functions small and focused
- Add docstrings for all public functions

### Example Code Style

```python
def detect_xss_vulnerability(code: str, ast_tree: Optional[ast.AST] = None) -> Optional[Dict[str, Any]]:
    """
    Detect potential XSS vulnerabilities in code.

    Args:
        code: Source code to analyze
        ast_tree: Parsed AST tree (optional)

    Returns:
        Dictionary with vulnerability details if found, None otherwise
    """
    # Implementation here
    pass
```

### Test Style

- Write descriptive test names
- Use AAA pattern (Arrange, Act, Assert)
- Test both positive and negative cases
- Mock external dependencies

```python
def test_detect_xss_in_script_tag():
    """Test detection of XSS in script tags."""
    # Arrange
    rule = XSSRule()
    code = "<script>alert('xss')</script>"

    # Act
    result = rule.check(code)

    # Assert
    assert result is not None
    assert result["id"] == "XSS001"
```

## 🔒 Adding New Security Rules

### 1. Create Rule Class

```python
# safeai/rules/python_rules.py

class XSSRule(BaseRule):
    """Rule XSS001: Detect potential XSS vulnerabilities."""

    id = "XSS001"
    description = "Potential XSS vulnerability detected"
    severity = "HIGH"
    recommendation = "Sanitize user input and use proper escaping"

    def check(self, code: str, ast_tree: Optional[ast.AST] = None) -> Optional[Dict[str, Any]]:
        """Check for XSS vulnerabilities."""
        # Your detection logic here
        if "dangerous_pattern" in code:
            return self._create_issue(
                line=1,
                column=0,
                code_snippet="dangerous_pattern",
                details="XSS vulnerability detected"
            )
        return None
```

### 2. Add to Rules List

```python
# safeai/rules/python_rules.py

def get_rules() -> List[BaseRule]:
    """Get all Python security rules."""
    return [
        # ... existing rules ...
        XSSRule(),
    ]
```

### 3. Write Tests

```python
# tests/test_rules.py

class TestXSSRule:
    """Test cases for XSSRule."""

    def test_xss_detection(self):
        """Test detection of XSS vulnerabilities."""
        rule = XSSRule()
        code = "<script>alert('xss')</script>"
        result = rule.check(code)

        assert result is not None
        assert result["id"] == "XSS001"
        assert result["severity"] == "HIGH"

    def test_no_xss(self):
        """Test code without XSS vulnerabilities."""
        rule = XSSRule()
        code = "print('hello world')"
        result = rule.check(code)

        assert result is None
```

### 4. Update Documentation

Add your rule to `docs/rules.md`:

````markdown
### XSS001: XSS Vulnerability

**Description**: Detects potential XSS vulnerabilities...

**Example Vulnerable Code**:

```python
# Vulnerable code
```
````

**Safe Alternative**:

```python
# Safe code
```

````

## 🧪 Testing Guidelines

### Test Coverage

- Aim for 80%+ test coverage
- Test all public methods
- Test edge cases and error conditions
- Test both positive and negative scenarios

### Test Structure

```python
class TestYourFeature:
    """Test cases for YourFeature."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        pass

    def test_edge_cases(self):
        """Test edge cases."""
        pass

    def test_error_conditions(self):
        """Test error conditions."""
        pass
````

### Fixtures

Use fixtures for common test data:

```python
# tests/fixtures/vulnerable_code.py
VULNERABLE_CODE = """
# Test code with vulnerabilities
result = eval('1 + 1')
"""

# tests/test_rules.py
def test_rule_with_fixture():
    """Test rule using fixture."""
    rule = SomeRule()
    result = rule.check(VULNERABLE_CODE)
    assert result is not None
```

## 📚 Documentation Guidelines

### Code Documentation

- Write clear docstrings for all public functions
- Include type hints
- Provide usage examples
- Document parameters and return values

### User Documentation

- Update README.md for new features
- Add examples to documentation
- Keep documentation up-to-date
- Use clear, concise language

### API Documentation

```python
def analyze_code(self, code: str, file_path: str = "") -> List[Dict[str, Any]]:
    """
    Analyze code string for security vulnerabilities.

    Args:
        code: Source code to analyze
        file_path: Optional file path for context

    Returns:
        List of security issues found

    Example:
        >>> analyzer = CodeAnalyzer()
        >>> issues = analyzer.analyze_code("result = eval('1 + 1')")
        >>> print(f"Found {len(issues)} issues")
    """
```

## 🔍 Code Review Process

### What We Look For

- **Functionality**: Does the code work as intended?
- **Security**: Are there any security implications?
- **Performance**: Is the code efficient?
- **Maintainability**: Is the code easy to understand and modify?
- **Tests**: Are there adequate tests?
- **Documentation**: Is the code well-documented?

### Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass and coverage is adequate
- [ ] Documentation is updated
- [ ] No security vulnerabilities introduced
- [ ] Performance is acceptable
- [ ] Code is maintainable

## 🚀 Release Process

### Version Numbering

We use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Release Checklist

- [ ] All tests pass
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Version number is incremented
- [ ] Release notes are written

## 🤝 Community Guidelines

### Be Respectful

- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Focus on what's best for the community
- Show empathy towards other community members

### Be Constructive

- Provide helpful feedback
- Suggest improvements
- Ask clarifying questions
- Share knowledge and experience

### Be Patient

- Remember that everyone has different experience levels
- Be patient with questions and contributions
- Give people time to respond
- Understand that everyone is volunteering their time

## 📞 Getting Help

### Communication Channels

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: whickybravo388@gmail.com for private matters

### Before Asking for Help

1. Check existing documentation
2. Search GitHub issues and discussions
3. Try to reproduce the issue
4. Provide minimal reproduction case
5. Include relevant error messages

## 🎉 Recognition

Contributors will be recognized in:

- **CONTRIBUTORS.md**: List of all contributors
- **Release notes**: Credit for significant contributions
- **GitHub**: Contributor statistics and activity

Thank you for contributing to SafeAI! 🚀
