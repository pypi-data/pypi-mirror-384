# PythonLibs

A.Sharapov Python libraries

---

## 🚀 Features

# Prod PyPI with token
$env:TWINE_USERNAME="__token__"
$env:TWINE_PASSWORD="pypi-AgEI..."
publish

# upload to TestPyPI
publish --testpypi  

# build + check, skip upload & git push
publish --dry-run             

# skip PyPI version comparison
publish --skip-version-check  

---

## 📦 Installation

```bash
pip install ImageKit