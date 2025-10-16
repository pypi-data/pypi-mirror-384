import numpy as np
from lazylinop.signal import fft
from lazylinop.butterfly import fuse, ksm
from lazylinop.wip.butterfly.utils import clean
from lazylinop.butterfly.ksm import _multiple_ksm
from lazylinop.basicops import bitrev
from lazylinop.butterfly.dft import _dft_square_dyadic_ks_values


def dft_helper(N: int, n_factors: int, backend: str = 'numpy',
               strategy: str = 'memory', dtype: str = 'complex64',
               device = 'cpu'):
    r"""
    Return a :class:`LazyLinOp` `L` corresponding to
    the Discrete-Fourier-Transform (DFT).

    Shape of ``L`` is $\left(N,~N\right)$ where
    $N=2^n$ must be a power of two.

    Args:
        N: ``int``
            DFT of size $N$. $N$ must be a power of two.
        n_factors: ``int``
            Number of factors ``n_factors <= n``.
            If ``n_factors = n``, return the square-dyadic decomposition.
            The performance of the algorithm depends on
            the number of factors, the size of the DFT
            as-well-as the strategy.
            Our experimentation shows that square-dyadic decomposition
            is always the worse choice.
            The best choice is two, three or four factors.
        backend: ``str``, ``tuple`` or ``pycuda.driver.Device``, optional
            See :py:func:`ksm` for more details.
        strategy: ``str``, optional
            It could be:

            - ``balanced`` fuse from left to right and right to left ($n>3$).

              - Case ``n = 6`` and ``n_factors = 2``:

                - step 0: 0 1 2 3 4 5
                - step 1: 01 2 3 45
                - step 2: 012 345
              - Case ``n = 7`` and ``n_factors = 2``:

                - step 0: 0 1 2 3 4 5 6
                - step 1: 01 2 3 4 56
                - step 2: 012 3 456
                - step 3: 0123 456
              - Case ``n = 7`` and ``n_factors = 3``:

                - step 0: 0 1 2 3 4 5 6
                - step 1: 01 2 3 4 56
                - step 2: 012 3 456
            - ``'memory'`` find the two consecutive ``ks_values`` that
              minimize the memory of the fused ``ks_values``.
              It is the default value.
        dtype: ``str``, optional
            It could be either ``'complex64'`` (default) or ``'complex128'``.

    Benchmark of our DFT implementation is
    (we use default hyper-parameters here):

    .. image:: _static/default_dft_batch_size512_complex64.svg

    Returns:
        :class:`LazyLinOp` `L` corresponding to the DFT.
    """
    if not (((N & (N - 1)) == 0) and N > 0):
        raise ValueError("N must be a power of two.")
    p = int(np.log2(N))
    if n_factors > p or n_factors < 1:
        raise Exception("n_factors must be positive and less or"
                        + " equal to int(np.log2(N)).")
    if 'complex' not in str(dtype):
        raise Exception("dtype must be either complex.")

    # FIXME
    params = None
    # if n_factors == ...:
    #     params = None
    # elif n_factors == ...:
    #     params = None
    # else:
    #     params = None

    ks_values = _dft_square_dyadic_ks_values(
        N, dtype=dtype, device=device)
    if p == n_factors:
        # Nothing to fuse.
        L = ksm(ks_values, backend=backend)
    else:
        m, target = p, p
        if strategy == 'balanced':
            if p <= 3:
                raise Exception("strategy 'balanced' does" +
                                " not work when p <= 3.")
            # Fuse from left to right and from right to left.
            step = 0
            idx = [str(i) for i in range(p)]
            print(f"      ", idx)
            lpos, rpos, n_left, n_right = 0, m - 1, 0, 0
            while True:
                if target > n_factors:
                    # From left to right.
                    idx[lpos + 1] = idx[lpos] + idx[lpos + 1]
                    target -= 1
                    lpos += 1
                    n_left += 1
                if target > n_factors:
                    # From right to left.
                    idx[rpos - 1] = idx[rpos - 1] + idx[rpos]
                    target -= 1
                    rpos -= 1
                    n_right += 1
                if lpos + 1 >= m / 2:
                    lpos, rpos = n_left, m - 1 - n_right
                print(f"step={step}", idx[n_left:(p - n_right)])
                step += 1
                if target == n_factors:
                    break
            m, target = p, p
            lpos, rpos, n_left, n_right = 0, m - 1, 0, 0
            while True:
                if target > n_factors:
                    # From left to right.
                    ks_values[lpos + 1] = fuse(ks_values[lpos],
                                               ks_values[lpos + 1])
                    target -= 1
                    lpos += 1
                    n_left += 1
                if target > n_factors:
                    # From right to left.
                    ks_values[rpos - 1] = fuse(ks_values[rpos - 1],
                                               ks_values[rpos])
                    target -= 1
                    rpos -= 1
                    n_right += 1
                if lpos + 1 >= m // 2:
                    lpos, rpos = n_left, m - 1 - n_right
                if target == n_factors:
                    break
            L = ksm(ks_values[n_left:(n_left + n_factors)], backend=backend)
        elif strategy in ('memory', 'speed', 'sparsity'):
            step = 0
            idx = [str(i) for i in range(p)]
            print(f"      ", idx)
            n_fuses = 0
            while True:
                # Build memory list.
                heuristic = np.full(p - n_fuses - 1, 0.0)
                memory = np.full(p - n_fuses - 1, 0)
                sparsity = np.full(p - n_fuses - 1, 0.0)
                for i in range(p - n_fuses - 1):
                    a1, b1, c1, d1 = ks_values[i].shape
                    a2, b2, c2, d2 = ks_values[i + 1].shape
                    b = (b1 * d1) // d2
                    c = (a2 * c2) // a1
                    memory[i] = a1 * b * c * d2
                    # Because of argmin, compute the inverse.
                    heuristic[i] = 1.0 / ((b + c) / (b * c))
                    sparsity[i] = 1.0 / (a1 * d2)
                # Find argmin.
                if strategy == 'memory':
                    # argmin = np.argmin(memory)
                    tmp = np.where(memory == memory[np.argmin(memory)])[0]
                    if n_fuses % 2 == 0:
                        argmin = tmp[0]
                    else:
                        argmin = tmp[-1]
                elif strategy == 'speed':
                    # argmin = np.argmin(heuristic)
                    tmp = np.where(
                        heuristic == heuristic[np.argmin(heuristic)])[0]
                    if n_fuses % 2 == 0:
                        argmin = tmp[0]
                    else:
                        argmin = tmp[-1]
                elif strategy == 'sparsity':
                    # argmin = np.argmin(sparsity)
                    tmp = np.where(
                        sparsity == sparsity[np.argmin(sparsity)])[0]
                    if n_fuses % 2 == 0:
                        argmin = tmp[0]
                    else:
                        argmin = tmp[-1]
                # Fuse argmin and argmin + 1.
                ks_values[argmin] = fuse(ks_values[argmin],
                                         ks_values[argmin + 1])
                idx[argmin] = idx[argmin] + idx[argmin + 1]
                n_fuses += 1
                # Delete argmin + 1.
                ks_values.pop(argmin + 1)
                idx.pop(argmin + 1)
                target -= 1
                print(f"step={step}", idx)
                step += 1
                if target == n_factors:
                    break
            L = ksm(ks_values, backend=backend)
        else:
            raise Exception("strategy must be either 'balanced'," +
                            " 'memory', 'sparsity' or 'speed'.")

    if backend in ('cupy', 'numpy', 'pytorch', 'scipy', 'xp'):
        F = ksm(L.ks_values, backend=backend) @ bitrev(2 ** p)
    else:
        F = _multiple_ksm(L.ks_values, backend=backend,
                          params=params, perm=True)
    F.ks_values = L.ks_values
    clean(L)
    del L
    return F
