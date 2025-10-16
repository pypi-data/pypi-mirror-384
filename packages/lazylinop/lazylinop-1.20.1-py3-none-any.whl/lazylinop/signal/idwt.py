import numpy as np
from lazylinop import LazyLinOp
from lazylinop.basicops import block_diag, eye
from lazylinop.basicops import hstack, padder, roll
from lazylinop.signal import convolve, dwt
from lazylinop.signal.dwt import dwt_coeffs_sizes
from lazylinop.signal.dwt import _max_level, _wavelet, _ncoeffs
from lazylinop.signal.utils import downsample
from warnings import warn
try:
    import pywt
    found_pywt = True
except ModuleNotFoundError:
    warn("PyWavelets is not installed.")
    found_pywt = False
from typing import Union
import sys
from array_api_compat import (
    array_namespace, device, is_torch_array)
sys.setrecursionlimit(100000)


def idwt(N: int, wavelet: Union[str, tuple] = 'haar',
         mode: str = 'zero', level: int = None,
         backend: str = 'pywavelets'):
    r"""
    Returns a :class:`.LazyLinOp` ``iL`` for the
    inverse Discrete Wavelet Transform (iDWT).

    If ``L = dwt(N, wavelet, mode, level, backend)`` is the DWT
    operator of shape $(M,~N)$ with $M\ge~N$, then
    ``iL = idwt(N, wavelet, mode, level, backend)`` is the iDWT
    operator such that ``iL @ L = Id``. As a result, if ``y = L @ x``
    is the coefficients at level decomposition ``level``, then the
    N-dimensionnal signal ``x`` can be reconstructed from the
    M-dimensionnal vector ``y`` as ``iL @ y``.

    Shape of ``iL`` is $(N,~M)$.

    - :octicon:`report;1em;sd-text-info` ``N`` is the size of
      the input signal *of the DWT* LazyLinop, *not* of the iDWT.
    - The order is not a typo since ``N`` is the input length of the associated
      DWT operator ``L``, which is of shape $(M,~N)$, and ``iL``
      is of the same shape as ``L.H``.

    :octicon:`alert-fill;1em;sd-text-danger` In general,
    ``iL`` is not orthogonal. See `technical notes <https://
    gitlab.inria.fr/faustgrp/lazylinop/-/blob/dwt_periodization/
    docs/dwt.pdf?ref_type=heads>`_ for more details.

    :octicon:`info;1em;sd-text-success` The implementation uses
    pre-built :class:`Lazylinop` operators to build iDWT operator.

    After removing some details the code looks like (for the first
    level of decomposition):

    .. code-block:: python

        # Wavelet length.
        W = pywt.Wavelet(wavelet).dec_len
        # Number of detail and approximation coefficients.
        m = (N + W - 1) // 2
        # Upsampling operator.
        U = downsample(2 * m, step=2, start=0).H
        # Convolution operators with low-pass and
        # high-pass reconstruction filters.
        Cl = convolve(U.shape[0], rec_lo, mode='same')
        Ch = convolve(U.shape[0], rec_hi, mode='same')
        C = hstack((Cl @ U, Ch @ U))
        # Restrict.
        R = eye(N, C.shape[0], k=(C.shape[0] - N) // 2)
        # Reconstruction operator.
        iL = R @ C

    :octicon:`alert-fill;1em;sd-text-danger` Reconstruction using
    ``'dmey'`` wavelet does not ensure ``np.allclose(x, L @ y) == True``.

    .. code-block:: python

        import numpy as np
        import pywt
        N = 133
        x = np.random.randn(N)
        y = pywt.wavedec(x, wavelet='dmey', level=1, mode='periodic')
        z = pywt.waverec(y, wavelet='dmey', mode='periodic')
        np.allclose(x, z[:N])
        False
        y = pywt.wavedec(x, wavelet='coif11', level=1, mode='periodic')
        z = pywt.waverec(y, wavelet='coif11', mode='periodic')
        np.allclose(x, z[:N])
        True

    Args:
        N: ``int``
            Length of the *output* array (i.e., length of the input
            array *of the associated DWT* :class:`LazyLinOp`, see above).
        wavelet: ``str`` or tuple of ``(rec_lo, rec_hi)``, optional

            - If a ``str`` is provided, the wavelet name from
              `Pywavelets library <https://pywavelets.readthedocs.io/en/latest/
              regression/wavelet.html#wavelet-families-and-builtin-wavelets-names>`_
            - If a tuple ``(rec_lo, rec_hi)`` of two NumPy, CuPy arrays or torch tensors
              is provided, the low and high-pass filters (for *reconstruction*)
              used to define the wavelet.

              :octicon:`megaphone;1em;sd-text-danger` The ``idwt()``
              function does not test whether these two filters are
              actually Quadrature-Mirror-Filters.
        mode: ``str``, optional

            - ``'zero'``, signal is padded with zeros (default).
            - ``'periodic'``, signal is treated as periodic signal.
            - ``'periodization'``, signal is extended like ``'periodic'``
              extension mode. Only the smallest possible number
              of coefficients is returned. Odd-length signal is extended
              first by replicating the last value.
            - ``'symmetric'``, use mirroring to pad the signal.
            - ``'antisymmetric'``, signal is extended by mirroring and
              multiplying elements by minus one.
            - ``'reflect'``, signal is extended by reflecting elements.
        level: ``int``, optional
            Decomposition level, by default (None) the maximum level is used.
        backend: ``str``, optional
            'pywavelets' (default) or 'lazylinop' for the underlying
            computation of the iDWT.
            ``backend='pywavelets'`` does not work for CuPy array
            and torch tensor inputs.

    Returns:
        :class:`.LazyLinOp` iDWT.

    Examples:
        >>> from lazylinop.signal import dwt, idwt
        >>> import numpy as np
        >>> N = 8
        >>> x = np.arange(1, N + 1, 1)
        >>> W = dwt(N, mode='periodic', level=2)
        >>> y = W @ x
        >>> L = idwt(N, mode='periodic', level=2)
        >>> x_ = L @ y
        >>> np.allclose(x, x_)
        True

    .. seealso::
        - `Pywavelets module <https://pywavelets.readthedocs.io/en/
          latest/index.html>`_,
        - `Wavelets <https://pywavelets.readthedocs.io/en/latest/
          regression/wavelet.html>`_,
        - `Extension modes <https://pywavelets.readthedocs.io/en/
          latest/ref/signal-extension-modes.html>`_,
        - `Efficient Adjoint Computation for Wavelet and Convolution
          Operators <https://arxiv.org/pdf/1707.02018>`_,
        - :func:`.dwt`.
    """

    if level is not None and level < 0:
        raise ValueError("Decomposition level must be >= 0.")
    if mode not in ['antisymmetric', 'reflect',
                    'periodic', 'periodization', 'symmetric', 'zero']:
        raise ValueError("mode is either 'antisymmetric', 'reflect',"
                         + " 'periodic', 'periodization',"
                         + " 'symmetric' or 'zero'.")

    if not found_pywt:
        warn("PyWavelets is not installed,"
             + " switch backend to 'lazylinop'.")
        backend = 'lazylinop'

    # Size of the DWT output y = dwt(...) @ x.
    M = np.sum(
        np.array(dwt_coeffs_sizes(N, wavelet, level=level, mode=mode)))

    n_levels = _max_level(N, wavelet, level)
    if n_levels == 0:
        # Nothing to reconstruct, return identity matrix.
        return eye(M)

    if backend == 'lazylinop':

        # Use an intermediate function because filters
        # need to know if x is NumPy array, CuPy array
        # or torch tensor.
        def _rec(x, wavelet, lvl, adjoint):

            # If wavelet is a string use xp from input x.
            # If wavelet is a tuple of arrays use xp from wavelet.
            yp = array_namespace(x)
            _device = device(x)
            # Handle dtype because torch expects the two
            # tensors to have the same dtype.
            dtype = x.dtype if is_torch_array(x) else 'float'
            _, filters, _, _ = _wavelet(wavelet, dec=False, xp=yp,
                                        dtype=dtype, device=_device)
            xp = array_namespace(filters[2])
            backend = 'torch' if 'torch' in str(xp) else 'scipy_convolve'
            rec_lo, rec_hi = filters[2], filters[3]
            W = rec_lo.shape[0]

            # First approximation coefficient.
            nc = [_ncoeffs(N, W, mode)]
            for _ in range(1, lvl):
                nc.insert(0, _ncoeffs(nc[0], W, mode))
            # Last detail coefficient.
            nc.insert(0, nc[0])
            d_start = 1 if mode == 'periodization' else 0

            # Last detail and approximation coefficients.
            m = nc[0]
            n = N if lvl == 1 else nc[2]
            if mode == 'periodization':
                # See https://github.com/PyWavelets/pywt/issues/329
                # for more details.
                E = padder(m, width=(W, W), mode='periodic')
            else:
                E = eye(m)
            # Upsampling.
            U = downsample(2 * E.shape[0], step=2, start=d_start).H
            # Convolution with reverse wavelet.
            Cl = convolve(U.shape[0], filter=rec_lo,
                          mode='same', backend=backend)
            Ch = convolve(U.shape[0], filter=rec_hi,
                          mode='same', backend=backend)
            if mode == 'periodization':
                C = hstack((Cl @ U @ E, Ch @ U @ E))
            else:
                C = hstack((Cl @ U, Ch @ U))
            # Restrict.
            R = eye(n, C.shape[0], k=(C.shape[0] - n) // 2)
            if lvl == 1:
                if mode == 'periodization':
                    # See Pywavelets source code
                    # https://github.com/PyWavelets/pywt/blob/main/pywt/_extensions/c/convolution.template.c
                    # for more details.
                    Lambda_z = roll(R.shape[0], -1) @ R @ C
                else:
                    Lambda_z = R @ C
            else:
                if mode == 'periodization':
                    # See Pywavelets source code
                    # https://github.com/PyWavelets/pywt/blob/main/pywt/_extensions/c/convolution.template.c
                    # for more details.
                    tmp = roll(R.shape[0], -1) @ R @ C
                else:
                    tmp = R @ C
                Lambda_z = block_diag(*[tmp, eye(M - tmp.shape[1])])

            # Loop over the decomposition levels.
            for i in range(1, lvl):
                m = nc[2 + (i - 1)]
                n = N if i == (lvl - 1) else nc[2 + (i - 1) + 1]
                if mode == 'periodization':
                    # See https://github.com/PyWavelets/pywt/issues/329
                    # for more details.
                    E = padder(m, width=(W, W), mode='periodic')
                else:
                    E = eye(m)
                # Upsampling.
                U = downsample(2 * E.shape[0], step=2, start=d_start).H
                # Convolution with reverse wavelet.
                Cl = convolve(U.shape[0], filter=rec_lo,
                              mode='same', backend=backend)
                Ch = convolve(U.shape[0], filter=rec_hi,
                              mode='same', backend=backend)
                if mode == 'periodization':
                    C = hstack((Cl @ U @ E, Ch @ U @ E))
                else:
                    C = hstack((Cl @ U, Ch @ U))
                # Restrict.
                R = eye(n, C.shape[0], k=(C.shape[0] - n) // 2)
                if mode == 'periodization':
                    # See Pywavelets source code
                    # https://github.com/PyWavelets/pywt/blob/main/pywt/_extensions/c/convolution.template.c
                    # for more details.
                    tmp = roll(R.shape[0], -1) @ R @ C
                else:
                    tmp = R @ C
                Lambda_z = block_diag(*[tmp,
                                        eye(Lambda_z.shape[0] - tmp.shape[1])
                                        ]) @ Lambda_z

            return (Lambda_z.H if adjoint else Lambda_z) @ x

        return LazyLinOp(
            shape=(N, M),
            matmat=lambda x: _rec(x, wavelet, n_levels, False),
            rmatmat=lambda x: _rec(x, wavelet, n_levels, True))

    elif backend == 'pywavelets':

        # Because idwt ask for reconstruction filters ...
        pwavelet, _, W, _ = _wavelet(wavelet, False)

        if pwavelet is None:
            raise TypeError("backend='pywavelets' does not work " +
                            " with CuPy arrays and torch tensors.")

        # Because rmatmat of dwt(...) for bior* (resp. rbio*)
        # uses rbio* (resp. bior*) we need to do the same
        # for the reconstruction operator.
        if isinstance(wavelet, str):
            if 'bior' in wavelet or 'rbio' in wavelet:
                xy = wavelet.replace('bior', '').replace('rbio', '')
                pwavelet, _, W, _ = _wavelet(
                    ('rbio' if 'bior' in wavelet else 'bior') + xy, True)

        # Reconstruction operator
        tmp_mode = mode if mode == 'periodization' else 'zero'
        # All the modes return 2 * floor((N + W - 1) / 2) coefficients
        # while periodization mode returns 2 * ceil(N / 2).
        # For odd signal length we have to delete last element
        # of the output.
        mod = N % 2 if mode == 'periodization' else 0
        iL = dwt(N + mod, wavelet=pwavelet,
                 level=1, mode=tmp_mode, backend=backend).H
        if mod == 1:
            R = eye(iL.shape[0] - 1, iL.shape[0])
            iL = R @ iL
        n = _ncoeffs(N, W, mode)
        for _ in range(1, n_levels):
            mod = n % 2 if mode == 'periodization' else 0
            tmp = dwt(n + mod, wavelet=pwavelet,
                      level=1, mode=tmp_mode, backend=backend).H
            if mod == 1:
                R = eye(tmp.shape[0] - 1, tmp.shape[0])
                tmp = R @ tmp
            iL = iL @ block_diag(
                *[tmp, eye(iL.shape[1] - tmp.shape[0])])
            n = _ncoeffs(n, W, mode)
        return iL
    else:
        raise ValueError("backend must be either 'pywavelets'"
                         + " or 'lazylinop'.")


# if __name__ == '__main__':
#     import doctest
#     doctest.testmod()
