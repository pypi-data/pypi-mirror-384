"""
Module for linear algebra related LazyLinOps.
"""
try:
    import dask
    from dask.distributed import Client, LocalCluster, wait
except ImportError:
    print("Dask ImportError")
try:
    import numba as nb
    from numba import njit, prange, set_num_threads, threading_layer
    nb.config.THREADING_LAYER = 'omp'
    _T = nb.config.NUMBA_NUM_THREADS
except ImportError:
    print('Did not find Numba.')
    def njit(*args, **kwargs):
        return lambda f: f

import numpy as np
import warnings
warnings.simplefilter(action='always')


@njit(parallel=False, cache=True)
def mm(A: np.ndarray, B: np.ndarray, M: int, K: int, N: int, swap_kn: bool=False):
    C = np.full(M * N, 0 * (A[0] * B[0]))
    if swap_kn:
        for m in range(M):
            for k in range(K):
                for n in range(N):
                    C[m * N + n] += A[m * K + k] * B[k * N + n]
    else:
        for m in range(M):
            for n in range(N):
                tmp = 0.0
                for k in range(K):
                    tmp += A[m * K + k] * B[k * N + n]
                C[m * N + n] = tmp
    return C

# these aliases should be deleted in a next version
# for now they are kept for backward compatibility
from lazylinop.wip.linalg import cosm
from lazylinop.wip.linalg import sinm
from lazylinop.wip.linalg import coshm
from lazylinop.wip.linalg import sinhm
from lazylinop.wip.linalg import expm
from lazylinop.wip.linalg import logm
from lazylinop.wip.linalg import sqrtm
