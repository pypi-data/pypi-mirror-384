import os
import ast
import sys
import importlib.util
import sysconfig
from importlib import metadata

PROJECT_DIR = "."  # Your project folder


class FindPackage:
    """Dependency scanner with accurate built-in, local, and third-party detection"""

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

            classification = self._classify_module(mod)

            if classification == "built_in":
                built_in.add(mod)
            elif classification == "local":
                local.add(mod)
            elif classification == "third_party":
                third_party[mod] = self._get_distribution_name(mod)

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
        """Return absolute path where module is loaded from, or None"""
        try:
            spec = importlib.util.find_spec(mod)
            if spec and spec.origin:
                return os.path.abspath(spec.origin)
        except Exception:
            pass
        return None

    def _classify_module(self, mod):
        """Classify module as built_in, local, or third_party"""
        if mod in sys.builtin_module_names:
            return "built_in"

        origin = self._get_module_origin(mod)
        stdlib_path = sysconfig.get_path("stdlib")
        site_packages_paths = [p for p in sys.path if 'site-packages' in p or 'dist-packages' in p]

        if origin:
            # include lib-dynload for Linux built-in modules
            if origin.startswith(stdlib_path) or "lib-dynload" in origin:
                return "built_in"
            elif origin.startswith(self.project_dir):
                return "local"
            elif any(origin.startswith(p) for p in site_packages_paths):
                return "third_party"

        # fallback: unknown origin → local
        return "local"

    def _is_local_module(self, mod):
        return os.path.exists(os.path.join(self.project_dir, mod + ".py")) or \
               os.path.isdir(os.path.join(self.project_dir, mod))

    def _get_distribution_name(self, mod):
        """Get installed pip package name for a module"""
        try:
            for dist in metadata.distributions():
                try:
                    top_level = dist.read_text("top_level.txt")
                    if top_level and mod in top_level.splitlines():
                        return dist.metadata["Name"]
                except Exception:
                    continue
        except Exception:
            pass
        # fallback to module name
        return mod


# --- Factory function ---
def scan(project_dir=PROJECT_DIR):
    return FindPackage(project_dir)


# --- Example usage ---
if __name__ == "__main__":
    fp = scan(PROJECT_DIR)
    fp.print_summary()
