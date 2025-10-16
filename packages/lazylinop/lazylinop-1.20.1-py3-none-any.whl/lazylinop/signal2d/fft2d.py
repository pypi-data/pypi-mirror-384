from lazylinop import LazyLinOp
from lazylinop.signal2d import colvec, uncolvec
from scipy.fft import fft2, ifft2
import sys
import array_api_compat

sys.setrecursionlimit(100000)


def fft2d(in_shape: tuple):
    """
    Alias for ``dft2d(in_shape: tuple)`` function.
    """
    return dft2d(in_shape)


def dft2d(in_shape: tuple):
    """
    Returns a :class:`.LazyLinOp` ``L`` for the orthogonal
    2D Discrete-Fourier-Transform (DFT) of a 2D signal
    of shape ``in_shape = (M, N)`` (provided in flattened version).

    Shape of ``L`` is $(MN,~MN)$ with $(M,~N)=\text{in_shape}$.
    After applying the operator as ``y = L @ colvec(X)``, a 2D
    output can be obtained via ``uncolvec(y, out_shape)``
    with ``out_shape = in_shape``. ``L`` is orthogonal.

    Args:
        in_shape: ``tuple``
            Shape of the 2d input array $(M,~N)$.

    Returns:
        :class:`.LazyLinOp`

    Example:
        >>> from lazylinop.signal2d import dft2d, colvec, uncolvec
        >>> import numpy as np
        >>> import scipy as sp
        >>> # Check the 2d DFT
        >>> N = 32
        >>> F = dft2d((N, N))
        >>> x = np.random.rand(N, N)
        >>> ly = F @ colvec(x)
        >>> sy = sp.fft.fft2(x, norm='ortho')
        >>> np.allclose(uncolvec(ly, (N, N)), sy)
        True
        >>> # Check the inverse DFT
        >>> lx_ = F.H @ ly
        >>> sx_ = sp.fft.ifft2(sy, norm='ortho')
        >>> np.allclose(lx_, colvec(sx_))
        True
        >>> # Orthogonal DFT
        >>> A = F.toarray()
        >>> H = F.H.toarray()
        >>> np.allclose(A @ H, np.eye(N ** 2))
        True

    .. seealso::
        - `SciPy fft2 <https://docs.scipy.org/doc/scipy/reference/
          generated/scipy.fft.fft2.html>`_,
        - :func:`lazylinop.signal.dft`.
    """

    s = in_shape[0] * in_shape[1]

    def _matmat(x):
        xp = array_api_compat.array_namespace(x)
        return colvec(xp.fft.fft2(uncolvec(x, in_shape), norm='ortho'))

    def _rmatmat(x):
        xp = array_api_compat.array_namespace(x)
        return colvec(xp.fft.ifft2(uncolvec(x, in_shape), norm='ortho'))

    return LazyLinOp(
        shape=(s, s),
        matvec=lambda x: _matmat(x),
        rmatvec=lambda x: _rmatmat(x))
