from lazylinop.basicops import kron
from lazylinop.signal import dst


def dst2d(in_shape: tuple, type: int = 2, backend: str = 'scipy'):
    r"""
    Returns a :class:`.LazyLinOp` ``L`` for the 2D
    Direct Sine Transform (DST) of a 2D signal of
    shape ``in_shape=(M, N)`` (provided in flattened version).

    Shape of ``L`` is $(MN,~MN)$ with $(M,~N)=\text{in_shape}$.
    After applying the operator as ``y = L @ colvec(X)``, a 2D
    output can be obtained via ``uncolvec(y, out_shape)``
    with ``out_shape = in_shape``. ``L`` is orthogonal.

    Args:
        in_shape: ``tuple``
            Shape of the 2d input array $(M,~N)$.

        type: ``int``, optional
            1, 2, 3, 4 (I, II, III, IV).
            Defaut is 2.
            See `SciPy DST <https://docs.scipy.org/doc/scipy/
            reference/generated/
            scipy.fft.dst.html#scipy-fft-dst>`_ for more details.

        backend: str, optional
            - ``'scipy'`` (default) uses ``scipy.fft.dst`` to compute the DST.
            - ``'lazylinop'`` Uses a composition of basic Lazylinop operators
              to compute the DST (:func:`.fft`, :func:`.vstack` etc.).

    Returns:
        :class:`.LazyLinOp`

    Example:
        >>> from lazylinop.signal2d import dst2d as lz_dst2d, colvec, uncolvec
        >>> from scipy.fft import dstn as sp_dstn
        >>> import numpy as np
        >>> M, N = 32, 32
        >>> X = np.random.randn(M, N)
        >>> L = lz_dst2d(X.shape)
        >>> Y = L @ colvec(X)
        >>> Z = sp_dstn(X, 2, (M, N), (0, 1), norm='ortho')
        >>> np.allclose(Y, colvec(Z))
        True
        >>> # compute the inverse DST
        >>> X_ = L.T @ Y
        >>> np.allclose(uncolvec(X_, (M, N)), X)
        True
        >>> # To mimick SciPy DST II norm='ortho' and orthogonalize=False
        >>> # Because of Kronecker vec trick we apply diagonal operator D
        >>> # on the left and on the right after reshaping of Y.
        >>> from lazylinop.basicops import diag
        >>> v = np.full(N, 1.0)
        >>> v[-1] = np.sqrt(2.0)
        >>> D = diag(v)
        >>> Z = sp_dstn(X, 2, (M, N), (0, 1), 'ortho', False, 1, orthogonalize=False)
        >>> np.allclose(D @ uncolvec(Y, (M, N)) @ D, Z)
        True

    .. seealso::
       - `DST (Wikipedia) <https://en.wikipedia.org/wiki/
         Discrete_sine_transform>`_,
       - `SciPy DST <https://docs.scipy.org/doc/scipy/,
         reference/generated/ scipy.fft.dstn.html#scipy-fft-dstn>`_,
       - :func:`lazylinop.signal.dst`.
    """

    # Use dst and kron lazy linear operators to write dst2d.
    # Kronecker product trick: vec(A @ X @ B) = kron(B^T, A) @ vec(X).
    return kron(dst(in_shape[1], type, backend),
                dst(in_shape[0], type, backend))
