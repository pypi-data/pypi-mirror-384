# Security Rules Documentation

This document provides detailed information about all security rules implemented in SafeAI.

## Rule Categories

SafeAI rules are categorized by severity level:

- **HIGH**: Critical security vulnerabilities that should be fixed immediately
- **MEDIUM**: Important security issues that should be addressed
- **LOW**: Security improvements and best practices

## HIGH Severity Rules

### PY001: eval()/exec() Usage

**Description**: Detects usage of `eval()` and `exec()` functions which can lead to code injection vulnerabilities.

**Risk**: Code injection attacks, arbitrary code execution

**Example Vulnerable Code**:
```python
def calculate(expression):
    return eval(expression)  # Dangerous!

# Attacker can execute arbitrary code
result = calculate("__import__('os').system('rm -rf /')")
```

**Safe Alternative**:
```python
import ast

def calculate(expression):
    try:
        return ast.literal_eval(expression)  # Safe for literals only
    except ValueError:
        # Handle non-literal expressions safely
        return None
```

**Recommendation**: Avoid `eval()` and `exec()`. Use `ast.literal_eval()` for safe evaluation of literals, or implement a proper parser for your specific use case.

---

### PY002: Hardcoded Secrets

**Description**: Detects hardcoded API keys, tokens, passwords, and other sensitive information.

**Risk**: Credential exposure, unauthorized access

**Example Vulnerable Code**:
```python
# All of these are dangerous
api_key = "sk-1234567890abcdef"
secret_token = "ghp_abcdef1234567890"
password = "mypassword123"
private_key = "-----BEGIN PRIVATE KEY-----..."
```

**Safe Alternative**:
```python
import os

# Use environment variables
api_key = os.getenv("API_KEY")
secret_token = os.getenv("SECRET_TOKEN")
password = os.getenv("PASSWORD")

# Or use a configuration management system
from config import settings
api_key = settings.api_key
```

**Recommendation**: Store secrets in environment variables, configuration files, or secret management systems. Never commit secrets to version control.

---

### PY003: SQL Injection

**Description**: Detects SQL queries constructed using string concatenation, which can lead to SQL injection attacks.

**Risk**: Database compromise, data theft, data manipulation

**Example Vulnerable Code**:
```python
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)  # Vulnerable to SQL injection

# Attacker can manipulate the query
user = get_user("1; DROP TABLE users; --")
```

**Safe Alternative**:
```python
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = %s"
    cursor.execute(query, (user_id,))  # Parameterized query

# Or use an ORM
from sqlalchemy import text
query = text("SELECT * FROM users WHERE id = :user_id")
result = session.execute(query, {"user_id": user_id})
```

**Recommendation**: Use parameterized queries or ORM methods. Never concatenate user input directly into SQL queries.

---

### PY004: Command Injection

**Description**: Detects dangerous command execution patterns that can lead to command injection attacks.

**Risk**: Remote code execution, system compromise

**Example Vulnerable Code**:
```python
import os
import subprocess

# Dangerous patterns
os.system("ls " + user_input)  # Command injection risk
subprocess.run(f"echo {user_input}", shell=True)  # Shell injection
```

**Safe Alternative**:
```python
import subprocess

# Safe command execution
subprocess.run(["ls", user_input], shell=False)  # No shell injection

# Or use specific APIs
import shutil
shutil.copy(user_input, destination)  # Safer file operations
```

**Recommendation**: Avoid `os.system()` and `subprocess` with `shell=True`. Use `subprocess.run()` with `shell=False` and pass arguments as a list.

---

### PY005: Unsafe Deserialization

**Description**: Detects unsafe deserialization of data that can lead to arbitrary code execution.

**Risk**: Remote code execution, object injection attacks

**Example Vulnerable Code**:
```python
import pickle
import yaml

# Dangerous deserialization
data = pickle.loads(user_input)  # Can execute arbitrary code
config = yaml.load(user_input)   # Unsafe without Loader
```

**Safe Alternative**:
```python
import json
import yaml

# Safe deserialization
data = json.loads(user_input)  # JSON is safe
config = yaml.safe_load(user_input)  # Safe YAML loading

# Or use yaml.load with SafeLoader
config = yaml.load(user_input, Loader=yaml.SafeLoader)
```

**Recommendation**: Avoid `pickle.loads()` and `yaml.load()` without a safe Loader. Use `json.loads()` or `yaml.safe_load()` for safe deserialization.

## MEDIUM Severity Rules

### PY006: Path Traversal

**Description**: Detects file operations that may be vulnerable to path traversal attacks.

**Risk**: Unauthorized file access, information disclosure

**Example Vulnerable Code**:
```python
def read_file(filename):
    with open(filename, 'r') as f:  # Vulnerable to path traversal
        return f.read()

# Attacker can access sensitive files
content = read_file("../../../etc/passwd")
```

**Safe Alternative**:
```python
import os.path

def read_file(filename):
    # Validate and sanitize path
    safe_path = os.path.abspath(filename)
    allowed_dir = "/safe/directory"
    
    if not safe_path.startswith(allowed_dir):
        raise ValueError("Invalid path")
    
    with open(safe_path, 'r') as f:
        return f.read()
```

**Recommendation**: Validate and sanitize file paths. Use `os.path.abspath()` and ensure paths are within allowed directories.

---

### PY007: Missing Input Validation

**Description**: Detects functions that accept user input without proper validation.

**Risk**: Data corruption, application errors, security bypass

**Example Vulnerable Code**:
```python
def process_data(data):
    return data.upper()  # No validation of input type or content

# Could cause errors or unexpected behavior
result = process_data(123)  # TypeError
result = process_data(None)  # AttributeError
```

**Safe Alternative**:
```python
def process_data(data):
    # Validate input
    if not isinstance(data, str):
        raise TypeError("Data must be a string")
    
    if len(data) > 1000:
        raise ValueError("Data too long")
    
    # Sanitize input
    data = data.strip()
    
    return data.upper()
```

**Recommendation**: Always validate input data types, ranges, and format. Implement proper error handling for invalid inputs.

---

### PY008: Assert for Security

**Description**: Detects use of `assert` statements for security checks, which can be disabled in production.

**Risk**: Security bypass, access control failure

**Example Vulnerable Code**:
```python
def secure_function():
    assert user.is_authenticated, "Access denied"  # Can be disabled with -O
    assert user.has_permission("admin"), "Insufficient privileges"
    # Critical security logic here
```

**Safe Alternative**:
```python
def secure_function():
    if not user.is_authenticated:
        raise PermissionError("Access denied")
    
    if not user.has_permission("admin"):
        raise PermissionError("Insufficient privileges")
    
    # Critical security logic here
```

**Recommendation**: Use explicit `if` statements with appropriate exceptions instead of `assert` for security checks. `assert` can be disabled with Python's `-O` flag.

---

### PY009: Insecure HTTP

**Description**: Detects HTTP requests with SSL verification disabled.

**Risk**: Man-in-the-middle attacks, data interception

**Example Vulnerable Code**:
```python
import requests

# Dangerous - disables SSL verification
response = requests.get("https://api.example.com", verify=False)
response = requests.post("https://api.example.com", verify=False)
```

**Safe Alternative**:
```python
import requests

# Safe - SSL verification enabled by default
response = requests.get("https://api.example.com")
response = requests.post("https://api.example.com")

# Or explicitly enable verification
response = requests.get("https://api.example.com", verify=True)
```

**Recommendation**: Always use HTTPS with SSL verification enabled. Only disable verification in development environments with proper justification.

## LOW Severity Rules

### PY010: Weak Cryptography

**Description**: Detects use of weak cryptographic algorithms that are no longer considered secure.

**Risk**: Cryptographic attacks, data compromise

**Example Vulnerable Code**:
```python
import hashlib
from Crypto.Cipher import DES

# Weak algorithms
hash_value = hashlib.md5(data).hexdigest()    # MD5 is broken
hash_value = hashlib.sha1(data).hexdigest()   # SHA1 is weak
cipher = DES.new(key, DES.MODE_ECB)           # DES is weak
```

**Safe Alternative**:
```python
import hashlib
from Crypto.Cipher import AES

# Strong algorithms
hash_value = hashlib.sha256(data).hexdigest()  # SHA256 is secure
hash_value = hashlib.sha3_256(data).hexdigest()  # SHA3 is even better
cipher = AES.new(key, AES.MODE_GCM)  # AES-GCM is secure
```

**Recommendation**: Use modern cryptographic algorithms: SHA-256 or SHA-3 for hashing, AES for encryption. Avoid MD5, SHA1, and DES.

---

### PY011: Missing Exception Handling

**Description**: Detects critical operations that lack proper exception handling.

**Risk**: Application crashes, information disclosure, poor user experience

**Example Vulnerable Code**:
```python
def read_file(filename):
    with open(filename, 'r') as f:  # No exception handling
        return f.read()

def connect_to_database():
    connection = database.connect()  # No exception handling
    return connection
```

**Safe Alternative**:
```python
def read_file(filename):
    try:
        with open(filename, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return None
    except PermissionError:
        raise PermissionError("Cannot read file")
    except Exception as e:
        raise IOError(f"Error reading file: {e}")

def connect_to_database():
    try:
        connection = database.connect()
        return connection
    except ConnectionError as e:
        raise ConnectionError(f"Database connection failed: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {e}")
```

**Recommendation**: Add proper exception handling for critical operations: file I/O, network requests, database operations. Use specific exception types when possible.

## Rule Configuration

### Customizing Rules

You can customize rule behavior by extending the base rule class:

```python
from safeai.rules.base import BaseRule

class CustomRule(BaseRule):
    id = "CUSTOM001"
    description = "Custom security rule"
    severity = "MEDIUM"
    recommendation = "Fix this custom issue"

    def check(self, code: str, ast_tree=None):
        # Your custom detection logic
        if "custom_pattern" in code:
            return self._create_issue(
                line=1,
                column=0,
                code_snippet="custom_pattern",
                details="Custom issue detected"
            )
        return None
```

### Disabling Rules

To disable specific rules, you can filter them out:

```python
from safeai import CodeAnalyzer

analyzer = CodeAnalyzer()
# Filter out specific rules
analyzer.rules = [rule for rule in analyzer.rules if rule.id != "PY011"]
```

## Best Practices

1. **Regular Scanning**: Run SafeAI regularly in your CI/CD pipeline
2. **Severity Prioritization**: Fix HIGH severity issues first
3. **Custom Rules**: Add project-specific security rules
4. **Team Education**: Educate team members about security best practices
5. **Continuous Improvement**: Regularly update and improve security rules

## Contributing New Rules

We welcome contributions of new security rules! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to add new rules to SafeAI.
