import numpy as np
from lazylinop import LazyLinOp
from lazylinop.basicops import block_diag, eye, kron
from lazylinop.signal import idwt
from lazylinop.signal.dwt import _wavelet, _max_level
from lazylinop.signal2d.dwt2d import _convert, dwt2d_coeffs_shapes
import sys
sys.setrecursionlimit(100000)


def idwt2d(out_shape: tuple,
           wavelet: str = 'haar',
           mode: str = 'zero', level: int = None,
           backend: str = 'pywavelets'):
    r"""
    Returns a :class:`.LazyLinOp` ``iL`` for the 2D
    inverse Discrete-Wavelet-Transform (iDWT) of a 2D signal of shape
    $(M',~N')$ (provided in flattened version).

    If ``L = dwt2d(out_shape, wavelet, mode, level, backend)`` is the
    2D DWT operator of shape $(M'N',~MN)$ (``out_shape`` is $(M,~N)$),
    then ``iL = idwt2d(out_shape, wavelet, mode, level, backend)``
    is the 2D iDWT operator such that ``iL @ L = Id``.
    As a result, if ``y = L @ x`` is the coefficients at level
    decomposition ``level``, then the $(M,~N)$-dimensionnal signal ``x``
    can be reconstructed from the $(M',~N')$-dimensionnal
    vector ``y`` as ``iL @ y``.

    Shape of ``iL`` is $(MN,~M'N')$ where $M'N'>=MN$.
    The value of $M'N'$ depends on the ``mode``.
    In general, ``iL`` is not orthogonal.

    Args:
        out_shape: ``tuple``
            Shape of the *output* array $(M,~N)$ (i.e., shape of the input
            array *of the associated DWT* :class:`LazyLinOp`, see above).
        wavelet: ``str`` or tuple of ``(np.ndarray, np.ndarray)``, optional

            - If a ``str`` is provided, the wavelet name from
              `Pywavelets library <https://pywavelets.readthedocs.io/
              en/latest/regression/wavelet.html#
              wavelet-families-and-builtin-wavelets-names>`_
            - If a tuple ``(rec_lo, rec_hi)`` of two ``np.ndarray``
              is provided, the low and high-pass filters (for *reconstruction*)
              used to define the wavelet.

              :octicon:`megaphone;1em;sd-text-danger` The ``idwt2d()``
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
        >>> from lazylinop.signal2d import dwt2d, idwt2d
        >>> from lazylinop.signal2d import colvec, uncolvec
        >>> import numpy as np
        >>> M, N = 2, 3
        >>> x = np.arange(M * N).reshape(M, N)
        >>> x
        array([[0, 1, 2],
               [3, 4, 5]])
        >>> W = dwt2d(x.shape, wavelet='db1', level=1)
        >>> y = W @ colvec(x)
        >>> L = idwt2d(x.shape, wavelet='db1', level=1)
        >>> z = L @ y
        >>> np.allclose(x, uncolvec(z, (M, N)))
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
        - :func:`lazylinop.signal.dwt2d`.
    """
    if not isinstance(out_shape, tuple) or len(out_shape) != 2:
        raise Exception("out_shape expects tuple (M, N).")
    if isinstance(level, int) and level < 0:
        raise ValueError("Decomposition level must be >= 0.")
    if backend != 'pywavelets' and backend != 'lazylinop':
        raise ValueError("backend must be either" +
                        " 'pywavelets' or 'lazylinop'.")

    # Shape of the 2d output array.
    M, N = out_shape[0], out_shape[1]

    # Shape of 2D DWT output.
    shapes = dwt2d_coeffs_shapes((M, N), wavelet=wavelet,
                                 level=level, mode=mode)
    n_out = np.sum(np.array([s[0] * s[1] for s in shapes]))

    # Number of decomposition levels.
    n_levels = min(_max_level(M, wavelet, level),
                   _max_level(N, wavelet, level))
    if n_levels == 0:
        return eye(n_out)

    # Loop over the decomposition levels.
    L = None
    m, n = M, N
    mm, nn = shapes[-1]
    for i in range(n_levels):
        # Use dwt and kron lazy linear operators to write idwt2d.
        # Kronecker product trick: vec(A @ X @ B) = kron(B^T, A) @ vec(X).
        K = kron(
            idwt(n, wavelet=wavelet, mode=mode, level=1, backend=backend),
            idwt(m, wavelet=wavelet, mode=mode, level=1, backend=backend)
        )
        # From vec(cA), vec(cH), vec(cV), vec(cD) to
        #     -----------
        #     | cA | cH |
        # vec(-----------)
        #     | cV | cD |
        #     -----------
        C = _convert(4 * mm * nn, dims=(mm, nn))
        if L is None:
            L = K @ C
        else:
            L = L @ block_diag(*[K @ C,
                                 eye(L.shape[1] - K.shape[0])])
        m, n = mm, nn
        mm, nn = shapes[-1 - 3 * (i + 1)]
    return L


# if __name__ == '__main__':
#     import doctest
#     doctest.testmod()
