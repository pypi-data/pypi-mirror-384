import numpy as np
import warnings
from lazylinop import LazyLinOp
from lazylinop.basicops import block_diag, eye, vstack
from lazylinop.basicops import padder, slicer
from lazylinop.signal import convolve
from lazylinop.signal.utils import downsample
try:
    import pywt
    found_pywt = True
except ModuleNotFoundError:
    warnings.warn("PyWavelets is not installed.")
    found_pywt = False

    # Fake pywt
    class Pywt():

        def __init__(self):
            self._pywt = type(None)

        class Wavelet():
            def __init__(self, dec_lo=None, dec_hi=None,
                         rec_lo=None, rec_hi=None):
                self.dec_lo = dec_lo
                self.dec_hi = dec_hi
                self.rec_lo = rec_lo
                self.rec_hi = rec_hi
                self.dec_len = None
                self.name = None

    pywt = Pywt()

from typing import Union
import sys
from array_api_compat import (
    array_namespace, device,
    is_cupy_array, is_numpy_array, is_torch_array)
sys.setrecursionlimit(100000)


def ds_mconv(
    N: int,
    wavelet: Union[str, tuple],
    mode: str = "full",
    offset: int = 0,
    disable_jit: int = 0,
    use_parallel: bool = False,
):
    """Creates convolution plus down-sampling lazy linear operator.
    It first computes convolution with the two filters defined by ``wavelet``.
    Then, it performs down-sampling (keep 1 every 2) on both convolution
    results (it is useful for Discrete-Wavelet-Transform).
    If input x is a 1d array, C @ x return concatenation of both convolution.
    If input X is a 2d array, C @ X return concatenation per column.
    offset (0 or 1) argument determines the first element to compute.
    The ouput C @ x is equivalent to the concatenation of
    :code:`(cupyx).scipy.signal.convolve(x, l, mode)[offset::2]` and
    :code:`(cupyx).scipy.signal.convolve(x, h, mode)[offset::2]`.

    Args:
        N: ``int``
            Length of the input.
        wavelet: ``str`` or tuple of ``(dec_lo, dec_hi)``, optional

            - If a ``str`` is provided, the wavelet name from
              `Pywavelets library <https://pywavelets.readthedocs.io/en/latest/
              regression/wavelet.html#wavelet-families-and-builtin-wavelets-names>`_.
              In that case, the namespace of the low and high-pass filters
              depends on the namespace of the input array.
            - If a tuple ``(dec_lo, dec_hi)`` of two NumPy, CuPy arrays or torch tensors.
              is provided, the low and high-pass filters (for *decomposition*)
              used to define the wavelet.
        mode: ``str``, optional

            - ``'full'`` computes convolution (input + padding).
            - ``'valid'`` computes ``'full'`` mode and extract centered output
              that does not depend on the padding.
            - ``'same'`` computes ``'full'`` mode and extract centered output
              that has the same shape that the input.
        offset: ``int``, optional
            First element to keep (default is 0).
        disable_jit: ``int``, optional
            If 0 (default) enable Numba jit.
        use_parallel: ``bool``, optional
            If True enable Numba ``prange``.
            ``False`` is default value.

    Returns:
        LazyLinOp

    Examples:
        >>> import numpy as np
        >>> import scipy as sp
        >>> from lazylinop.signal import ds_mconv
        >>> N = 512
        >>> x = np.random.rand(N)
        >>> l = np.random.rand(32)
        >>> h = np.random.rand(32)
        >>> L = ds_mconv(N, (l, h), mode='same')
        >>> c1 = L @ x
        >>> c2 = sp.signal.convolve(x, l, mode='same')
        >>> c3 = sp.signal.convolve(x, h, mode='same')
        >>> np.allclose(c1, np.hstack((c2[0::2], c3[0::2])))
        True

    .. seealso::
        `SciPy convolve function <https://docs.scipy.org/doc/scipy/
        reference/generated/scipy.signal.convolve.html>`_,
        `SciPy correlate function <https://docs.scipy.org/doc/scipy/
        reference/generated/scipy.signal.correlate.html>`_.
    """

    def njit(*args, **kwargs):
        def dummy(f):
            return f
        return dummy

    def prange(n):
        return range(n)

    try:
        import numba as nb
        from numba import njit, prange
        nb.config.THREADING_LAYER = "omp"
        T = nb.config.NUMBA_NUM_THREADS
        nb.config.DISABLE_JIT = disable_jit
    except ImportError:
        warnings.warn("Did not find Numba.")
        T = 1

    if mode not in ["full", "valid", "same"]:
        raise ValueError("mode is either 'full' (default), 'valid' or 'same'.")

    # Check if length of the input has been passed to the function
    if type(N) is not int:
        raise Exception("Length of the input are expected (int).")

    _, filters, _, _ = _wavelet(wavelet)

    if filters[0].ndim != 1 or filters[0].ndim != 1:
        raise ValueError("Number of dimensions of the kernel must be 1.")
    if N <= 0:
        raise Exception("Negative input length.")

    K = filters[1].shape[0]
    if K != filters[0].shape[0]:
        raise Exception("The two filters must have the same length.")

    if K > N and mode == "valid":
        raise ValueError(
            "Size of the kernel is greater than the size"
            + " of the signal and mode is valid."
        )
    if offset != 0 and offset != 1:
        raise ValueError("offset must be either 0 or 1.")

    every = 2

    # Length of the output as a function of convolution mode
    n_out = N + (int(mode == 'full') - int(mode == 'valid')) * (K - 1)
    start = (N + K - 1 - n_out) // 2 + offset
    end = min(N + K - 1, start + n_out - offset)
    n_samples = int(np.ceil((n_out - offset) / every))
    if n_samples <= 0:
        raise Exception(
            "mode and offset values are incompatibles"
            + " with kernel and signal sizes."
        )

    perT = int(every * np.ceil(np.ceil((N + K - 1 - start) / T) / every))
    rperT = int(np.ceil(N / T))

    wavelets, ops = {}, {}

    @njit(parallel=use_parallel, cache=True)
    def _numba_mm(x, in2, in3):
        # x is always 2d
        batch_size = x.shape[1]
        if batch_size == 1:
            acc1 = np.empty(T, dtype=(in2[0] * in3[0] * x[0, :]).dtype)
            acc2 = np.empty(T, dtype=(in2[0] * in3[0] * x[0, :]).dtype)
            y = np.empty((2 * n_samples, batch_size),
                         dtype=(in2[0] * in3[0] * x[0, :]).dtype)
            for t in prange(T):
                for i in range(start + t * perT,
                               min(end, start + (t + 1) * perT),
                               every):
                    # i - j < N
                    # i - j >= 0
                    # j < K
                    acc1[t], acc2[t] = 0.0, 0.0
                    for j in range(max(0, i - N + 1), min(K, i + 1), 1):
                        acc1[t] += in2[j] * x[i - j, 0]
                        acc2[t] += in3[j] * x[i - j, 0]
                    y[(i - start) // every, 0] = acc1[t]
                    y[n_samples + (i - start) // every, 0] = acc2[t]
        else:
            tmp2 = np.empty(T, dtype=in2.dtype)
            tmp3 = np.empty(T, dtype=in3.dtype)
            y = np.zeros((2 * n_samples, batch_size),
                         dtype=(in2[0] * in3[0] * x[0, :]).dtype)
            for t in prange(T):
                for i in range(start + t * perT,
                               min(end, start + (t + 1) * perT),
                               every):
                    # i - j < N
                    # i - j >= 0
                    # j < K
                    for j in range(max(0, i - N + 1), min(K, i + 1), 1):
                        # Store values of the two filters
                        tmp2[t], tmp3[t] = in2[j], in3[j]
                        # NumPy uses row-major format
                        for b in range(batch_size):
                            y[(i - start) // every, b] += (
                                tmp2[t] * x[i - j, b]
                            )
                            y[n_samples + (i - start) // every, b] += (
                                tmp3[t] * x[i - j, b]
                            )
        return y

    @njit(parallel=use_parallel, cache=True)
    def _numba_rmm(x, in2, in3):
        # x is always 2d
        batch_size = x.shape[1]
        a = 0 if mode == 'full' and offset == 0 else 1
        y = np.full((N, batch_size),
                    0.0 * (in2[0] * in3[0] * x[0, 0]))
        for t in prange(T):
            for i in range(t * rperT, min(N, (t + 1) * rperT)):
                if every == 2:
                    jstart = (i - a * start) - (i - a * start) // every
                elif every == 1:
                    jstart = i - a * start
                else:
                    pass
                for j in range(max(0, jstart), n_samples):
                    if every == 2:
                        k = (i - a * start) % 2 + (j - jstart) * every
                    elif every == 1:
                        k = j - jstart
                    else:
                        pass
                    if k < K:
                        # NumPy uses row-major format
                        for b in range(batch_size):
                            y[i, b] += in2[k] * x[j, b]
                            y[i, b] += in3[k] * x[n_samples + j, b]
        return y

    def _matmat(x, wavelet, adjoint):
        # A string wavelet needs to know namespace of x.
        # If wavelet is a string use xp from input x.
        # If wavelet is a tuple of arrays use xp from wavelet.
        xp = array_namespace(x)
        # Handle dtype because torch expects the two
        # tensors to have the same dtype.
        _dtype = x.dtype if is_torch_array(x) else 'float'
        _device = device(x)
        # Get pre-computed window or compute it
        # according to x.
        str_t = str(_dtype)
        str_d = str(_device)
        if 'numpy' in str(xp.__package__):
            lib = 'numpy'
        elif 'cupy' in str(xp.__package__):
            lib = 'cupy'
        elif 'torch' in str(xp.__package__):
            lib = 'torch'
        if lib not in wavelets.keys():
            wavelets[lib] = {}
            ops[lib] = {}
        if str_t not in wavelets[lib].keys():
            wavelets[lib][str_t] = {}
            ops[lib][str_t] = {}
        if str_d not in wavelets[lib][str_t].keys():
            wavelets[lib][str_t][str_d] = None
            ops[lib][str_t][str_d] = None
        if wavelets[lib][str_t][str_d] is None:
            # Handle dtype because torch expects the two
            # tensors to have the same dtype.
            _, filters, _, _ = _wavelet(
                wavelet, xp=xp, dtype=_dtype, device=_device)
            wavelets[lib][str_t][str_d] = filters
            build = True
        else:
            filters = wavelets[lib][str_t][str_d]
            build = False

        if is_numpy_array(
                filters[0]) and filters[0].shape[0] < (
                    3 * int(np.log2(N))):
            if adjoint:
                return _numba_rmm(x, filters[0], filters[1])
            else:
                return _numba_mm(x, filters[0], filters[1])
        elif is_numpy_array(
                filters[0]) and filters[0].shape[0] >= (
                    3 * int(np.log2(N))):
            backend = 'scipy_convolve'
        elif is_cupy_array(x):
            backend = 'scipy_convolve'
        elif is_torch_array(x):
            backend = 'torch'
        if build:
            # Convolution
            G = convolve(N, filters[0], mode=mode,
                         backend=backend)
            H = convolve(N, filters[1], mode=mode,
                         backend=backend)
            # Down-sampling
            DG = downsample(G.shape[0], every, offset)
            DH = downsample(H.shape[0], every, offset)
            # Vertical stack
            V = vstack((DG @ G, DH @ H))
            ops[lib][str_t][str_d] = V
        else:
            V = ops[lib][str_t][str_d]
        return (V.H if adjoint else V) @ x

    return LazyLinOp(
        shape=(2 * n_samples, N),
        matmat=lambda x: _matmat(x, wavelet, False),
        rmatmat=lambda x: _matmat(x, wavelet, True))


def _wavelet(wavelet: Union[str, tuple] = 'haar',
             dec: bool = True, xp=np, dtype=None, device=None):
    """
    Build filters.

    Args:
        wavelet: optional
            Name of the wavelet or tuple of filters.
            ``'haar'`` is the default value.
        dec: ``bool``, optional

            - ``dec = True`` decomposition filters.
            - ``dec = False`` reconstruction filters.
        xp: optional
            Namespace of the filters.
            NumPy ``np`` is default value.
        dtype: optional
            dtype of the filters.
        device: optional
            Device of the filters.

    Returns:
        wavelet, tuple of filters, wavelet length
        and wavelet name.
    """

    if isinstance(wavelet, pywt.Wavelet):
        # Use pywt or the fake one.
        return wavelet, \
            (np.asarray(wavelet.dec_lo),
             np.asarray(wavelet.dec_hi),
             np.asarray(wavelet.rec_lo),
             np.asarray(wavelet.rec_hi)), \
            wavelet.dec_len, \
            wavelet.name
    elif isinstance(wavelet, tuple) and len(wavelet) == 2:
        try:
            filters = tuple(wavelet)
            assert (
                (
                    isinstance(filters[0], np.ndarray) and
                    isinstance(filters[1], np.ndarray)
                ) or (
                    is_cupy_array(filters[0]) and
                    is_cupy_array(filters[1])
                ) or (
                    is_torch_array(filters[0]) and
                    is_torch_array(filters[1])
                )
            )
        except Exception:
            raise ValueError("'wavelet' argument must be a string" +
                             " or a tuple of two NumPy, CuPy arrays" +
                             " or torch tensors.")
        W = filters[0].shape[0]
        name = "user_provided"
        xp = array_namespace(filters[0])
        if dec:
            # wavelet=(dec_lo, dec_hi) for dwt(...)
            if is_numpy_array(filters[0]):
                return pywt.Wavelet(
                    name,
                    [filters[0], filters[1],
                     filters[0][::-1], filters[1][::-1]]), \
                     (filters[0], filters[1],
                      filters[0][::-1], filters[1][::-1]), W, name
            else:
                # pywt.Wavelet does not accept CuPy arrays
                # and torch tensors.
                return None, \
                    (filters[0], filters[1],
                     xp.flip(filters[0]), xp.flip(filters[1])), W, name
        else:
            # wavelet=(rec_lo, rec_hi) for idwt(...)
            if is_numpy_array(filters[0]):
                return pywt.Wavelet(
                    name,
                    [filters[0][::-1], filters[1][::-1],
                     filters[0], filters[1]]), \
                     (filters[0][::-1], filters[1][::-1],
                      filters[0], filters[1]), W, name
            else:
                # pywt.Wavelet does not accept CuPy arrays
                # and torch tensors.
                return None, \
                    (xp.flip(filters[0]), xp.flip(filters[1]),
                     filters[0], filters[1]), W, name
    elif isinstance(wavelet, str):
        try:
            pwavelet = pywt.Wavelet(wavelet)
            return pwavelet, (
                    xp.asarray(pwavelet.dec_lo,
                               dtype=dtype, device=device),
                    xp.asarray(pwavelet.dec_hi,
                               dtype=dtype, device=device),
                    xp.asarray(pwavelet.rec_lo,
                               dtype=dtype, device=device),
                    xp.asarray(pwavelet.rec_hi,
                               dtype=dtype, device=device)
                ), pwavelet.dec_len, wavelet
        except NameError:
            raise Exception("pywavelets module is required" +
                            " if 'wavelet' is a 'str')")
    else:
        raise ValueError("'wavelet' argument must be a string" +
                         " or a tuple of two numpy arrays.")


def _max_level(N: int, wavelet: Union[str, tuple] = 'haar',
               level: int = None):
    """
    Maximum decomposition level: stop decomposition when
    the signal becomes shorter than the filter length.
    """
    _, _, W, _ = _wavelet(wavelet)
    K = int(np.log2(N / (W - 1)))
    if level is not None and level > K:
        raise ValueError("level is greater than the" +
                         " maximum decomposition level.")
    return K if level is None else level


def _ncoeffs(N: int, W: int, mode):
    """
    Number of coefficients per decomposition level.
    """
    if mode == 'periodization':
        return int(np.ceil(N / 2))
    else:
        return (N + W - 1) // 2


def _len_coeffs(N: int, W: int, mode: int, lvl: str):
    """
    Total number of coefficients for a
    given decomposition level.
    """
    tmp, n_coeffs = N, 0
    for i in range(lvl):
        # Number of details coefficients.
        tmp = pywt.dwt_coeff_len(
            tmp, W,
            mode=mode if mode == 'periodization' else 'zero')
        n_coeffs += int(tmp)
    # Number of approximation coefficients.
    n_coeffs += int(tmp)
    return n_coeffs


def dwt(N: int, wavelet: Union[str, tuple] = 'haar',
        mode: str = 'zero', level: int = None,
        backend: str = 'pywavelets'):
    r"""
    Returns a :class:`.LazyLinOp` ``L`` for the
    Discrete Wavelet Transform (DWT).
    ``L @ x`` will return a 1D numpy array as the concatenation
    of the DWT coefficients in the form
    ``[cAₙ, cDₙ, cDₙ₋₁, …, cD₂, cD₁]``,
    where ``n`` is the decomposition level,
    ``cAₙ`` is the approximation coefficients for level ``n``
    and ``cDᵢ`` is the detail coefficients at decomposition level ``i``.

    Shape of ``L`` is $(M,~N)$ where $M$ depends on the ``wavelet``,
    input size ``N`` and decomposition ``level``.

    :octicon:`alert-fill;1em;sd-text-danger` In general,
    ``L`` is not orthogonal.
    However, when ``wavelet`` is either the name of an orthogonal
    wavelet (see `Pywavelets documentation <https://pywavelets.readthedocs
    .io/en/latest/regression/wavelet.html#wavelet-families-and-builtin
    -wavelets-names>`_), or a tuple of Quadrature-Mirrors-Filters, the
    following properties holds:
    - if ``mode='zero'`` then ``L.T`` is a left-inverse to ``L``,
      i.e. ``L.T @ L = Id`` (but since ``L.shape = (M, N)`` with
      $M>N$, ``L`` does *not* satisfy ``L @ L.T = Id``.
    - if ``mode='periodization'`` and if the signal size ``N``
      is a power of two, then $M=N$ and ``L`` is orthogonal
      so that ``L @ L.T = L.T @ L = Id``
    See `technical notes <https://gitlab.inria.fr/faustgrp/lazylinop/
    -/blob/dwt_periodization/docs/dwt.pdf?ref_type=heads>`_ for more details.

    After removing some details the code looks like (for the first
    level of decomposition and without extension mode):

    .. code-block:: python3

        # Convolution operators with low-pass and
        # high-pass decomposition filters.
        G = convolve(N, dec_lo, mode='same')
        H = convolve(N, dec_hi, mode='same')
        # Downsampling operator.
        DG = downsample(G.shape[0], 2, 1)
        DH = downsample(H.shape[0], 2, 1)
        # Decomposition operator.
        L = vstack((DG @ G, DH @ H))

    Args:
        N: ``int``
            Size of the input array.
        wavelet: ``str`` or tuple of ``(dec_lo, dec_hi)``, optional

            - If a ``str`` is provided, the wavelet name from
              `Pywavelets library <https://pywavelets.readthedocs.io/en/latest/
              regression/wavelet.html#wavelet-families-and-builtin-wavelets-names>`_.
              In that case, the namespace of the low and high-pass filters
              depends on the namespace of the input array.
            - If a tuple ``(dec_lo, dec_hi)`` of two NumPy, CuPy arrays or torch tensors.
              is provided, the low and high-pass filters (for *decomposition*)
              used to define the wavelet.

              :octicon:`megaphone;1em;sd-text-danger` The ``dwt()`` function
              does not test whether these two filters are
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
            Decomposition level, by default (None) the maximum level is used.
        backend: ``str``, optional
            ``'pywavelets'`` (default) or ``'lazylinop'`` for the underlying
            computation of the DWT.
            ``backend='pywavelets'`` does not work for CuPy array
            and torch tensor inputs.

    Returns:
        :class:`.LazyLinOp` DWT.

    Examples:
        >>> from lazylinop.signal import dwt
        >>> import numpy as np
        >>> import pywt
        >>> N = 8
        >>> x = np.arange(1, N + 1, 1)
        >>> L = dwt(N, wavelet='haar', mode='periodic', level=1)
        >>> y = L @ x
        >>> z = pywt.wavedec(x, wavelet='haar', mode='periodic', level=1)
        >>> np.allclose(y, np.concatenate(z))
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
        - :func:`.idwt`.
    """

    if level is not None and level < 0:
        raise ValueError("Decomposition level must be >= 0.")
    if mode not in ['antisymmetric', 'reflect',
                    'periodic', 'periodization', 'symmetric', 'zero']:
        raise ValueError("mode is either 'antisymmetric', 'reflect',"
                         + " 'periodic', 'periodization',"
                         + " 'symmetric' or 'zero'.")

    n_levels = _max_level(N, wavelet, level)

    if not found_pywt:
        warnings.warn("PyWavelets is not installed,"
                      + " switch backend to 'lazylinop'.")
        backend = 'lazylinop'

    if backend == 'pywavelets':

        pwavelet, lwavelet, W, name = _wavelet(wavelet)

        if pwavelet is None or not is_numpy_array(lwavelet[0]):
            raise TypeError("backend='pywavelets' does not work " +
                            " with CuPy arrays and torch tensors.")

        # Name of the wavelet to use with rmatmat.
        if 'rbio' in name:
            rwavelet = pywt.Wavelet('bior' + name[-3:])
        elif 'bior' in name:
            rwavelet = pywt.Wavelet('rbio' + name[-3:])
        else:
            rwavelet = pwavelet

        # DWT operator for zero mode extension.
        def _Psi_z(N, level: int = 1):

            if level is None or not isinstance(level, int):
                raise TypeError("Type of level must be int.")

            # Compute length of the output (number of coefficients).
            ncoeffs = _len_coeffs(N, W, 'zero', level)

            # Get slices for further reconstruction (rmatmat).
            # Do it once and for all.
            # Of note, we have no idea about the batch size here.
            rslices = pywt.coeffs_to_array(
                pywt.wavedecn(
                    np.full((N, 1), 1.0), wavelet=pwavelet,
                    level=level, mode='zero', axes=(0, )
                ), axes=(0, )
            )[1]

            def _matmat(x):
                if not is_numpy_array(x):
                    raise TypeError("backend='pywavelets' does not work " +
                                    " with CuPy arrays and torch tensors.")
                if level == 0:
                    # Nothing to decompose, return input.
                    return x.copy()
                # Decomposition (return array from coefficients)
                # x is always 2d
                y = pywt.coeffs_to_array(
                    pywt.wavedecn(
                        x, wavelet=pwavelet,
                        level=level, mode='zero', axes=(0, )
                    ),
                    axes=(0, )
                )[0]
                return y[:ncoeffs, :]

            def _rmatmat(x, rslices):
                if not is_numpy_array(x):
                    raise TypeError("backend='pywavelets' does not work " +
                                    " with CuPy arrays and torch tensors.")
                if level == 0:
                    # Nothing to decompose, return input.
                    return x.copy()
                # Reconstruction
                # x is always 2d
                # Size of the batch is not always the same.
                tmp = slice(rslices[0][1].start,
                            x.shape[1], rslices[0][1].step)
                rslices[0] = (rslices[0][0], tmp)
                x_ = pywt.array_to_coeffs(x, rslices, output_format='wavedecn')
                y = pywt.waverecn(x_, wavelet=rwavelet,
                                  mode='zero', axes=(0, ))
                return y[:N, :]

            return LazyLinOp(
                shape=(ncoeffs, N),
                matmat=lambda x: _matmat(x),
                rmatmat=lambda x: _rmatmat(x, rslices)
            )

        if mode == 'zero':
            return _Psi_z(N, n_levels)
        else:
            # Analysis operator Psi is given by R @ Psi_z @ E
            # where Psi_z is the analysis operator with zero mode extension.
            # R is the restriction operator.
            # Adjoint operator is given by E^H @ Psi_z^H @ R^H where
            # Psi_z^H is the reconstruction operator for orthogonal wavelets.
            # Of note, for zero mode extension we can easily define
            # a LazyLinOp from Pywavelets wavedec and waverec functions.

            # Init.
            n = N
            Psi = _Psi_z(n, n_levels)

            # Loop over the decomposition level
            for _ in range(n_levels):
                # Restriction operator
                if mode == 'periodization':
                    # Pywavelets starts down-sampling at odd indices
                    # periodization mode starts at odd or even indices
                    # depending on the wavelet length.
                    # See https://github.com/PyWavelets/pywt/issues/329
                    # for more details.
                    npad = W + 1 - (W // 2) % 2
                    n_cAs = (n + 2 * npad + W - 1) // 2
                    n_out = int(np.ceil(n / 2))
                    k_offset = int(np.ceil((n_cAs - n_out) / 2))
                    R = vstack(
                        (
                            eye(n_out, 2 * n_cAs, k=k_offset),
                            eye(n_out, 2 * n_cAs, k=n_cAs + k_offset)
                        )
                    )
                else:
                    npad = W
                    n_cAs = (n + 2 * npad + W - 1) // 2
                    n_out = (n + W - 1) // 2
                    R = vstack(
                        (
                            eye(n_out, 2 * n_cAs, k=W // 2),
                            eye(n_out, 2 * n_cAs,
                                k=(n + 2 * npad + W - 1) // 2 + W // 2)
                        )
                    )
                # Analysis operator R for the current level
                if mode == 'periodization':
                    L = _Psi_z(n + n % 2 + 2 * npad, 1)
                else:
                    L = _Psi_z(n + 2 * npad, 1)
                # Extension operator E
                if mode == 'periodization':
                    E = padder(n + n % 2, (npad, npad), mode='periodic')
                    if (n % 2) == 1:
                        E = E @ padder(n, (0, 1), mode='symmetric')
                else:
                    E = padder(n, (npad, npad), mode=mode)
                if n == N:
                    # First level
                    Psi = R @ L @ E
                else:
                    # Apply R @ Psi_z @ E only to approximation coefficients.
                    tmp = Psi.shape[0] - (R @ L @ E).shape[1]
                    Psi = block_diag(*[R @ L @ E, eye(tmp)]) @ Psi
                n = _ncoeffs(n, W, mode)
            return Psi

    elif backend == 'lazylinop':

        # Compute length of the output (number of coefficients).
        _, filters, _, _ = _wavelet(wavelet)
        ncoeffs = _len_coeffs(N, filters[0].shape[0], mode, n_levels)

        if n_levels == 0:
            # Nothing to decompose, return x.
            return eye(N)
        else:
            dec_lo, dec_hi = filters[0], filters[1]
            W = dec_lo.shape[0]
            boffset = (W % 4) == 0
            # Loop over the decomposition level
            Op, cx, nc = None, N, N
            for i in range(n_levels):
                # Boundary conditions
                npd = W - 2
                NN = cx + 2 * npd
                if mode == 'zero':
                    NN += NN % 2
                    B = eye(NN, cx, k=-npd)
                elif mode == 'periodization':
                    if (nc % 2) == 0:
                        NN = nc + 2 * npd
                        mx = NN % 2
                        bn = npd
                        an = npd + mx
                        NN += mx
                        B = padder(nc, (bn, an), mode='periodic')
                    else:
                        B = padder(nc, (0, 1), mode='symmetric')
                        bn = npd
                        an = npd
                        NN = nc + 1 + bn + an
                        B = padder(nc + 1, (bn, an), mode='periodic') @ B
                else:
                    mx = NN % 2
                    bn = npd
                    an = npd + mx
                    NN += mx
                    B = padder(cx, (bn, an), mode=mode)
                # Low and high-pass filters + downsampling.
                # Downsampling starts at offset_d.
                if mode == 'periodization':
                    offset_d = 1
                else:
                    offset_d = 1 - int(boffset)
                # Convolution low and high-pass filters + down-sampling
                GH = ds_mconv(NN, wavelet, mode='same',
                              offset=offset_d) @ B
                # Extract approximation and
                # details coefficients cA, cD (slices)
                if mode == 'periodization':
                    nc = int(np.ceil(nc / 2))
                    mid = NN // 2
                    offset = (mid - nc) // 2
                    V = slicer(GH.shape[0], [offset, offset + mid],
                               [offset + nc, offset + mid + nc])
                else:
                    cx = (cx + W - 1) // 2
                    mid = NN // 2
                    offset = (mid - cx) // 2 + int(boffset)
                    V = slicer(GH.shape[0], [offset, offset + mid],
                               [offset + cx, offset + mid + cx])
                if i == 0:
                    # First level of decomposition
                    Op = V @ GH
                else:
                    # Apply low and high-pass filters.
                    # Apply downsampling only to cA.
                    # Because of lazy linear operator V, cA always comes first.
                    Op = block_diag(*[V @ GH,
                                      eye(Op.shape[0] - GH.shape[1])]) @ Op

            return Op
    else:
        raise ValueError("backend must be either 'pywavelets'"
                         + " or 'lazylinop'.")


def dwt_coeffs_sizes(N: int, wavelet: Union[str, tuple] = 'haar',
                     level: int = None, mode: str = 'zero'):
    """
    Return a ``list`` of ``int`` that gives the size
    of the coefficients ``[cAn, cDn, ..., cD2, cD1]``.

    Args:
        N, wavelet, level, mode:
            See :func:`dwt` for more details.

    Returns:
        ``list`` of ``int``.

    Examples:
        >>> from lazylinop.signal.dwt import dwt_coeffs_sizes
        >>> import pywt
        >>> W = pywt.Wavelet('haar').dec_len
        >>> dwt_coeffs_sizes(5, 'haar', level=2)
        [2, 2, 3]
    """

    n_levels = _max_level(N, wavelet, level)
    if n_levels == 0:
        # Nothing to do.
        return [N]
    _, _, W, _ = _wavelet(wavelet)

    # First approximation coefficients.
    ll = [_ncoeffs(N, W, mode)]
    for _ in range(1, n_levels):
        ll.insert(0, _ncoeffs(ll[0], W, mode))
    # Last approximation coefficients.
    ll.insert(0, ll[0])
    return ll


def dwt_to_pywt_coeffs(x, N: int, wavelet: Union[str, tuple] = 'haar',
                       level: int = None, mode: str = 'zero'):
    r"""
    Returns Pywavelets compatible
    ``[cAn, cDn, ..., cD2, cD1]`` computed from ``x``
    where ``n`` is the decomposition level.

    Args:
        x: ``np.ndarray``
            List of coefficients
            ``[cAn, cDn, ..., cD2, cD1]``.
        N, wavelet, level, mode:
            See :func:`dwt` for more details.

    Returns:
        Pywavelets compatible ``list``
        ``[cAn, cDn, ..., cD2, cD1]``.

    Examples:
        >>> import numpy as np
        >>> from lazylinop.signal import dwt, dwt_to_pywt_coeffs
        >>> import pywt
        >>> N = 11
        >>> x = np.arange(N)
        >>> L = dwt(N, wavelet='haar', level=2, mode='zero')
        >>> y = dwt_to_pywt_coeffs(L @ x, N, 'haar', level=2, mode='zero')
        >>> z = pywt.wavedec(x, wavelet='haar', level=2, mode='zero')
        >>> np.allclose(y[0], z[0])
        True
        >>> np.allclose(y[1], z[1])
        True
    """
    if not isinstance(N, int):
        raise Exception("N must be an int.")

    n_levels = _max_level(N, wavelet, level)

    if n_levels == 0:
        # Nothing to convert.
        return [x]

    # Shape of coefficients per decomposition level.
    sizes = dwt_coeffs_sizes(N, wavelet, n_levels, mode)

    # Stop decomposition when the signal becomes
    # shorter than the filter length.
    cum, y, idx = 0, [], 0
    for i in range(n_levels):
        # Current size of the coefficients.
        n = sizes[idx]
        if i == 0:
            # cA, cD
            y.append(x[:n])
            y.append(x[n:(2 * n)])
            cum += 2 * n
            idx += 2
        else:
            # cD
            y.append(x[cum:(cum + n)])
            cum += n
            idx += 1
    return y


# if __name__ == '__main__':
#     import doctest
#     doctest.testmod()
