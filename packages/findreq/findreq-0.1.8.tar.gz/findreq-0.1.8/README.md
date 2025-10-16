# 🔍 findreq — Auto-detect Missing Python Dependencies

![PyPI](https://img.shields.io/pypi/v/findreq?color=blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Downloads](https://img.shields.io/pypi/dm/findreq?color=orange)

---

**findreq** is a lightweight Python utility that scans your project directory and automatically detects:

* Built-in modules
* Local project modules
* Third-party packages

It suggests the exact pip install commands for missing dependencies. Perfect for debugging dependency issues or preparing a clean `requirements.txt`.

---

## 🚀 Features

* ✅ Auto-detects built-in, local, and third-party modules.
* 📁 Scans nested directories and submodules.
* ⚙️ Detects standard library modules automatically.
* 🧠 Uses PyPI lookup for third-party packages with caching.
* 💻 Works on Linux, macOS, and Windows.

---

## 📦 Installation

```bash
pip install findreq
```

Or install the latest development version directly from GitHub:

```bash
pip install git+https://github.com/syedrakesh/findreq.git
```

---

## 🧰 Usage

### 🔸 Scan the current project (default)

```python
from findreq import scan

fp = scan()  # scans the current working directory

fp.print_summary()
print("Pip install command:", fp.install_command())
```

### 🔸 Scan a specific project directory

```python
from findreq import scan

fp = scan("/path/to/your/project")

print("Built-in modules:", fp.built_in)
print("Local modules:", fp.local)
print("Third-party packages:", fp.third_party)

fp.print_summary()
print("Pip install command:", fp.install_command())
```

---

## 🧱 Project Structure

```
findreq/
├── findreq/
│   └── __init__.py
├── LICENSE
├── README.md
└── pyproject.toml
```

* `findreq/` — Python package code
* `LICENSE` — MIT license
* `README.md` — Project documentation
* `pyproject.toml` — Build and package metadata

---

## 🧑‍💻 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you’d like to change.

---

## ⚖️ License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ by [Syed Rakesh Uddin](mailto:syedrakeshuddin@gmail.com)**

> “Code smart, automate smarter.”
