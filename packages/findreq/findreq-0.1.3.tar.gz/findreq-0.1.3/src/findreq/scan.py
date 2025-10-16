import os
import ast
import sys
import importlib.util
import sysconfig
from importlib import metadata
import requests


class FindPackage:
    """Main scanner class without cache"""

    def __init__(self, project_dir="."):
        self.project_dir = project_dir
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

    # --- Methods ---
    def print_summary(self):
        print("\n🧩 Built-in modules:")
        for mod in sorted(self._built_in):
            print(f"- {mod}")

        print("\n📁 Local modules:")
        for mod in sorted(self._local):
            print(f"- {mod}")

        print("\n📦 Third-party packages:")
        for mod in sorted(self._third_party):
            print(f"- {mod}")

        cmd = self.install_command()
        if cmd:
            print("\n💡 Suggested installation command:")
            print(cmd)

    def install_command(self):
        if not self._third_party:
            return ""
        return "pip install " + " ".join(sorted(set(self._third_party)))

    # --- Internal ---
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
            # Check built-in / stdlib first
            if self._is_builtin_or_stdlib(mod):
                built_in.add(mod)
            elif self._is_local_module(mod):
                local.add(mod)
            else:
                third_party.add(self._lookup_package(mod))

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

    def _is_builtin_or_stdlib(self, mod):
        try:
            if mod in sys.builtin_module_names:
                return True
            spec = importlib.util.find_spec(mod)
            if not spec or not spec.origin:
                return False
            if spec.origin in ("built-in", None):
                return True
            stdlib_path = sysconfig.get_path("stdlib")
            return os.path.commonpath([os.path.realpath(spec.origin), stdlib_path]) == stdlib_path
        except Exception:
            return False

    def _lookup_package(self, mod):
        # Try local installed packages
        try:
            for dist, modules in metadata.packages_distributions().items():
                if mod in modules:
                    return dist
        except Exception:
            pass

        # PyPI fallback
        for name in {mod, mod.lower(), mod.replace("_", "-"), mod.lower().replace("_", "-")}:
            try:
                r = requests.get(f"https://pypi.org/pypi/{name}/json", timeout=2)
                if r.status_code == 200:
                    return name
            except Exception:
                pass

        return mod


# --- Factory function ---
def scan(project_dir="."):
    return FindPackage(project_dir)


# --- Example usage ---
if __name__ == "__main__":
    fp = scan(".")
    fp.print_summary()
