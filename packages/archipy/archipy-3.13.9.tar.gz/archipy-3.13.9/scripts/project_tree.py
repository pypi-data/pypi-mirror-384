import importlib
import inspect
import os
import sys
from typing import get_type_hints

# Set the project root to the parent directory of the scripts folder
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)  # Add project root to sys.path for imports


# Load .gitignore patterns from the root directory
def load_gitignore(root_dir=PROJECT_ROOT):
    gitignore_path = os.path.join(root_dir, ".gitignore")
    ignore_patterns = [".venv", "__pycache__", ".idea", ".git"]  # Default ignores including .git
    if os.path.exists(gitignore_path):
        with open(gitignore_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    ignore_patterns.append(line.rstrip("/"))
    return ignore_patterns


IGNORE_PATTERNS = load_gitignore()


def is_ignored(path, root_dir=PROJECT_ROOT):
    """Check if a path matches any .gitignore patterns or .git."""
    rel_path = os.path.relpath(path, root_dir)
    for pattern in IGNORE_PATTERNS:
        if pattern in rel_path or rel_path.endswith(pattern) or pattern == os.path.basename(rel_path):
            return True
    return False


def list_project_structure(root_dir=PROJECT_ROOT):
    """Print the project directory tree, respecting .gitignore and excluding .git."""
    print(f"Project Tree for: {os.path.abspath(root_dir)}")
    for root, dirs, files in os.walk(root_dir):
        if is_ignored(root):
            dirs[:] = []  # Stop walking this directory
            continue
        level = root.replace(root_dir, "").count(os.sep)
        indent = "  " * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = "  " * (level + 1)
        for f in sorted(files):
            file_path = os.path.join(root, f)
            if not is_ignored(file_path) and f.endswith((".py", ".feature")) and f != "__init__.py":
                print(f"{sub_indent}{f}")


def list_classes_and_public_methods(module_path):
    """List classes and their public methods with input/output types."""
    try:
        module_name = module_path.replace(os.sep, ".").replace(".py", "").strip(".")
        module = importlib.import_module(module_name)
        print(f"File: {module_path}")
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and obj.__module__ == module_name:
                print(f"  Class: {name}")
                for method_name, method in inspect.getmembers(obj, inspect.isfunction):
                    if not method_name.startswith("_"):
                        print(f"    Public Method: {method_name}")
                        try:
                            hints = get_type_hints(method)
                            sig = inspect.signature(method)
                            params = sig.parameters
                            if params:
                                print("      Inputs:")
                                for param_name, param in params.items():
                                    param_type = hints.get(param_name, "unspecified")
                                    print(f"        {param_name}: {param_type}")
                            else:
                                print("      Inputs: None")
                            return_type = hints.get("return", "unspecified")
                            print(f"      Output: {return_type}")
                        except Exception as e:
                            print(f"      (Type info unavailable: {e})")
    except Exception as e:
        print(f"  Error loading module {module_name}: {e}")


def analyze_python_files(root_dir=PROJECT_ROOT):
    """Find and analyze Python files, respecting .gitignore and excluding .git."""
    print("\nClasses and Public Methods in Python files:")
    for root, _, files in os.walk(root_dir):
        if is_ignored(root):
            continue
        for f in files:
            file_path = os.path.join(root, f)
            if not is_ignored(file_path) and f.endswith(".py") and f != "__init__.py":
                module_path = os.path.relpath(file_path, PROJECT_ROOT)
                list_classes_and_public_methods(module_path)


if __name__ == "__main__":
    list_project_structure()
    analyze_python_files()
