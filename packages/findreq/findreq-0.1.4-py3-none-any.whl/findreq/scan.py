import os
import ast
import sys
import importlib.util
import sysconfig
from importlib import metadata

PROJECT_DIR = "."  # Set your project folder


class FindPackage:
    """Dependency scanner with correct built-in detection"""

    def __init__(self, project_dir=PROJECT_DIR):
        self.project_dir = os.path.abspath(project_dir)
        self._script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        self._built_in, self._local, self._third_party = self._analyze_project()

    @property
    def built_in(self):
        return self._built_in

    @property
    def local(self):
        return self._local

    @property
    def third_party(self):
        return self._third_party

    def print_summary(self):
        print("\n🧩 Built-in modules:")
        for mod in sorted(self._built_in):
            print(f"- {mod}")

        print("\n📁 Local modules:")
        for mod in sorted(self._local):
            print(f"- {mod}")

        print("\n📦 Third-party packages:")
        for mod in sorted(self._third_party.keys()):
            print(f"- {mod}  (install: {self._third_party[mod]})")

        if self._third_party:
            print("\n💡 Suggested installation command:")
            cmd = "pip install " + " ".join(sorted(set(self._third_party.values())))
            print(cmd)

    # ----------------- Internal -----------------

    def _analyze_project(self):
        all_imports = set()
        for root, _, files in os.walk(self.project_dir):
            if any(skip in root for skip in ["venv", ".venv", "__pycache__", "node_modules"]):
                continue
            for file in files:
                if file.endswith(".py"):
                    all_imports.update(self._find_imports_in_file(os.path.join(root, file)))

        built_in, local, third_party = set(), set(), {}

        for mod in all_imports:
            if mod == self._script_name:
                continue

            # 1️⃣ Built-in / frozen modules
            if mod in sys.builtin_module_names or self._is_stdlib(mod):
                built_in.add(mod)
            # 2️⃣ Third-party / pip packages
            elif self._is_third_party(mod):
                third_party[mod] = self._get_distribution_name(mod)
            # 3️⃣ Local project modules
            elif self._is_local_module(mod):
                local.add(mod)
            # else unknown → assume built-in if frozen, else local
            else:
                origin = self._get_module_origin(mod)
                if origin is None:
                    built_in.add(mod)
                else:
                    local.add(mod)

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

    def _get_module_origin(self, mod):
        """Return the file path where the module is loaded from, or None"""
        try:
            spec = importlib.util.find_spec(mod)
            if spec and spec.origin:
                return os.path.abspath(spec.origin)
        except Exception:
            pass
        return None

    def _is_stdlib(self, mod):
        """Check if module is in stdlib"""
        origin = self._get_module_origin(mod)
        if not origin:
            return False
        stdlib_path = sysconfig.get_path("stdlib")
        try:
            return os.path.commonpath([origin, stdlib_path]) == stdlib_path
        except Exception:
            return False

    def _is_local_module(self, mod):
        for root, dirs, files in os.walk(self.project_dir):
            if mod + ".py" in files or mod in dirs:
                return True
        return False

    def _is_third_party(self, mod):
        # Check installed distributions
        try:
            for dist_name in metadata.distributions():
                try:
                    if mod in dist_name.read_text("top_level.txt").splitlines():
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def _get_distribution_name(self, mod):
        try:
            for dist_name in metadata.distributions():
                try:
                    if mod in dist_name.read_text("top_level.txt").splitlines():
                        return dist_name.metadata["Name"]
                except Exception:
                    continue
        except Exception:
            pass
        return mod


# --- Factory function ---
def scan(project_dir=PROJECT_DIR):
    return FindPackage(project_dir)


# --- Example usage ---
if __name__ == "__main__":
    fp = scan(PROJECT_DIR)
    fp.print_summary()
