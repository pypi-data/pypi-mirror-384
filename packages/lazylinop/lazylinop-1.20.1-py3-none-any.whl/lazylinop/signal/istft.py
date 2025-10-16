import numpy as np
from scipy.signal.windows import get_window
from lazylinop import LazyLinOp
from lazylinop.basicops import diag, eye, kron
from lazylinop.signal.stft import _diag
from lazylinop.signal.utils import overlap_add
import sys
from array_api_compat import (
    array_namespace, device, is_cupy_array, is_torch_array)
sys.setrecursionlimit(100000)


def _rfft_helper(N: int, n: int):

    def _matmat(x):
        xp = array_namespace(x)
        y = xp.real(
            xp.fft.rfftn(xp.real(x), axes=(0,),
                         s=(n,), norm='ortho'))
        y[1:(1 + (n - 1) // 2), :] *= 2.0
        return y / np.sqrt(n)

    def _rmatmat(x):
        xp = array_namespace(x)
        return xp.fft.irfftn(x, axes=(0,), s=(n,),
                             norm="ortho")[:N, :] / np.sqrt(n)

    n_out = n // 2 + 1 if (n % 2) == 0 else (n + 1) // 2
    return LazyLinOp(
        shape=(n_out, N),
        matmat=lambda x: _matmat(x),
        rmatmat=lambda x: _rmatmat(x),
        dtype='float64'
    )


def _fft_helper(N: int, n: int):

    def _matmat(x):
        xp = array_namespace(x)
        y = xp.fft.fftn(x, axes=(0,),
                        s=(n,), norm='ortho')
        return y / np.sqrt(n)

    def _rmatmat(x):
        xp = array_namespace(x)
        return xp.fft.ifftn(x, axes=(0,), s=(n,),
                            norm="ortho")[:N, :] / np.sqrt(n)

    return LazyLinOp(
        shape=(n, N),
        matmat=lambda x: _matmat(x),
        rmatmat=lambda x: _rmatmat(x),
        dtype='complex128'
    )


def istft(N: int, window=('hann', 256),
          hop: int = None,
          # fft_mode: str = 'onesided',
          fft_size: int = None):
    r"""
    Returns a LazyLinOp :class:`.LazyLinOp` ``iL`` for the inverse
    Short-Time-Fourier-Transform (iSTFT), so that if ``L`` is the
    LazyLinop of the STFT with the same arguments, ``iL @ L``
    is the identity.

    Shape of ``iL`` is $(N,~M)$ with $M\ge~N$.

    - :octicon:`report;1em;sd-text-info` ``N`` is the size of
      the input signal *of the STFT* LazyLinop, *not* of the iSTFT.
    - The order is not a typo since ``N`` is the input length of the associated
      STFT operator ``L``, which is of shape $(M,~N)$, and ``iL``
      is of the same shape as ``L.H``.

    Args:
        N: ``int``
            Length of the *output* array (i.e., length of the input
            array *of the associated STFT* :class:`LazyLinOp`, see above).
        window: NumPy array, CuPy array, torch tensor or ``(str, int)``, optional
            Window, either directly provided as an 1d (real or
            complex valued) array , or as a pair ``(name: str, win_size: int)``
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
            This can incur a loss of performance.
        hop: ``int``, optional
            The increment in sample location between two consecutives slices.
            ``None`` (default) corresponds to ``len(window) // 2``.
        .. fft_mode: ``str``, optional
            .. See :func:`stft` for more details.
        fft_size: ``int``, optional
            See :func:`stft` for more details.

    Returns:
        :class:`.LazyLinOp` ``iL`` for the inverse STFT

    Examples:
        >>> import lazylinop as lz
        >>> import numpy as np
        >>> N = 1024
        >>> x = np.random.randn(N)
        >>> L = lz.signal.stft(N)
        >>> y = L @ x
        >>> iL = lz.signal.istft(N)
        >>> np.allclose(x, iL @ y)
        True

    .. seealso::
        - `scipy.signal.stft <https://docs.scipy.org/doc/scipy/
          reference/generated/scipy.signal.stft.html>`_,
        - `scipy.signal.istft <https://docs.scipy.org/doc/scipy/
          reference/generated/scipy.signal.istft.html>`_,
        - `scipy.signal.ShortTimeFFT <https://docs.scipy.org/doc/
          scipy/reference/generated/
          scipy.signal.ShortTimeFFT.html#scipy.signal.ShortTimeFFT>`_,
        - `scipy.signal.get_window <https://docs.scipy.org/doc/
          scipy/reference/generated/scipy.signal.get_window.html>`_,
        - :func:`stft`.
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
         _is_cupy_array(window) or _is_torch_tensor(window):
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
    xp = array_namespace(sq_win)
    _pad = -win_size
    w_mid = win_size // 2 if (win_size % 2) == 0 else (win_size - 1) // 2
    for idx, _pad in enumerate(range(-w_mid, -w_mid - win_size - 1, -hop)):
        tmp = _pad - hop
        if (tmp + win_size) <= 0 or xp.all(sq_win[tmp:] == 0.0):
            break
    # Post-padding (see SciPy source core for more details).
    pad_ = 0
    nh = N // hop
    end = nh * hop - w_mid
    for idx, cum in enumerate(range(end, N + win_size, hop), start=nh):
        tmp = cum + hop
        if tmp >= N or xp.all(sq_win[:(N - tmp)] == 0.0):
            pad_ = cum + win_size - N
            idx += 1
            break
    M = abs(_pad) + N + pad_
    M = M + (-(M - win_size) % hop) % win_size
    # Number of slices.
    ns = 1 + (M - win_size) // hop

    # Compute dual window (see SciPy source core for more details).
    dual_win = xp.asarray(sq_win,
                          device=device(sq_win),
                          copy=True)
    for i in range(hop, win_size, hop):
        dual_win[i:] += sq_win[:(-i)]
        dual_win[:(-i)] += sq_win[i:]
    if not xp.all(dual_win > 1e-10):
        raise Exception("STFT is not invertible.")
    dual_win = xp.divide(win, dual_win)

    # Lazy linear operator for the FFT.
    tmp = win_size if fft_size is None else max(win_size, fft_size)
    F = _fft_helper(win_size, tmp)
    # if fft_mode == 'onesided':
    #     F = _rfft_helper(win_size, tmp)
    # elif fft_mode == 'twosided':
    #     F = _fft_helper(win_size, tmp)
    # else:
    #     raise ValueError("fft_mode must be either" +
    #                      " onesided or twosided.")
    # Lazy linear operator "one operation" per slice.
    E = eye(ns)
    # Apply iFFT per segment.
    K = kron(E, F.H)
    # Apply window per slice and scale.
    W = kron(E, _diag(dual_win))
    # Overlap and add.
    A = overlap_add(W.shape[0], size=win_size, overlap=win_size - hop)
    # iSTFT so far.
    L = A @ W @ K

    if N != L.shape[0]:
        # Remove zeros at both ends.
        B = eye(N, L.shape[0], k=abs(_pad))
        return B @ L
    else:
        return L


# if __name__ == '__main__':
#     import doctest
#     doctest.testmod()
