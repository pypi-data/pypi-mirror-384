import numpy as np


def spectral_norm(L, nits=20, thres=1e-6):
    """
    Computes the approximate spectral norm or 2-norm of operator L.

    Args:
        L: (LazyLinOperator)
            The operator to compute the 2-norm.
        nits: (int)
            The number of iterations of the power iteration algorithm.
        thres: (float)
            The precision of the the prower iteration algorithm.

    Returns:
        The 2-norm of the operator L.

    Example:
        >>> import numpy as np
        >>> from numpy.linalg import norm
        >>> from numpy.random import rand, seed
        >>> from lazylinop.wip.linalg import spectral_norm
        >>> from lazylinop import aslazylinop
        >>> from scipy.linalg.interpolative import estimate_spectral_norm
        >>> seed(42) # reproducibility
        >>> M = rand(10, 12)
        >>> L = aslazylinop(M)
        >>> ref_norm = norm(M, 2)
        >>> l_norm = spectral_norm(L)
        >>> np.round(ref_norm, 3)
        5.34
        >>> np.round(l_norm, 3)
        5.34
        >>> np.round(estimate_spectral_norm(L), 3)
        5.34

    """
    s = L.shape
    if s[0] < s[1]:
        sL = L @ L.H
    else:
        sL = L.H @ L
    xk = np.random.rand(sL.shape[1])
    k = 0
    prev_lambda = -1
    _lambda = 0
    while (k == 0 or k < nits and
           (np.abs(_lambda - prev_lambda) > thres or np.abs(_lambda) < thres)):
        xk_norm = xk / np.linalg.norm(xk)
        xk = sL @ xk_norm
        prev_lambda = _lambda
        _lambda = np.dot(xk, xk_norm)
        k += 1
    return np.abs(np.sqrt(_lambda))
