from lazylinop import islazylinop, LazyLinOp
import scipy as sp
import numpy as np


def sinhm(L, scale: float=1.0, nmax: int=8, backend: str='scipy', use_numba: bool=False):
    """Constructs an hyperbolic cosine of linear operator L as a lazy linear operator S(L).
    It uses the equation 2 * sinh(z) = exp(scale * L) - exp(-scale * L).
    Of note, it is only an approximation (see nmax argument).

    Args:
        L: 2d array
        Linear operator.
        scale: float, optional
        Scale factor cosh(scale * L) (default is 1).
        nmax: int, optional
        Stop the serie expansion after nmax (default is 8).
        backend: str, optional
        It can be 'scipy' (default) to use scipy.linalg.sinhm function.
        nmax parameter is useless if backend is 'scipy'.
        It can be 'serie' to use a serie expansion of sinhm(scale * L).

    Returns:
        LazyLinOp

    Raises:
        ValueError
            L @ x does not work because # of columns of L is not equal to the # of rows of x.
        ValueError
            backend value is either 'scipy' or 'serie'.

    Examples:
        >>> import numpy as np
        >>> import scipy as sp
        >>> from lazylinop import eye
        >>> from lazylinop.wip.linear_algebra import sinhm
        >>> scale = 0.01
        >>> N = 10
        >>> L = np.eye(N, N, k=0)
        >>> E1 = sinhm(L, scale=scale, nmax=32, backend='serie')
        >>> E2 = sp.linalg.sinhm(scale * L)
        >>> E3 = sinhm(eye(N, N, k=0), scale=scale, nmax=32, backend='serie')
        >>> X = np.random.rand(N, 2 * N)
        >>> np.allclose(E1 @ X, E2 @ X)
        True
        >>> np.allclose(E2 @ X, E3 @ X)
        True

    References:
        See also `scipy.linalg.sinhm function <https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.sinhm.html>`_.
    """
    if backend == 'scipy':
        if islazylinop(L):
            L = np.eye(L.shape[0], L.shape[0]) @ L
        if use_numba:
            S = sp.linalg.sinhm(scale * L) @ X
            nb.config.DISABLE_JIT = 0 if use_numba else 1
            @njit(nopython=True, parallel=True, cache=True)
            def _matmat(S, x):
                # x is always 2d
                batch_size = x.shape[1]
                if use_numba:
                    y = np.empty((S.shape[0], batch_size), dtype=x.dtype)
                    for b in prange(batch_size):
                        y[:, b] = S @ X[:, b]
                else:
                    y = S @ X
                return y
            return LazyLinOp(
                shape=L.shape,
                matmat=lambda X: _matmat(S, X),
                rmatmat=lambda X: _matmat(S.T.conj(), X)
            )
        else:
            return LazyLinOp(
                shape=L.shape,
                matmat=lambda X: sp.linalg.sinhm(scale * L) @ X,
                rmatmat=lambda X: sp.linalg.sinhm(scale * L.T.conj()) @ X
            )
    elif backend == 'serie':
        def _matmat(L, x):
            # x is always 2d
            if L.shape[1] != x.shape[0]:
                raise ValueError("L @ x does not work because # of columns of L is not equal to the # of rows of x.")
            batch_size = x.shape[1]
            y = np.zeros((L.shape[0], batch_size), dtype=x.dtype)
            Lx = np.empty(L.shape[0], dtype=x.dtype)
            # loop over the batch size
            for b in range(batch_size):
                # Taylor expansion
                # exp(scale * L) ~= Id + scale * L + (scale * L) ** 2 / 2 + ...
                # exp(-scale * L) ~= Id - scale * L + (scale * L) ** 2 / 2 + ...
                # sinh(scale * L) ~= scale * L + ...
                pfactor = scale
                mfactor = -scale
                if nmax > 1:
                    np.copyto(Lx, L @ x[:, b])
                    for i in range(1, nmax):
                        if (i % 2) == 1:
                            np.add(y[:, b], np.multiply(0.5 * (pfactor - mfactor), Lx), out=y[:, b])
                        pfactor *= scale / (i + 1)
                        mfactor *= -scale / (i + 1)
                        np.copyto(Lx, L @ Lx)
            return y
        return LazyLinOp(
            shape=L.shape,
            matmat=lambda X: _matmat(L, X),
            rmatmat=lambda X: _matmat(L.T.conj(), X)
        )
    else:
        raise ValueError("backend value is either 'scipy' or 'serie'.")

