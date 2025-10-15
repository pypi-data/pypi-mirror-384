# Welcome

pip-importer is a small utility that can import a package, or pip install first if the package does not exist.


#  Installation

```bash
pip install pip-importer
```

# Usage

```python
from pip_importer import pip_import

# If the environment has pytest, this is same as `import pytest`.
# Otherwise, it will run `pip install pytest` then `import pytest`.
pytest = pip_import("pytest")
```
