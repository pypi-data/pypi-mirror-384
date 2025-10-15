import os
import ast
import sys

STANDARD_MODULES = {
    'abc', 'argparse', 'array', 'ast', 'asyncio', 'base64', 'binascii', 'bisect',
    'calendar', 'cmath', 'collections', 'concurrent', 'contextlib', 'copy', 'csv',
    'ctypes', 'datetime', 'decimal', 'difflib', 'email', 'enum', 'errno', 'faulthandler',
    'fnmatch', 'functools', 'gc', 'getopt', 'getpass', 'glob', 'gzip', 'hashlib',
    'heapq', 'hmac', 'html', 'http', 'imaplib', 'importlib', 'inspect', 'io', 'itertools',
    'json', 'keyword', 'linecache', 'locale', 'logging', 'lzma', 'math', 'mimetypes',
    'multiprocessing', 'numbers', 'operator', 'os', 'pathlib', 'pickle', 'platform',
    'plistlib', 'queue', 'random', 're', 'sched', 'select', 'selectors', 'shlex',
    'shutil', 'signal', 'site', 'socket', 'sqlite3', 'ssl', 'statistics', 'string',
    'struct', 'subprocess', 'sys', 'tempfile', 'textwrap', 'threading', 'time',
    'timeit', 'tkinter', 'traceback', 'types', 'typing', 'unittest', 'urllib', 'uuid',
    'warnings', 'weakref', 'xml', 'xmlrpc', 'zipfile', 'zoneinfo'
}

PACKAGE_MAP = {
    "dotenv": "python-dotenv",
    "mysql": "mysql-connector-python",
    "bs4": "beautifulsoup4",
    "cv2": "opencv-python",
    "pil": "pillow",
    "yaml": "pyyaml",
    "sklearn": "scikit-learn",
    "PIL": "pillow",
}

def find_imports_in_file(file_path):
    imports = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])
    except Exception:
        pass
    return imports

def is_local_module(module_name, project_dir):
    for root, dirs, files in os.walk(project_dir):
        if module_name + ".py" in files or module_name in dirs:
            return True
    return False

def analyze_project(project_dir):
    all_imports = set()
    for root, _, files in os.walk(project_dir):
        for file in files:
            if file.endswith(".py"):
                all_imports.update(find_imports_in_file(os.path.join(root, file)))

    built_in, local, external = set(), set(), set()

    for mod in all_imports:
        if mod in sys.builtin_module_names or mod in STANDARD_MODULES:
            built_in.add(mod)
        elif is_local_module(mod, project_dir):
            local.add(mod)
        else:
            external.add(mod)

    return built_in, local, external

def main():
    PROJECT_DIR = "./"
    built_in, local, external = analyze_project(PROJECT_DIR)

    print("Built-in modules used:")
    for mod in sorted(built_in):
        print(f"- {mod}")

    print("\nLocal project modules used:")
    for mod in sorted(local):
        print(f"- {mod}")

    print("\nExternal packages (need to be installed via pip):")
    for mod in sorted(external):
        mapped = PACKAGE_MAP.get(mod, mod)
        print(f"- {mod}  (install: {mapped})")

    if external:
        install_names = [PACKAGE_MAP.get(m, m) for m in sorted(external)]
        print("\n💡 Suggested installation command:")
        print("pip install " + " ".join(install_names))
    else:
        print("\n✅ No external packages found.")

if __name__ == "__main__":
    main()
