import array_api_compat
import scipy
import numpy as np
from functools import partial

try:
    import torch
except ModuleNotFoundError:
    torch = None
try:
    import cupyx as cpx
    from cupyx.scipy.sparse import issparse
except ModuleNotFoundError:
    cpx = None

__all__ = ['_iscxsparse', '_istsparse', '_issparse', 'is_array', 'array_xnamespace']

def _iscxsparse(x):
    if cpx is None:
        return False
    else:
        return issparse(x)


def _istsparse(x):
    if torch is None:
        return False
    else:
        if hasattr(x, "is_sparse") and hasattr(x, "layout"):
            return x.is_sparse or x.layout == torch.sparse_csr
        else:
            return False


def _issparse(x):
    return scipy.sparse.issparse(x) or _iscxsparse(x) or _istsparse(x)


def is_array(x):
    return (
        array_api_compat.is_array_api_obj(x)
        or _issparse(x)
        or _istsparse(x)
        or _iscxsparse(x)
    )


def array_xnamespace(x):
    try:
        return array_api_compat.array_namespace(x)
    except TypeError:
        if scipy.sparse.issparse(x):
            xp = scipy.sparse
            xp.conj = lambda x, *args, **kwargs: x.conj(*args, **kwargs)
            xp.empty = scipy.sparse.csc_array
            xp.eye = scipy.sparse.eye
            xp.isdtype = np.isdtype
            xp.asarray = lambda x, *args, **kwargs: x
            return xp
        elif _istsparse(x):
            xp = array_api_compat.torch
            xp.empty = partial(xp.empty, layout=torch.sparse_csc)
            xp.eye = lambda *args, **kwargs: xp.eye(*args, **kwargs).to_sparse()
            xp.__package__ = "torch.sparse"
            return xp
        elif _iscxsparse(x):
            xp = array_api_compat.cupy
            xp.empty = cpx.scipy.sparse.csc_array
            xp.eye = cpx.scipy.sparse.eye
            xp.asarray = lambda x, *args, **kwargs: x
            xp.__package__ = "cupyx.scipy.sparse"
            return xp
    raise TypeError("Unknown array", x)
