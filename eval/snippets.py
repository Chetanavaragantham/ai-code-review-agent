"""
20 labeled Python snippets for evaluating agent tool selection accuracy.

Each snippet has:
  - code:           the Python code string
  - description:    what kind of code it is
  - expected_tools: which tools SHOULD be called for a good review
  - category:       clean / style / security / complexity / buggy
"""

SNIPPETS = [
    # ── CLEAN CODE (5) ────────────────────────────────────────────────────────
    {
        "id": 1,
        "category": "clean",
        "description": "Well-written function with docstring",
        "expected_tools": ["analyze_ast", "analyze_style"],
        "code": (
            "def celsius_to_fahrenheit(celsius: float) -> float:\n"
            "    \"\"\"Convert Celsius to Fahrenheit.\"\"\"\n"
            "    return celsius * 9 / 5 + 32\n"
        ),
    },
    {
        "id": 2,
        "category": "clean",
        "description": "Simple class with docstrings",
        "expected_tools": ["analyze_ast", "analyze_style"],
        "code": (
            "class Stack:\n"
            "    \"\"\"A simple LIFO stack.\"\"\"\n\n"
            "    def __init__(self):\n"
            "        \"\"\"Initialize empty stack.\"\"\"\n"
            "        self._items = []\n\n"
            "    def push(self, item):\n"
            "        \"\"\"Push item onto stack.\"\"\"\n"
            "        self._items.append(item)\n\n"
            "    def pop(self):\n"
            "        \"\"\"Pop item from stack.\"\"\"\n"
            "        return self._items.pop()\n"
        ),
    },
    {
        "id": 3,
        "category": "clean",
        "description": "Pure function, no side effects",
        "expected_tools": ["analyze_ast", "analyze_complexity"],
        "code": (
            "def fibonacci(n: int) -> list[int]:\n"
            "    \"\"\"Return first n Fibonacci numbers.\"\"\"\n"
            "    if n <= 0:\n"
            "        return []\n"
            "    seq = [0, 1]\n"
            "    while len(seq) < n:\n"
            "        seq.append(seq[-1] + seq[-2])\n"
            "    return seq[:n]\n"
        ),
    },
    {
        "id": 4,
        "category": "clean",
        "description": "Context manager with proper resource handling",
        "expected_tools": ["analyze_ast", "analyze_style"],
        "code": (
            "from contextlib import contextmanager\n\n"
            "@contextmanager\n"
            "def open_file(path: str, mode: str = \"r\"):\n"
            "    \"\"\"Safely open a file and ensure it is closed.\"\"\"\n"
            "    fh = open(path, mode)\n"
            "    try:\n"
            "        yield fh\n"
            "    finally:\n"
            "        fh.close()\n"
        ),
    },
    {
        "id": 5,
        "category": "clean",
        "description": "Dataclass with type hints",
        "expected_tools": ["analyze_ast", "analyze_style"],
        "code": (
            "from dataclasses import dataclass\n\n"
            "@dataclass\n"
            "class Point:\n"
            "    \"\"\"A 2D point.\"\"\"\n"
            "    x: float\n"
            "    y: float\n\n"
            "    def distance_to(self, other: \"Point\") -> float:\n"
            "        \"\"\"Euclidean distance to another point.\"\"\"\n"
            "        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5\n"
        ),
    },

    # ── STYLE ISSUES (5) ──────────────────────────────────────────────────────
    {
        "id": 6,
        "category": "style",
        "description": "Missing docstrings on all functions",
        "expected_tools": ["analyze_ast", "analyze_style"],
        "code": (
            "def add(a, b):\n"
            "    return a + b\n\n"
            "def subtract(a, b):\n"
            "    return a - b\n\n"
            "def multiply(a, b):\n"
            "    return a * b\n"
        ),
    },
    {
        "id": 7,
        "category": "style",
        "description": "Poor naming: single-letter variables",
        "expected_tools": ["analyze_ast", "analyze_style"],
        "code": (
            "def f(x, y, z):\n"
            "    a = x + y\n"
            "    b = a * z\n"
            "    c = b / x if x != 0 else 0\n"
            "    return c\n"
        ),
    },
    {
        "id": 8,
        "category": "style",
        "description": "Long function, no docstring, magic numbers",
        "expected_tools": ["analyze_ast", "analyze_style", "analyze_complexity"],
        "code": (
            "def process(data):\n"
            "    out = []\n"
            "    for item in data:\n"
            "        if item > 100:\n"
            "            out.append(item * 1.15)\n"
            "        elif item > 50:\n"
            "            out.append(item * 1.08)\n"
            "        elif item > 25:\n"
            "            out.append(item * 1.03)\n"
            "        else:\n"
            "            out.append(item)\n"
            "    return out\n"
        ),
    },
    {
        "id": 9,
        "category": "style",
        "description": "Unused imports and variables",
        "expected_tools": ["analyze_ast", "analyze_style"],
        "code": (
            "import os\n"
            "import sys\n"
            "import json\n\n"
            "def greet(name):\n"
            "    unused_var = 42\n"
            "    return f\"Hello, {name}!\"\n"
        ),
    },
    {
        "id": 10,
        "category": "style",
        "description": "Inconsistent return types, no type hints",
        "expected_tools": ["analyze_ast", "analyze_style"],
        "code": (
            "def divide(a, b):\n"
            "    if b == 0:\n"
            "        return None\n"
            "    return a / b\n\n"
            "def safe_get(d, key):\n"
            "    if key in d:\n"
            "        return d[key]\n"
        ),
    },

    # ── SECURITY ISSUES (5) ───────────────────────────────────────────────────
    {
        "id": 11,
        "category": "security",
        "description": "Shell injection via subprocess",
        "expected_tools": ["analyze_security", "analyze_ast"],
        "code": (
            "import subprocess\n\n"
            "def run_command(user_input: str) -> str:\n"
            "    result = subprocess.check_output(user_input, shell=True)\n"
            "    return result.decode()\n"
        ),
    },
    {
        "id": 12,
        "category": "security",
        "description": "Hardcoded credentials",
        "expected_tools": ["analyze_security", "analyze_ast"],
        "code": (
            "import psycopg2\n\n"
            "def get_connection():\n"
            "    return psycopg2.connect(\n"
            "        host=\"prod-db.internal\",\n"
            "        user=\"admin\",\n"
            "        password=\"super_secret_123\",\n"
            "        dbname=\"users\",\n"
            "    )\n"
        ),
    },
    {
        "id": 13,
        "category": "security",
        "description": "SQL injection via string formatting",
        "expected_tools": ["analyze_security", "analyze_ast"],
        "code": (
            "import sqlite3\n\n"
            "def get_user(username: str):\n"
            "    conn = sqlite3.connect(\"users.db\")\n"
            "    cursor = conn.cursor()\n"
            "    query = f\"SELECT * FROM users WHERE username = \'{username}\'\"\n"
            "    cursor.execute(query)\n"
            "    return cursor.fetchone()\n"
        ),
    },
    {
        "id": 14,
        "category": "security",
        "description": "Use of eval() on user input",
        "expected_tools": ["analyze_security", "analyze_ast"],
        "code": (
            "def calculate(expression: str) -> float:\n"
            "    \"\"\"Evaluate a math expression from user input.\"\"\"\n"
            "    return eval(expression)\n"
        ),
    },
    {
        "id": 15,
        "category": "security",
        "description": "Insecure random for token generation",
        "expected_tools": ["analyze_security", "analyze_ast"],
        "code": (
            "import random\n"
            "import string\n\n"
            "def generate_token(length: int = 32) -> str:\n"
            "    \"\"\"Generate an auth token.\"\"\"\n"
            "    chars = string.ascii_letters + string.digits\n"
            "    return \"\.join(random.choice(chars) for _ in range(length))\n"
        ),
    },

    # ── COMPLEXITY ISSUES (5) ─────────────────────────────────────────────────
    {
        "id": 16,
        "category": "complexity",
        "description": "Deeply nested conditionals",
        "expected_tools": ["analyze_complexity", "analyze_ast"],
        "code": (
            "def classify(x, y, z):\n"
            "    if x > 0:\n"
            "        if y > 0:\n"
            "            if z > 0:\n"
            "                return \"all positive\"\n"
            "            else:\n"
            "                return \"z negative\"\n"
            "        else:\n"
            "            if z > 0:\n"
            "                return \"y negative\"\n"
            "            else:\n"
            "                return \"y and z negative\"\n"
            "    else:\n"
            "        if y > 0:\n"
            "            return \"x negative\"\n"
            "        else:\n"
            "            return \"x and y negative\"\n"
        ),
    },
    {
        "id": 17,
        "category": "complexity",
        "description": "O(n^2) nested loop",
        "expected_tools": ["analyze_complexity", "analyze_ast"],
        "code": (
            "def find_duplicates(items: list) -> list:\n"
            "    duplicates = []\n"
            "    for i in range(len(items)):\n"
            "        for j in range(len(items)):\n"
            "            if i != j and items[i] == items[j]:\n"
            "                if items[i] not in duplicates:\n"
            "                    duplicates.append(items[i])\n"
            "    return duplicates\n"
        ),
    },
    {
        "id": 18,
        "category": "complexity",
        "description": "Function doing too many things (SRP violation)",
        "expected_tools": ["analyze_complexity", "analyze_ast", "analyze_style"],
        "code": (
            "def handle_order(order_id, db, email_client, logger):\n"
            "    order = db.query(f\"SELECT * FROM orders WHERE id={order_id}\")\n"
            "    if not order:\n"
            "        logger.error(\"Order not found\")\n"
            "        return False\n"
            "    if order[\"status\"] == \"paid\":\n"
            "        db.execute(\"UPDATE orders SET status=\'processing\' WHERE id={}\".format(order_id))\n"
            "        email_client.send(order[\"email\"], \"Your order is being processed\")\n"
            "        logger.info(\"Order processed\")\n"
            "        return True\n"
            "    return False\n"
        ),
    },
    {
        "id": 19,
        "category": "complexity",
        "description": "Long chained conditions",
        "expected_tools": ["analyze_complexity", "analyze_ast"],
        "code": (
            "def is_valid_user(user):\n"
            "    if user and user.get(\"name\") and user.get(\"email\") and \"@\" in user[\"email\"]:\n"
            "        if user.get(\"age\") and user[\"age\"] >= 18 and user[\"age\"] <= 120:\n"
            "            if user.get(\"role\") and user[\"role\"] in [\"admin\", \"user\", \"guest\"]:\n"
            "                if user.get(\"active\") and user[\"active\"] is True:\n"
            "                    return True\n"
            "    return False\n"
        ),
    },
    {
        "id": 20,
        "category": "complexity",
        "description": "Recursive function with no memoization",
        "expected_tools": ["analyze_complexity", "analyze_ast"],
        "code": (
            "def count_paths(m: int, n: int) -> int:\n"
            "    \"\"\"Count paths in an m x n grid (top-left to bottom-right).\"\"\"\n"
            "    if m == 1 or n == 1:\n"
            "        return 1\n"
            "    return count_paths(m - 1, n) + count_paths(m, n - 1)\n"
        ),
    },
]
