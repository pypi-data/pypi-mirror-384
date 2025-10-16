from lazylinop import islazylinop, LazyLinOp
import scipy as sp


def logm(L, scale: float=1.0, nmax: int=8, backend: str='scipy', use_numba: str=False):
    """Constructs logarithm of linear operator L as a lazy linear operator Log(L).
    Of note, it is only an approximation Log(L) @ X ~= sum((-1)^(n + 1) * (L - Id)^n / n, n=1 to nmax) @ X.

    Args:
        L: 2d array
        Linear operator.
        scale: float, optional
        Scale factor logm(scale * L) (default is 1).
        nmax: int, optional
        Stop the serie expansion after nmax (default is 8).
        backend: str, optional
        It can be 'scipy' (default) to use scipy.linalg.logm function.
        nmax parameter is useless if backend is 'scipy'.
        It can be 'serie' to use a serie expansion of logm(scale * L).

    Returns:
        LazyLinOp

    Raises:
        ValueError
            L @ x does not work because # of columns of L is not equal to the # of rows of x.
        ValueError
            backend value is either 'scipy' or 'serie'.
        ValueError
            nmax must be >= 1.

    Examples:
        >>> import numpy as np
        >>> import scipy as sp
        >>> from lazylinop import eye
        >>> from lazylinop.wip.linear_algebra import logm
        >>> scale = 0.01
        >>> N = 10
        >>> E1 = logm(eye(N, N, k=0), scale=scale, nmax=4, backend='scipy')
        >>> E2 = sp.linalg.logm(scale * np.eye(N, N, k=0))
        >>> X = np.random.rand(N, 2 * N)
        >>> np.allclose(E1 @ X, E2 @ X)

    References:
        See also `scipy.linalg.logm function <https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.logm.html>`_.
        See also `logarithm of a matrix <https://en.wikipedia.org/wiki/Logarithm_of_a_matrix>`_.
    """
    if True or backend == 'scipy':
        # backend has to be 'scipy' because 'serie' is not precise enough
        if islazylinop(L):
            L = np.eye(L.shape[0], L.shape[0]) @ L
        if use_numba:
            M = sp.linalg.logm(scale * L)
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
                matmat=lambda X: sp.linalg.logm(scale * L) @ X,
                rmatmat=lambda X: sp.linalg.logm(scale * L.T.conj()) @ X
            )
    elif backend == 'serie':
        if nmax < 1:
            raise ValueError("nmax must be >= 1.")
        def _matmat(L, x):
            # x is always 2d
            if L.shape[1] != x.shape[0]:
                raise ValueError("L @ x does not work because # of columns of L is not equal to the # of rows of x.")
            batch_size = x.shape[1]
            Lx = np.empty(L.shape[0], dtype=x.dtype)
            # Taylor expansion
            # It uses the equation log(scale * L) ~= sum((-1)^(n + 1) * (scale * L - Id)^n / n, n=1 to nmax)
            y = np.subtract(np.multiply(scale, L @ x), x)
            if nmax > 2:
                # loop over the batch size
                for b in range(batch_size):
                    # compute (scale * L - Id) @ x
                    np.subtract(np.multiply(scale, L @ x[:, b]), x[:, b], out=Lx)
                    for n in range(2, nmax):
                        factor = (2 * (n % 2) - 1) / n
                        np.add(y[:, b], np.multiply(factor, Lx), out=y[:, b])
                        np.subtract(np.multiply(scale, L @ Lx), Lx, out=Lx)
            return y
        return LazyLinOp(
            shape=L.shape,
            matmat=lambda X: _matmat(L, X),
            rmatmat=lambda X: _matmat(L.T.conj(), X)
        )
    else:
        raise ValueError("backend value is either 'scipy' or 'serie'.")


