"""Test fixtures with safe code examples."""

# Safe alternatives to vulnerable patterns

# Safe alternative to eval()
def calculate_expression(expr):
    # Use ast.literal_eval for safe evaluation
    import ast
    try:
        return ast.literal_eval(expr)
    except ValueError:
        return None

# Safe secret management
import os
api_key = os.getenv("API_KEY")
secret_token = os.getenv("SECRET_TOKEN")

# Safe SQL queries
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = %s"
    cursor.execute(query, (user_id,))

# Safe command execution
import subprocess
result = subprocess.run(["ls", "-la"], shell=False, capture_output=True)

# Safe deserialization
import json
data = json.loads(user_input)

# Safe file operations
import os.path
def read_file(filename):
    # Validate and sanitize path
    safe_path = os.path.abspath(filename)
    if not safe_path.startswith("/safe/directory"):
        raise ValueError("Invalid path")
    
    try:
        with open(safe_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return None

# Input validation
def process_data(data):
    if not isinstance(data, str):
        raise TypeError("Data must be a string")
    if len(data) > 1000:
        raise ValueError("Data too long")
    return data.upper()

# Safe security checks
if not user.is_authenticated:
    raise PermissionError("Access denied")

# Secure HTTP requests
import requests
response = requests.get("https://api.example.com", verify=True)

# Strong cryptography
import hashlib
hash_value = hashlib.sha256(data).hexdigest()
