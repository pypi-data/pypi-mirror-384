import os
import ast
import sys
import sysconfig
import importlib.util
from importlib import metadata
import requests

class FindPackage:
    """Dynamic Python project dependency scanner"""

    def __init__(self, project_dir="."):
        self.project_dir = os.path.abspath(project_dir)
        self._built_in, self._local, self._third_party = self._analyze_project()

    # --- Properties ---
    @property
    def built_in(self):
        return self._built_in

    @property
    def local(self):
        return self._local

    @property
    def third_party(self):
        return self._third_party

    # --- Public methods ---
    def print_summary(self):
        print("\n🧩 Built-in modules:")
        for mod in sorted(self._built_in):
            print(f"- {mod}")

        print("\n📁 Local modules:")
        for mod in sorted(self._local):
            print(f"- {mod}")

        print("\n📦 Third-party packages:")
        for mod in sorted(self._third_party):
            package_name = self._guess_pypi_package(mod)
            print(f"- {mod}  (install: {package_name})")

        cmd = self.install_command()
        if cmd:
            print("\n💡 Suggested installation command:")
            print(cmd)

    def install_command(self):
        if not self._third_party:
            return ""
        packages = [self._guess_pypi_package(m) for m in sorted(self._third_party)]
        return "pip install " + " ".join(packages)

    # --- Internal methods ---
    def _analyze_project(self):
        all_imports = set()
        for root, _, files in os.walk(self.project_dir):
            if any(skip in root for skip in ["venv", ".venv", "__pycache__", "node_modules"]):
                continue
            for file in files:
                if file.endswith(".py"):
                    all_imports.update(self._find_imports_in_file(os.path.join(root, file)))

        built_in, local, third_party = set(), set(), set()

        for mod in all_imports:
            if mod in sys.builtin_module_names or self._is_stdlib(mod):
                built_in.add(mod)
            elif self._is_local_module(mod):
                local.add(mod)
            else:
                third_party.add(mod)

        return built_in, local, third_party

    def _find_imports_in_file(self, file_path):
        imports = set()
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=file_path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
        except Exception:
            pass
        return imports

    def _is_local_module(self, mod):
        for root, dirs, files in os.walk(self.project_dir):
            if mod + ".py" in files or mod in dirs:
                return True
        return False

    def _is_stdlib(self, mod):
        try:
            spec = importlib.util.find_spec(mod)
            if not spec or not spec.origin:
                return False
            if spec.origin in ("built-in", None):
                return True
            stdlib_path = sysconfig.get_path("stdlib")
            return os.path.commonpath([os.path.realpath(spec.origin), stdlib_path]) == stdlib_path
        except Exception:
            return False

    def _guess_pypi_package(self, mod):
        """Return the correct PyPI package name dynamically"""
        # 1️⃣ Check installed distributions
        try:
            for dist, modules in metadata.packages_distributions().items():
                if mod in modules:
                    return dist
        except Exception:
            pass

        # 2️⃣ Try PyPI lookup if not installed
        for name in {mod, mod.lower(), mod.replace("_", "-"), mod.lower().replace("_", "-")}:
            try:
                r = requests.get(f"https://pypi.org/pypi/{name}/json", timeout=2)
                if r.status_code == 200:
                    return name
            except Exception:
                continue

        # 3️⃣ fallback: use module name
        return mod


# --- Factory function ---
def scan(project_dir="."):
    return FindPackage(project_dir)


# --- Run as script ---
if __name__ == "__main__":
    PROJECT_DIR = "."
    scanner = scan(PROJECT_DIR)
    scanner.print_summary()
