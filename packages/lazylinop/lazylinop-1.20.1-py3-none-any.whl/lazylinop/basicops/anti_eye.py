import numpy as np
from lazylinop import LazyLinOp
from lazylinop.basicops import zeros
import array_api_compat


def anti_eye(M: int, N: int = None, k: int = 0):
    """Constructs a :class:`.LazyLinOp` whose equivalent array is filled with
    ones on the k-th antidiagonal and zeros everywhere else.

    ``L = anti_eye(M, N, k)`` is such that ``L.toarray() ==
    numpy.flip(numpy.eye(M, N, k), axis=1)``.

    Args:
        M: ``int``
            Number of rows.
        N: ``int``, optional
            Number of columns (default is ``M``).
        k: ``int``, optional
            Anti-diagonal to place ones on.

            - zero for the main antidiagonal (default),
              the one starting from the upper right corner.
            - positive integer for an upper antidiagonal.
            - negative integer for a lower antidiagonal,

            if ``k >= N`` or ``k <= - M`` then ``anti_eye(M, N, k)`` is
            ``zeros((M, N))`` (k-th antidiagonal is out of operator shape).

    Returns:
        The anti-eye :class:`.LazyLinOp`.

    Examples:
        >>> import lazylinop as lz
        >>> import numpy as np
        >>> x = np.arange(3)
        >>> L = lz.basicops.anti_eye(3)
        >>> np.allclose(L @ x, np.flip(x))
        True
        >>> # Check the main diagonal is the one starting
        >>> # from the upper right corner.
        >>> L = lz.basicops.anti_eye(3, 4, k=0)
        >>> L.toarray(dtype='float')
        array([[0., 0., 0., 1.],
               [0., 0., 1., 0.],
               [0., 1., 0., 0.]])
        >>> L = lz.basicops.anti_eye(3, N=3, k=0)
        >>> L.toarray(dtype='int')
        array([[0, 0, 1],
               [0, 1, 0],
               [1, 0, 0]])
        >>> L = lz.basicops.anti_eye(3, N=3, k=1)
        >>> L.toarray(dtype='int')
        array([[0, 1, 0],
               [1, 0, 0],
               [0, 0, 0]])
        >>> L = lz.basicops.anti_eye(3, N=3, k=-1)
        >>> L.toarray(dtype='int')
        array([[0, 0, 0],
               [0, 0, 1],
               [0, 1, 0]])
        >>> L = lz.basicops.anti_eye(3, N=4, k=0)
        >>> L.toarray(dtype='int')
        array([[0, 0, 0, 1],
               [0, 0, 1, 0],
               [0, 1, 0, 0]])
        >>> L = lz.basicops.anti_eye(3, N=4, k=1)
        >>> L.toarray(dtype='int')
        array([[0, 0, 1, 0],
               [0, 1, 0, 0],
               [1, 0, 0, 0]])
        >>> L = lz.basicops.anti_eye(3, N=4, k=-1)
        >>> L.toarray(dtype='int')
        array([[0, 0, 0, 0],
               [0, 0, 0, 1],
               [0, 0, 1, 0]])

    .. seealso::
        :py:func:`.eye`,
        :py:func:`.LazyLinOp.toarray`,
        `numpy.eye
        <https://numpy.org/doc/stable/reference/generated/numpy.eye.html>`_,
        `numpy.flip
        <https://numpy.org/doc/stable/reference/generated/numpy.flip.html>`_.
    """
    nn = M if N is None else N
    if M < 1 or nn < 1:
        raise ValueError("M and N must be >= 1.")

    if k >= nn or k <= - M:
        # diagonal is out of shape
        # return zeros LazyLinOp
        return zeros((M, nn))

    def _arange(start, stop, step, x):
        if array_api_compat.is_torch_array(x):
            # torch does not support negative step.
            from torch import from_numpy
            return x[from_numpy(np.arange(start, stop, step))]
        else:
            return x[np.arange(start, stop, step)]

    def _matmat(x, M, N, k):
        # x is always 2d
        xp = array_api_compat.array_namespace(x)
        y = xp.zeros((M, x.shape[1]), dtype=x.dtype,
                     device=x.device)
        if k == 0:
            # Main anti-diagonal
            nc = min(M, N)
            y[:nc, :] = _arange(-1, -1 - nc, -1, x)
        elif k > 0:
            # Above anti-diagonal
            # k <= N
            nc = max(0, min(M, N - k))
            y[:nc] = _arange(-1 - k, -1 - k - nc, -1, x)
        else:
            # Below anti-diagonal (k < 0)
            nc = max(0, min(M + k, N))
            y[-k:-k+nc] = _arange(-1, -1 - nc, -1, x)
        return y

    def _rmatmat(x, N, M, k):
        xp = array_api_compat.array_namespace(x)
        y = xp.zeros((N, x.shape[1]), dtype=x.dtype,
                     device=x.device)
        if k == 0:
            # Main anti-diagonal transpose
            y[max(N - M, 0):] = _arange(min(M - 1, N - 1), -1, -1, x)
        elif k > 0:
            # Above anti-diagonal transpose
            if M >= N:
                # k < N
                nc = N - k
                y[:nc] = _arange(nc - 1, -1, -1, x)
            else:
                # M < N
                ys = max(0, N - M - k)
                nc = min(N - k - 1, M - 1)
                y[ys:ys + nc + 1] = _arange(nc, -1, -1, x)
        else:
            # Below anti-diagonal (k < 0) transpose
            mpk = M + k
            if N == M:
                nc = max(0, min(mpk, N))
                y[-k:-k+nc] = _arange(-1, -1 - nc, -1, x)
            elif M > N:
                nc = min(N, mpk)  # number entries to copy
                xs = M-1-max(mpk-N, 0)  # x read start
                ys = max(N - nc, 0)  # y write start
                y[ys:nc + ys] = _arange(xs, xs - nc, -1, x)
            else:
                y[N-M-k:] = _arange(M - 1, -k - 1, -1, x)
        return y

    return LazyLinOp(
        shape=(M, nn),
        matmat=lambda x: _matmat(x, M, nn, k),
        rmatmat=lambda x: _rmatmat(x, nn, M, k)
    )
