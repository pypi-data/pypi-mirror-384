from typing import Union
import array_api_compat
from lazylinop import LazyLinOp
from lazylinop.utils import _iscxsparse
from scipy.sparse import issparse


def ones(shape: tuple[int, int]):
    """
    Returns a :class:`LazyLinOp` ones.

    .. admonition:: Fixed memory cost
        :class: admonition note

        Whatever is the shape of the ``ones``, it has the same memory cost.

    Args:

        shape: ``tuple[int, int]``
            Operator shape, e.g., ``(2, 3)``.

    Returns:
        :class:`LazyLinOp` ones.

    Example:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> L = lz.ones((6, 5))
        >>> v = np.arange(5)
        >>> v
        array([0, 1, 2, 3, 4])
        >>> L @ v
        array([10, 10, 10, 10, 10, 10])
        >>> Oa = np.ones((6, 5)).astype('int')
        >>> Oa @ v
        array([10, 10, 10, 10, 10, 10])
        >>> M = np.arange(5 * 4).reshape(5, 4)
        >>> L @ M
        array([[40, 45, 50, 55],
               [40, 45, 50, 55],
               [40, 45, 50, 55],
               [40, 45, 50, 55],
               [40, 45, 50, 55],
               [40, 45, 50, 55]])
        >>> Oa @ M
        array([[40, 45, 50, 55],
               [40, 45, 50, 55],
               [40, 45, 50, 55],
               [40, 45, 50, 55],
               [40, 45, 50, 55],
               [40, 45, 50, 55]])

    .. seealso::
        `numpy.ones <https://numpy.org/devdocs/reference/generated/
        numpy.ones.html>`_

    """
    if not isinstance(shape, tuple):
        raise TypeError('shape is not a tuple')

    if len(shape) != 2:
        raise ValueError('shape must be of length 2')

    m, n = shape

    def mul(nrows, ncols, x):
        # x is always 2d.
        # x is a NumPy or CuPy array or SciPy matrix (see LazyLinOp.__matmul__)
        # so it has a sum method.
        if issparse(x):
            import numpy as xp
        elif _iscxsparse(x):
            import cupy as xp
        else:
            xp = array_api_compat.array_namespace(x)
        s = xp.sum(x, axis=0)
        return xp.tile(s, (nrows, 1))

    return LazyLinOp(shape=(m, n),
                     matmat=lambda x: mul(m, n, x),
                     rmatmat=lambda x: mul(n, m, x))
