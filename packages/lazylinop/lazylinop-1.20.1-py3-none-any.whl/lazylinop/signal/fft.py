import numpy as np
import scipy as sp
from lazylinop import LazyLinOp
from array_api_compat import array_namespace, is_torch_array


def dft(N):
    r"""
    Returns a :class:`.LazyLinOp` ```L`` for the
    Discrete Fourier Transform (DFT).

    Shape of ``L`` is $(N,~N)$.

    ``L`` is orthonormal, and the :class:`.LazyLinOp`
    for the inverse DFT is ``L.H``.

    `SciPy FFT <https://docs.scipy.org/doc/scipy /reference/generated/scipy.
    fft.fft.html>`_ is used as underlying implementation.

    Of note, we provide an alias ``fft`` of the ``dft`` function.

    Args:
        N: ``int``
            Size of the input ($N > 0$).

    Returns:
        :class:`.LazyLinOp` DFT

    Examples:
        >>> from lazylinop.signal import dft as lz_dft
        >>> from scipy.fft import fft as sp_fft
        >>> from scipy.fft import ifft as sp_ifft
        >>> import numpy as np
        >>> N = 32
        >>> x = np.random.randn(N)
        >>> F = lz_dft(N)
        >>> y = F @ x
        >>> np.allclose(y, sp_fft(x, norm='ortho'))
        True
        >>> # easy inverse
        >>> x_ = F.H @ y
        >>> np.allclose(x_, x)
        True
        >>> # To mimick SciPy FFT norm='backward'
        >>> scale = np.sqrt(N)
        >>> y = scale * F @ x
        >>> np.allclose(y, sp_fft(x))
        True
        >>> x_ = F.H @ y / scale
        >>> np.allclose(x_, sp_ifft(y))
        True

    .. seealso::
        `scipy.fft.fft
        <https://docs.scipy.org/doc/scipy/reference/generated/scipy.fft.fft.html>`_,
        `scipy.fft.ifft
        <https://docs.scipy.org/doc/scipy/reference/generated/scipy.fft.ifft.html>`_,
        :func:`.rfft`
    """
    return _fft_helper(N, None, 'ortho', None)


def fft(N):
    return dft(N)


def _fft_helper(N, n: int = None,
                norm: str = 'ortho', workers: int = None):
    r"""
    Builds a Discrete Fourier Transform (DFT) :class:`.LazyLinOp`.

    Operator dimensions: $n \times N$ (or $N \times N$ if ``n=None``).

    `SciPy FFT <https://docs.scipy.org/doc/scipy /reference/generated/scipy.
    fft.fft.html>`_ is used as underlying implementation.

    To compute the inverse FFT, simply use ``fft(...).inv()``
    (see example below). It works for any ``norm``.

    Args:
        N: ``int``
            Size of the input ($N > 0$).

        n: ``int``, optional
            Length of the output / size of the DFT.

            - If ``n < N``, crop the input before DFT.

            - If ``n > N``, zero-pad the input before DFT.

            - If ``n=None`` or equivalent ``n=N``, no cropping/padding.

        norm: ``str``, optional
            Normalization mode:

                - ``norm='ortho'`` (default): normalization with scale factor
                  $1/\sqrt{n}$. if square ($N = n$) the operator is
                  unitary.

                  Inverse FFT is the adjoint.

                - ``norm=None``: no normalization. The operator is not
                  unitary.

                  Inverse FFT is the adjoint scaled by ``1/n``.

                - ``norm='1/n'``: the operator is scaled by $1/n$. The
                  operator is not unitary.

                  Inverse FFT is the adjoint scaled by ``n``.

            See below the table for conversion to SciPy ``norm`` argument.

        workers: ``int``, optional
            Number of workers (default is ``os.cpu_count()``) to use
            for parallel computation.

            See `scipy.fft.fft <https://docs.scipy.org/doc/scipy/
            reference/generated/scipy.fft.fft.html>`_
            for more details.

    Returns:
        :class:`.LazyLinOp` DFT

    Raises:
        ValueError
            norm must be either 'ortho', '1/n' or None.

    .. admonition:: Correspondence to `scipy.fft.fft <https://docs.scip
                    y.org/doc/scipy/reference/generated/scipy.fft.fft.
                    html>`_/`ifft
                    <https://docs.scipy.org/doc/scipy/reference/
                    generated/scipy.fft.ifft.html>`_ norm argument:
        :class: admonition note

        +------------------------------+-----------------------------+
        |                    **Forward operator**                    |
        +------------------------------+-----------------------------+
        |       Lazylinop              |        SciPy                |
        +------------------------------+-----------------------------+
        |    ``fft(N, norm=None) @ x`` | ``fft(x, norm='backward')`` |
        +------------------------------+-----------------------------+
        | ``fft(N, norm='ortho') @ x`` | ``fft(x, norm='ortho')``    |
        +------------------------------+-----------------------------+
        | ``fft(N, norm='1/n') @ x``   | ``fft(x, norm='forward')``  |
        +------------------------------+-----------------------------+

        +------------------------------+-----------------------------+
        |                    **Adjoint operator**                    |
        +------------------------------+-----------------------------+
        |       Lazylinop              |        SciPy                |
        +------------------------------+-----------------------------+
        | ``fft(N, norm=None).H @ y``  | ``ifft(y, norm='forward')`` |
        +------------------------------+-----------------------------+
        |``fft(N, norm='ortho').H @ y``| ``ifft(y, norm='ortho')``   |
        +------------------------------+-----------------------------+
        |``fft(N, norm='1/n').H  @ y`` | ``ifft(y, norm='backward')``|
        +------------------------------+-----------------------------+


    .. seealso::
        `scipy.fft.fft
        <https://docs.scipy.org/doc/scipy/reference/generated/scipy.fft.fft.html>`_,
        `scipy.fft.ifft
        <https://docs.scipy.org/doc/scipy/reference/generated/scipy.fft.ifft.html>`_,
        :func:`.rfft`
    """
    n, N = _check_n(n, N)
    return _fft(N, n, norm, workers, n)


def _fft(N, n: int = None,
         norm: str = None, workers: int = None, L: int = None):

    # n is input size
    # L is output size

    norm = _check_norm(norm)
    sp_norm, sp_norm_inv = _scipy_norm(norm)

    def _matmat(x):
        # x is always 2d
        xp = array_namespace(x)
        return xp.fft.fft(x, axis=0, n=n, norm=sp_norm)

    def _rmatmat(x):
        # x is always 2d
        xp = array_namespace(x)
        y = xp.fft.ifft(x, axis=0, n=n, norm=sp_norm_inv)
        # len(y) must be N to match LazyLinOp shape
        if n == N:
            return y
        elif n < N:
            # crop case
            if is_torch_array(y):
                from torch.nn.functional import pad
                return pad(y, (0, 0, 0, N - n), mode='constant', value=0)
            else:
                return xp.pad(y, ((0, N - n), (0, 0)))
        else:
            # padded case
            # n > N
            return y[:N]

    L = LazyLinOpFFT(
        shape=(L, N),
        matmat=lambda x: _matmat(x),
        rmatmat=lambda x: _rmatmat(x))
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


_valid_norms = ['ortho', None, '1/n']


def _check_norm(norm):
    if norm not in _valid_norms:
        raise ValueError("norm must be either 'ortho'," +
                         " '1/n' or None.")
    return norm


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
