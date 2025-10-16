from lazylinop import LazyLinOp
from lazylinop.basicops import block_diag, eye, kron, vstack
from lazylinop.signal.dwt import dwt, _wavelet, _max_level, _ncoeffs
from lazylinop.signal.utils import chunk
from lazylinop.signal2d.flatten import uncolvec
from array_api_compat import array_namespace
import sys
sys.setrecursionlimit(100000)


def dwt2d(in_shape: tuple, wavelet: str = 'haar',
          mode: str = 'zero', level: int = None,
          backend: str = 'pywavelets'):
    """
    Returns a :class:`.LazyLinOp` ``L`` for the 2D
    Discrete-Wavelet-Transform (DWT) of a 2D signal of shape
    ``in_shape = (M, N)`` (provided in flattened version).

    ``L @ x`` will return a 1d NumPy/CuPy array or torch tensor
    as the concatenation of the DWT coefficients in the form
    ``[cAn, cHn, cVn, cDn, ..., cH1, cV1, cD1]``
    where ``n`` is the decomposition level.

    - ``cAi`` are the approximation coefficients for level ``i``.
    - ``cHi`` are the horizontal coefficients for level ``i``.
    - ``cVi`` are the vertical coefficients for level ``i``.
    - ``cDi`` are the detail coefficients for level ``i``.
    ``cAi``, ``cHi``, ``cVi`` and ``cDi`` matrices have been flattened.

    Shape of ``L`` is $(P,~MN)$ where $P>=MN$.
    The value of $P$ depends on the ``mode``.
    In general, ``L`` is not orthogonal.

    Args:
        in_shape: ``tuple``
            Shape of the 2d input array $(M,~N)$.
        wavelet: ``str`` or tuple of ``(dec_lo, dec_hi)``, optional

            - If a ``str`` is provided, the wavelet name from
              `Pywavelets library <https://pywavelets.readthedocs.io/
              en/latest/regression/wavelet.html#
              wavelet-families-and-builtin-wavelets-names>`_
            - If a tuple ``(dec_lo, dec_hi)`` of two NumPy/CuPy arrays
              or torch tensors is provided, the low and high-pass filters
              (for *decomposition*) used to define the wavelet.

              :octicon:`megaphone;1em;sd-text-danger` The ``dwt2d()``
              function does not test whether these two filters are
              actually Quadrature-Mirror-Filters.
        mode: ``str``, optional

            - ``'zero'``, signal is padded with zeros (default).
            - ``'periodic'``, signal is treated as periodic signal.
            - ``'symmetric'``, use mirroring to pad the signal.
            - ``'antisymmetric'``, signal is extended by mirroring and
              multiplying elements by minus one.
            - ``'reflect'``, signal is extended by reflecting elements.
            - ``'periodization'``, signal is extended like ``'periodic'``
              extension mode. Only the smallest possible number
              of coefficients is returned. Odd-length signal is extended
              first by replicating the last value.
        level: ``int``, optional
            If level is None compute full decomposition (default).
        backend: ``str``, optional
            ``'pywavelets'`` (default) or ``'lazylinop'`` for
            the underlying computation of the DWT.

    Returns:
        :class:`.LazyLinOp`

    Examples:
        >>> from lazylinop.signal2d import dwt2d, colvec
        >>> import numpy as np
        >>> import pywt
        >>> X = np.array([[1., 2.], [3., 4.]])
        >>> L = dwt2d(X.shape, wavelet='db1', level=1)
        >>> y = L @ colvec(X)
        >>> cA, (cH, cV, cD) = pywt.wavedec2(X, wavelet='db1', level=1)
        >>> z = np.concatenate([cA, cH, cV, cD], axis=1)
        >>> np.allclose(y, z)
        True

    .. seealso::
        - `Pywavelets module <https://pywavelets.readthedocs.io/en/
          latest/ref/2d-dwt-and-idwt.html#ref-dwt2>`_,
        - `Wavelets <https://pywavelets.readthedocs.io/en/latest/
          regression/wavelet.html>`_,
        - `Extension modes <https://pywavelets.readthedocs.io/en/
          latest/ref/signal-extension-modes.html>`_,
        - :func:`lazylinop.signal.dwt`,
        - :func:`lazylinop.signal.idwt`,
        - :func:`lazylinop.signal.idwt2d`.
    """
    if not isinstance(in_shape, tuple) or len(in_shape) != 2:
        raise Exception("in_shape expects tuple (M, N).")
    if isinstance(level, int) and level < 0:
        raise ValueError("Decomposition level must be >= 0.")
    if backend != 'pywavelets' and backend != 'lazylinop':
        raise ValueError("backend must be either" +
                         " 'pywavelets' or 'lazylinop'.")

    _, _, W, _ = _wavelet(wavelet)

    # Shape of the 2d array.
    M, N = in_shape[0], in_shape[1]

    # Number of decomposition levels.
    n_levels = min(_max_level(M, wavelet, level),
                   _max_level(N, wavelet, level))
    if n_levels == 0:
        # Nothing to decompose, return identity matrix.
        return eye(M * N)

    L = None
    for _ in range(n_levels):
        # Use dwt and kron lazy linear operators to write dwt2d.
        # Kronecker product trick: vec(A @ X @ B) = kron(B^T, A) @ vec(X).
        K = kron(
            dwt(N, wavelet=wavelet, mode=mode, level=1, backend=backend),
            dwt(M, wavelet=wavelet, mode=mode, level=1, backend=backend)
        )
        # Number of coefficients per dimension.
        M, N = _ncoeffs(M, W, mode), _ncoeffs(N, W, mode)
        # Extract four sub-images (use chunk operator).
        # ---------------------
        # | LL (cA) | LH (cH) |
        # ---------------------
        # | HL (cV) | HH (cD) |
        # ---------------------
        # Slices to extract sub-image LL
        V = chunk(K.shape[0], M, 2 * M, start=0, stop=2 * N * M)
        # Slices to extract sub-image HL
        V = vstack((V, chunk(K.shape[0], M, 2 * M,
                             start=M, stop=2 * N * M + M)))
        # Slices to extract sub-image LH
        V = vstack((V, chunk(K.shape[0], M, 2 * M,
                             start=2 * N * M, stop=4 * N * M)))
        # Slices to extract sub-image HH
        V = vstack((V, chunk(K.shape[0], M, 2 * M, start=2 * N * M + M)))
        if L is None:
            # First level of decomposition.
            L = V @ K
        else:
            # Apply low and high-pass filters + decimation only to LL.
            # Because of lazy linear operator V, LL always comes first.
            L = block_diag(*[V @ K,
                             eye(L.shape[0] - K.shape[1])]) @ L
    return L


def dwt2d_coeffs_shapes(in_shape: tuple, wavelet: str = 'haar',
                        level: int = None, mode: str = 'zero'):
    """
    Return a ``list`` of ``tuple`` that gives the shape
    of the flattened coefficients
    ``[cAn, cHn, cVn, cDn, ..., cH1, cV1, cD1]``.

    Args:
        in_shape, wavelet, level, mode:
            See :func:`dwt2d` for more details.

    Returns:
        ``list`` of ``tuple``.

    Examples:
        >>> from lazylinop.signal2d import dwt2d_coeffs_shapes
        >>> dwt2d_coeffs_shapes((5, 6), 'haar', level=2)
        [(2, 2), (2, 2), (2, 2), (2, 2), (3, 3), (3, 3), (3, 3)]
    """
    M, N = in_shape
    n_levels = min(_max_level(M, wavelet, level),
                   _max_level(N, wavelet, level))
    if n_levels == 0:
        return [in_shape]

    _, _, W, _ = _wavelet(wavelet)

    # First approximation coefficients.
    ll = [(_ncoeffs(M, W, mode), _ncoeffs(N, W, mode))] * 3
    for _ in range(1, n_levels):
        tmp = (_ncoeffs(ll[0][0], W, mode),
               _ncoeffs(ll[0][1], W, mode))
        for _ in range(3):
            ll.insert(0, tmp)
    # Last approximation coefficients.
    ll.insert(0, (ll[0][0], ll[0][1]))
    return ll


def dwt2d_to_pywt_coeffs(x, in_shape: tuple, wavelet: str = 'haar',
                         level: int = None, mode: str = 'zero'):
    r"""
    Returns Pywavelets compatible
    ``[cAn, (cHn, cVn, cDn), ..., (cH1, cV1, cD1)]``
    built from the 1d array ``x`` of flattened coefficients
    ``[cAn, cHn, cVn, cDn, ..., cH1, cV1, cD1]``
    where ``n`` is the decomposition level.

    Args:
        x: ``np.ndarray``
            List of coefficients
            ``[cAn, cHn, cVn, cDn, ..., cH1, cV1, cD1]``.
        in_shape, wavelet, level, mode:
            See :func:`dwt2d` for more details.

    Returns:
        Pywavelets compatible ``list``
        ``[cAn, (cHn, cVn, cDn), ..., (cH1, cV1, cD1)]``.

    Examples:
        >>> import numpy as np
        >>> from lazylinop.signal2d import dwt2d, colvec, dwt2d_to_pywt_coeffs
        >>> import pywt
        >>> M, N = 5, 6
        >>> x = np.arange(M * N).reshape(M, N)
        >>> L = dwt2d((M, N), wavelet='haar', level=2, mode='zero')
        >>> y = L @ colvec(x)
        >>> y = dwt2d_to_pywt_coeffs(y, (M, N), 'haar', level=2, mode='zero')
        >>> z = pywt.wavedec2(x, wavelet='haar', level=2, mode='zero')
        >>> np.allclose(y[0], z[0])
        True
        >>> np.allclose(y[0][0], z[0][0])
        True
    """
    if not isinstance(in_shape, tuple) or len(in_shape) != 2:
        raise Exception("in_shape expects tuple (M, N).")
    if isinstance(level, int) and level < 0:
        raise ValueError("Decomposition level must be >= 0.")

    # Shape of the 2d array.
    M, N = in_shape[0], in_shape[1]

    # Number of decomposition levels.
    n_levels = min(_max_level(M, wavelet, level),
                   _max_level(N, wavelet, level))

    if n_levels == 0:
        # Nothing to convert, return identity matrix.
        return [uncolvec(x, (M, N))]

    # Shape of coefficients per decomposition level.
    shapes = dwt2d_coeffs_shapes((M, N), wavelet, level, mode)

    cum, y, idx = 0, [], 0
    for i in range(n_levels):
        # Current shape of the coefficients.
        m, n = shapes[idx]
        mn = m * n
        if i == 0:
            # cA, (cH, cV, cD)
            y.append(uncolvec(x[:mn], (m, n)))
            y.append((uncolvec(x[mn:(2 * mn)], (m, n)),
                      uncolvec(x[(2 * mn):(3 * mn)], (m, n)),
                      uncolvec(x[(3 * mn):(4 * mn)], (m, n))))
            cum += 4 * mn
            idx += 4
        else:
            # (cH, cV, cD)
            y.append((uncolvec(x[cum:(cum + mn)], (m, n)),
                      uncolvec(x[(cum + mn):(cum + 2 * mn)], (m, n)),
                      uncolvec(x[(cum + 2 * mn):(cum + 3 * mn)], (m, n))))
            cum += 3 * mn
            idx += 3
    return y


def _convert(N: int, dims: tuple):
    r"""
    From $vec(A),~vec(B),~vec(C),~vec(D)$ to

    .. math::

        \begin{equation}
        vec\begin{pmatrix}
        A & C\\
        B & D
        \end{pmatrix}
        \end{equation}

    $vec(A)$ corresponds to the stacking of the columns of $A$.
    $vec(A),~vec(B),~vec(C),~vec(D)$ is a concatenation of
    1d arrays.

    Args:
        N: ``int``
            Size of $vec(A),~vec(B),~vec(C),~vec(D)$.
        dims: ``tuple``
            Shape of ``A``, ``B``, ``C`` and ``D``.

    Returns:
        NumPy/CuPy array or torch tensor.

    Examples:
        >>> import numpy as np
        >>> import pywt
        >>> from lazylinop.signal2d.flatten import colvec, uncolvec
        >>> from lazylinop.signal2d.dwt2d import _convert, dwt2d
        >>> from lazylinop.signal2d.dwt2d import dwt2d_to_pywt_coeffs
        >>> x = np.arange(16).reshape(4, 4)
        >>> L = dwt2d(x.shape, wavelet='haar', mode='zero', level=1)
        >>> y = L @ colvec(x)
        >>> z = dwt2d_to_pywt_coeffs(y, x.shape, wavelet='haar', level=1, mode='zero')
        >>> A = pywt.coeffs_to_array(z)[0]
        >>> dims = (z[0].shape[0], z[0].shape[1])
        >>> M = uncolvec(_convert(y.size, dims=dims) @ y, A.shape)
        >>> np.allclose(A, M)
        True
    """

    def _matmat(x):
        xp = array_namespace(x)
        m, n = dims
        y = xp.empty_like(x)
        idx = xp.arange(m * n)
        col = idx // m
        row = idx - col * m
        y[col * 2 * m + row, :] = x[:(m * n), :]
        y[col * 2 * m + row + m, :] = x[(m * n):(2 * m * n), :]
        y[(col + n) * 2 * m + row, :] = x[(2 * m * n):(3 * m * n), :]
        y[(col + n) * 2 * m + row + m, :] = x[(3 * m * n):(4 * m * n), :]
        return y

    def _rmatmat(x):
        xp = array_namespace(x)
        m, n = dims
        y = xp.empty_like(x)
        idx = xp.arange(m * n)
        col = idx // m
        row = idx - col * m
        y[:(m * n), :] = x[col * 2 * m + row, :]
        y[(m * n):(2 * m * n), :] = x[col * 2 * m + row + m, :]
        y[(2 * m * n):(3 * m * n), :] = x[(col + n) * 2 * m + row, :]
        y[(3 * m * n):(4 * m * n), :] = x[(col + n) * 2 * m + row + m, :]
        return y

    return LazyLinOp(
        shape=(N, N),
        matmat=lambda x: _matmat(x),
        rmatmat=lambda x: _rmatmat(x)
    )


# if __name__ == '__main__':
#     import doctest
#     doctest.testmod()
