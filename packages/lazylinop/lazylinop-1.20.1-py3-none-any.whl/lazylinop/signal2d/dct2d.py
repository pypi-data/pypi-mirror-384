from lazylinop.basicops import kron
from lazylinop.signal import dct


def dct2d(in_shape: tuple, type: int = 2, backend: str = 'scipy'):
    r"""
    Returns a :class:`.LazyLinOp` ```L`` for the 2D
    Direct Cosine Transform (DCT) of a 2D signal of
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
            See `SciPy DCT <https://docs.scipy.org/doc/scipy/
            reference/generated/
            scipy.fft.dct.html#scipy-fft-dct>`_ for more details.

        backend: ``str``, optional
            - ``'scipy'`` (default) uses ``scipy.fft.dct`` to compute the DCT.
            - ``'lazylinop'`` uses a composition of basic Lazylinop operators
              to compute the DCT (:func:`.fft`, :func:`.vstack` etc.).

    Returns:
        :class:`.LazyLinOp`

    Examples:
        >>> from lazylinop.signal2d import dct2d as lz_dct2d, colvec, uncolvec
        >>> from scipy.fft import dctn as sp_dctn
        >>> import numpy as np
        >>> M, N = 32, 32
        >>> X = np.random.randn(M, N)
        >>> L = lz_dct2d(X.shape)
        >>> Y = L @ colvec(X)
        >>> Z = sp_dctn(X, 2, (M, N), (0, 1), norm='ortho')
        >>> np.allclose(Y, colvec(Z))
        True
        >>> # compute the inverse DCT
        >>> X_ = L.T @ Y
        >>> np.allclose(X_, colvec(X))
        True
        >>> # To mimick SciPy DCT II norm='ortho' and orthogonalize=False
        >>> # Because of Kronecker vec trick we apply diagonal operator D
        >>> # on the left and on the right after reshaping of Y.
        >>> from lazylinop.basicops import diag
        >>> v = np.full(N, 1.0)
        >>> v[0] = np.sqrt(2.0)
        >>> D = diag(v)
        >>> Z = sp_dctn(X, 2, (M, N), (0, 1), 'ortho', False, 1, orthogonalize=False)
        >>> np.allclose(D @ uncolvec(Y, (M, N)) @ D, Z)
        True

    .. seealso::
        - `DCT (Wikipedia) <https://en.wikipedia.org/
          wiki/Discrete_cosine_transform>`_,
        - `SciPy DCT <https://docs.scipy.org/doc/scipy/
          reference/generated/scipy.fft.dctn.html#scipy-fft-dctn>`_,
        - :func:`lazylinop.signal.dct`.
    """

    # Use dct and kron lazy linear operators to write dct2d.
    # Kronecker product trick: vec(A @ X @ B) = kron(B^T, A) @ vec(X)
    return kron(dct(in_shape[1], type, backend),
                dct(in_shape[0], type, backend))
