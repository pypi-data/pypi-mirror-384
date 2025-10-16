import numpy as np
import scipy as sp
from scipy.signal.windows import get_window
from lazylinop import LazyLinOp
from lazylinop.basicops import diag, eye, kron
from lazylinop.signal import dft
from lazylinop.signal.utils import chunk
import sys
from array_api_compat import (
    array_namespace, device, is_numpy_array,
    is_cupy_array, is_torch_array)
try:
    from torch.nn.functional import pad as torch_pad
except:
    torch_pad = None
from warnings import warn
from os import cpu_count
sys.setrecursionlimit(100000)


_valid_norms = ['ortho', None, '1/n']


def rfft(N, n: int = None,
         norm: str = 'ortho', workers: int = None, fft_output=True):
    r"""
    Builds a Discrete Fourier Transform (DFT) :class:`.LazyLinOp` for real
    input.

    Operator dimensions:
        - ``fft_output=True``: $n \times N$.
        - ``fft_output=False``: $L \times N$ with $L = (n + 1) / 2$ if $n$ is
          odd, $L = (n / 2) + 1$ otherwise (take $n = N$ if $n$ is ``None``).

    `SciPy real FFT <https://docs.scipy.org/doc/scipy /reference/generated/
    scipy.fft.rfft.html>`_ is used as underlying implementation.

    To compute the inverse real FFT, simply use ``rfft(...).inv()``
    (see example below). It works for any ``norm``.

    Args:
        N: ``int``
            Size of the input ($N > 0$).
        n: ``int``, optional
            Crop/zero-pad the input to get a signal of size ``n``
            to apply the DFT on. ``None`` (default) means ``n=N``.
        norm: ``str``, optional
            Normalization mode:
            ``'ortho'`` (default), ``None`` or ``'1/n'``.
            See :func:`.fft` for more details.
        workers: ``int``, optional
            Number of workers (default is ``os.cpu_count()``) to use
            for parallel computation.

            See `scipy.fft.rfft <https://docs.scipy.org/doc/scipy/
            reference/generated/scipy.fft.rfft.html>`_
            for more details.
        fft_output: ``bool``, optional
            - ``True`` to get same output as fft (default).
            - ``False`` to get truncated output (faster but :func:`.check`
              fails on forward - adjoint operators consistency).

    Returns:
        :class:`.LazyLinOp` real DFT

    Example:
        >>> import lazylinop as lz
        >>> import numpy as np
        >>> import scipy as sp
        >>> F = lz.signal.rfft(32)
        >>> x = np.random.rand(32)
        >>> np.allclose(F @ x, sp.fft.fft(x, norm='ortho'))
        True
        >>> # easy inverse
        >>> F = lz.signal.rfft(32, norm=None)
        >>> y = F @ x
        >>> x_ = F.inv() @ y # inverse works for any norm
        >>> np.allclose(x_, x)
        True

    .. seealso::
        `scipy.fft.rfft
        <https://docs.scipy.org/doc/scipy/reference/generated/scipy.fft.rfft.html>`_,
        `scipy.fft.ifft
        <https://docs.scipy.org/doc/scipy/reference/generated/scipy.fft.ifft.html>`_,
        :func:`.fft`.
    """
    n_, N = _check_n(n, N)
    # L: size of output when real input
    nr = (n_ + 1) // 2 if (n_ & 1) else (n_ // 2) + 1

    def fft_rfft(x, axis, n, norm, workers):
        xp = array_namespace(x)
        if is_numpy_array(x):
            with sp.fft.set_workers(
                    cpu_count() if workers is None else workers):
                y = sp.fft.rfft(x.real, axis=axis, n=n, norm=norm)
        else:
            y = xp.fft.rfft(x.real, axis=axis, n=n, norm=norm)
        # assert nr == y.shape[0]
        if fft_output:
            # apply symmetry to build full fft output
            if n & 1:
                # n is odd
                if is_torch_array(y):
                    fft_y = xp.vstack((y, xp.flip(y[1:], axis=0).conj()))
                else:
                    fft_y = xp.vstack((y, y[:0:-1].conj()))
            else:
                # n is even
                if is_torch_array(y):
                    fft_y = xp.vstack((y, xp.flip(y[1:(nr - 1)], axis=0).conj()))
                else:
                    fft_y = xp.vstack((y, y[nr-2:0:-1].conj()))
            # assert fft_y.shape[0] == n
            return fft_y
        else:
            return y

    def ifft_irfft(y, axis, n, norm, workers):
        yp = array_namespace(y)
        # x = yp.fft.irfft(y[:nr], axis=axis, n=nr, norm=norm, workers=workers)
        # can't get irfft work properly
        if fft_output:
            if is_numpy_array(y):
                with sp.fft.set_workers(
                        cpu_count() if workers is None else workers):
                    x = sp.fft.ifft(y, axis=axis, n=n, norm=norm)
            else:
                x = yp.fft.ifft(y, axis=axis, n=n, norm=norm)
        else:
            if is_numpy_array(y):
                with sp.fft.set_workers(
                        cpu_count() if workers is None else workers):
                    x = sp.fft.irfft(y, axis=axis, n=n, norm=norm, workers=workers)
            else:
                x = yp.fft.irfft(y, axis=axis, n=n, norm=norm)
        return x

    return _fft(fft_rfft, ifft_irfft, N, n_, norm, workers, n_ if fft_output
                else nr, 'complex')


def _fft(xp_fft, xp_ifft, N, n: int = None,
         norm: str = None, workers: int = None, L: int = None,
         dtype: str = None):

    # n is input size
    # L is output size

    if norm not in _valid_norms:
        raise ValueError("norm must be either 'ortho'," +
                         " '1/n' or None.")
    sp_norm, sp_norm_inv = _scipy_norm(norm)

    def _matmat(x):
        # x is always 2d
        return xp_fft(x, axis=0, n=n,
                      norm=sp_norm, workers=workers)

    def _rmatmat(x):
        # x is always 2d
        y = xp_ifft(x, axis=0, n=n,
                    norm=sp_norm_inv, workers=workers)
        # len(y) must be N to match LazyLinOp shape
        if n == N:
            return y
        elif n < N:
            # crop case
            if is_torch_array(y):
                return torch_pad(
                    y, (0, 0, 0, N - n), mode='constant', value=0.0)
            else:
                xp = array_namespace(x)
                return xp.pad(y, ((0, N - n), (0, 0)))
        else:
            # padded case
            # n > N
            return y[:N]

    L = LazyLinOpFFT(
        shape=(L, N),
        matmat=lambda x: _matmat(x),
        rmatmat=lambda x: _rmatmat(x),
        dtype=dtype
    )
    L.norm = norm
    L.n = n
    return L


class LazyLinOpFFT(LazyLinOp):

    def inv(lz_fft):
        norm = lz_fft.norm
        n = lz_fft.n
        if norm == 'ortho':
            return lz_fft.H
        elif norm == '1/n':
            return n * lz_fft.H
        else:
            assert norm is None
            return 1/n * lz_fft.H


def _check_n(n, N):
    if isinstance(N, (int, float)):
        N = int(N)
    else:
        raise ValueError('N must be a number (int)')
    if n is None:
        n = N
    elif isinstance(n, (int, float)):
        n = int(n)
    else:
        raise ValueError('n must be a number (int)')
    return n, N


def _scipy_norm(lz_norm):
    # determine *fft, i*fft norm arguments
    # form lz norm argument
    if lz_norm is None:
        sp_norm = 'backward'
        sp_norm_inv = 'forward'
    elif lz_norm == '1/n':
        sp_norm = 'forward'
        sp_norm_inv = 'backward'
    else:  # lz_norm is 'ortho'
        assert lz_norm == 'ortho'
        sp_norm = sp_norm_inv = 'ortho'
    return sp_norm, sp_norm_inv


def _rfft_helper(N: int, n: int):

    M = n // 2 + 1 if (n % 2) == 0 else (n + 1) // 2

    def _matmat(x):
        xp = array_namespace(x)
        return xp.fft.rfftn(x, axes=(0,),
                            s=(n,), norm="backward")

    def _rmatmat(x):
        xp = array_namespace(x)
        return np.multiply(
            n, xp.fft.ifftn(x, axes=(0,),
                            s=(n,), norm="backward"))[:N, :]

    return LazyLinOp(
        shape=(M, N),
        matmat=lambda x: _matmat(x),
        rmatmat=lambda x: _rmatmat(x),
        dtype='float64'
    )


def _fft_helper(N: int, n: int):

    def _matmat(x):
        xp = array_namespace(x)
        return xp.fft.fftn(x, axes=(0,),
                           s=(n,), norm="backward")

    def _rmatmat(x):
        xp = array_namespace(x)
        return xp.multiply(
            n, xp.fft.ifftn(x, axes=(0,),
                            s=(n,), norm="backward"))[:N, :]

    return LazyLinOp(
        shape=(n, N),
        matmat=lambda x: _matmat(x),
        rmatmat=lambda x: _rmatmat(x),
        dtype='complex128'
    )


def stft(N: int, window=('hann', 256),
         hop: int = None,
         # fft_mode: str = 'twosided',
         fft_size: int = None):
    r"""Returns a :class:`.LazyLinOp` for the
    Short-Time-Fourier-Transform (STFT), so that ``L @ x``
    is equivalent to:

    .. code-block:: python

        import scipy as sp
        win_size = window[1]
        STFT = sp.signal.ShortTimeFFT(
            win=sp.signal.windows.get_window(window, win_size),
            hop=hop,
            fs=1.0,
            fft_mode='twosided',
            fft_size=None,
            phase_shift=None
        )
        STFT.stft(x)

    The STFT computes and concatenates Fourier transforms of
    windowed signal slices where consecutive windows
    are slided by ``hop`` samples.

    :octicon:`info;1em;sd-text-success` The implementation uses
    pre-built :class:`Lazylinop` operators to build the STFT operator.

    After removing some details the code looks like:

    .. code-block:: python3

        # For a 1d real valued array
        win = sp.signal.get_window(win_name, win_size)
        # Number of chunks.
        n = 1 + (N - win_size) // hop
        # Lazy linear operator that extracts and
        # concatenates chunks from a signal of length N.
        G = chunk(N, win_size, hop)
        # Lazy operator that multiplies a (batch of)
        # chunk(s) of length win_len by the window.
        W = diag(win)
        # Lazy operator computing the DFT of a (batch of)
        # windowed chunk(s) of length win_len with appropriate padding.
        FW = dft(fft_size)[:win_size, :] @ W

    and using the `mixed Kronecker product property <https://en.wikipedia.org/
    wiki/Kronecker_product>`_ $(I^T\otimes A)\mathtt{vec}(X)=vec(AXI)=vec(AX)$:

    .. code-block:: python3

        # Final lazy operator that extract chunks, applies F on each chunk.
        L = kron(eye(n), FW) @ G

    Shape of ``L`` is $(M,~N)$. In general $M\ge~N$.

    Args:
        N: ``int``
            Length of the input array.
        window: NumPy/CuPy array, torch tensor or ``(str, int)``, optional
            Window, either directly provided as an 1d (real or
            complex valued) array, or as a pair ``(name: str, win_size: int)``
            which is equivalent to use
            ``window=scipy.signal.get_window(name, length)``.
            Default is ``('hann', 256)``.
            See `scipy.signal.get_window <https://docs.scipy.org/
            doc/scipy/reference/generated/scipy.signal.get_window.html>`_
            for a list of available windows.

            :octicon:`alert-fill;1em;sd-text-danger` Be aware that if ``window``
            does not have the same namespace
            ``xp = array_api_compat.array_namespace(x)`` than ``x``,
            computation of ``L @ x`` uses an extra
            ``xp.asarray(window, device=array_api_compat.device(x), copy=True)``.
            This incur a loss of performance.

        hop: ``int``, optional
            The increment in sample location between two consecutives slices.
            ``None`` (default) corresponds to ``len(window) // 2``.
        .. fft_mode: ``str``, optional
        ..
            .. - ``'onesided'`` computes only non-negative frequency values.
            ..   This is the default value. It does not work for complex-valued
            ..   input arrays and/or complex-valued windows.
            .. - ``'twosided'`` computes all the ``fft_size`` frequency values.
        fft_size: ``int``, optional
            Size of the FFT, if zero-padding is required.
            Default value is ``None``.
            It corresponds to ``fft_size=len(window)``.

    Returns:
        :class:`.LazyLinOp` L for the STFT

    Examples:
        >>> import lazylinop as lz
        >>> import numpy as np
        >>> import scipy as sp
        >>> x = np.random.randn(1024)
        >>> L = lz.signal.stft(x.shape[0])
        >>> win = sp.signal.windows.get_window('hann', 256)
        >>> STFT = sp.signal.ShortTimeFFT(win=win, hop=128, fs=1.0, fft_mode="twosided", phase_shift=None)
        >>> np.allclose(STFT.stft(x).ravel(order='F'), L @ x)
        True

    .. seealso::
        - `scipy.signal.stft <https://docs.scipy.org/doc/scipy/
          reference/generated/scipy.signal.stft.html>`_,
        - `scipy.signal.ShortTimeFFT <https://docs.scipy.org/doc/
          scipy/reference/generated/
          scipy.signal.ShortTimeFFT.html#scipy.signal.ShortTimeFFT>`_,
        - `scipy.signal.get_window <https://docs.scipy.org/doc/
          scipy/reference/generated/scipy.signal.get_window.html>`_,
        - :func:`istft`.
    """
    msg = (
        "window must be either a NumPy/CuPy array," +
        " torch tensor or a tuple (str, int)."
    )
    if isinstance(window, tuple):
        if not (isinstance(window[0], str) and isinstance(window[1], int)):
            raise Exception(msg)
        win_size = window[1]
        win = get_window(window[0], window[1], fftbins=True)
    elif isinstance(window, np.ndarray) or \
         is_cupy_array(window) or is_torch_array(window):
        win_size = window.shape[0]
        win = window
    else:
        raise Exception(msg)
    if win_size < 1:
        raise ValueError("win_size expects value greater than 0.")
    if win_size > N:
        raise ValueError(f"win_size={win_size} is greater than"
                         + f" input length N={N}.")

    if hop is None:
        hop = win_size // 2
    if hop == 0:
        raise ValueError("hop must be > 0.")
    if hop > win_size:
        raise ValueError("hop must be <= win_size.")

    if fft_size is not None and fft_size < win_size:
        raise ValueError("fft_size must be >= window size.")

    # Boundary and then zero-padding.
    sq_win = win.real ** 2 + win.imag ** 2
    # Pre-padding (see SciPy source core for more details).
    _pad = -win_size
    w_mid = win_size // 2 if (win_size % 2) == 0 else (win_size - 1) // 2
    for idx, _pad in enumerate(range(-w_mid, -w_mid - win_size - 1, -hop)):
        tmp = _pad - hop
        if (tmp + win_size) <= 0 or np.all(sq_win[tmp:] == 0.0):
            break
    # Post-padding (see SciPy source core for more details).
    pad_ = 0
    nh = N // hop
    end = nh * hop - w_mid
    for idx, cum in enumerate(range(end, N + win_size, hop), start=nh):
        tmp = cum + hop
        if tmp >= N or np.all(sq_win[:(N - tmp)] == 0.0):
            pad_ = cum + win_size - N
            idx += 1
            break
    P = abs(_pad) + N + pad_
    Q = P + (-(P - win_size) % hop) % win_size

    # Number of slices.
    ns = 1 + (Q - win_size) // hop

    # Lazy linear operator for the FFT (default fft mode is onesided).
    tmp = win_size if fft_size is None else max(fft_size, win_size)
    F = _fft_helper(win_size, tmp)
    # if fft_mode == 'twosided':
    #     F = _fft_helper(win_size, tmp)
    # elif fft_mode == 'onesided':
    #     F = _rfft_helper(win_size, tmp)
    # else:
    #     raise ValueError("fft_mode must be either" +
    #                      " onesided or twosided.")
    # Lazy linear operator "scatter and gather the windows".
    G = chunk(Q, win_size, hop)
    # Apply FFT per segment.
    FW = F @ _diag(win.conj())
    S = kron(eye(ns), FW)
    # STFT :class:`.LazyLinOp` so far.
    L = S @ G
    # We first apply boundary and then zero-pad,
    # see scipy.signal.stft documentation for more details.
    if win_size == 1:
        R = None
    else:
        R = eye(P, N, k=-abs(_pad))
    if Q > P:
        if R is None:
            R = eye(Q, P)
        else:
            R = eye(Q, P) @ R
    # Return complete operator.
    return L @ R


def _diag(window):
    """
    Use an intermediate function _diag because window
    need to know if x is NumPy/CuPy array or torch tensor.
    """

    windows = {'matmat': {}, 'rmatmat': {}}

    def _matmat(x, window, adjoint: bool = False):
        xp = array_namespace(x)
        mul = 'rmatmat'  if adjoint else 'matmat'
        # Get pre-computed window or compute it
        # according to x.
        if 'numpy' in str(xp):
            lib = 'numpy'
        elif 'cupy' in str(xp):
            lib = 'cupy'
        elif 'torch' in str(xp):
            lib = 'torch'
        if lib not in windows[mul].keys():
            windows[mul][lib] = {}
        # Get dtype and device of x.
        _dtype = x.dtype
        str_t = str(_dtype)
        if str_t not in windows[mul][lib].keys():
            windows[mul][lib][str_t] = {}
        _device = device(x)
        str_d = str(_device)
        # Cast window if needed.
        if str_d not in windows[mul][lib][str_t].keys():
            windows[mul][lib][str_t][str_d] = None
        if windows[mul][lib][str_t][str_d] is None:
            windows[mul][lib][str_t][str_d] = xp.asarray(
                window.tolist(), copy=True,
                dtype=x.dtype, device=_device)
        return windows[mul][
            lib][str_t][str_d].reshape(-1, 1) * x

    return LazyLinOp(
        shape=(window.shape[0], window.shape[0]),
        matmat=lambda x: _matmat(x, window),
        rmatmat=lambda x: _matmat(x, window.conj(), True))


# if __name__ == '__main__':
#     import doctest
#     doctest.testmod()
