import os
import sys
import tempfile
import shutil
import types
import pytest

from findreq import scan
from findreq.scan import FindPackage

# -------------------------------
# Utility functions for tests
# -------------------------------
def create_py_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# -------------------------------
# Test Cases
# -------------------------------

def test_find_imports_in_file_basic(tmp_path):
    # Create a file with some imports
    file_path = tmp_path / "sample.py"
    create_py_file(file_path, """
import os
import sys
from math import sqrt
from mymodule import foo
""")
    fp = FindPackage(project_dir=str(tmp_path))
    imports = fp._find_imports_in_file(str(file_path))
    assert "os" in imports
    assert "sys" in imports
    assert "math" in imports
    assert "mymodule" in imports

def test_classify_module_builtin(tmp_path):
    fp = FindPackage(project_dir=str(tmp_path))
    assert fp._classify_module("sys") == "built_in"
    assert fp._classify_module("os") == "built_in"

def test_classify_module_local(tmp_path):
    # Create a local module
    local_mod = tmp_path / "localmod.py"
    create_py_file(local_mod, "")
    fp = FindPackage(project_dir=str(tmp_path))
    assert fp._classify_module("localmod") == "local"

def test_classify_module_third_party(tmp_path):
    # Use a standard third-party module (assuming pytest installed)
    fp = FindPackage(project_dir=str(tmp_path))
    classification = fp._classify_module("pytest")
    assert classification == "third_party"

def test_get_distribution_name_known_module():
    fp = FindPackage()
    dist_name = fp._get_distribution_name("pytest")
    assert dist_name.lower() in ["pytest"]  # could be PyPI name

def test_analyze_project_detects_modules(tmp_path):
    # Create local module
    create_py_file(tmp_path / "mymodule.py", "")
    # Create Python file importing built-in and local module
    create_py_file(tmp_path / "scan.py", """
import os
import mymodule
""")
    fp = FindPackage(project_dir=str(tmp_path))
    built_in, local, third_party = fp._analyze_project()
    assert "os" in built_in
    assert "mymodule" in local

def test_skip_non_python_files(tmp_path):
    # Non-Python files should be ignored
    create_py_file(tmp_path / "script.js", "console.log('hi');")
    fp = FindPackage(project_dir=str(tmp_path))
    built_in, local, third_party = fp._analyze_project()
    # No imports should be found
    assert not built_in and not local and not third_party

def test_empty_file(tmp_path):
    create_py_file(tmp_path / "empty.py", "")
    fp = FindPackage(project_dir=str(tmp_path))
    imports = fp._find_imports_in_file(str(tmp_path / "empty.py"))
    assert imports == set()

def test_is_local_module(tmp_path):
    create_py_file(tmp_path / "localfile.py", "")
    os.mkdir(tmp_path / "localpkg")
    fp = FindPackage(project_dir=str(tmp_path))
    assert fp._is_local_module("localfile") is True
    assert fp._is_local_module("localpkg") is True
    assert fp._is_local_module("nonexistent") is False

def test_get_module_origin_existing():
    fp = FindPackage()
    origin = fp._get_module_origin("os")
    assert origin is not None
    assert os.path.isfile(origin)

def test_scan_runs_without_error():
    try:
        scan()
    except Exception as e:
        pytest.fail(f"scan() raised an exception: {e}")

def test_print_summary_output(capsys, tmp_path):
    create_py_file(tmp_path / "sample.py", "import os\n")
    fp = FindPackage(project_dir=str(tmp_path))
    fp.print_summary()
    captured = capsys.readouterr()
    assert "Built-in modules:" in captured.out
    assert "os" in captured.out


def test_project_with_venv_skipped(tmp_path):
    # Create a venv folder with a python file (should be skipped)
    venv_dir = tmp_path / "venv"
    venv_dir.mkdir()
    create_py_file(venv_dir / "ignoreme.py", "import sys\n")
    create_py_file(tmp_path / "scan.py", "import os\n")

    fp = FindPackage(project_dir=str(tmp_path))
    built_in, local, third_party = fp._analyze_project()

    # Check venv files are ignored
    assert "ignoreme" not in local
    # scan.py is detected as local (depends on classify_module)
    assert "scan" in local
