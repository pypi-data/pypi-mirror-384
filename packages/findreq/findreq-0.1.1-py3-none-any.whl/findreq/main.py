import os
import ast
import sys
import importlib.util
import sysconfig
import json
from importlib import metadata
import requests

CACHE_FILE = ".pypi_cache.json"

class FindPackage:
    """Main scanner class"""

    def __init__(self, project_dir="."):
        self.project_dir = project_dir
        self._cache = self._load_cache()
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
        return "pip install " + " ".join(sorted(self._third_party))

    # --- Internal ---
    def _load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_cache(self):
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump(self._cache, f, indent=2)
        except Exception:
            pass

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
            if self._is_local_module(mod):
                local.add(mod)
            elif self._is_builtin_or_stdlib(mod):
                built_in.add(mod)
            else:
                third_party.add(self._lookup_package(mod))

        self._save_cache()
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
        if mod in self._cache:
            return self._cache[mod]

        # Local installed packages
        try:
            for dist, modules in metadata.packages_distributions().items():
                if mod in modules:
                    self._cache[mod] = dist
                    return dist
        except Exception:
            pass

        # PyPI fallback
        for name in {mod, mod.lower(), mod.replace("_", "-"), mod.lower().replace("_", "-")}:
            try:
                r = requests.get(f"https://pypi.org/pypi/{name}/json", timeout=2)
                if r.status_code == 200:
                    self._cache[mod] = name
                    return name
            except Exception:
                pass

        self._cache[mod] = mod
        return mod


# --- Factory function ---
def scan(project_dir="."):
    return FindPackage(project_dir)
