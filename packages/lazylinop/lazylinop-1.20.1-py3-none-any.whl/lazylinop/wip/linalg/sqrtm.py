from lazylinop import islazylinop, LazyLinOp
import scipy as sp
import numpy as np


def sqrtm(L, scale: float=1.0, nmax: int=8, backend: str='scipy'):
    """Constructs square root of linear operator L as a lazy linear operator R(L).
    It uses the equation L^1/2 = sum((-1)^n * (1/2 n) * (Id - L)^n, n=0 to inf).
    Of note, it is only an approximation (see nmax argument).

    Args:
        L: 2d array
        Linear operator.
        scale: float, optional
        Scale factor cosh(scale * L) (default is 1).
        nmax: int, optional
        Stop the serie expansion after nmax (default is 8).
        backend: str, optional
        It can be 'scipy' (default) to use scipy.linalg.sqrtm function.
        nmax parameter is useless if backend is 'scipy'.
        It can be 'serie' to use a serie expansion of sqrtm(scale * L).

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
        >>> from lazylinop.wip.linear_algebra import sqrtm
        >>> scale = 0.1
        >>> N = 4
        >>> L = np.eye(N, N, k=0)
        >>> X = np.random.rand(N, 2 * N)
        >>> E1 = sqrtm(L, scale=scale, nmax=256, backend='serie')
        >>> E2 = sp.linalg.sqrtm(scale * L)
        >>> np.allclose(E1 @ X, E2 @ X)
        >>> L = eye(N, N, k=0)
        >>> E3 = sqrtm(L, scale=scale, nmax=256, backend='serie')
        >>> np.allclose(E2 @ X, E3 @ X)

    References:
        See also `scipy.linalg.sqrtm function <https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.sqrtm.html>`_.
    """
    if backend == 'scipy':
        if islazylinop(L):
            R = sp.linalg.sqrtm(scale * np.eye(L.shape[0], L.shape[0]) @ L)
        else:
            R = sp.linalg.sqrtm(scale * L)
        return LazyLinOp(
            shape=L.shape,
            matmat=lambda X: R @ X,
            rmatmat=lambda X: R.T.conj() @ X
        )
    elif backend == 'serie':
        def _matmat(L, x):
            # x is always 2d
            if L.shape[1] != x.shape[0]:
                raise ValueError("L @ x does not work because # of columns of L is not equal to the # of rows of x.")
            batch_size = x.shape[1]
            Lx = np.empty(L.shape[0], dtype=x.dtype)
            # Taylor expansion
            # It uses the equation (scale * L)^1/2 = sum((-1)^n * (1/2 n) * (Id - scale * L)^n, n=0 to inf)
            y = np.copy(x)
            if nmax > 1:
                # loop over the batch size
                for b in range(batch_size):
                    # compute (Id - scale * L) @ x
                    np.subtract(x[:, b], np.multiply(scale, L @ x[:, b]), out=Lx)
                    for n in range(1, nmax):
                        # factor = (1 - 2 * (n % 2)) * sp.special.comb(0.5, n)
                        factor = (1 - 2 * (n % 2)) * sp.special.binom(0.5, n)
                        np.add(y[:, b], np.multiply(factor, Lx), out=y[:, b])
                        np.subtract(Lx, np.multiply(scale, L @ Lx), out=Lx)
            return y
        return LazyLinOp(
            shape=L.shape,
            matmat=lambda X: _matmat(L, X),
            rmatmat=lambda X: _matmat(L.T.conj(), X)
        )
    else:
        raise ValueError("backend value is either 'scipy' or 'serie'.")
