from lazylinop import LazyLinOp
import array_api_compat


def roll(N, shift: int = 0):
    r"""Returns a :class:`.LazyLinOp` for rolling the elements
    of a vector ``x``.

    The elements that roll beyond the first position (resp. the last) re-enter
    at the last (resp. the first).
    Rolling of $x=\left(x_0,x_1,\cdots,x_{N-1}\right)$ with ``shift=s`` is:
    $x_{s}=\left(x_s,\cdots,x_{N-1},x_0,\cdots,x_{s-1}\right)$.

    Args:
        N: ``int``
            Size of the input.
        shift: ``int``, optional
            Shift the elements by this number (to the left
            or to the right).

            - If negative, shift to the left.
            - If positive, shift to the right.
            - If zero (default), do nothing.

    Returns:
        :class:`.LazyLinOp`

    .. seealso::
        `NumPy roll function <https://numpy.org/doc/stable/
        reference/generated/numpy.roll.html>`_.

    Examples:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> x = np.arange(4)
        >>> L = roll(4, 2)
        >>> y = L @ x
        >>> np.allclose(np.array([2, 3, 0, 1]), y)
        True
        >>> L = roll(4, -1)
        >>> y = L @ x
        >>> np.allclose(np.array([1, 2, 3, 0]), y)
        True
    """

    def _matmat(x, shift):
        xp = array_api_compat.array_namespace(x)
        if shift > x.shape[0]:
            s = shift % x.shape[0]
        elif -shift > x.shape[0]:
            s = -(-shift % x.shape[0])
        else:
            s = shift
        if abs(s) == x.shape[0]:
            return x
        elif s > 0:
            y = xp.empty(x.shape, dtype=x.dtype,
                         device=x.device)
            y[s:, :] = x[:(N - s), :]
            y[:s, :] = x[(N - s):, :]
            return y
        elif s < 0:
            y = xp.empty(x.shape, dtype=x.dtype,
                         device=x.device)
            y[(N + s):, :] = x[:(-s), :]
            y[:(N + s), :] = x[(-s):, :]
            return y
        else:
            return x

    return LazyLinOp(
        shape=(N, N),
        matmat=lambda x: _matmat(x, shift),
        rmatmat=lambda x: _matmat(x, -shift)
    )
