"""Test fixtures with vulnerable code examples."""

# PY001: eval() usage
def calculate_expression(expr):
    return eval(expr)

# PY002: Hardcoded secrets
api_key = "sk-1234567890abcdef"
secret_token = "ghp_abcdef1234567890"
password = "mypassword123"

# PY003: SQL injection
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)

# PY004: Command injection
import os
os.system("ls -la")

# PY005: Unsafe deserialization
import pickle
data = pickle.loads(user_input)

# PY006: Path traversal
with open("../etc/passwd", "r") as f:
    content = f.read()

# PY007: Missing input validation
def process_data(data):
    return data.upper()

# PY008: Assert for security
assert user.is_authenticated, "Access denied"

# PY009: Insecure HTTP
import requests
requests.get("https://api.example.com", verify=False)

# PY010: Weak cryptography
import hashlib
hash_value = hashlib.md5(data).hexdigest()

# PY011: Missing exception handling
def read_file(filename):
    with open(filename, "r") as f:
        return f.read()
