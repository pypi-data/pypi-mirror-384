import numpy as np
import scipy as sp
from os import environ, cpu_count
import sys
from lazylinop import LazyLinOp, mpad
from lazylinop.basicops import block_diag, diag, eye, padder
from lazylinop.signal import fft
from lazylinop.signal.utils import overlap_add
import warnings
from warnings import warn
import array_api_compat
from array_api_compat import (
    device, is_torch_array, is_cupy_array, is_numpy_array)
import contextlib

sys.setrecursionlimit(100000)
warnings.simplefilter(action='always')


def _dims(N: int, K: int, mode: str, cupy_conv: bool = False):
    """Return length of the output as a function
    of the length of the input, of the length of kernel
    and of the convolution mode.

    Args:
        N: ``int``
            Size of the input array (if 1d, number of rows if 2d).
        K: ``int``
            Length of the kernel.
        mode: ``str``
            Convolution mode.
        cvupy_conv: ``bool``, optional
            Follow dimension convention of ``cupy.convolve``.
            Default value if ``False``.

    Returns:
        ``int``
    """
    imode = 0 * int(mode == 'full') + 1 * int(mode == 'valid') + \
        2 * int(mode == 'same') + 3 * int(mode == 'circ')
    return np.array([N + K - 1,  # full
                     max(N, K) - min(N, K) + 1,  # valid
                     max(N, K) if cupy_conv else N,  # same
                     N  # circ
                     ], dtype=np.int_)[imode]


def _rmode(mode: str):
    """Return adjoint convolution mode.

    Args:
        mode: ``str``
            Convolution mode.

    Returns:
        ``str``
    """
    return {'full': 'valid', 'valid': 'full',
            'same': 'same', 'circ': 'circ'}[mode]


def _is_cplx(t1, t2):
    return 'complex' in str(t1) or 'complex' in str(t2)


def convolve(N: int, filter, mode: str = 'full',
             backend: str = 'scipy_convolve'):
    r"""
    Returns a :class:`.LazyLinOp` ``L`` for the 1d convolution of
    signal(s) of size ``N`` with a kernel ``filter``.

    Shape of ``L`` is $(M,~N)$. See ``mode`` for output size $M$.

    Args:
        N: ``int``
            Size of the signal to be convolved.

        filter: ``np.ndarray``, ``cp.ndarray`` or ``torch.Tensor``
            Filter to be applied to the signal. ``filter`` must be a 1d-array.
        mode: ``str``, optional
            - ``'full'``: compute full convolution including at points of
              non-complete overlapping of inputs. Output size ``M`` is ``N +
              filter.size - 1``.
            - ``'valid'``: compute only fully overlapping part of the
              convolution. This is the 'full' center part of (output)
              size ``M = max(N, K) - min(N, K) + 1`` where
              ``K = filter.size``.
            - ``'same'``: compute only the center part of ``'full'`` to
              obtain an output size ``M`` equal to the input size ``N``.
            - ``'circ'``: compute circular convolution (``filter.size <= N``
              must be satisfied). Output size ``M`` is ``N``.
        backend: ``str``, optional
            - ``'auto'``: use best ``backend`` available according
              to the namespace of filter.

                - for ``mode='circ'`` use ``backend='fft'``.
                - for any other mode use ``backend='direct'``
                  if ``filter`` is a NumPy array and ``filter.size < log2(M)``,
                  ``backend='scipy_convolve'`` if ``filter`` is
                  a NumPy array and ``filter.size >= log2(M)``,
                  ``backend='scipy_convolve'`` if ``filter`` is
                  a CuPy or NumPy array,
                  ``backend='torch'`` if ``filter`` is a torch tensor.
            - ``'scipy_convolve'``: (default) encapsulates
              ``(cupyx).scipy.signal.convolve``.

              It uses internally the best SciPy backend between ``'fft'`` and
              ``'direct'`` (see `scipy.signal.choose_conv_method <https://
              docs.scipy.org/doc/scipy/reference/generated/scipy.signal.
              choose_conv_method.html#scipy.signal.choose_conv_method>`_).
              If the filter and the input are CuPy arrays the function
              uses ``cupyx.scipy.signal.convolve``.
            - ``'direct'``: direct computation using nested for-loops with
              Numba and parallelization.
              It does not work if the input is CuPy array or torch tensor.
            - ``'fft'``: (only for ``mode='circ'``) compute circular
              convolution using ``(cupyx).scipy.fft.fft``.
            - ``'toeplitz'``: encapsulate ``(cupyx).scipy.linalg.toeplitz``
              if ``N < 2048``, ``(cupyx).scipy.linalg.matmul_toeplitz`` otherwise.
              Of note, there is no torch implementation for Toeplitz matrix.
            - ``'oa'``: use Lazylinop implementation of overlap-add backend.
            - ``'torch'``: use ``torchaudio.functional.convolve``.

    Returns:
        :class:`.LazyLinOp`

    Examples:
        >>> import numpy as np
        >>> import scipy.signal as sps
        >>> import lazylinop.signal as lzs
        >>> N = 1024
        >>> x = np.random.randn(N)
        >>> kernel = np.random.randn(32)
        >>> L = lzs.convolve(N, kernel)
        >>> c1 = L @ x
        >>> c2 = sps.convolve(x, kernel)
        >>> np.allclose(c1, c2)
        True
        >>> N = 32768
        >>> x = np.random.randn(N)
        >>> kernel = np.random.randn(48)
        >>> L = lzs.convolve(N, kernel, mode='circ', backend='fft')
        >>> c1 = L @ x
        >>> L = lzs.convolve(N, kernel, mode='circ', backend='direct')
        >>> c2 = L @ x
        >>> np.allclose(c1, c2)
        True

    .. seealso::
        - `SciPy convolve function <https://docs.scipy.org/doc/scipy/
          reference/generated/scipy.signal.convolve.html>`_,
        - `SciPy oaconvolve function <https://docs.scipy.org/doc/scipy/
          reference/generated/scipy.signal.oaconvolve.html>`_,
        - `CuPy convolve function <https://docs.cupy.dev/en/latest/
          reference/generated/cupy.convolve.html#cupy-convolve>`_,
        - `cupyx.scipy.signal.convolve function <https://docs.cupy.dev/
          en/latest/reference/generated/cupyx.scipy.signal.convolve.html>`_,
        - `cupyx.scipy.signal.oaconvolve function <https://docs.cupy.dev/
          en/latest/reference/generated/cupyx.scipy.signal.oaconvolve.html>`_,
        - `torchaudio.functional.convolve function <https://docs.pytorch.org/
          audio/2.5.0/generated/torchaudio.functional.convolve.html>`_,
        - `Overlap-add method (wikipedia) <https://en.wikipedia.org/
          wiki/Overlap%E2%80%93add_method>`_,
        - `Circular convolution (wikipedia) <https://en.wikipedia.org/
          wiki/Circular_convolution>`_,
        - `SciPy correlate function <https://docs.scipy.org/doc/scipy/
          reference/generated/scipy.signal.correlate.html>`_,
        - `SciPy matmul_toeplitz function <https://docs.scipy.org/doc/
          scipy/reference/generated/
          scipy.linalg.matmul_toeplitz.html#scipy.linalg.matmul_toeplitz>`_.
    """
    return _convolve_helper(N, filter, mode, backend, None)


def _convolve_helper(N: int, filter, mode: str = 'full',
                     backend: str = 'scipy_convolve', workers: int = None):
    r"""
    Returns a :class:`.LazyLinOp` for the 1d convolution of
    signal(s) of size ``N`` with a kernel ``filter``.

    See below, ``N`` and ``filter`` for input sizes.
    See ``mode`` for output size.

    Args:
        workers: ``int``, optional
            The number of threads used to parallelize
            ``backend='direct', 'toeplitz', 'scipy_convolve'`` using
            respectively Numba, NumPy and SciPy capabilities.
            Default is ``os.cpu_count()`` (number of CPU threads available).
            Of note, ``cupy.fft`` has no attribute ``set_workers``.

            .. admonition:: Environment override

                ``workers`` can be overridden from the environment using
                ``NUMBA_NUM_THREADS`` for ``backend='direct'`` and
                ``OMP_NUM_THREADS`` for ``backend='toeplitz'``,
                ``'scipy_convolve'``.

    Returns:
        :class:`.LazyLinOp`
    """
    # never disable JIT except if env var NUMBA_DISABLE_JIT is used
    if 'NUMBA_DISABLE_JIT' in environ.keys():
        disable_jit = int(environ['NUMBA_DISABLE_JIT'])
    else:
        disable_jit = 0

    if workers is None:
        workers = cpu_count()  # default

    if mode not in ['full', 'valid', 'same', 'circ']:
        raise ValueError("mode is not valid ('full' (default), 'valid', 'same'"
                         " or 'circ').")

    all_backend = [
        'auto',
        'direct',
        'toeplitz',
        'scipy_convolve',
        'oa',
        'fft',
        'torch'
    ]

    circ_backend = [
        'auto',
        'direct',
        'fft'
    ]

    if mode != 'circ' and backend not in all_backend:
        raise ValueError(
            "backend is not in " + str(all_backend))
    if mode == 'circ' and backend not in circ_backend:
        raise ValueError("mode='circ' expects backend" +
                         " to be in " + str(circ_backend))

    if mode != 'circ' and backend == 'fft':
        raise ValueError("backend='fft' works only with mode='circ'.")

    if type(N) is not int:
        raise TypeError("N must be an int.")

    if N <= 0:
        raise ValueError("size N < 0")

    if len(filter.shape) >= 2:
        raise Exception("filter must be 1d array.")

    K = filter.shape[0]
    if K > N and mode == 'circ':
        raise ValueError("filter.size > N and mode='circ'")

    if mode == 'circ':
        if backend == 'auto':
            compute = 'circ.fft'
        else:
            compute = 'circ.' + backend
    else:
        if backend == 'auto':
            if K < np.log2(_dims(N, K, mode)) and \
               isinstance(filter, np.ndarray):
                compute = 'direct'
            if K >= np.log2(_dims(N, K, mode)) and \
               isinstance(filter, np.ndarray):
                compute = 'scipy_convolve'
            elif is_cupy_array(filter):
                # Use cupyx.scipy.signal.convolve.
                compute = 'scipy_convolve'
            elif is_torch_array(filter):
                # Use torchaudio.functional.convolve.
                compute = 'torch'
            else:
                compute = 'scipy_convolve'
        else:
            compute = backend

    if compute == 'direct':
        try:
            import numba  # noqa: F401
        except ImportError:
            warn("Did not find Numba, switch to 'scipy_convolve'.")
            compute = 'scipy_convolve'

    # Check which backend is asked for
    if compute == 'direct':
        C = _direct(N, filter, mode, disable_jit, workers)
    elif compute == 'toeplitz':
        C = _toeplitz(N, filter, mode, workers)
    elif compute == 'scipy_convolve':
        C = _scipy_encapsulation(N, filter, mode, workers)
    elif compute == 'oa':
        C = _oaconvolve(N, filter, mode=mode, workers=workers)
    elif 'circ.' in compute:
        C = _circconvolve(N, filter,
                          backend.replace('circ.', ''), disable_jit, workers)
    elif compute == 'torch':
        C = _torch_encapsulation(N, filter, mode)
    else:
        raise ValueError("backend is not in " + str(all_backend))

    L = LazyLinOp(
        shape=C.shape,
        matmat=lambda x: (
            C @ x if _is_cplx(x.dtype, filter.dtype)
            else (C @ x).real),
        rmatmat=lambda x: (
            C.H @ x if _is_cplx(x.dtype, filter.dtype)
            else (C.H @ x).real))
    # for callee information
    L.disable_jit = disable_jit
    return L


def _direct(N: int, filter: np.ndarray,
            mode: str = 'full', disable_jit: int = 0, workers=None):
    r"""Builds a :class:`.LazyLinOp` for the convolution of
    a signal of size ``N`` with a kernel ``filter``.
    If shape of the input array is ``(N, batch)``,
    return convolution per column.
    Function uses direct computation: nested for loops.
    You can switch on Numba jit and enable ``prange``.
    Larger the signal is better the performances are.
    Larger the batch size is better the performances are.
    Do not call ``_direct`` function outside
    of ``convolve`` function.

    Args:
        N: ``int``
            Length of the input.
        filter: ``np.ndarray``
            Kernel to convolve with the signal, shape is ``(K, )``.
        mode: ``str``, optional

            - 'full' computes convolution (input + padding).
            - 'valid' computes 'full' mode and extract centered output that
              does not depend on the padding.
            - 'same' computes 'full' mode and extract centered output that has
              the same shape that the input.
        disable_jit: ``int``, optional
            If 0 (default) enable Numba jit.
            It only matters for ``backend='direct'``.
            Be careful that ``backend='direct'`` is very slow
            when Numba jit is disabled.
            Prefix by ``NUMBA_NUM_THREADS=$t`` to launch ``t`` threads.

    Returns:
        :class:`.LazyLinOp`
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
        nb.config.THREADING_LAYER = 'omp'
        nb.config.DISABLE_JIT = disable_jit
        if workers is not None and 'NUMBA_NUM_THREADS' not in environ.keys():
            nb.config.NUMBA_NUM_THREADS = workers
    except:
        pass

    K = filter.shape[0]
    M = _dims(N, K, mode)
    P = (
        (max(N, K) - min(N, K) + 1) * int(mode == 'full') +
        (N + K - 1) * int(mode == 'valid') +
        N * int(mode == 'same')
    )

    if is_cupy_array(filter) or is_torch_array(filter):
        raise TypeError("backend='direct' does not work" +
                        " with CuPy arrays and torch tensors.")

    def _matmat(x, kernel):
        if is_cupy_array(x) or is_torch_array(x):
            raise TypeError("backend='direct' does not work" +
                            " with CuPy arrays and torch tensors.")
        return _mm(x, kernel)

    def _rmatmat(x, kernel):
        if is_cupy_array(x) or is_torch_array(x):
            raise TypeError("backend='direct' does not work" +
                            " with CuPy arrays and torch tensors.")
        return _rmm(x, kernel)

    @njit(parallel=True, cache=True)
    def _mm(x, kernel):

        K = kernel.shape[0]
        batch_size = x.shape[1]
        y = np.full((M, batch_size),
                    0.0 * (kernel[0] * x[0, 0]))
        # y[n] = sum(h[k] * x[n - k], k, 0, K - 1)
        # n - k > 0 and n - k < len(x)
        start = (N + K - 1 - M) // 2
        for i in prange(start, start + M):
            # i - j >= 0
            # i - j < N
            for j in range(
                    min(max(0, i - N + 1), K),
                    min(K, i + 1)
            ):
                # NumPy (defaultly) uses row-major format
                for b in range(batch_size):
                    y[i - start, b] += kernel[j] * x[i - j, b]
        return y

    @njit(parallel=True, cache=True)
    def _rmm(x, kernel):

        K = kernel.shape[0]
        S, batch_size = x.shape
        y = np.full((N, batch_size), 0.0 * (kernel[0] * x[0, 0]))
        # y[n] = sum(h[k] * x[k + n], k, 0, K - 1)
        # k + n < len(x)
        rstart = (S + K - 1 - N) // 2
        for i in prange(rstart, rstart + N):
            for j in range(min(max(0, i - S + 1), K),
                           min(K, i + 1)):
                # NumPy (defaultly) uses row-major format
                for b in range(batch_size):
                    y[N + rstart - i - 1, b] += np.conjugate(
                        kernel[j]) * x[j - i + S - 1, b]
        return y

    return LazyLinOp(
        shape=(M, N),
        matmat=lambda x: _matmat(x, filter),
        rmatmat=lambda x: _rmatmat(x, filter)
    )


def _toeplitz(N: int, filter: np.ndarray, mode: str = 'full',
              workers: int = None):
    r"""Builds a :class:`.LazyLinOp` for the convolution of
    a signal of size ``N`` with a kernel ``filter``.
    If shape of the input array is ``(N, batch)``,
    return convolution per column.
    Function uses ``(cupyx).scipy.linalg.toeplitz`` or
    ``(cupyx).scipy.linalg.matmul_toeplitz``
    implementation to compute convolution.
    Do not call ``_toeplitz`` function outside
    of ``convolve`` function.
    Of note, there is no torch implementation
    for Toeplitz matrix.

    Args:
        N: ``int``
            Length of the input.
        filter: ``np.ndarray``
            Kernel to convolve with the signal, shape is ``(K, )``.
        mode: ``str``, optional

            - ``'full'`` computes convolution (input + padding).
            - ``'valid'`` computes 'full' mode and extract centered output that
              does not depend on the padding.
            - ``'same'`` computes 'full' mode and extract centered output that has
              the same shape that the input.
        workers:
            See convolve().
            Used only for matmul_toeplitz (if N > 2048).
            Can be overridden by OMP_NUM_THREADS environment variable.

    Returns:
        :class:`.LazyLinOp`
    """

    if is_torch_array(filter):
        raise TypeError("backend='toeplitz' does not work" +
                        " with torch tensors.")

    if is_cupy_array(filter):
        import cupyx.scipy.linalg as xpl
        import array_api_compat.cupy as xp
    else:
        import scipy.linalg as xpl
        import array_api_compat.numpy as xp

    K = filter.shape[0]
    M = _dims(N, K, mode)
    i0 = (N + K - 1 - M) // 2

    if mode == 'full':
        # No need to slice rows
        c = xp.pad(filter, (0, N - 1))
        r = xp.pad(xp.asarray([filter[0]]), (0, N - 1))
    else:
        # Slice rows of the Toeplitz matrix
        if filter[i0:].shape[0] > M:
            # Handle the case such that kernel length
            # is bigger than signal length.
            c = xp.copy(filter[i0:(i0 + M)])
        else:
            c = xp.pad(filter[i0:], (0, M - (K - i0)))
        if filter[:(i0 + 1)].shape[0] > N:
            # Handle the case such that kernel length
            # is bigger than signal length.
            r = xp.flip(filter[(i0 + 1 - N):(i0 + 1)])
        else:
            r = xp.pad(xp.flip(filter[:(i0 + 1)]), (0, N - (i0 + 1)))

    tmp = "OMP_NUM_THREADS"
    workers = (
        int(environ[tmp]) if tmp in environ.keys()
        else (-1 if workers is None else workers)
    )

    def _mat(c, r, x):
        if is_torch_array(x):
            raise TypeError("backend='toeplitz' does not work" +
                            " with torch tensors.")
        if N < 2048:
            y = xpl.toeplitz(c, r) @ x
        else:
            y = xpl.matmul_toeplitz(
                (c, r), x,
                check_finite=False, workers=workers)
        return y

    # Convolution Toeplitz matrix is lower triangular,
    # therefore we have toeplitz(c, r).T = toeplitz(r, c)
    return LazyLinOp(
        shape=(_dims(N, K, mode), _dims(N, K, 'same')),
        matmat=lambda x: _mat(c, r, x),
        rmatmat=lambda x: _mat(r.conj(), c.conj(), x))


# def _pre_compute(f, filters, xp, dtype, device):
#     """
#     Get pre-computed window or compute it
#     according to x.
#     """
#     str_t = str(dtype)
#     str_d = str(device)
#     if 'numpy' in str(xp):
#         lib = 'numpy'
#     elif 'cupy' in str(xp):
#         lib = 'cupy'
#     elif 'torch' in str(xp):
#         lib = 'torch'
#     else:
#         raise Exception("Unknown namespace.")
#     if lib not in filters.keys():
#         filters[lib] = {}
#     if not str_t in filters[lib].keys():
#         filters[lib][str_t] = {}
#     if not str_d in filters[lib][str_t].keys():
#         filters[lib][str_t][str_d] = None
#     if filters[lib][str_t][str_d] is None:
#         filters[lib][str_t][str_d] = xp.asarray(
#             f.tolist(), copy=True, device=device)
#     return filters[lib][str_t][str_d]


def _scipy_encapsulation(N: int, filter, mode: str = 'full',
                         workers=None):
    r"""Builds a :class:`.LazyLinOp` for the convolution of
    a signal of size ``N`` with a kernel ``filter``.
    If shape of the input array is ``(N, batch)``,
    return convolution per column.
    Function uses encapsulation of ``(cupyx).scipy.signal.convolve``
    to compute convolution.
    Do not call ``_scipy_encapsulation`` function outside
    of ``convolve`` function.

    Args:
        N: ``int``
            Length of the input.
        filter: ``np.ndarray`` or ``cp.ndarray``
            Kernel to convolve with the signal, shape is ``(K, )``.
        mode: ``str``, optional

            - ``'full'`` computes convolution (input + padding).
            - ``'valid'`` computes 'full' mode and extract centered output that
              does not depend on the padding.
            - ``'same'`` computes 'full' mode and extract centered output that has
              the same shape that the input.
        workers:
            See :py:func:`convolve`.

    Returns:
        :class:`.LazyLinOp`
    """

    if is_torch_array(filter):
        raise TypeError("backend='scipy_convolve' does not work" +
                        " with torch tensors.")
        # If ``filter`` is a torch tensor, cast to NumPy array.
        # filter = filter.numpy(force=True)
        # warn("Cast torch tensor to NumPy array." +
        #      " This incur a loss of performance.")

    if is_cupy_array(filter):
        import cupyx.scipy.signal as xps
    else:
        import scipy.signal as xps
    xp = array_api_compat.array_namespace(filter)

    # Length of the output as a function of convolution mode
    K = filter.shape[0]
    tmp = "OMP_NUM_THREADS"
    workers = (
        int(environ[tmp]) if tmp in environ.keys()
        else (-1 if workers is None else workers)
    )

    # In order to avoid overhead, measure convolve duration
    # outside of `_matmat()` function.
    # It will only run during the creation of the `LazyLinOp()`.
    if is_cupy_array(filter):
        @contextlib.contextmanager
        def _set_workers(workers):
            try:
                yield
            finally:
                pass
    else:
        _set_workers = sp.fft.set_workers

    filters = {}

    def _matmat(x, f):
        if is_torch_array(x):
            raise TypeError("backend='scipy_convolve' does not work" +
                            " with torch tensors.")
        # xp = array_api_compat.array_namespace(x)
        # filter = _pre_compute(f, filters,
        #                       xp, x.dtype, device(x))
        # x is always 2d
        if x.shape[1] > 1:
            with _set_workers(workers):
                # (cupyx).scipy.signal.convolve does not handle batch.
                y = xps.fftconvolve(x, f.reshape(-1, 1),
                                    mode=mode, axes=0)
        else:
            # FIXME: cupyx.scipy.signal.convolve(..., method='direct')
            # returns an error.
            # cupy.fft has no attribute 'set_workers'.
            with _set_workers(workers):
                y = xps.convolve(x[:, 0],
                                 f, mode=mode,
                                 method='auto').reshape(-1, 1)
        return y

    def _rmatmat(x, f):
        if is_torch_array(x):
            raise TypeError("backend='scipy_convolve' does not work" +
                            " with torch tensors.")
        xp = array_api_compat.array_namespace(x)
        # filter = _pre_compute(f, filters,
        #                       xp, x.dtype, device(x))
        # x is always 2d
        rmode = {str(_dims(x.shape[0], K, 'full')): 'full',
                 str(_dims(x.shape[0], K, 'valid')): 'valid',
                 str(_dims(x.shape[0], K, 'same')): 'same'}
        with _set_workers(workers):
            y = xp.flip(
                xps.fftconvolve(
                    xp.flip(x, axis=0),
                    f.conj().reshape(-1, 1),
                    mode=rmode[str(N)], axes=0), axis=0)
        return y

    return LazyLinOp(
        shape=(_dims(N, K, mode), _dims(N, K, 'same')),
        matmat=lambda x: _matmat(x, filter),
        rmatmat=lambda x: _rmatmat(x, filter))


def _oaconvolve(N: int, filter, mode: str = 'full',
                workers: int = None):
    """This function implements overlap-add backend for convolution.
    Builds a :class:`.LazyLinOp` for the convolution
    of a signal of length ``N`` with the kernel ``filter``.
    Do not call ``_oaconvolve`` function outside of ``convolve`` function.

    Args:
        N: ``int``
            Length of the input.
        filter: ``np.ndarray``, ``cp.ndarray`` or ``torch.Tensor``
            Kernel to use for the convolution.
        mode: ``str``, optional

            - 'full' computes convolution (input + padding).
            - 'valid' computes 'full' mode and extract centered
              output that does not depend on the padding.
            - 'same' computes 'full' mode and extract centered
              output that has the same shape that the input.
        workers:
            see convolve().
            Can be overridden by OMP_NUM_THREADS environment variable.

    Returns:
        :class:`.LazyLinOp`
    """

    # FIXME: dead code?
    tmp = "OMP_NUM_THREADS"
    workers = (
        int(environ[tmp]) if tmp in environ.keys()
        else (cpu_count() if workers is None else workers)
    )

    # Size of the kernel
    K = filter.shape[0]
    # Size of the output (full mode)
    Y = N + K - 1

    # Block size B, number of blocks X = N / B
    B = K
    while B < min(N, K) or not (((B & (B - 1)) == 0) and B > 0):
        B += 1

    # Number of blocks
    step = B
    B *= 2
    R = N % step
    X = N // step + 1 if R > 0 else N // step

    # Create LazyLinOp C that will be applied to all the blocks.
    # Use mpad to pad each block.
    if N > (2 * K):
        # If the signal size is greater than twice
        # the size of the kernel use overlap-based convolution
        F = fft(B) * np.sqrt(B)
        D = diag(F @ eye(B, K, k=0) @ filter, k=0)
        G = (F.H / B) @ D @ F
        # block_diag(*[G] * X) is equivalent to kron(eye, G)
        C = overlap_add(
            G.shape[0] * X, B, overlap=B - step) @ block_diag(
                *[G] * X) @ mpad(
                    step, X, n=B - step, add='after')
        if (X * step) > N:
            C = C @ eye(X * step, N, k=0)
    else:
        # If the signal size is not greater than twice
        # the size of the kernel use FFT-based convolution
        F = fft(Y) * np.sqrt(Y)
        D = diag(F @ eye(Y, K, k=0) @ filter, k=0)
        C = (F.H / Y) @ D @ F @ eye(Y, N, k=0)

    # Convolution mode
    if mode == 'valid' or mode == 'same':
        if mode == 'valid':
            # Compute full mode, valid mode returns
            # elements that do not depend on the padding.
            extract = max(N, K) - min(N, K) + 1
        else:
            # Keep the middle of full mode (centered)
            # and returns the same size that the signal size.
            extract = N
        start = (Y - extract) // 2
    else:
        extract, start = Y, 0
    # Use eye operator to extract
    return eye(extract, C.shape[0], k=start) @ C


def _circconvolve(N: int, filter,
                  backend: str = 'auto', disable_jit: int = 0,
                  workers: int = None):
    r"""Builds a :class:`.LazyLinOp` for the circular convolution.
    Do not call ``_circconvolve`` function outside of ``convolve`` function.

    Args:
        N: ``int``
            Length of the input.
        filter: ``np.ndarray``, ``cp.ndarray`` or ``torch.Tensor``
            Kernel to use for the convolution.
        backend: ``str``, optional

            - 'auto' use best implementation.
            - 'direct' direct computation using
              nested for loops (Numba implementation).
              Larger the batch is better the performances are.
            - 'fft' use SciPy encapsulation of the FFT.
        disable_jit: int, optional
            If 0 (default) enable Numba jit.
        workers:
            see convolve().
            Used only if ``backend == 'direct'`` and
            filter shape smaller than $\log2(N)$.
            Can be overridden by OMP_NUM_THREADS environment variable.

    Returns:
        :class:`.LazyLinOp`
    """

    def njit(*args, **kwargs):
        def dummy(f):
            return f
        return dummy

    def prange(n):
        return range(n)

    if backend == 'direct' and (
            is_cupy_array(filter) or is_torch_array(filter)):
        raise TypeError("backend='direct' does not work" +
                        " with CuPy arrays and torch tensors.")

    tmp = backend
    try:
        import numba as nb
        from numba import njit, prange
        nb.config.THREADING_LAYER = 'omp'
        nb.config.DISABLE_JIT = disable_jit
        if workers is not None and 'NUMBA_NUM_THREADS' not in environ.keys():
            nb.config.NUMBA_NUM_THREADS = workers
    except ImportError:
        if tmp == 'direct':
            warn("Did not find Numba, switch to fft.")
            tmp = 'fft'

    if tmp == 'direct' or (
            tmp == 'auto' and filter.shape[0] < np.log2(N)):
        def _matmat(kernel, x):
            if is_cupy_array(x) or is_torch_array(x):
                raise TypeError("backend='direct' does not work" +
                                " with CuPy arrays and torch tensors.")
            return _mm(kernel, x)

        def _rmatmat(kernel, x):
            if is_cupy_array(x) or is_torch_array(x):
                raise TypeError("backend='direct' does not work" +
                                " with CuPy arrays and torch tensors.")
            return _rmm(kernel, x)

        @njit(parallel=True, cache=True)
        def _mm(kernel, signal):
            K = kernel.shape[0]
            B = signal.shape[1]
            y = np.full((N, B), 0.0 * (kernel[0] * signal[0, 0]))
            # y[n] = sum(h[k] * s[n - k mod N], k, 0, K - 1)
            for i in prange(N):
                # Split the loop to avoid computation of ``np.mod``.
                for j in range(min(K, i + 1)):
                    # NumPy uses row-major format
                    for b in range(B):
                        y[i, b] += (
                            kernel[j] * signal[i - j, b]
                        )
                for j in range(i + 1, K, 1):
                    # NumPy uses row-major format
                    for b in range(B):
                        y[i, b] += (
                            kernel[j] * signal[N + i - j, b]
                        )
            return y

        @njit(parallel=True, cache=True)
        def _rmm(kernel, signal):
            K = kernel.shape[0]
            B = signal.shape[1]
            y = np.full((N, B), 0.0 * (kernel[0] * signal[0, 0]))
            # y[n] = sum(h[k] * s[k + n mod N], k, 0, K - 1)
            for i in prange(N):
                # Split the loop to avoid computation of ``np.mod``.
                for j in range(min(K, N - i)):
                    # NumPy uses row-major format
                    for b in range(B):
                        y[i, b] += (
                            np.conjugate(kernel[j]) * signal[i + j, b]
                        )
                for j in range(min(K, N - i), K, 1):
                    # NumPy uses row-major format
                    for b in range(B):
                        y[i, b] += (
                            np.conjugate(kernel[j]) * signal[i + j - N, b]
                        )
            return y

        return LazyLinOp(
            shape=(N, N),
            matmat=lambda x: _matmat(filter, x),
            rmatmat=lambda x: _rmatmat(filter, x)
        )
    else:
        # Zero-pad the kernel
        pfilter = padder(filter.shape[0],
                         (0, N - filter.shape[0]), mode='zero') @ filter
        # Op = FFT^-1 @ diag(FFT(kernel)) @ FFT
        DFT = fft(N) * np.sqrt(N)
        D = diag(DFT @ pfilter, k=0)
        return (DFT / N).H @ D @ DFT


def _dsconvolve(in1: int, in2: np.ndarray, mode: str = 'full',
                offset: int = 0, every: int = 2, disable_jit: int = 0):
    """Creates convolution plus down-sampling lazy linear operator.
    If input is a 2d array shape=(in1, batch), return convolution per column.
    offset (0 or 1) argument determines the first element to compute while
    every argument determines distance between two elements (1 or 2).
    The ouput of convolution followed by down-sampling C @ x is equivalent
    to :code:`scipy.signal.convolve(x, in2, mode)[offset::every]`.

    Args:
        in1: int
            Length of the input.
        in2: np.ndarray
            1d kernel to convolve with the signal, shape is (K, ).
        mode: str, optional

            - ``'full'`` computes convolution (input + padding).
            - ``'valid'`` computes 'full' mode and extract centered output
              that does not depend on the padding.
            - ``'same'`` computes 'full' mode and extract centered output
              that has the same shape that the input.
        offset: int, optional
            First element to keep (default is 0).
        every: int, optional
            Keep element every this number (default is 2).
        disable_jit: int, optional
            If 0 (default) enable Numba jit.

    Returns:
        LazyLinOp

    Examples:
        >>> import numpy as np
        >>> import scipy as sp
        >>> from lazylinop.signal.convolve import _dsconvolve
        >>> N = 1024
        >>> x = np.random.rand(N)
        >>> kernel = np.random.rand(32)
        >>> L = _dsconvolve(N, kernel, mode='same', offset=0, every=2)
        >>> c1 = L @ x
        >>> c2 = sp.signal.convolve(x, kernel, mode='same', method='auto')
        >>> np.allclose(c1, c2[0::2])
        True

    .. seealso::
        `SciPy convolve function <https://docs.scipy.org/doc/scipy/
        reference/generated/scipy.signal.convolve.html>`_,
        `SciPy correlate function <https://docs.scipy.org/doc/scipy/
        reference/generated/scipy.signal.correlate.html>`_.
    """

    if not is_numpy_array(in2):
        raise TypeError("dsconvolve expects a NumPy array.")

    def njit(*args, **kwargs):
        def dummy(f):
            return f
        return dummy

    def prange(n):
        return range(n)

    try:
        import numba as nb
        from numba import njit, prange
        nb.config.THREADING_LAYER = 'omp'
        T = nb.config.NUMBA_NUM_THREADS
        nb.config.DISABLE_JIT = disable_jit
    except ImportError:
        warn("Did not find Numba.")
        T = 1

    if mode not in ['full', 'valid', 'same']:
        raise ValueError("mode is either 'full' (default), 'valid' or 'same'.")

    # Check if length of the input has been passed to the function
    if type(in1) is not int:
        raise Exception("Length of the input are expected (int).")

    if in2.ndim != 1:
        raise ValueError("Number of dimensions of the kernel must be 1.")
    if in1 <= 1:
        raise Exception("Length of the input must be > 1.")

    K = in2.shape[0]

    if offset != 0 and offset != 1:
        raise ValueError('offset must be either 0 or 1.')
    if every != 1 and every != 2:
        raise ValueError('every must be either 1 or 2.')

    # Length of the output as a function of convolution mode
    dims = np.array([in1 + K - 1, max(in1, K) - min(in1, K) + 1,
                     in1, in1], dtype='int')
    imode = (
        0 * int(mode == 'full') +
        1 * int(mode == 'valid') +
        2 * int(mode == 'same')
    )
    start = (dims[0] - dims[imode]) // 2 + offset
    end = min(dims[0], start + dims[imode] - offset)
    L = int(np.ceil((dims[imode] - offset) / every))
    if L <= 0:
        raise Exception("mode, offset and every are incompatibles" +
                        " with kernel and signal sizes.")

    def _matmat(x, kernel):
        if not is_numpy_array(x):
            raise TypeError("dsconvolve expects a NumPy array.")
        return _mm(x, kernel)

    def _rmatmat(x, kernel):
        if not is_numpy_array(x):
            raise TypeError("dsconvolve expects a NumPy array.")
        return _rmm(x, kernel)

    @njit(parallel=True, cache=True)
    def _mm(x, kernel):
        # x is always 2d
        batch_size = x.shape[1]
        perT = int(np.ceil((dims[0] - start) / T))
        y = np.full((L, batch_size), 0.0 * (kernel[0] * x[0, 0]))
        for t in prange(T):
            for i in range(
                    start + t * perT,
                    min(end, start + (t + 1) * perT)):
                # Down-sampling
                if ((i - start) % every) == 0:
                    for j in range(max(0, i - in1 + 1), min(K, i + 1)):
                        # NumPy uses row-major format
                        for b in range(batch_size):
                            y[(i - start) // every,
                              b] += kernel[j] * x[i - j, b]
        return y

    @njit(parallel=True, cache=True)
    def _rmm(x, kernel):
        # x is always 2d
        batch_size = x.shape[1]
        rperT = int(np.ceil(dims[2] / T))
        a = 0 if imode == 0 and offset == 0 else 1
        y = np.full((dims[2], batch_size), 0.0 * (kernel[0] * x[0, 0]))
        for t in prange(T):
            for i in range(t * rperT, min(dims[2], (t + 1) * rperT)):
                if every == 2:
                    jstart = (i - a * start) - (i - a * start) // every
                elif every == 1:
                    jstart = i - a * start
                else:
                    pass
                for j in range(L):
                    if j < jstart:
                        continue
                    if every == 2:
                        k = (i - a * start) % 2 + (j - jstart) * every
                    elif every == 1:
                        k = j - jstart
                    else:
                        pass
                    if k < K:
                        # NumPy uses row-major format
                        for b in range(batch_size):
                            y[i, b] += np.conjugate(
                                kernel[k]) * x[j, b]
        return y

    return LazyLinOp(
        shape=(L, dims[2]),
        matmat=lambda x: _matmat(x, in2),
        rmatmat=lambda x: _rmatmat(x, in2))


def _torch_encapsulation(N: int, filter, mode: str = 'full'):
    r"""Builds a :class:`.LazyLinOp` for the convolution of
    a signal of size ``N`` with a kernel ``filter``.
    If shape of the input array is ``(N, batch)``,
    return convolution per column.
    Function uses encapsulation of ``torchaudio.functional.convolve``
    to compute convolution.
    Because torch uses batch first convention, the function
    transposes ``x`` before to compute ``y = L @ x.T``.
    The function returns the transposition ``y.T``.
    Do not call ``_torch_encapsulation`` function outside
    of ``convolve`` function.

    Args:
        N: ``int``
            Length of the input.
        filter: ``torch.Tensor``
            Kernel to convolve with the signal, shape is ``(K, )``.
        mode: ``str``, optional

            - 'full' computes convolution (input + padding).
            - 'valid' computes 'full' mode and extract centered output that
              does not depend on the padding.
            - 'same' computes 'full' mode and extract centered output that has
              the same shape that the input.

    Returns:
        :class:`.LazyLinOp`
    """

    if not is_torch_array(filter):
        raise TypeError("backend='torch' expects a torch tensor.")

    try:
        from torchaudio.functional import convolve as tconv
    except ImportError:
        raise RuntimeError("convolve with torch backend requires torchaudio package")

    from torch import flip as tflip

    K = filter.shape[0]

    def _matmat(x):
        # x is always 2d
        # ValueError: The operands must be the same dimension (got 2 and 1).
        # Batch first convention.
        return tconv(x.T, filter.reshape(1, -1), mode).T

    def _rmatmat(x):
        # x is always 2d
        rmode = {str(_dims(x.shape[0], K, 'full')): 'full',
                 str(_dims(x.shape[0], K, 'valid')): 'valid',
                 str(_dims(x.shape[0], K, 'same')): 'same'}
        # ValueError: The operands must be the same dimension (got 2 and 1).
        # Batch first convention.
        return tflip(tconv(
            tflip(x.T, (1,)),
            filter.reshape(1, -1).conj(), mode=rmode[str(N)]), (1,)).T

    return LazyLinOp(
        shape=(_dims(N, K, mode), _dims(N, K, 'same')),
        matmat=lambda x: _matmat(x),
        rmatmat=lambda x: _rmatmat(x))


# if __name__ == '__main__':
#     import doctest
#     doctest.testmod()
