from lazylinop import LazyLinOp
from lazylinop.basicops import anti_eye, diag, eye, kron
from lazylinop.basicops import roll, vstack
from lazylinop.signal import dct, mdct
from lazylinop.signal.mdct import _cupy_kbd, _torch_kbd
from lazylinop.signal.utils import overlap_add
from math import sqrt
import sys
import array_api_compat
from array_api_compat import is_cupy_array, is_torch_array
sys.setrecursionlimit(100000)


def _helper(N, backend: str = 'scipy', method: int = 2):

    if (N % 4) != 0:
        raise Exception("N must be a multiple of 4.")

    H = N // 2
    Q = H // 2

    if method == 1:
        return mdct(N, backend=backend).T
    elif method == 2:
        # Compute dct4 and split the result.
        return vstack((
            vstack((
                eye(Q, H, k=Q),
                -anti_eye(Q) @ eye(Q, H, k=Q))),
            vstack((
                -anti_eye(Q) @ eye(Q, H),
                -eye(Q, H)))
        )) @ dct(H, type=4, backend=backend)
    else:
        # Method 3 (see Ref [1]):
        return sqrt(2.0) * (
            roll(N, shift=-(H // 2)) @
            vstack((eye(H), -anti_eye(H))) @
            dct(H, type=4, backend=backend))


def imdct(N, window=('vorbis', 128),
          backend: str = 'scipy'):
    r"""
    Returns a :class:`.LazyLinOp` ``iL`` for the
    inverse Modified Direct Cosine Transform (iMDCT).

    Shape of ``iL`` is $(P,~M)$ with $M=n\frac{W}{2}$ and
    $P=(n-1)\frac{W}{2}+W$.

    $n$ is the number of chunks and $W$ is the window size.

    :octicon:`report;1em;sd-text-info` ``N`` is the size of
    the input signal *of the MDCT* LazyLinop, *not* of the iMDCT.

    Our implementation matches the one from TensorFlow,
    ``iL @ y`` where ``iL = imdct(N, window=('vorbis', N))``
    is equivalent to:

    .. code-block:: python3

       import tensorflow as tf
       tf.signal.inverse_mdct(y,
                              window_fn=tf.signal.vorbis_window,
                              norm='ortho')

    .. For perfect reconstruction, user must zero-pads
    .. ``x_ = np.pad(x, pad_width=(N // 2, N // 2))`` the input ``x``
    .. with ``N // 2`` zeros on both size before to apply MDCT.
    .. If ``L = mdct(x_.shape[0])`` denotes the MDCT operator
    .. and ``iL = imdct(x_.shape[0])`` denotes the inverse MDCT then
    .. ``(iL @ y)[(N // 2):(N // 2 + N)] = x`` where ``y = L @ x_``.

    The operator ``iL`` is rectangular and is not right invertible.
    It is however left-invertible as ``iL.T @ iL``.
    Thus, ``iL.T`` can be used as a left-inverse.

    After removing some details the code looks like:

    .. code-block:: python3

        # Consecutive windows are slided by hop samples.
        hop = win_size // 2
        # Number of chunks.
        n = 1 + (N - win_size) // hop

        if N == win_size:
            return diag(win) @ _helper(N, backend)
        else:
            # Apply inverse MDCT per chunk followed by windowing.
            K = kron(eye(n), diag(win) @ _helper(win_size, backend))
            # Overlap and add.
            A = overlap_add(K.shape[0], size=win_size, overlap=win_size - hop)
            # Restrict to get the output of length N.
            iL = eye(N, A.shape[0]) @ A @ K

    where ``_helper(...)`` encapsulates underlying implementation
    using DCT of type IV (see Ref [1] for more details).

    The function provides two backends: SciPy and Lazylinop for
    the underlying computation of the DCT of type IV.

    Args:
        N: ``int``
            Length of the *output* array (see above).
        window: ``(str, int)`` or ``(str, int, float)``, optional
            Window, a tuple ``(name: str, win_size: int)``
            or ``(name: str, win_size: int, beta: float)``.
            Window size must be a mutliple of 4.
            Default is ``('vorbis', 128)``.
            ``beta`` has no effect excepts
            for ``'kaiser_bessel_derived'`` window.
            Possible windows are:

            - ``'None'`` corresponds to a rectangular window
              with a scale $\frac{1}{\sqrt{2}}$.
            - ``'kaiser_bessel_derived'``
              see `scipy.signal.window.kaiser_bessel_derived <https://
              docs.scipy.org/doc/scipy/reference/generated/
              scipy.signal.windows.kaiser_bessel_derived.html>`_
              for more details.
            - ``'vorbis'`` (default) or ``'sin'``
              see `<https://en.wikipedia.org/wiki/
              Modified_discrete_cosine_transform>`_ for more details.
        backend: str, optional
            - ``'scipy'`` (default) uses ``scipy.fft.dct``
              encapsulation for the underlying computation
              of the DCT of type IV.
              ``backend='scipy'`` does not work with CuPy input array
              because ``cupyx.signal.fft.dct`` only implements
              type II and III.
            - ``'lazylinop'`` uses pre-built Lazylinop operators
              (Lazylinop :func:`.dct`, :func:`eye`, :func:`kron`,
              :func:`.vstack` etc.) to build the pipeline
              that will compute the MDCT and the underlying
              DCT of type IV.

    Returns:
        :class:`.LazyLinOp`

    Example:
        >>> from lazylinop.signal import mdct, imdct
        >>> import numpy as np
        >>> N = 64
        >>> x = np.random.randn(N)
        >>> # MDCT with a rectangular window
        >>> # of size equal to the size of the input.
        >>> L = imdct(N, window=('None', N))
        >>> L.shape[0] == 64
        True
        >>> L.shape[1] == 32
        True

    References:
        - [1] Xuancheng Shao, Steven G. Johnson, Type-IV DCT, DST, and MDCT
          algorithms with reduced numbers of arithmetic operations,
          Signal Processing, Volume 88, Issue 6, 2008, Pages 1313-1326,
          ISSN 0165-1684, https://doi.org/10.1016/j.sigpro.2007.11.024.

    .. seealso::
        - `MDCT (Wikipedia) <https://en.wikipedia.org/wiki/
          Modified_discrete_cosine_transform>`_,
        - `Type-IV DCT, DST, and MDCT algorithms with reduced
          numbers of arithmetic operations <https://www.sciencedirect.com/
          science/article/pii/S0165168407003829?via%3Dihub>`_,
        - `SMAGT/MDCT <https://github.com/smagt/mdct>`_,
        - `MDCT.jl <https://github.com/stevengj/
          MDCT.jl/blob/master/src/MDCT.jl>`_,
        - `Nils Werner <https://github.com/nils-werner/mdct/blob/
          master/mdct/fast/transforms.py>`_,
        - `TensorFlow iMDCT <https://www.tensorflow.org/api_docs/
          python/tf/signal/inverse_mdct>`_,
        - :func:`.dct`,
        - :func:`.mdct`.
    """

    windows = {}

    msg = "window must be a tuple (str, int) or (str, int, float)."
    msg_win = (
        "window name must be either" +
        " kaiser_bessel_derived, vorbis, sin or None."
    )
    if isinstance(window, tuple):
        if not (isinstance(window[0], str) and
                isinstance(window[1], int)):
            raise Exception(msg)
        if window[0] == 'kaiser_bessel_derived':
            if not (len(window) == 3 and isinstance(window[2], float)):
                raise Exception(msg)
        elif (window[0] == 'vorbis' or window[0] == 'sin' or
              window[0] == 'None'):
            pass
        else:
            raise ValueError(msg_win)
        win_size = window[1]
    else:
        raise Exception(msg)

    if win_size < 1:
        raise ValueError("win_size expects value greater than 0.")
    if win_size > N:
        raise ValueError(f"win_size={win_size} is greater than"
                         + f" input length N={N}.")
    if (win_size % 4) != 0:
        raise ValueError(f"win_size={win_size} is not a multiple of 4.")

    # Consecutive windows are slided by hop samples.
    hop = win_size // 2
    # Number of chunks.
    n = 1 + (N - win_size) // hop
    # Size of the input.
    size_in = (1 + (N - win_size) // hop) * hop
    # Size of the output.
    size_out = (n - 1) * hop + win_size
    H = _helper(win_size, backend, method=2)
    E = eye(n)
    # Overlap and add.
    A = overlap_add(n * win_size, size=win_size, overlap=win_size - hop)

    def _matmat(x, adjoint):

        xp = array_api_compat.array_namespace(x)
        # Get pre-computed window.
        if 'numpy' in str(xp):
            lib = 'numpy'
        elif 'cupy' in str(xp):
            lib = 'cupy'
        elif 'torch' in str(xp):
            lib = 'torch'
        if lib not in windows.keys():
            windows[lib] = {}
        _dtype = x.dtype
        _device = array_api_compat.device(x)
        if str(_dtype) in windows[lib].keys():
            win = windows[lib][str(_dtype)]
        else:
            msg = "window must be a tuple (str, int) or (str, int, float)."
            if window[0] == 'kaiser_bessel_derived':
                if not (len(window) == 3 and isinstance(window[2], float)):
                    raise Exception(msg)
                if lib == 'numpy':
                    from scipy.signal.windows import \
                        kaiser_bessel_derived as kbd
                    windows[lib][str(_dtype)] = kbd(
                        window[1], beta=window[2]).astype(_dtype)
                elif lib == 'cupy':
                    try:
                        windows[lib][str(_dtype)] = _cupy_kbd(
                            window[1], beta=window[2],
                            dtype=_dtype, device=_device)
                    except:
                        pass
                elif lib == 'torch':
                    try:
                        windows[lib][str(_dtype)] = _torch_kbd(
                            window[1], beta=window[2],
                            dtype=_dtype, device=_device)
                    except:
                        pass
            elif window[0] == 'vorbis':
                windows[lib][str(_dtype)] = xp.sin(
                    0.5 * xp.pi * xp.sin(
                        (xp.pi / window[1]) *
                        (xp.arange(
                            window[1],
                            dtype=_dtype, device=_device) + 0.5)) ** 2)
            elif window[0] == 'sin':
                windows[lib][str(_dtype)] = xp.sin(
                    (xp.pi / window[1]) *
                    (xp.arange(window[1], dtype=_dtype,
                               device=_device) + 0.5))
            elif window[0] == 'None':
                windows[lib][str(_dtype)] = xp.sqrt(xp.full(
                    window[1], 0.5, dtype=_dtype, device=_device))
            else:
                raise ValueError(msg_win)
        win = windows[lib][str(_dtype)]
        win_size = array_api_compat.size(win)

        if N == win_size:
            L = diag(win) @ H
        else:
            # Apply inverse MDCT per chunk followed by windowing.
            K = kron(E, diag(win) @ H)
            # Overlap and add.
            L = A @ K
            if A.shape[0] != N:
                # Restrict to get the output of length N.
                L = eye(N, A.shape[0]) @ L

        return L.H @ x if adjoint else L @ x

    L = LazyLinOp(
        shape=(size_out, size_in),
        matmat=lambda x: _matmat(x, False),
        rmatmat=lambda x: _matmat(x, True))
    L.windows = windows

    return L
