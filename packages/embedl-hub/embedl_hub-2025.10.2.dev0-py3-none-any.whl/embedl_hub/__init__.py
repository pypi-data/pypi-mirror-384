# Copyright (C) 2025 Embedl AB

"""
Public Embedl Hub library API.
```pycon
>>> import embedl_hub
>>> embedl_hub.__version__
'2025.9.0'
```
"""

import importlib.metadata


try:
    __version__ = importlib.metadata.version("embedl_hub")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"
