from lazylinop import LazyLinOp
from lazylinop.basicops import eye
import array_api_compat
from warnings import warn


def diff(N, n: int = 1,
         prepend: int = 0, append: int = 0, backend="numpy"):
    """Returns a :class:`.LazyLinOp` ``L`` that calculates the n-th
    discrete difference of an input vector.

    Shape of ``L`` is $(M,~N)$ where $M = prepend + N + append - n$.

    Args:
        N: ``int``
            Size of the input.

        n : ``int``, optional
            The number of times values are differenced (default is 1).
            If zero, the input is returned as-is.

        prepend, append : ``int``, optional
            Prepend or append input vector with a number of zeros equals to
            the argument, prior to performing the difference.
            By default it is equal to 0.

    Returns:
        :class:`.LazyLinOp`

    .. seealso::
        `NumPy diff function <https://numpy.org/doc/stable/
        reference/generated/numpy.diff.html>`_.

    Examples:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> x = np.array([1, 2, 2, 4, 2, 2, 1])
        >>> D = diff(x.shape[0])
        >>> y = D @ x
        >>> np.allclose(np.array([1,  0,  2, -2,  0, -1]), y)
        True
    """

    warn("backend argument is deprecated." +
         " It will be removed in a future version.")

    if n < 0 or n >= N:
        raise Exception("n must be positive and lower than N,"
                        + "the size of the input")
    if prepend < 0 or append < 0:
        raise Exception("prepend/append must be positive")

    if n == 0:
        return eye(N)

    out_size = N - n + prepend + append

    def _matmat(x):
        xp = array_api_compat.array_namespace(x)
        opts = {}
        if prepend > 0:
            opts["prepend"] = xp.zeros((prepend, x.shape[1]),
                                       dtype=x.dtype,
                                       device=x.device)
        if append > 0:
            opts["append"] = xp.zeros((append, x.shape[1]),
                                      dtype=x.dtype,
                                      device=x.device)
        return xp.diff(x, n=n, axis=0, **opts)

    def _rmatmat(y):
        xp = array_api_compat.array_namespace(y)
        out = xp.zeros((y.shape[0] + n, y.shape[1]),
                       dtype=y.dtype,
                       device=y.device)
        out[n:] = y
        for _ in range(n):
            out[:-1, :] = out[:-1, :] - out[1:, :]
        return out[prepend: y.shape[0] - append + n, :]

    return LazyLinOp(shape=(out_size, N), matmat=_matmat, rmatmat=_rmatmat)
