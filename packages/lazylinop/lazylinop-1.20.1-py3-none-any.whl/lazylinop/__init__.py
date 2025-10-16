import importlib as _importlib

from .lazylinop import ArrayBasedLazyLinOp, LazyLinOp, aslazylinop, check, islazylinop
from .basicops import *
from .check_op import check_op

del utils, lazylinop

submodules = [
    "polynomial",
    "signal",
    "signal2d",
    "butterfly",
]

orig_dir = dir()


def __dir__():
    return orig_dir + submodules


def __getattr__(name):
    if name in submodules:
        return _importlib.import_module(f"lazylinop.{name}")
    else:
        try:
            return globals()[name]
        except KeyError:
            raise AttributeError(f"Module 'lazylinop' has no attribute '{name}'")
__version__ = '1.20.1'
