import sys
import importlib

# Cache heavy modules
_LAZY_MODULES = {
    "pandas": None,
    "openpyxl": None,
}


def get_module(name):
    """Lazy load and cache heavy modules."""
    if name not in _LAZY_MODULES:
        raise ValueError(f"Unknown module: {name}")

    if _LAZY_MODULES[name] is None:
        _LAZY_MODULES[name] = importlib.import_module(name)

    return _LAZY_MODULES[name]


from .fount import Fount

__version__ = "0.1.0"
__author__ = "Bibek Sahu"
__email__ = "bibek@datapoem.com"


__all__ = [
    # Main client
    "Fount",
    # Version
    "__version__",
    "get_module",
]
