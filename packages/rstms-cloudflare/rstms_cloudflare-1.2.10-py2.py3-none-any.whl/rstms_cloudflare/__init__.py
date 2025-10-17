"""Top-level package for rstms-cloudflare."""

import sys
import warnings

if sys.platform.startswith("openbsd"):
    # suppress urllib3 complaint about libreSSL on OpenBSD
    warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")

from .cli import cli
from .version import __author__, __email__, __timestamp__, __version__

__all__ = ["cli", "__version__", "__timestamp__", "__author__", "__email__"]
