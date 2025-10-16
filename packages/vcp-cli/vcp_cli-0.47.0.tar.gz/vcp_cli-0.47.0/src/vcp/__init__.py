"""VCP CLI - A command-line interface (CLI) to the Chan Zuckerberg Initiative's Virtual Cells Platform (VCP)"""

import importlib.metadata

try:
    __version__ = importlib.metadata.version("vcp-cli")
except importlib.metadata.PackageNotFoundError:
    # Fallback for development when package isn't installed
    __version__ = "development"
