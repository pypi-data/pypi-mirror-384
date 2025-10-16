import numpy as np
from lazylinop import LazyLinOp
import sys
sys.setrecursionlimit(100000)
import array_api_compat
from array_api_compat import is_torch_array


def flip(N, start: int = 0, end: int = None):
    r"""
    Returns a :class:`.LazyLinOp` ``L`` that flips an input array
    or a sub-interval of the array.

    For an input ``x`` with entries $x_0, x_1, \ldots, x_{N - 1}$,
    the result of ``y = L @ x`` is:

    - with defaults parameters, the entries of ``y`` are:

      $x_{N - 1}, x_{N - 2}, \ldots, x_0$

    - with ``start = a`` and ``end = b`` (``a < b``), the
      entries of ``y`` are:

      $x_0, x_1, \ldots, x_{b - 1}, \ldots, x_a, x_b, \ldots, x_{N - 1}$

    Shape of ``L`` is $(N,~N)$.

    Args:
        N: ``int``
            Size of the input.
        start: ``int``, optional
            Start to flip from this value (default is 0).
        end: ``int``, optional
            Stop to flip (not included, default is None).

    Returns:
        :class:`.LazyLinOp`

    Examples:
        >>> import numpy as np
        >>> from lazylinop.basicops import flip
        >>> N = 6
        >>> x = np.arange(N)
        >>> x
        array([0, 1, 2, 3, 4, 5])
        >>> y = flip(N, 0, 5) @ x
        >>> y
        array([4, 3, 2, 1, 0, 5])
        >>> z = flip(N, 2, 4) @ x
        >>> z
        array([0, 1, 3, 2, 4, 5])
        >>> X = np.eye(6, 5)
        >>> X
        array([[1., 0., 0., 0., 0.],
               [0., 1., 0., 0., 0.],
               [0., 0., 1., 0., 0.],
               [0., 0., 0., 1., 0.],
               [0., 0., 0., 0., 1.],
               [0., 0., 0., 0., 0.]])
        >>> flip(N, 1, 4) @ X
        array([[1., 0., 0., 0., 0.],
               [0., 0., 0., 1., 0.],
               [0., 0., 1., 0., 0.],
               [0., 1., 0., 0., 0.],
               [0., 0., 0., 0., 1.],
               [0., 0., 0., 0., 0.]])
    """

    if start < 0:
        raise ValueError("start is < 0.")
    if start >= N:
        raise ValueError("start is >= length of the input.")
    if end is not None and end < 1:
        raise ValueError("end is < 1.")
    if end is not None and end > N:
        raise ValueError("end is > length of the input.")
    if end is not None and end <= start:
        raise Exception("end is <= start.")

    def _matmat(x, start, end):
        # x is always 2d
        if is_torch_array(x):
            from torch import clone, arange
            y = clone(x)
            _arange = arange
        else:
            xp = array_api_compat.array_namespace(x)
            y = xp.copy(x)
            _arange = xp.arange
        y[start:end, :] = x[end - 1 - _arange(end - start), :]
        return y

    return LazyLinOp(
        shape=(N, N),
        matmat=lambda x: _matmat(x, start, N if end is None else end),
        rmatmat=lambda x: _matmat(x, start, N if end is None else end)
    )


# if __name__ == '__main__':
#     import doctest
#     doctest.testmod()
