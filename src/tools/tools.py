import ast
import tempfile
import subprocess
import os


def analyze_ast(code: str) -> str:
    parsed = ast.parse(code)
    fnames = []
    cnames = []
    fcount = 0
    ccount = 0

    for node in ast.walk(parsed):
        if isinstance(node, ast.FunctionDef):
            fnames.append(node.name)
            fcount += 1
        elif isinstance(node, ast.ClassDef):
            cnames.append(node.name)
            ccount += 1

    return f"Functions: {fcount} {fnames}\nClasses: {ccount} {cnames}"


def analyze_complexity(code: str) -> str:
    f = tempfile.NamedTemporaryFile(suffix=".py", delete=False)
    path = f.name
    f.write(code.encode())
    f.close()
    results = subprocess.run(
        ["radon", "cc", "-s", path],
        capture_output=True,
        text=True,
    )
    os.remove(path)
    return results.stdout


def analyze_security(code: str) -> str:
    f = tempfile.NamedTemporaryFile(suffix=".py", delete=False)
    path = f.name
    f.write(code.encode())
    f.close()
    results = subprocess.run(
        ["bandit", "-r", path],
        capture_output=True,
        text=True,
    )
    os.remove(path)
    return results.stdout


def analyze_style(code: str) -> str:
    results = subprocess.run(
        ["pylint", "--from-stdin", "reviewed_module"],
        input=code,
        capture_output=True,
        text=True,
    )
    return results.stdout
