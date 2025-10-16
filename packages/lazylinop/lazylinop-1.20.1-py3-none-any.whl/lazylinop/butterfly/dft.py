import numpy as np
from lazylinop.basicops import bitrev
from lazylinop.butterfly.ksm import ksm, _multiple_ksm
try:
    import torch
except ModuleNotFoundError:
    torch = None
try:
    import cupy as cp
except ModuleNotFoundError:
    cp = None


def _dft_square_dyadic_ks_values(N: int,
                                 dtype: str = 'complex64',
                                 device = 'cpu'):
    r"""
    Return a list of ``ks_values`` that corresponds
    to the ``F @ P.T`` matrix decomposition into
    ``n = int(np.log2(N))`` factors, where ``F`` is the DFT matrix
    and ``P`` the bit-reversal permutation matrix.
    The size $N=2^n$ of the DFT must be a power of $2$.

    We can draw the square-dyadic decomposition for $N=16$:

    .. image:: _static/square_dyadic.svg

    Args:
        N: ``int``
            DFT of size $N=2^n$.
        dtype: ``str``, optional
            It could be either ``'complex64'`` (default) or ``'complex128'``.
        device: optional
            Send ``ks_values`` to device ``device``.
            The default value is ``'cpu'``.

    Returns:
        List of 4d arrays corresponding to ``ks_values``.
        Infer the namespace (see
        `array-api-compat <https://data-apis.org/array-api-compat/>`_
        for more details)
        of ``ks_values`` from ``dtype`` and ``device`` arguments.
        By default, namespace of ``ks_values`` is ``numpy``
        and dtype is ``'complex64'``.

    Examples:
        >>> import numpy as np
        >>> from lazylinop.butterfly.dft import _dft_square_dyadic_ks_values
        >>> from lazylinop.butterfly import ksm
        >>> from lazylinop.signal import fft
        >>> from lazylinop.basicops import bitrev
        >>> N = 2 ** 5
        >>> ks_values = _dft_square_dyadic_ks_values(N,dtype='complex128' )
        >>> x = np.random.randn(N)
        >>> L = ksm(ks_values)
        >>> P = bitrev(N)
        >>> np.allclose(fft(N) @ x, L @ P @ x)
        True

    References:
        - Learning Fast Algorithms for Linear Transforms Using Butterfly Factorizations.
          Dao T, Gu A, Eichhorn M, Rudra A, Re C.
          Proc Mach Learn Res. 2019 Jun;97:1517-1527. PMID: 31777847; PMCID: PMC6879380.
    """
    if not (((N & (N - 1)) == 0) and N > 0):
        raise ValueError("N must be a power of two.")
    p = int(np.log2(N))
    # Infer the namespace from dtype and device.
    if torch is not None and isinstance(dtype, torch.dtype):
        import array_api_compat.torch as xp
    elif cp is not None and not 'cpu' in str(device):
        import array_api_compat.cupy as xp
    else:
        xp = np
    inv_sqrt2 = 1.0 / xp.sqrt(
        xp.asarray([2.0], dtype=dtype, device=device))
    # Build ks_values.
    ks_values = [None] * p
    for n in range(p):
        if n == (p - 1):
            f2 = xp.asarray([[1.0, 1.0], [1.0, -1.0]],
                            dtype=dtype, device=device) * inv_sqrt2
            a = N // 2
            b, c = 2, 2
            d = 1
            ks_values[n] = xp.empty((a, b, c, d), dtype=dtype,
                                    device=device)
            for i in range(a):
                ks_values[n][i, :, :, 0] = f2
        else:
            s = N // 2 ** (p - n)
            t = N // 2 ** (n + 1)
            w = xp.exp(
                xp.asarray([2.0j * xp.pi / (2 * t)],
                           dtype=dtype, device=device))
            omega = w ** (-xp.arange(t, device=device))
            a = s
            b, c = 2, 2
            d = t
            ks_values[n] = xp.empty((a, b, c, d), dtype=dtype,
                                    device=device)
            # Map between 2d and 4d representations.
            # col = i * c * d + k * d + l
            # row = i * b * d + j * d + l
            # Loop over the a blocks.
            for i in range(a):
                for u in range(t):
                    for v in range(4):
                        if v == 0:
                            # Identity.
                            sub_col = u
                            sub_row = u
                            tmp = inv_sqrt2
                        elif v == 1:
                            # diag(omega).
                            sub_col = u + t
                            sub_row = u
                            tmp = omega[u] * inv_sqrt2
                        elif v == 2:
                            # Identity.
                            sub_col = u
                            sub_row = u + t
                            tmp = inv_sqrt2
                        else:
                            # -diag(omega)
                            sub_col = u + t
                            sub_row = u + t
                            tmp = -omega[u] * inv_sqrt2
                        j = sub_row // d
                        k = sub_col // d
                        ks_values[n][i, j, k, sub_col - k * d] = tmp[0]
    return ks_values


def dft(N: int, backend: str = 'numpy', dtype: str = 'complex64',
        device = 'cpu'):
    r"""
    Return a :class:`LazyLinOp` `L` with the Butterfly structure
    corresponding to the Discrete-Fourier-Transform (DFT).

    Shape of ``L`` is $\left(N,~N\right)$ where
    $N=2^n$ must be a power of two.

    The number of factors $n$ of the square-dyadic decomposition
    is given by $n=\log_2\left(N\right)$

    Infer the namespace (see
    `array-api-compat <https://data-apis.org/array-api-compat/>`_
    for more details)
    of ``L.ks_values`` from ``dtype`` and ``device`` arguments.
    By default, namespace of ``L.ks_values`` is ``numpy``
    and dtype is ``'complex64'``.

    Args:
        N: ``int``
            Size of the DFT. $N$ must be a power of two.
        backend: ``str``, ``tuple`` or ``pycuda.driver.Device``, optional
            See :py:func:`ksm` for more details.
        dtype: ``str``, optional
            It could be either ``'complex64'`` (default) or ``'complex128'``.

    Returns:
        :class:`LazyLinOp` `L` corresponding to the DFT.

    Examples:
        >>> import numpy as np
        >>> from lazylinop.butterfly import dft as bdft
        >>> from lazylinop.signal import dft as sdft
        >>> N = 2 ** 7
        >>> x = np.random.randn(N).astype('float32')
        >>> y = bdft(N) @ x
        >>> z = sdft(N) @ x
        >>> np.allclose(y, z)
        True

    .. _dec:

        **References:**

        [1] Learning Fast Algorithms for Linear Transforms Using Butterfly Factorizations.
        Dao T, Gu A, Eichhorn M, Rudra A, Re C.
        Proc Mach Learn Res. 2019 Jun;97:1517-1527. PMID: 31777847; PMCID: PMC6879380.
    """
    if not (((N & (N - 1)) == 0) and N > 0):
        raise ValueError("N must be a power of two.")
    if 'complex' not in str(dtype):
        raise Exception("dtype must be either complex.")

    ks_values = _dft_square_dyadic_ks_values(N, dtype=dtype, device=device)
    if backend in ('cupy', 'numpy', 'pytorch', 'xp'):
        F = ksm(ks_values, backend='xp') @ bitrev(N)
    elif backend in ('cupyx', 'scipy'):
        F = ksm(ks_values, backend=backend) @ bitrev(N)
    else:
        # FIXME: params=None.
        F = _multiple_ksm(ks_values, backend=backend,
                          params=None, perm=True)
    F.ks_values = ks_values
    return F
