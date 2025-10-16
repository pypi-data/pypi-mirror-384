from lazylinop import islazylinop, LazyLinOp
import scipy as sp
import numpy as np


def expm(L, scale: float=1.0, nmax: int=8, backend: str='scipy', use_numba: bool=False):
    """Constructs exponentiation of linear operator L as a lazy linear operator E(L).
    Of note, it is only an approximation E(L) @ X ~= sum((scale * L)^i / factorial(i), i=0 to nmax) @ X.

    Args:
        L: 2d array
            Linear operator.
        scale: float, optional
            Scale factor expm(scale * L) (default is 1).
        nmax: int, optional
            Stop the serie expansion after nmax (default is 8).
        backend: str, optional
            It can be 'scipy' (default) to use scipy.linalg.expm function.
            nmax parameter is useless if backend is 'scipy'.
            It can be 'serie' to use a serie expansion of expm(scale * L).
        use_numba: bool, optional
            If True, use prange from Numba (default is False)
            to compute batch in parallel.
            It is useful only and only if the batch size and
            the length of a are big enough.

    Returns:
        LazyLinOp

    Raises:
        ValueError
            L @ x does not work because # of columns of L is not equal to the # of rows of x.
        ValueError
            backend value is either 'scipy' or 'serie'.
        ValueError
            If L is a 2d array, backend must be 'scipy'.

    Examples:
        >>> import numpy as np
        >>> import scipy as sp
        >>> from lazylinop import eye
        >>> from lazylinop.wip.linear_algebra import expm
        >>> scale = 0.01
        >>> coefficients = np.array([1.0, scale, 0.5 * scale ** 2])
        >>> N = 10
        >>> L = np.eye(N, N, k=0)
        >>> E1 = expm(L, scale=scale, nmax=4)
        >>> E2 = sp.linalg.expm(scale * L)
        >>> np.allclose(E1.toarray(), E2)
        >>> E3 = eye(N, N, k=0)
        >>> X = np.random.rand(N, 2 * N)
        >>> np.allclose(E2 @ X, E3 @ X)

    References:
        See also `scipy.linalg.expm function <https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.expm.html>`_.
    """
    if backend == 'scipy':
        if islazylinop(L):#type(L) is np.ndarray:
            raise ValueError("If L is a 2d array, backend must be 'scipy'.")
        if use_numba:
            M = sp.linalg.expm(scale * L)
            nb.config.DISABLE_JIT = 0 if use_numba else 1
            @njit(nopython=True, parallel=True, cache=True)
            def _matmat(M, x):
                # x is always 2d
                batch_size = x.shape[1]
                if use_numba:
                    y = np.empty((M.shape[0], batch_size), dtype=x.dtype)
                    for b in prange(batch_size):
                        y[:, b] = M @ X[:, b]
                else:
                    y = M @ X
                return y
            return LazyLinOp(
                shape=L.shape,
                matmat=lambda X: _matmat(M, X),
                rmatmat=lambda X: _matmat(M.T.conj(), X)
            )
        else:
            return LazyLinOp(
                shape=L.shape,
                matmat=lambda X: sp.linalg.expm(scale * L) @ X,
                rmatmat=lambda X: sp.linalg.expm(scale * L.T.conj()) @ X
            )
    if backend == 'scipy':
        if islazylinop(L):#type(L) is np.ndarray:
            raise ValueError("If L is a 2d array, backend must be 'scipy'.")
        return LazyLinOp(
            shape=L.shape,
            matmat=lambda X: sp.linalg.expm(scale * L) @ X,
            rmatmat=lambda X: sp.linalg.expm(scale * L.T.conj()) @ X
        )
    elif backend == 'serie':
        from lazylinop.polynomial import _polyval
        coefficients = np.empty(nmax + 1, dtype=np.float64)
        factor = 1.0
        factorial = 1.0
        for i in range(nmax + 1):
            coefficients[i] = factor / factorial
            factor *= scale
            factorial *= (i + 1)
        return _polyval(L, coefficients)
    else:
        raise ValueError("backend value is either 'scipy' or 'serie'.")

