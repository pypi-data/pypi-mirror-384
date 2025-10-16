# -*- coding: utf-8 -*-

from lazylinop import LazyLinOp, islazylinop
from lazylinop.basicops import bitrev
import numpy as np
from pathlib import Path
from typing import Union
import warnings
import itertools
import importlib

try:
    import pyopencl as cl
except (ImportError, ModuleNotFoundError):
    cl = None
try:
    import pycuda.driver as cuda
    import pycuda._driver as _cuda
    cuda.init()
    # No need of an automatic make_default_context().
    # Memory leak ?
    # import pycuda.autoinit
    from pycuda.compiler import SourceModule
    from pycuda.tools import clear_context_caches
    found_pycuda = True
except:  # ImportError:
    cuda = None
    _cuda = None
    SourceModule = None
    found_pycuda = False
from scipy.sparse import csr_matrix
try:
    import numba as nb
    from numba import njit
except ImportError:
    def njit(f):
        return f
    # def njit(*args, **kwargs):
    #     def dummy(f):
    #         return f
    #     return dummy
try:
    import json
except ModuleNotFoundError:
    from warnings import warn
    warn("json not found, " +
         " please install json to save result of ksd function.")
from array_api_compat import (
    array_namespace,
    is_cupy_array, is_numpy_array, is_torch_array)
try:
    import cupy as cp
except ModuleNotFoundError:
    cp = None
try:
    import torch
except ModuleNotFoundError:
    torch = None


contexts = []
kernel_duration = []


def _get_all_platforms() -> list:
    """
    Print all platforms and devices.
    """
    platforms = cl.get_platforms()
    print("List of platforms and devices.")
    tmp = []
    for i, p in enumerate(platforms):
        devices = p.get_devices()
        for d in devices:
            print(i, p.get_info(cl.platform_info.NAME), d)
            print(" ", p.get_info(cl.platform_info.EXTENSIONS))
            tmp.append((p, d))
    return tmp


def _get_platform(platform_name: str, device: str = 'cpu'):
    """
    Return platform and device specified by arguments.

    Args:
        platform_name: ``str``
            Run ``get_all_platforms()`` to list all
            the available platforms and devices.
        device_type: ``str``, optional
            Device type, ``'cpu'`` (default) or ``'gpu'``.

    Returns:
        ``pyopencl.Device``
    """
    platform, device = None, None
    platforms = cl.get_platforms()
    for p in platforms:
        if p.get_info(cl.platform_info.NAME) != platform_name:
            continue
        if device == 'gpu':
            devices = p.get_devices(device_type=cl.device_type.GPU)
        else:
            devices = p.get_devices(device_type=cl.device_type.CPU)
        for d in devices:
            # print('selection', p, d)
            return d
    return platform, device


def _check_hyper_parameters(hp, a: int, b: int, c: int, d: int,
                            batch_size: int, smem: int, nbytes: int,
                            max_block_dim: tuple,
                            max_grid_dim: tuple) -> bool:
    """
    Check if the given hyper-parameters satisfy the kernel assertions.

    Args:
        hp:
            Tuple of hyper-parameters
            ``(TILEX, TILEK, TILEY, TX, TY, VSIZE)``.
        a, b, c, d: ``int``, ``int``, ``int``, ``int``
            Pattern of the Kronecker-Sparse factor.
        batch_size: ``int``
            Size of the batch ``x.shape[1]`` in ``L @ x``.
        smem: ``int``
            Size of shared memory of your hardware.
        nbytes: ``int``
            Number of bytes of the elements of the
            Kronecker-Sparse factor.
        max_block_dim: ``tuple``
            Tuple ``(x, y, z)`` for max block dimensions.
        max_grid_dim: ``tuple``
            Tuple ``(x, y, z)`` for max grid dimensions.

    Returns:
        ``bool``
    """
    n_rows = a * b * d
    n_cols = a * c * d
    tile_x, tile_k, tile_y = hp[0], hp[1], hp[2]
    tx, ty, vsize = hp[3], hp[4], hp[5]
    if tile_k > n_cols or tile_k > c or (c % tile_k) != 0:
        return False
    if max_grid_dim is not None and \
       ((n_rows + tile_y - 1) // tile_y) > max_grid_dim[1]:
        return False
    if tile_y > n_rows or tile_y > b:
        return False
    if max_grid_dim is not None and \
       ((batch_size + tile_x - 1) // tile_x) > max_grid_dim[0]:
        return False
    if batch_size > 0 and (tile_x > batch_size or
                           batch_size % tile_x != 0):
        return False
    if (nbytes * 2 * (tile_y * tile_k + tile_k * tile_x)) >= smem:
        return False
    if (tx % vsize) != 0 or (ty % vsize) != 0:
        return False
    x, y = tile_x // tx, tile_y // ty
    if max_block_dim is not None and \
       x > max_block_dim[0]:
        return False
    if max_block_dim is not None and \
       y > max_block_dim[1]:
        return False
    strideInput = (vsize * x * y) / tile_x
    if (vsize * x * y) % tile_x != 0:
        return False
    strideValues = (vsize * x * y) / tile_k
    if (vsize * x * y) % tile_k != 0:
        return False
    if tile_k > tile_x or tile_k > tile_y:
        return False
    if (b * d) % (d * tile_y) != 0:
        return False
    if tile_k % strideInput != 0:
        return False
    if tile_y % strideValues != 0:
        return False
    return True


@njit
def _find_hyper_parameters(a, b, c, d, batch_size: int = 0,
                           smem: int = 163000, nbytes: int = 8,
                           max_block_dim: tuple = None,
                           max_grid_dim: tuple = None) -> tuple:
    """
    Nested loops over tile size to find one possible set
    of hyper-parameters for a given pattern.

    Args:
        a, b, c, d: ``int``, ``int``, ``int``, ``int``
            Pattern of the Kronecker-Sparse factor.
        batch_size: ``int``, optional
            Size of the batch ``x.shape[1]`` in ``L @ x``.
            Default value is 0 (skip batch size condition).
        smem: ``int``
            Size of shared memory of your hardware.
            Default size is 163000 bytes.
        nbytes: ``int``
            Number of bytes of the elements of the
            Kronecker-Sparse factor.
            Default value is 8.
        max_block_dim: ``tuple``, optional
            Tuple ``(x, y, z)`` for max block dimensions.
            ``None`` is default value.
        max_grid_dim: ``tuple``, optional
            Tuple ``(x, y, z)`` for max grid dimensions.
            ``None`` is default value.

    Returns:
        Tuple of hyper-parameters
        ``(TILEX, TILEK, TILEY, TX, TY, VSIZE)``.
    """
    n_rows = a * b * d
    n_cols = a * c * d
    if isinstance(max_block_dim, tuple) and len(max_block_dim) > 1:
        tmp = max(max_block_dim[0], max_block_dim[1])
    else:
        tmp = 16
    for vsize in range(4, 0, -1):
        for x in range(tmp, 0, -1):
            if max_block_dim is not None and \
               x > max_block_dim[0]:
                continue
            for tx in range(16, vsize - 1, -1):
                if (tx % vsize) != 0:
                    continue
                tile_x = x * tx
                if max_grid_dim is not None and \
                   ((batch_size + tile_x - 1) // tile_x) > max_grid_dim[0]:
                    continue
                if batch_size > 0 and (tile_x > batch_size or
                                       batch_size % tile_x != 0):
                    continue
                for k in range(16, 0, -1):
                    tile_k = k * vsize
                    if tile_k > n_cols or tile_k > c or (c % tile_k) != 0:
                        continue
                    if tile_k > tile_x:
                        continue
                    for y in range(tmp, 0, -1):
                        if max_block_dim is not None and \
                           y > max_block_dim[1]:
                            continue
                        strideInput = (vsize * x * y) / tile_x
                        if (vsize * x * y) % tile_x != 0:
                            continue
                        if tile_k % strideInput != 0:
                            continue
                        strideValues = (vsize * x * y) / tile_k
                        if (vsize * x * y) % tile_k != 0:
                            continue
                        for ty in range(16, vsize - 1, -1):
                            if (ty % vsize) != 0:
                                continue
                            tile_y = y * ty
                            if (
                                    max_grid_dim is not None and
                                    ((n_rows + tile_y - 1)
                                     // tile_y) > max_grid_dim[1]
                            ):
                                continue
                            if (nbytes * 2 * (tile_y * tile_k
                                              + tile_k * tile_x)) >= smem:
                                continue
                            if tile_y > n_rows or tile_y > b:
                                continue
                            if tile_y % strideValues != 0:
                                continue
                            if tile_k > tile_y:
                                continue
                            if (b * d) % (d * tile_y) != 0:
                                continue
                            return (tile_x, tile_k, tile_y, tx, ty, vsize)
    raise Exception("Did not find hyper-parameters.")


@njit
def _find_all_hyper_parameters(a, b, c, d, batch_size: int = 0,
                               smem: int = 163000, nbytes: int = 8,
                               max_block_dim: tuple = None,
                               max_grid_dim: tuple = None) -> list:
    """
    Nested loops over tile size to find all the possible sets
    of hyper-parameters for a given pattern.

    Args:
        a, b, c, d: ``int``, ``int``, ``int``, ``int``
            Pattern of the Kronecker-Sparse factor.
        batch_size: ``int``, optional
            Size of the batch ``x.shape[1]`` in ``L @ x``.
            Default value is 0 (skip batch size condition).
        smem: ``int``
            Size of shared memory of your hardware.
            Default size is 163000 bytes.
        nbytes: ``int``
            Number of bytes of the elements of the
            Kronecker-Sparse factor.
            Default value is 8.
        max_block_dim: ``tuple``, optional
            Tuple ``(x, y, z)`` for max block dimensions.
            ``None`` is default value.
        max_grid_dim: ``tuple``, optional
            Tuple ``(x, y, z)`` for max grid dimensions.
            ``None`` is default value.

    Returns:
        ``List`` of ``tuple`` of hyper-parameters
        ``(TILEX, TILEK, TILEY, TX, TY, VSIZE)``.
    """
    n_rows = a * b * d
    n_cols = a * c * d
    hp = []
    if isinstance(max_block_dim, tuple) and len(max_block_dim) > 1:
        tmp = max(max_block_dim[0], max_block_dim[1])
    else:
        tmp = 16
    for vsize in range(4, 0, -1):
        for x in range(tmp, 0, -1):
            if max_block_dim is not None and \
               x > max_block_dim[0]:
                continue
            for tx in range(16, vsize - 1, -1):
                if (tx % vsize) != 0:
                    continue
                tile_x = x * tx
                if max_grid_dim is not None and \
                   (batch_size + tile_x - 1) // tile_x > max_grid_dim[0]:
                    continue
                if batch_size > 0 and (tile_x > batch_size or
                                       batch_size % tile_x != 0):
                    continue
                for k in range(16, 0, -1):
                    tile_k = k * vsize
                    if tile_k > n_cols or tile_k > c or (c % tile_k) != 0:
                        continue
                    if tile_k > tile_x:
                        continue
                    for y in range(tmp, 0, -1):
                        if max_block_dim is not None and \
                           y > max_block_dim[1]:
                            continue
                        strideInput = (vsize * x * y) / tile_x
                        if (vsize * x * y) % tile_x != 0:
                            continue
                        if tile_k % strideInput != 0:
                            continue
                        strideValues = (vsize * x * y) / tile_k
                        if (vsize * x * y) % tile_k != 0:
                            continue
                        for ty in range(16, vsize - 1, -1):
                            if (ty % vsize) != 0:
                                continue
                            tile_y = y * ty
                            if (
                                    max_grid_dim is not None and
                                    (n_rows + tile_y - 1)
                                    // tile_y > max_grid_dim[1]
                            ):
                                continue
                            if (nbytes * 2 * (tile_y * tile_k
                                              + tile_k * tile_x)) >= smem:
                                continue
                            if tile_y > n_rows or tile_y > b:
                                continue
                            if tile_y % strideValues != 0:
                                continue
                            if tile_k > tile_y:
                                continue
                            if (b * d) % (d * tile_y) != 0:
                                continue
                            hp.append((tile_x, tile_k, tile_y, tx, ty, vsize))
    if len(hp) == 0:
        raise Exception("Did not find hyper-parameters.")
    return hp


def _modify_template(a: int, b: int, c: int, d: int, batch_size: int = 0,
                     smem: int = 163000,
                     max_block_dim: tuple = None,
                     max_grid_dim: tuple = None,
                     params: tuple = (None, None),
                     dtype: np.dtype = np.float32, ext: str = 'clh'):
    r"""
    Add explicit values of the hyper-parameters to the kernel.

    Args:
        a, b, c, d: ``int``, ``int``, ``int``, ``int``
            Pattern of the Kronecker-Sparse factor.
        batch_size: ``int``, optional
            Size of the batch ``x.shape[1]`` in ``L @ x``.
            Default value is 0 (skip batch size condition).
        smem: ``int``
            Size of shared memory of your hardware.
            Default size is 163000 bytes.
        params: ``tuple``, optional
            ``params[0]`` and ``params[1]`` expect a tuple of six elements
            ``(TILEX, TILEK, TILEY, TX, TY, VSIZE)`` (see :ref:`[1] <ksm>`
            for more details).
            If ``(None, None)`` (default), the choice of
            hyper-parameters for multiplication ``L @ X`` and the
            multiplication ``L.H @ X`` is automatic.
            Because we did not run a fine-tuning for all the
            possible $\left(a,~b,~c,~d\right)$ and $\left(a,~c,~b,~d\right)$
            tuples, automatic does not always correspond to the best choice.
        dtype: ``np.dtype``, optional
            dtype of the Kronecker-Sparse factor.
        ext: ``str``, optional

            - ``'clh'`` uses OpenCL kernel template.
            - ``'cuh'`` uses CUDA kernel template.
    """
    lines = {}
    for f in ["ksmm", "rksmm"]:
        lines[f] = []
        with open(
                Path(__file__).parent.joinpath(
                    f"kernels/{f}.{ext}"), 'w') as out_file:
            with open(
                    Path(__file__).parent.joinpath(
                        f"kernels/template_ksmm.{ext}"), 'r') as in_file:
                if f == 'ksmm':
                    if params is None or params[0] is None:
                        hp = _find_hyper_parameters(
                            a, b, c, d, batch_size,
                            smem=smem,
                            nbytes=dtype.itemsize,
                            max_block_dim=max_block_dim,
                            max_grid_dim=max_grid_dim)
                        if hp == tuple([0] * 6):
                            raise Exception("matmat: Did not find" +
                                            " hyper-parameters.")
                    else:
                        if len(params[0]) != 6:
                            raise Exception(
                                "matmat: hyper-parameters must be "
                                + "a tuple of six elements.")
                        else:
                            hp = params[0]
                            if not _check_hyper_parameters(
                                    hp, a, b, c, d,
                                    batch_size,
                                    smem=smem, nbytes=dtype.itemsize,
                                    max_block_dim=max_block_dim,
                                    max_grid_dim=max_grid_dim):
                                raise Exception(
                                    "matmat: hyper-parameters do not" +
                                    " satisfy the kernel assertions.")
                else:
                    if params is None or params[1] is None:
                        rhp = _find_hyper_parameters(
                            a, c, b, d, batch_size,
                            smem=smem,
                            nbytes=dtype.itemsize,
                            max_block_dim=max_block_dim,
                            max_grid_dim=max_grid_dim)
                        if rhp == tuple([0] * 6):
                            raise Exception("rmatmat: Did not find"
                                            + " hyper-parameters.")
                    else:
                        if len(params[1]) != 6:
                            raise Exception(
                                "rmatmat: hyper-parameters must be "
                                + "a tuple of six elements.")
                        else:
                            rhp = params[1]
                            if not _check_hyper_parameters(
                                    rhp, a, c, b, d,
                                    batch_size,
                                    smem=smem, nbytes=dtype.itemsize,
                                    max_block_dim=max_block_dim,
                                    max_grid_dim=max_grid_dim):
                                raise Exception(
                                    "rmatmat: hyper-parameters do not" +
                                    " satisfy the kernel assertions.")

                p = hp if f == "ksmm" else rhp

                # Number of threads.
                nthreads = (p[0] // p[3]) * (p[2] // p[4])
                # Define floating point precision.
                if 'float16' in str(dtype):
                    lines[f].append("#define USE_FLOAT16\n")
                elif 'float32' in str(dtype):
                    lines[f].append("#define USE_FLOAT32\n")
                elif 'float64' in str(dtype):
                    lines[f].append("#define USE_FLOAT64\n")
                elif 'complex64' in str(dtype):
                    lines[f].append("#define USE_COMPLEX64\n")
                elif 'complex128' in str(dtype):
                    lines[f].append("#define USE_COMPLEX128\n")
                else:
                    pass
                # vloadn and vstoren depend on the values of b and c.
                lines[f].append("#define V" + str(p[5]) + "\n")
                lines[f].append("#define xTILEXx " + str(p[0]) + "\n")
                lines[f].append("#define xTILEKx " + str(p[1]) + "\n")
                lines[f].append("#define xTILEYx " + str(p[2]) + "\n")
                lines[f].append("#define xTXx " + str(p[3]) + "\n")
                lines[f].append("#define xTYx " + str(p[4]) + "\n")
                lines[f].append(
                    "#define xNTHREADSx " + str(nthreads) + "\n\n")
                lines[f].extend(in_file.readlines())

    return hp, rhp, lines['ksmm'], lines['rksmm']


def _find_all_hyper_parameters_perm(M: int, batch_size: int,
                                    max_block_dim: tuple = None,
                                    max_grid_dim: tuple = None):
    r"""
    Find all the possible hyper-parameters
    for the bit-reversal permutation kernel.
    ``(TILEX, TILEY, VSIZE)`` that must satisfy
    the following conditions:

    - ``M % TILEY == 0``
    - ``VSIZE >= 1`` and ``VSIZE <= 4``
    - ``batch_size % (VSIZE * TILEX) == 0``

    Args:
        M: ``int``
            Number of rows of the bit-reversal permutation matrix.
        batch_size: ``int``
            Size of the batch ``x.shape[1]`` in ``L @ x``.
        max_block_dim: ``tuple``
            Tuple ``(x, y, z)`` for max block dimensions.
        max_grid_dim: ``tuple``
            Tuple ``(x, y, z)`` for max grid dimensions.

    Returns:
        ``List`` of ``tuple`` of hyper-parameters
        ``(TILEX, TILEY, VSIZE)``.
    """
    hp = []
    for v in range(4, 0, -1):
        # batch_size % (v * tile) = 0
        # for tx in range(1, 32, 1):
        for tx in range(32, 0, -1):
            if max_grid_dim is not None:
                if (batch_size + v * tx - 1) // (v * tx) > max_grid_dim[0]:
                    continue
            if max_block_dim is not None:
                if tx > max_block_dim[0]:
                    continue
            if batch_size % (v * tx) == 0:
                # M % tile = 0
                # for ty in range(1, 32, 1):
                for ty in range(32, 0, -1):
                    if max_grid_dim is not None:
                        if (M + ty - 1) // ty > max_grid_dim[1]:
                            continue
                    if max_block_dim is not None:
                        if ty > max_block_dim[1]:
                            continue
                    if M % ty == 0:
                        hp.append((tx, ty, v))
    if len(hp) == 0:
        raise Exception("Did not find hyper-parameters.")
    return hp


def _modify_template_bitrev_perm(M: int, batch_size: int,
                                 smem: int = 163000,
                                 max_block_dim: tuple = None,
                                 max_grid_dim: tuple = None,
                                 params: tuple = None,
                                 dtype: np.dtype = np.float32,
                                 ext: str = 'clh'):
    r"""
    Add explicit values of the hyper-parameters to the kernel.

    Args:
        M: ``int``
            Number of rows of the bit-reversal permutation matrix.
        batch_size: ``int``
            Size of the batch ``x.shape[1]`` in ``L @ x``.
        smem: ``int``
            Size of shared memory of your hardware.
            Default size is 163000 bytes.
        max_block_dim: ``tuple``
            Tuple ``(x, y, z)`` for max block dimensions.
        max_grid_dim: ``tuple``
            Tuple ``(x, y, z)`` for max grid dimensions.
        params: ``tuple``, optional
            ``params`` expect a tuple of three elements
            ``(TILEX, TILEY, VSIZE)`` that must satisfy
            the following conditions:

            - ``M % TILEY == 0``
            - ``VSIZE >= 1`` and ``VSIZE <= 4``
            - ``batch_size % (VSIZE * TILEX) == 0``
            If ``None`` (default), the choice of
            hyper-parameters for multiplication ``L @ X`` and the
            multiplication ``L.H @ X`` is automatic.
            Because we did not run a fine-tuning for all the
            possible $\left(a,~b,~c,~d\right)$ and $\left(a,~c,~b,~d\right)$
            tuples, automatic does not always correspond to the best choice.
        dtype: ``np.dtype``, optional
            dtype of the input array.
        ext: ``str``, optional

            - ``'clh'`` uses OpenCL kernel template.
            - ``'cuh'`` uses CUDA kernel template.
    """
    lines, pbx, pby, vsize = [], None, None, None
    msg = (
        "bit-reversal permutation: hyper-parameters do not" +
        " satisfy the kernel assertions.")
    with open(
            Path(__file__).parent.joinpath(
                f"kernels/template_bitrev_perm.{ext}"), 'r') as in_file:

        # Define floating point precision.
        if 'float16' in str(dtype):
            lines.append("#define USE_FLOAT16\n")
        elif 'float32' in str(dtype):
            lines.append("#define USE_FLOAT32\n")
        elif 'float64' in str(dtype):
            lines.append("#define USE_FLOAT64\n")
        elif 'complex64' in str(dtype):
            lines.append("#define USE_COMPLEX64\n")
        elif 'complex128' in str(dtype):
            lines.append("#define USE_COMPLEX128\n")
        else:
            pass
        if params is None:
            if batch_size % 4 == 0:
                vsize = 4
            elif batch_size % 3 == 0:
                vsize = 3
            elif batch_size % 2 == 0:
                vsize = 2
            else:
                vsize = 1
            # batch_size % (vsize * tile) = 0
            # for t in range(1, 64, 1):
            for t in range(64, 0, -1):
                if max_grid_dim is not None:
                    if (batch_size + vsize * t - 1) // (vsize * t) > max_grid_dim[0]:
                        continue
                if max_block_dim is not None:
                    if t > max_block_dim[0]:
                        continue
                if batch_size % (vsize * t) == 0:
                    pbx = t
                    break
            # M % tile = 0
            # for t in range(1, 64, 1):
            for t in range(64, 0, -1):
                if max_grid_dim is not None:
                    if (M + t - 1) // t > max_grid_dim[1]:
                        continue
                if max_block_dim is not None:
                    if t > max_block_dim[1]:
                        continue
                if M % t == 0:
                    pby = t
                    break
        else:
            pbx = params[0]
            pby = params[1]
            vsize = params[2]
            if (
                    batch_size % (vsize * pbx) != 0 or
                    M % pby != 0 or
                    vsize < 1 or vsize > 4
            ):
                raise Exception(msg)
            if max_block_dim is not None:
                if pbx > max_block_dim[0] or (
                        batch_size + vsize * pbx - 1) // (vsize * pbx) > max_grid_dim[0]:
                    raise Exception(msg)
            if max_grid_dim is not None:
                if pby > max_block_dim[1] or (
                        M + pby - 1) // pby > max_grid_dim[1]:
                    raise Exception(msg)

        lines.append("#define V" + str(vsize) + "\n")
        lines.extend(in_file.readlines())

    return pbx, pby, vsize, lines


class Ksm_data():
    """
    This class keeps track of the last batch size.
    """
    def __init__(self, batch_size: int = None):
        self.batch_size = batch_size
        self.hp = None
        self.rhp = None
        self.program = None
        self.rprogram = None
        self.d_values = None
        self.d_rvalues = None


def ksm(ks_values: Union[np.ndarray, list],
        params: Union[tuple, list] = None,
        backend: str = 'xp'):
    r"""
    Returns a :class:`.LazyLinOp` ``L`` for
    Kronecker Sparse Matrix Multiplication (KSMM see :ref:`[1] <ksm>`).
    The sparsity pattern (or support) of a Kronecker-Sparse factor
    is defined as $I_a\otimes 1_{b,c}\otimes I_d$
    while its values are given by a 4D ``np.ndarray``
    of shape ``(a, b, c, d)``.

    The shape of ``L`` is $\left(abd,~acd\right)$.

    To fill a ``ks_values`` and its Kronecker-Sparse factor ``M``:

    .. _indexing:

    .. code-block:: python3

        M = np.zeros((a * b * d, a * c * d), dtype=np.float32)
        ks_values = np.empty((a, b, c, d), dtype=M.dtype)
        for i in range(a):
            for j in range(b):
                for k in range(c):
                    for l in range(d):
                        tmp = np.random.randn()
                        ks_values[i, j, k, l] = tmp
                        M[i * b * d + j * d + l,
                          i * c * d + k * d + l] = tmp

    For ``a = 3, b = 3, c = 5, d = 5`` we have the following pattern.

    .. image:: _static/abcd.svg

    .. note::

        You can access the ``ks_values`` of
        ``L = ksm(...)`` using ``L.ks_values``.

    :octicon:`megaphone;1em;sd-text-danger` With OpenCL and CUDA
    backend, ``L @ X`` will implicitly cast ``X`` to:

    - match the dtype of ``L.ks_values``
    - be of contiguous type
    This can incur a loss of performance, as-well-as a loss of
    precision if the dtype of X was initially of higher precision
    than that of ``L.ks_values``.

    Args:
        ks_values: CuPy/NumPy arrays, torch tensors or ``list`` of arrays
            It could be:

            - A 4D array of values of the Kronecker-Sparse factor.
            - List of values of the Kronecker-Sparse factors.
              The length of the list corresponds to the number
              of Kronecker-Sparse factors.
            The ``dtype`` of each ``ks_values`` is either ``'float16'``,
            ``'float32'``, ``'float64'``, ``'complex64'`` or ``'complex128'``.
            See :ref:`code <indexing>` above for details on the
            expected indexing of ``ks_values``.
        backend: optional
            The available backends depend on the namespace (see
            `array-api-compat <https://data-apis.org/array-api-compat/>`_
            for more details) of the ``ks_values``.
            By default, use a namespace-based implementation.

            - For ``torch`` namespace:

                - ``backend='ksmm'`` to run the algorithm of :ref:`[1] <ksm>`.
                  :octicon:`info;1em;sd-text-danger` It uses a CUDA device
                  determined by ``ks_values`` and relies on ``cp.RawModule``.
            - For ``cupy`` namespace:

                - ``backend='ksmm'`` to run the algorithm of :ref:`[1] <ksm>`.
                  :octicon:`info;1em;sd-text-danger` It uses a CUDA device
                  determined by ``ks_values`` (must be on GPU) and
                  relies on ``cp.RawModule``,
                  ``__cuda_array_interface__``, ``DLPack``.
                - ``backend='cupyx'`` uses the ``cupyx.scipy.sparse.csr_matrix``
                  function.
            - For ``numpy`` namespace:

                - ``backend='scipy'`` uses the SciPy sparse functions ``scipy.sparse.block_diag``
                  and ``scipy.sparse.csr_matrix``.
                - ``backend=(platform, device)`` to use OpenCL
                  to run the algorithm of :ref:`[1] <ksm>`.

                    - ``(None, None)``  uses the first platform and device.
                    - ``(None, 'cpu')`` use the first platform and CPU device.
                    - ``(None, 'gpu')`` use the first platform and GPU device.

                  Please consider the following piece of code
                  for advanced choices:

                  .. code-block:: python3

                      import pyopencl as cl
                      # Get your favorite platform.
                      platform = cl.get_platforms()[pl_id]
                      # To get your favorite CPU device.
                      device = platform.get_devices(device_type=cl.device_type.CPU)[dev_id]
                      # To get your favorite GPU device.
                      device = platform.get_devices(device_type=cl.device_type.GPU)[dev_id]
                  To check platforms and devices of your system you can also
                  run the command line ``clinfo -a``.
                  See `PyOpenCL documentation <https://documen.tician.de/pyopencl/>`_
                  for more details.
                - ``backend=pycuda.driver.Device(id)`` uses a CUDA device
                  to run the algorithm of :ref:`[1] <ksm>`.
                  See `PyCUDA documentation <https://documen.tician.de/pycuda/>`_
                  for more details.
        params: ``tuple`` or ``list`` of ``tuple``, optional
            Argument ``params`` only works for OpenCL and CUDA backends.
            It could be:

            - A tuple ``params`` of tuples where
              ``params[0]`` and ``params[1]`` expect a tuple of six elements
              ``(TILEX, TILEK, TILEY, TX, TY, VSIZE)`` (see :ref:`[1] <ksm>`
              for more details).
              If ``(None, None)`` (default), the choice of
              hyper-parameters for multiplication ``L @ X`` and the
              multiplication ``L.H @ X`` is automatic.
              Because we did not run a fine-tuning for all the
              possible $\left(a,~b,~c,~d\right)$ and $\left(a,~c,~b,~d\right)$
              tuples, automatic does not always correspond to the best choice.
            - List of tuple of length the number of factors.
              ``params[i][0]`` and ``params[i][1]`` expect a tuple
              of six elements ``(TILEX, TILEK, TILEY, TX, TY, VSIZE)``
              (see :ref:`[1] <ksm>` for more details).
              If ``None`` (default), the choice of
              hyper-parameters for multiplication ``L @ X`` and the
              multiplication ``L.H @ X`` is automatic.
              Because we did not run a fine-tuning for all the
              possible $\left(a,~b,~c,~d\right)$ and $\left(a,~c,~b,~d\right)$
              tuples, automatic does not always correspond to the best choice.

            List of assertions the tuple
            ``(TILEX, TILEK, TILEY, TX, TY, VSIZE)`` must satisfy:

            - ``TILEX = X * TX``
            - ``TILEY = Y * TY``
            - ``batch size % TILEX == 0`` for performance reason.
              Consider zero-padding of the batch.
            - ``TILEX < batch size``
            - ``TILEK <= c and c % TILEK == 0`` for performance reason.
            - ``TILEX > TILEK and TILEY > TILEK``
            - ``(VSIZE * X * Y) % TILEX == 0``
            - ``TILEK % strideInput == 0``
            - ``(VSIZE * X * Y) % TILEK == 0``
            - ``TILEY % strideValues == 0``
            - ``TILEY <= b``
            - ``(b * d) % (d * TILEY) == 0``
            - ``ks_values.dtype.itemsize * 2 * (TILEY * TILEK + TILEK * TILEX) < smem``

            where ``smem`` is the shared memory of the hardware
            used to compute, ``VSIZE`` ranges from $1$ to $4$,
            ``strideValues = VSIZE * X * Y / TILEK``
            and ``strideInput = VSIZE * X * Y / TILEX``.

    Returns:
        A :class:`.LazyLinOp` instance ``L`` for
        Kronecker Sparse Matrix Multiplication (KSMM).
        You can access the ``ks_values`` of
        ``L = ksm(...)`` using ``L.ks_values``.

    Examples:
        >>> from lazylinop.butterfly.ksm import ksm
        >>> import numpy as np
        >>> a, b, c, d = 2, 4, 4, 2
        >>> ks_values = np.full((a, b, c, d), 1.0, dtype=np.float32)
        >>> L = ksm(ks_values)
        >>> L.toarray(dtype='float')
        array([[1., 0., 1., 0., 1., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
               [0., 1., 0., 1., 0., 1., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0.],
               [1., 0., 1., 0., 1., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
               [0., 1., 0., 1., 0., 1., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0.],
               [1., 0., 1., 0., 1., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
               [0., 1., 0., 1., 0., 1., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0.],
               [1., 0., 1., 0., 1., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
               [0., 1., 0., 1., 0., 1., 0., 1., 0., 0., 0., 0., 0., 0., 0., 0.],
               [0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 1., 0., 1., 0., 1., 0.],
               [0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 1., 0., 1., 0., 1.],
               [0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 1., 0., 1., 0., 1., 0.],
               [0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 1., 0., 1., 0., 1.],
               [0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 1., 0., 1., 0., 1., 0.],
               [0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 1., 0., 1., 0., 1.],
               [0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 1., 0., 1., 0., 1., 0.],
               [0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 1., 0., 1., 0., 1.]])
        >>> # List of Kronecker-Sparse factors.
        >>> a1, b1, c1, d1 = 2, 4, 3, 3
        >>> ks_values1 = np.full((a1, b1, c1, d1), 1.0, dtype=np.float32)
        >>> a2, b2, c2, d2 = 3, 3, 5, 2
        >>> ks_values2 = np.full((a2, b2, c2, d2), 1.0, dtype=np.float32)
        >>> L = ksm(ks_values1) @ ksm(ks_values2)
        >>> M = ksm([ks_values1, ks_values2])
        >>> np.allclose(L.toarray(dtype='float'), M.toarray(dtype='float'))
        True

    .. _ksm:

        **References:**

        [1] Fast inference with Kronecker-sparse matrices.
        Antoine Gonon and Léon Zheng and Pascal Carrivain and Quoc-Tung Le
        https://arxiv.org/abs/2405.15013

    .. seealso::

        - `CuPy RawModule <https://docs.cupy.dev/en/stable/reference/
          generated/cupy.RawModule.html#cupy.RawModule>`_,
        - `Interoperability <https://docs.cupy.dev/en/stable/
          user_guide/interoperability.html>`_,
        - `Data interchange mechanism <https://data-apis.org/array-api/
          latest/design_topics/data_interchange.html>`_.
    """

    xp_backend = ["numpy", "scipy",
                  "cupy", "cupyx", "pytorch", "xp"]
    if isinstance(backend, str) and backend in xp_backend:
        backend_name = backend
    elif isinstance(backend, str) and backend in (
            'opencl-cpu', 'opencl-gpu', 'cuda'):
        if not is_numpy_array(ks_values[0]):
            raise Exception(f"backend={backend}" +
                            " expects ks_values to be NumPy arrays.")
        backend_name = 'ksmm'
    elif (is_cupy_array(ks_values[0]) or
          is_torch_array(ks_values[0])) and backend == 'ksmm':
        print('here', backend, ks_values[0].__class__)
        backend_name = 'ksmm'
    elif (
            isinstance(backend, tuple) and
            len(backend) == 2 and
            cl is not None and (
                (isinstance(backend[0], cl.Platform) and
                 isinstance(backend[1], cl.Device)) or
                backend == (None, None) or
                backend == (None, 'cpu') or
                backend == (None, 'gpu'))
    ):
        if not is_numpy_array(ks_values[0]):
            raise Exception("backend=(cl.platform, cl.Device) (PyOpenCL)" +
                            " expects ks_values to be NumPy arrays.")
        backend_name = 'ksmm'
    elif cuda is not None and isinstance(backend, cuda.Device):
        if not is_numpy_array(ks_values[0]):
            raise Exception("backend=pycuda.driver.Device (PyCUDA)" +
                            " expects ks_values to be NumPy arrays.")
        backend_name = 'ksmm'
    else:
        raise Exception(f"No such backend found: {backend}." +
                        " Please check if CuPy, PyTorch, PyCUDA and/or" +
                        " PyOpenCL have been installed.")

    if cp is None and torch is not None and backend_name == 'ksmm':
        raise RuntimeError("ksm with torch backend relies" +
                           " on CuPy DLPack that is not found.")

    if not isinstance(ks_values, (list, tuple)):
        ks_values = [ks_values]

    n_factors = len(ks_values)
    for i in range(n_factors):
        if ks_values[i].ndim != 4 or not (
                is_cupy_array(ks_values[i]) or
                is_numpy_array(ks_values[i]) or
                is_torch_array(ks_values[i])):
            raise Exception("ks_values elements must be a" +
                            " 4D CuPy/NumPy array or torch tensor.")
        if backend not in xp_backend:
            if ks_values[i].dtype not in (
                    np.float16,
                    np.float32,
                    np.float64,
                    np.complex64,
                    np.complex128,
                    torch.float16,
                    torch.float32,
                    torch.float64,
                    torch.complex64,
                    torch.complex128,
            ):
                raise TypeError(
                    "dtype of ks_values must be either np.float16,"
                    + " np.float32, np.float64, np.complex64"
                    + f" or np.complex128 with {backend} backend.")

    if backend_name == 'ksmm':
        if is_torch_array(
                ks_values[0]) and 'cpu' in str(ks_values[0].device):
            raise RuntimeError("For torch tensor and backend='ksmm'," +
                               " ks_values must be on CUDA device.")
        L = _multiple_ksm(ks_values, params, backend)
    else:
        if backend in ("cupy", "numpy", "pytorch", "xp"):
            ksm_fn = getattr(importlib.import_module(__name__), "_ksm_xp")
        else:
            ksm_fn = getattr(
                importlib.import_module(__name__), "_ksm_" + backend)
        L = ksm_fn(ks_values[0])
        for i in range(1, n_factors):
            L = L @ ksm_fn(ks_values[i])
        L.context = None
        L.context_idx = -1

    # Add data to instance for further use.
    ks_patterns = []
    for i in range(len(ks_values)):
        a, b, c, d = ks_values[i].shape
        ks_patterns.append((a, b, c, d))
    L.ks_patterns = ks_patterns
    L.ks_values = ks_values
    L.params = params
    L.backend = backend

    return L


def _fp_support(platform, dtype):
    """
    Check OpenCL and platform fp support.

    Args:
        platform: ``cl.Platform``
            OpenCL platform.
        dtype: ``str`` or ``torch.dtype``
            dtype of the arrays.

    Returns:
        ``tuple`` of ``bool``
        (``True`` if dtype is in ``cl.platform_info.EXTENSIONS``)
        and ``str`` (message if dtype is not in
        ``cl.platform_info.EXTENSIONS``).
        
    """
    # Return False if dtype is not in cl.platform_info.EXTENSIONS.
    _extensions = platform.get_info(cl.platform_info.EXTENSIONS)
    if (
            ('float16' in str(dtype) or 'half' in str(dtype)) and
            not ('cl_khr_fp16' in _extensions or
                 'cl_amd_fp16' in _extensions)
    ):
        return False, f"{platform} has no fp16 extension."
    if (
            ('float64' in str(dtype) or 'complex128' in str(dtype)) and
            not ('cl_khr_fp64' in _extensions or
                 'cl_amd_fp64' in _extensions)
    ):
        return False, f"{platform} has no fp64 extension."
    return True, ""


def _context(backend, dtype: str = 'float'):
    """
    Return either PyOpenCL, PyCUDA context or ``None`` for other backends``.

    Args:
        backend: ``str``, ``tuple[cl.Platform, cl.Device]`` or ``pycuda.driver.Device``
        dtype: ``str`` or ``torch.dtype``

    Returns:
        ``cl.Context``, ``pycuda.driver.Context``
        or ``None`` for other backends``.
    """
    global contexts
    # OpenCL variables declaration.
    if isinstance(backend, tuple) and len(backend) == 2 and \
       isinstance(backend[0], cl.Platform) and \
       isinstance(backend[1], cl.Device):
        # OpenCL and fp support.
        _support, msg = _fp_support(backend[0], dtype)
        if not _support:
            raise RuntimeError(msg)
       # Do we already have a cl.Context ?
        for i in range(len(contexts)):
            if isinstance(contexts[i], cl.Context) and \
               contexts[i].devices[0].platform.name == backend[0].name and \
               contexts[i].devices[0].name == backend[1].name:
                return contexts[i], i
        # If not create a new cl.Context.
        contexts.append(cl.Context(devices=[backend[1]]))
        return contexts[len(contexts) - 1], len(contexts) - 1
    elif (
            backend == (None, None) or
            backend == (None, 'cpu') or
            backend == (None, 'gpu')
    ):
        # Do we already have a cl.Context ?
        for i in range(len(contexts)):
            if isinstance(contexts[i], cl.Context):
                # OpenCL and fp support.
                if _fp_support(contexts[i].devices[0].platform,
                               dtype)[0]:
                    return contexts[i], i
        # If not create a new cl.Context.
        n_devices, no_fp_support = 0, False
        platforms = cl.get_platforms()
        for platform in platforms:
            # OpenCL and fp support.
            if not _fp_support(platform, dtype)[0]:
                no_fp_support = True
                continue
            devices = platform.get_devices(
                device_type=(
                    cl.device_type.GPU if backend[1] == 'gpu' else
                    cl.device_type.CPU))
            n_devices += len(devices)
            if len(devices) == 0:
                continue
            # Use the first device.
            contexts.append(cl.Context(devices=[devices[0]]))
            return contexts[len(contexts) - 1], len(contexts) - 1
        if no_fp_support:
            raise RuntimeError("backend does not support {dtype}.")
        if n_devices == 0:
            raise Exception("No device found.")
    elif cuda is not None and isinstance(backend, cuda.Device):
        # Do we already have a cuda.Context ?
        for i in range(len(contexts)):
            if (
                    isinstance(contexts[i], cuda.Context) and
                    contexts[i].get_device().name() == backend.name()
            ):
                # Push it at the top of the stack ?
                # PyCUDA ERROR: The context stack
                # was not empty upon module cleanup.
                contexts[i].push()
                return contexts[i], i
        # If not create a new cuda.Context.
        contexts.append(backend.make_context())
        return contexts[len(contexts) - 1], len(contexts) - 1
    elif (
            cuda is not None and
            isinstance(backend, str) and 'cuda' in backend
    ):
        # Do we already have a cuda.Context ?
        for i in range(len(contexts)):
            if isinstance(contexts[i], cuda.Context):
                # Push it at the top of the stack?
                # PyCUDA ERROR: The context stack
                # was not empty upon module cleanup.
                contexts[i].push()
                return contexts[i], i
        # If not create a new cuda.Context.
        for i in range(cuda.Device.count()):
            try:
                contexts.append(cuda.Device(i).make_context())
                return contexts[len(contexts) - 1], len(contexts) - 1
            except _cuda.LogicError:
                pass
    elif backend in ('cupy', 'ksmm', 'numpy',
                     'pytorch', 'scipy', 'xp'):
        # backend does not need context.
        # CuPy/PyTorch get device from ks_values.
        return None, -1
    else:
        raise Exception("backend not found.")


def _multiple_ksm(ks_values: list,
                  params: list = None, backend=(None, 'cpu'),
                  perm: bool = False, params_perm: tuple = None):
    """
    pyopencl and pycuda versions of ``multiple_ksm()``.
    """

    n_factors = len(ks_values)
    dtype = ks_values[0].dtype
    for i in range(1, n_factors):
        if dtype != ks_values[i].dtype:
            raise TypeError("All elements of ks_values" +
                            " must have the same dtype.")
    xp = array_namespace(ks_values[0])

    if cp is not None and 'cupy' in str(
            xp.__package__) and backend == 'ksmm':
        context, context_idx = None, -1
        is_opencl = False
        is_cuda = False
        is_cupy = True
        is_torch = False
    elif torch is not None and 'torch' in str(
            xp.__package__) and backend == 'ksmm':
        context, context_idx = None, -1
        is_opencl = False
        is_cuda = False
        is_cupy = False
        is_torch = True
    else:
        context, context_idx = _context(backend, ks_values[0].dtype)
        is_opencl = isinstance(context, cl.Context)
        is_cuda = not is_opencl
        is_cupy = False
        is_torch = False

    # Use this instance to keep track of the last batch size.
    # If batch size changes, we need to compute new hyper-parameters.
    ksm_data = Ksm_data()

    if is_opencl:
        # Create command queue
        queue = cl.CommandQueue(
            context,
            properties=cl.command_queue_properties.PROFILING_ENABLE)

    # Input and output sizes.
    a, b, c, d = ks_values[n_factors - 1].shape
    input_size = a * c * d
    a, b, c, d = ks_values[0].shape
    output_size = a * b * d

    # Device pointers of the Kronecker-Sparse values.
    patterns = []
    d_values, d_rvalues, = [None] * n_factors, [None] * n_factors
    # Array namespace of ks_values.
    xp = array_namespace(ks_values[0])
    for f in range(n_factors):
        # Transform ks_values from 4D to 2d array once and for all.
        if len(ks_values[f].shape) != 4:
            raise Exception("Element of ks_values must be a" +
                            " np.ndarray with four dimensions.")
        a, b, c, d = ks_values[f].shape
        patterns.append((a, b, c, d))
        if is_torch_array(ks_values[f]):
            d_values[f] = cp.from_dlpack(
                ks_values[f].permute(
                    0, 1, 3, 2).reshape(
                        a * d * b, c).contiguous())
        elif is_cupy_array(ks_values[f]):
            # CuPy array is already on the device.
            d_values[f] = xp.ascontiguousarray(
                xp.swapaxes(
                    ks_values[f], 2, 3).reshape(a * d * b, c))
        else:
            values = xp.ascontiguousarray(
                xp.swapaxes(ks_values[f], 2, 3).reshape(a * d * b, c))
        # Host to device.
        if is_opencl:
            d_values[f] = cl.Buffer(
                context,
                cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                hostbuf=values)
        elif is_cuda:
            d_values[f] = cuda.mem_alloc(values.nbytes)
            cuda.memcpy_htod(d_values[f], values)
            context.synchronize()

        # Transform acbd from 4D to 2d array once and for all.
        # The transpose of the support I_a\otimes 1_{b,c}\otimes I_d
        # is given by I_a\otimes 1_{c,b}\otimes I_d.
        a, b, c, d = ks_values[f].shape
        if is_torch_array(ks_values[f]):
            acbd = xp.conj(ks_values[f]).permute(0, 2, 1, 3)
            d_rvalues[f] = cp.from_dlpack(
                acbd.permute(
                    0, 1, 3, 2).reshape(
                        a * d * c, b).contiguous())
        elif is_cupy_array(ks_values[f]):
            # CuPy array is already on the device.
            acbd = xp.swapaxes(xp.conjugate(ks_values[f]), 1, 2)
            d_rvalues[f] = xp.ascontiguousarray(
                xp.swapaxes(
                    acbd, 2, 3).reshape(a * d * c, b))
        else:
            acbd = xp.swapaxes(xp.conjugate(ks_values[f]), 1, 2)
            rvalues = xp.ascontiguousarray(
                xp.swapaxes(acbd, 2, 3).reshape(a * d * c, b))
        # Host to device.
        if is_opencl:
            d_rvalues[f] = cl.Buffer(
                context,
                cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                hostbuf=rvalues)
        elif is_cuda:
            d_rvalues[f] = cuda.mem_alloc(rvalues.nbytes)
            cuda.memcpy_htod(d_rvalues[f], rvalues)
            context.synchronize()

    if perm:
        if is_torch:
            # Use DLPack to manipulate torch tensor as CuPy array.
            dp_bitrev_idx = cp.from_dlpack(
                bitrev(input_size) @ xp.arange(
                    input_size, dtype=torch.int32,
                    device=ks_values[0].device))
            dp_rbitrev_idx = cp.from_dlpack(
                bitrev(output_size) @ xp.arange(
                    output_size, dtype=torch.int32,
                    device=ks_values[0].device))
        elif is_cupy:
            dp_bitrev_idx = bitrev(input_size) @ xp.arange(
                input_size, dtype='int32', device=ks_values[0].device)
            dp_rbitrev_idx = bitrev(output_size) @ xp.arange(
                output_size, dtype='int32', device=ks_values[0].device)
        else:
            bitrev_idx = bitrev(input_size) @ xp.arange(
                input_size, dtype='int32', device=ks_values[0].device)
            rbitrev_idx = bitrev(output_size) @ xp.arange(
                output_size, dtype='int32', device=ks_values[0].device)
        # Use bit-reversal permutation for DFT.
        if is_opencl:
            dp_bitrev_idx = cl.Buffer(
                context,
                cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                hostbuf=bitrev_idx)
            dp_rbitrev_idx = cl.Buffer(
                context,
                cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                hostbuf=rbitrev_idx)
        elif is_cuda:
            dp_bitrev_idx = cuda.mem_alloc(bitrev_idx.nbytes)
            cuda.memcpy_htod(dp_bitrev_idx, bitrev_idx)
            dp_rbitrev_idx = cuda.mem_alloc(rbitrev_idx.nbytes)
            cuda.memcpy_htod(dp_rbitrev_idx, rbitrev_idx)
            context.synchronize()
        elif is_cupy:
            # CuPy arrays are already on the device.
            pass
        elif is_torch:
            # torch tensors are already on the device.
            pass
    else:
        dp_bitrev_idx, dp_rbitrev_idx = None, None

    # To keep track of the kernel duration.
    global kernel_duration
    m, n = len(kernel_duration), len(ks_values)
    if m < n:
        kernel_duration.extend([0.0] * (n - m))
    else:
        for i in range(n - m):
            kernel_duration.pop(i)

    def _kx(x, patterns, buf_val, context, adjoint,
            perm: bool = False, dp_perm=None):

        if is_cuda:
            context.push()

        # Shared memory and grid/block sizes.
        if is_opencl:
            smem = context.devices[0].get_info(cl.device_info.LOCAL_MEM_SIZE)
            max_block_dim = None
            max_grid_dim = None
        elif is_cuda:
            smem = context.get_device().get_attribute(
                _cuda.device_attribute.MAX_SHARED_MEMORY_PER_BLOCK)
            max_block_dim = (
                context.get_device().get_attribute(
                    cuda.device_attribute.MAX_BLOCK_DIM_X),
                context.get_device().get_attribute(
                    cuda.device_attribute.MAX_BLOCK_DIM_Y),
                context.get_device().get_attribute(
                    cuda.device_attribute.MAX_BLOCK_DIM_Z))
            max_grid_dim = (
                context.get_device().get_attribute(
                    cuda.device_attribute.MAX_GRID_DIM_X),
                context.get_device().get_attribute(
                    cuda.device_attribute.MAX_GRID_DIM_Y),
                context.get_device().get_attribute(
                    cuda.device_attribute.MAX_GRID_DIM_Z))
        elif is_cupy or is_torch:
            # Use device id of ks_values.
            if is_torch:
                _id = cp.cuda.Device(int(str(
                    ks_values[0].device).replace('cuda:', '')))
            else:
                _id = cp.cuda.Device(ks_values[0].device)
            smem = _id.attributes['MaxSharedMemoryPerBlock']
            max_block_dim = (
                _id.attributes['MaxBlockDimX'],
                _id.attributes['MaxBlockDimY'],
                _id.attributes['MaxBlockDimZ'])
            max_grid_dim = (
                _id.attributes['MaxGridDimX'],
                _id.attributes['MaxGridDimY'],
                _id.attributes['MaxGridDimZ'])

        if ksm_data.batch_size is None or ksm_data.batch_size != x.shape[1]:
            # Because of new batch size, reset data.
            # batch_size = None corresponds to the first call.
            new_batch_size = True
            ksm_data.batch_size = x.shape[1]
            ksm_data.hp = [None] * n_factors
            ksm_data.rhp = [None] * n_factors
            ksm_data.kernels = [None] * n_factors
            ksm_data.rkernels = [None] * n_factors
            ksm_data.program = [None] * n_factors
            ksm_data.rprogram = [None] * n_factors
            if perm:
                ksm_data.pbx = None
                ksm_data.pby = None
                ksm_data.b_program = None
        else:
            new_batch_size = False

        batch_size = x.shape[1]

        # Max output size.
        max_out_size = 0
        for i in range(n_factors):
            a, b, c, d = patterns[i]
            max_out_size = max(max_out_size,
                               a * c * d if adjoint else a * b * d)
        if is_torch:
            # Use DLPack to manipulate torch tensor as CuPy array.
            y = cp.from_dlpack(
                xp.empty((max_out_size, batch_size),
                         dtype=ks_values[0].dtype,
                         device=ks_values[0].device))
        else:
            y = xp.empty((max_out_size, batch_size),
                         dtype=ks_values[0].dtype,
                         device=ks_values[0].device)

        # Loop over the factors (from right to left).
        dp, read, store = [], 0, 1
        for i in range(n_factors - 1, -1, -1):
            idx = n_factors - 1 - i if adjoint else i
            kernel_duration[idx] = 0.0
            if ks_values[idx].dtype != x.dtype:
                x = x.astype(ks_values[idx].dtype)
                warnings.warn("Cast X to match the dtype of L.ks_values." +
                              " This can incur a loss of performance," +
                              " as-well-as a loss of precision if the dtype" +
                              " of X was initially of higher precision than" +
                              " that of L.ks_values.")
            a, b, c, d = patterns[idx]
            if new_batch_size:
                # Because of new batch size ...
                hp, rhp, knl, rknl = _modify_template(
                    a, b, c, d, x.shape[1],
                    smem, max_block_dim, max_grid_dim,
                    (None, None) if params is None else params[idx],
                    ks_values[idx].dtype, 'clh' if is_opencl else 'cuh')
                kernel = ''.join(knl)
                rkernel = ''.join(rknl)
                if perm:
                    # Read bit-reversal permutation kernel.
                    # Bit-reversal permutation matrix is its own transpose.
                    pbx, pby, pvsize, knl = _modify_template_bitrev_perm(
                        x.shape[0], x.shape[1],
                        smem, max_block_dim, max_grid_dim, params_perm,
                        ks_values[idx].dtype, 'clh' if is_opencl else 'cuh')
                    b_kernel = ''.join(knl)

                # Compile kernels (L and L.H).
                if is_opencl:
                    program = cl.Program(context, kernel).build()
                    rprogram = cl.Program(context, rkernel).build()
                elif is_cuda:
                    # Because of overloading function no_extern_c=True.
                    # Use extern "C" { __global__ void ksmm(...) {...} }.
                    program = SourceModule(kernel, no_extern_c=True)
                    rprogram = SourceModule(rkernel, no_extern_c=True)
                elif is_cupy or is_torch:
                    compiler = 'nvcc'
                    cpp = 11
                    options = []
                    for _c in ['03', '11', '12']:  # , '14', '17', '20']:
                        options.append(f"-I/usr/include/c++/{_c}")
                        options.append(f"-I/usr/include/x86_64-linux-gnu/c++/{_c}")
                        if compiler == 'nvrtc':
                            options.append(f"-I/usr/include/c++/{_c}/tr1")
                    if compiler == 'nvrtc':
                        options.append("-I/usr/include/linux")
                    options.append(f"--std=c++{cpp}")
                    if compiler == 'nvcc':
                        options.append("--x=cu")
                    options = tuple(options)
                    # Prefer RawModule over RawKernel here.
                    program = cp.RawModule(
                        code=kernel, options=options,
                        backend=compiler, translate_cucomplex=True).get_function('ksmm')
                    rprogram = cp.RawModule(
                        code=rkernel, options=options,
                        backend=compiler, translate_cucomplex=True).get_function('ksmm')
                if perm:
                    if is_opencl:
                        b_program = cl.Program(context, b_kernel).build()
                    elif is_cuda:
                        b_program = SourceModule(b_kernel, no_extern_c=True)
                    elif is_cupy or is_torch:
                        # Prefer RawModule over RawKernel here.
                        b_program = cp.RawModule(
                            code=b_kernel, options=options, backend=compiler,
                            translate_cucomplex=True).get_function('bitrev_perm')
                    ksm_data.pbx = pbx
                    ksm_data.pby = pby
                    ksm_data.pvsize = pvsize
                    ksm_data.b_program = b_program
                # Store data.
                ksm_data.hp[idx] = hp
                ksm_data.rhp[idx] = rhp
                ksm_data.program[idx] = program
                ksm_data.rprogram[idx] = rprogram
                ksm_data.kernels[idx] = kernel
                ksm_data.rkernels[idx] = rkernel
            else:
                # Read data for L and L.H.
                hp = ksm_data.hp[idx]
                rhp = ksm_data.rhp[idx]
                program = ksm_data.program[idx]
                rprogram = ksm_data.rprogram[idx]
                # kernel = ksm_data.kernels[idx]
                # rkernel = ksm_data.rkernels[idx]
                if perm:
                    pbx = ksm_data.pbx
                    pby = ksm_data.pby
                    pvsize = ksm_data.pvsize
                    b_program = ksm_data.b_program

            # Define the grid.
            if adjoint:
                out_size = a * c * d
                rntx, rnty = rhp[0] // rhp[3], rhp[2] // rhp[4]
                if is_opencl:
                    local_work_size = (rntx, rnty)
                    global_work_size = (
                        ((batch_size + rhp[0] - 1) // rhp[0]) * rntx,
                        ((out_size + rhp[2] - 1) // rhp[2]) * rnty)
                elif is_cuda:
                    block = (rntx, rnty, 1)
                    grid = ((batch_size + rhp[0] - 1) // rhp[0],
                            (out_size + rhp[2] - 1) // rhp[2], 1)
                elif is_cupy or is_torch:
                    block = (rntx, rnty, 1)
                    grid = ((batch_size + rhp[0] - 1) // rhp[0],
                            (out_size + rhp[2] - 1) // rhp[2], 1)
            else:
                out_size = a * b * d
                ntx, nty = hp[0] // hp[3], hp[2] // hp[4]
                if is_opencl:
                    local_work_size = (ntx, nty)
                    global_work_size = (
                        ((batch_size + hp[0] - 1) // hp[0]) * ntx,
                        ((out_size + hp[2] - 1) // hp[2]) * nty)
                elif is_cuda:
                    block = (ntx, nty, 1)
                    grid = ((batch_size + hp[0] - 1) // hp[0],
                            (out_size + hp[2] - 1) // hp[2], 1)
                elif is_cupy or is_torch:
                    block = (ntx, nty, 1)
                    grid = ((batch_size + hp[0] - 1) // hp[0],
                            (out_size + hp[2] - 1) // hp[2], 1)

            # print("local work size",
            #       local_work_size if is_opencl else block)
            # print("global work size",
            #       global_work_size if is_opencl else grid)

            # The kernel computes K @ X where the input K and X
            # are in row-major format.
            # The output y of the computation is in row-major format.
            # Host to device.
            not_contiguous = False
            if is_torch_array(x):
                not_contiguous = not x.is_contiguous()
            else:
                not_contiguous = not x.flags['C_CONTIGUOUS']
            if not_contiguous:
                warnings.warn("Cast X to be of C-contiguous type." +
                              " This can incur a loss of performance.")
            if i == (n_factors - 1):
                # Multiply most right factor with x.
                if is_opencl:
                    dp.append(cl.Buffer(
                        context,
                        cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                        hostbuf=x if x.flags['C_CONTIGUOUS'] else
                        np.ascontiguousarray(x)))
                elif is_cuda:
                    dp.append(cuda.mem_alloc(x.nbytes))
                    cuda.memcpy_htod(
                        dp[-1], x if x.flags['C_CONTIGUOUS'] else
                        np.ascontiguousarray(x))
                elif is_cupy:
                    # CuPy array is already on the device.
                    dp.append(x if x.flags['C_CONTIGUOUS'] else
                              cp.ascontiguousarray(x))
                elif is_torch:
                    dp.append(cp.from_dlpack(x if x.is_contiguous() else
                                             x.contiguous()))
                if is_opencl:
                    for _ in range(2):
                        dp.append(
                            cl.Buffer(context,
                                      cl.mem_flags.READ_WRITE, y.nbytes))
                elif is_cuda:
                    for _ in range(2):
                        dp.append(cuda.mem_alloc(y.nbytes))
                elif is_cupy:
                    for _ in range(2):
                        dp.append(xp.empty((max_out_size, batch_size),
                                           dtype=ks_values[0].dtype,
                                           device=ks_values[0].device))
                elif is_torch:
                    for _ in range(2):
                        dp.append(cp.from_dlpack(
                            xp.empty((max_out_size, batch_size),
                                     dtype=ks_values[0].dtype,
                                     device=ks_values[0].device)))
            # Run the kernel.
            bb = np.uint32(c if adjoint else b)
            cc = np.uint32(b if adjoint else c)
            if is_opencl:
                if perm and i == (n_factors - 1) and not adjoint:
                    # Apply bit-reversal permutation to x (right-most factor).
                    knl = cl.Kernel(b_program, 'bitrev_perm')
                    knl.set_args(dp_perm,
                                 dp[read], dp[store],
                                 np.uint32(batch_size))
                    event = cl.enqueue_nd_range_kernel(
                        queue, knl,
                        (((x.shape[1] + pvsize * pbx - 1)
                          // (pvsize * pbx)) * pbx,
                         ((x.shape[0] + pby - 1) // pby) * pby, 1),
                        (pbx, pby, 1))
                    event.wait()
                    complete = cl.command_execution_status.COMPLETE
                    if event.command_execution_status != complete:
                        raise Exception("OpenCL command execution" +
                                        " status is not complete.")
                    kernel_duration[idx] += 1e-9 * (event.profile.end
                                                    - event.profile.start)
                    read, store = 1, 2
                # Kronecker-sparse multiplication.
                # knl = rprogram.ksmm if adjoint else program.ksmm
                if adjoint:
                    knl = cl.Kernel(rprogram, 'ksmm')
                else:
                    knl = cl.Kernel(program, 'ksmm')
                knl.set_args(
                    buf_val[idx],
                    dp[read], dp[store],
                    np.uint32(a), bb, cc, np.uint32(d),
                    np.uint32(batch_size))
                event = cl.enqueue_nd_range_kernel(
                    queue, knl, global_work_size, local_work_size)
                event.wait()
                kernel_duration[idx] += 1e-9 * (event.profile.end
                                                - event.profile.start)
                complete = cl.command_execution_status.COMPLETE
                if event.command_execution_status != complete:
                    raise Exception("OpenCL command execution" +
                                    " status is not complete.")
                if perm and i == 0 and adjoint:
                    # Apply bit-reversal permutation to x.
                    # Because of adjoint, bit-reversal permutation
                    # is the left-most factor.
                    read, store = store, read
                    knl = cl.Kernel(b_program, 'bitrev_perm')
                    knl.set_args(dp_perm,
                                 dp[read], dp[store],
                                 np.uint32(batch_size))
                    event = cl.enqueue_nd_range_kernel(
                        queue, knl,
                        (((x.shape[1] + pbx * pvsize - 1) // (pbx * pvsize)) * pbx,
                         ((x.shape[0] + pby - 1) // pby) * pby, 1),
                        (pbx, pby, 1))
                    event.wait()
                    complete = cl.command_execution_status.COMPLETE
                    if event.command_execution_status != complete:
                        raise Exception("OpenCL command execution" +
                                        " status is not complete.")
                    kernel_duration[idx] += 1e-9 * (
                        event.profile.end - event.profile.start)
            elif is_cuda:
                if perm and i == (n_factors - 1) and not adjoint:
                    # Apply bit-reversal permutation to x (right-most factor).
                    knl = b_program.get_function('bitrev_perm')
                    start, end = cuda.Event(), cuda.Event()
                    start.record()
                    knl(dp_perm,
                        dp[read], dp[store],
                        np.uint32(batch_size),
                        block=(pbx, pby, 1),
                        grid=((x.shape[1] + pbx * pvsize - 1)
                              // (pbx * pvsize),
                              (x.shape[0] + pby - 1) // pby, 1))
                    context.synchronize()
                    end.record()
                    end.synchronize()
                    kernel_duration[idx] += 1e-3 * end.time_since(start)
                    read, store = 1, 2
                # Kronecker-sparse multiplication.
                knl = (rprogram if adjoint else program).get_function('ksmm')
                start, end = cuda.Event(), cuda.Event()  # ???
                start.record()  # ???
                # No extern shared memory,
                # therefore do not use shared argument.
                knl(buf_val[idx],
                    dp[read], dp[store],
                    np.uint32(a), bb, cc, np.uint32(d),
                    np.uint32(batch_size),
                    block=block,
                    grid=grid)
                context.synchronize()
                end.record()  # ???
                end.synchronize()  # ???
                kernel_duration[idx] += 1e-3 * end.time_since(start)  # ???
                if perm and i == 0 and adjoint:
                    # Apply bit-reversal permutation to x.
                    # Because of adjoint, bit-reversal permutation
                    # is the left-most factor.
                    read, store = store, read
                    knl = b_program.get_function('bitrev_perm')
                    start, end = cuda.Event(), cuda.Event()
                    start.record()
                    knl(dp_perm,
                        dp[read], dp[store],
                        np.uint32(batch_size),
                        block=(pbx, pby, 1),
                        grid=((x.shape[1] + pvsize * pbx - 1)
                              // (pvsize * pbx),
                              (x.shape[0] + pby - 1) // pby, 1))
                    context.synchronize()
                    end.record()
                    end.synchronize()
                    kernel_duration[idx] += 1e-3 * end.time_since(start)
            elif is_cupy or is_torch:
                if perm and i == (n_factors - 1) and not adjoint:
                    # Apply bit-reversal permutation to x (right-most factor).
                    b_program(((x.shape[1] + pbx * pvsize - 1)
                               // (pbx * pvsize),
                               (x.shape[0] + pby - 1) // pby, 1),
                              (pbx, pby, 1),
                              (dp_perm, dp[read], dp[store], batch_size))
                    read, store = 1, 2
                # Last multiplication?
                last = i == 0 and not (perm and adjoint)
                # Kronecker-sparse multiplication.
                knl = rprogram if adjoint else program
                knl(grid, block,
                    (buf_val[idx],
                     dp[read], y if last else dp[store],
                     a, bb, cc, d, batch_size))
                if perm and i == 0 and adjoint:
                    # Apply bit-reversal permutation to x.
                    # Because of adjoint, bit-reversal permutation
                    # is the left-most factor.
                    read, store = store, read
                    b_program(((x.shape[1] + pvsize * pbx - 1)
                               // (pvsize * pbx),
                               (x.shape[0] + pby - 1) // pby, 1),
                              (pbx, pby, 1),
                              (dp_perm, dp[read], y, batch_size))
                cp.cuda.Stream.null.synchronize()  # ???
            # Get the output after multiplication
            # with the most left factor.
            if i == 0:
                if is_opencl:
                    event = cl.enqueue_copy(queue, y, dp[store])
                    event.wait()
                    complete = cl.command_execution_status.COMPLETE
                    if event.command_execution_status != complete:
                        raise Exception("OpenCL command execution" +
                                        " status is not complete.")
                elif is_cuda:
                    cuda.memcpy_dtoh(y, dp[store])
                    context.synchronize()
                elif is_cupy:
                    # CuPy array result stays on the device.
                    pass
                elif is_torch:
                    # torch tensor result stays on the device.
                    y = torch.from_dlpack(y)
            else:
                if read == 0:
                    read, store = 1, 2
                else:
                    read, store = store, read
        if is_opencl:
            for i in range(3):
                dp[i].release()
        elif is_cuda:
            for i in range(3):
                dp[i].free()
            context.synchronize()
        if max_out_size == (input_size if adjoint else output_size):
            return y
        else:
            return y[:(input_size if adjoint else output_size), :]

    L = LazyLinOp(
        shape=(output_size, input_size),
        matmat=lambda x: _kx(x, patterns, d_values, context, False,
                             perm, dp_bitrev_idx),
        rmatmat=lambda x: _kx(x, patterns, d_rvalues, context, True,
                              perm, dp_rbitrev_idx)
    )

    L.context = context
    L.context_idx = context_idx

    if is_opencl or is_cuda:
        L.device_pointers = [None] * (2 * n_factors)
        for f in range(n_factors):
            L.device_pointers[f] = d_values[f]
            L.device_pointers[n_factors + f] = d_rvalues[f]
        if perm:
            L.device_pointers.append(dp_bitrev_idx)
            L.device_pointers.append(dp_rbitrev_idx)
    else:
        # CuPy arrays are already on the device.
        pass

    L.kernel_duration = kernel_duration

    return L


def _ksm_xp(ks_values):
    """
    CuPy, NumPy and PyTorch version of ``ksm()``.
    """

    xp = array_namespace(ks_values)

    a, b, c, d = ks_values.shape
    if 'torch' in str(xp.__package__):
        # values = xp.einsum("abcd->bcad", ks_values).clone()
        values = xp.einsum("abcd->bcad", ks_values)
        # rvalues = xp.einsum(
        #     "acbd->cbad", xp.conj(ks_values).swapaxes(1, 2)).clone()
        rvalues = xp.einsum(
            "acbd->cbad", xp.conj(ks_values).swapaxes(1, 2))
    else:
        # values = xp.einsum("abcd->bcad", ks_values).copy(order="F")
        values = xp.einsum("abcd->bcad", ks_values)
        # rvalues = xp.einsum(
        #     "acbd->cbad", xp.conj(ks_values).swapaxes(1, 2)).copy(order="F")
        rvalues = xp.einsum(
            "acbd->cbad", xp.conj(ks_values).swapaxes(1, 2))

    def ksm_matmat(x, rmatmat=False):
        if not rmatmat:
            v = values
        else:
            v = rvalues

        dtype = (ks_values[0, 0, 0, :1] * x[0, :1]).dtype
        if x.ndim == 1:
            x = x.reshape(-1, 1)
        B = x.shape[1]
        x = x.reshape(a, c if not rmatmat else b, d, B)

        r = xp.empty((a, d, b if not rmatmat else c, B), dtype=dtype,
                     device=ks_values.device)
        if 'torch' in str(xp.__package__):
            for i_a, i_d in itertools.product(range(a), range(d)):
                xi = x[i_a, :, i_d, :]  # .clone()
                r[i_a, i_d] = v[:, :, i_a, i_d] @ xi
        else:
            for i_a, i_d in itertools.product(range(a), range(d)):
                xi = x[i_a, :, i_d, :]  # .copy(order='F')
                r[i_a, i_d] = v[:, :, i_a, i_d] @ xi

        return r.swapaxes(1, 2).reshape(-1, B)

    return LazyLinOp(
        shape=(a * b * d, a * c * d),
        matmat=lambda x: ksm_matmat(x),
        rmatmat=lambda x: ksm_matmat(x, True)
    )


def _ksm_scipy(ks_values: np.ndarray):
    """
    SciPy version of ``ksm()``.
    """

    if not is_numpy_array(ks_values):
        raise TypeError("backend='scipy', ks_values must be NumPy array.")

    from scipy.sparse import block_diag, csr_matrix

    a, b, c, d = ks_values.shape

    rows = np.arange(b * d)
    # Compute length of indices array.
    size = 0
    for i in rows:
        size += int(np.ceil((c * d - i % d) / d))
    # Fill indices array.
    indices = np.empty(size, dtype='int')
    cum = 0
    for i in rows:
        size = int(np.ceil((c * d - i % d) / d))
        indices[cum:(cum + size)] = np.arange(i % d, c * d, d)
        cum += size
    indptr = np.array([0] + [(i + 1) * c for i in range(b * d)])

    # Block-diagonal matrix with a block(s).
    B = block_diag([
        csr_matrix(
            (
                ks_values[i, :, :, :].swapaxes(1, 2).reshape(b * d, c).ravel(),
                indices,
                indptr
            ), shape=(b * d, c * d)) for i in range(a)])

    L = LazyLinOp(
        shape=(a * b * d, a * c * d),
        matmat=lambda x: B @ x,
        rmatmat=lambda x: B.T.conj() @ x
    )

    L.context = None
    L.context_idx = -1

    return L


def _ksm_cupyx(ks_values):
    """
    ``cupyx.scipy`` version of ``ksm()``.
    """

    if not is_cupy_array(ks_values):
        raise TypeError("backend='cupyx.scipy'," +
                        " ks_values must be CuPy array.")

    from cupyx.scipy.sparse import csr_matrix

    a, b, c, d = ks_values.shape

    # Fill indices array.
    device = ks_values.device
    cp.cuda.runtime.setDevice(device)
    indices = cp.empty(a * b * c * d, dtype='int')
    for r in range(a * b * d):
        # Index of the block.
        i = r // (b * d)
        # Row inside the block.
        _r = r - i * b * d
        indices[(r * c):((r + 1) * c)] = i * c * d + cp.arange(_r % d, c * d, d)
    indptr = cp.asarray([0] + [(i + 1) * c for i in range(a * b * d)])

    # Block-diagonal matrix with a block(s).
    values = cp.empty(a * b * c * d, dtype=ks_values.dtype)
    for i in range(a):
        values[(i * b * c * d):((i + 1) * b * c * d)] = ks_values[
            i, :, :, :].swapaxes(1, 2).reshape(b * d, c).ravel()
    B = csr_matrix(
        (values, indices, indptr), shape=(a * b * d, a * c * d))
    C = B.T.conj()

    L = LazyLinOp(
        shape=(a * b * d, a * c * d),
        matmat=lambda x: B @ x,
        rmatmat=lambda x: C @ x
    )

    L.context = None
    L.context_idx = -1

    return L


def _time_ksm(ks_values: list, x: np.ndarray,
              n_runs: int = 100, n_repeats: int = 100,
              params: list = None, backend=(None, 'cpu'),
              perm: bool = False, params_perm: list = None):
    """
    Function to compute duration time of OpenCL and CUDA kernels.

    Args:
        ks_values: ``list``
            See :py:func:`ksm` for more details.
        x: ``np.ndarray``
            Input array used by the product ``y = K @ x``.
        n_runs: ``int`` optional
            Run the product ``K @ x`` this number of times.
        n_repeats: ``int`` optional
            For each run, repeat ``K @ x`` this number of times.
        params: ``list``, optional
            A list of hyper-parameters to benchmark.

            - ``params`` must be a ``list``.
            - ``params[i]`` must be a ``list``.
            - ``len(params[i])`` must be equal to ``len(ks_values)``.
            - ``params[i][j]`` must be a ``tuple`` (matmat and rmatmat).
            See :py:func:`ksm` for more details.
            The default value is ``None`` (use default hyper-parameters).
        backend: ``str``, ``tuple`` or ``pycuda.driver.Device``, optional
            See :py:func:`ksm` for more details.
        perm: ``bool``, optional
            Multiply input array by a bit-reversal permutation matrix.
            Default value is ``False``.
        params_perm: ``list``, optional
            A list of hyper-parameters for the bit-reversal permutation
            kernel to benchmark.

            - ``params_perm`` must be a ``list``.
            - ``params_perm[i]`` must be a ``tuple``.
            - ``len(params_perm[i])`` must be equal to ``len(ks_values)``.
            The default value is ``None`` (use default hyper-parameters).

    Returns:
        A ``tuple`` ``(y, duration)`` where ``y`` is the output
        and ``duration`` the duration time divided by the batch size
        for each factor and for each run.
        The shape of ``duration`` is
        ``(len(params), n_runs, len(ks_values) + int(perm))``.

    .. seealso::
        - :py:func:`ksm`
    """

    n_factors = len(ks_values)
    dtype = ks_values[0].dtype
    if not isinstance(ks_values, list):
        raise TypeError("ks_values must be a list.")
    for i in range(1, n_factors):
        if dtype != ks_values[i].dtype:
            raise TypeError("All elements of ks_values" +
                            " must have the same dtype.")

    context, context_idx = _context(backend)
    is_opencl = isinstance(context, cl.Context)

    if is_opencl:
        # Create command queue
        queue = cl.CommandQueue(
            context,
            properties=cl.command_queue_properties.PROFILING_ENABLE)

    # Input and output sizes.
    a, b, c, d = ks_values[n_factors - 1].shape
    input_size = a * c * d
    a, b, c, d = ks_values[0].shape
    output_size = a * b * d

    d_values, patterns = [], []
    for f in range(n_factors):
        # Transform ks_values from 4D to 2d array once and for all.
        if len(ks_values[f].shape) != 4:
            raise Exception("Element of ks_values must be a" +
                            " np.ndarray with four dimensions.")
        a, b, c, d = ks_values[f].shape
        patterns.append((a, b, c, d))
        values = np.ascontiguousarray(
            np.swapaxes(ks_values[f], 2, 3).reshape(a * d * b, c))
        # Host to device.
        if is_opencl:
            d_values.append(
                cl.Buffer(
                    context,
                    cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                    hostbuf=values))
        else:
            d_values.append(cuda.mem_alloc(values.nbytes))
            cuda.memcpy_htod(d_values[f], values)
            context.synchronize()

    bitrev_idx = bitrev(x.shape[0]) @ np.arange(x.shape[0]).astype('int32')
    if perm:
        # Use bit-reversal permutation for DFT.
        if is_opencl:
            dp_bitrev_idx = cl.Buffer(
                context,
                cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                hostbuf=bitrev_idx)
        else:
            dp_bitrev_idx = cuda.mem_alloc(bitrev_idx.nbytes)
            cuda.memcpy_htod(dp_bitrev_idx, bitrev_idx)
            context.synchronize()
    else:
        dp_bitrev_idx = None

    def _kx(x, patterns, buf_val, context,
            perm: bool = False, dp_perm=None):

        if not is_opencl:
            context.push()

        # Shared memory and grid/block sizes.
        if is_opencl:
            smem = context.devices[0].get_info(cl.device_info.LOCAL_MEM_SIZE)
            max_block_dim = None
            max_grid_dim = None
        else:
            smem = context.get_device().get_attribute(
                _cuda.device_attribute.MAX_SHARED_MEMORY_PER_BLOCK)
            max_block_dim = (
                context.get_device().get_attribute(
                    cuda.device_attribute.MAX_BLOCK_DIM_X),
                context.get_device().get_attribute(
                    cuda.device_attribute.MAX_BLOCK_DIM_Y),
                context.get_device().get_attribute(
                    cuda.device_attribute.MAX_BLOCK_DIM_Z))
            max_grid_dim = (
                context.get_device().get_attribute(
                    cuda.device_attribute.MAX_GRID_DIM_X),
                context.get_device().get_attribute(
                    cuda.device_attribute.MAX_GRID_DIM_Y),
                context.get_device().get_attribute(
                    cuda.device_attribute.MAX_GRID_DIM_Z))

        if x.ndim == 1:
            batch_size = 1
        else:
            batch_size = x.shape[1]

        # Max output size.
        max_out_size = 0
        for i in range(n_factors):
            a, b, c, d = patterns[i]
            max_out_size = max(max_out_size, a * b * d)
        y = np.empty((max_out_size, batch_size),
                     dtype=ks_values[0].dtype)

        if params is None:
            # Default hyper-parameters: use the largest tile values.
            hparams = [[(None, None)] * n_factors]
            for i in range(n_factors):
                a, b, c, d = patterns[i]
                hparams[0][i] = (
                    _find_hyper_parameters(
                        a, b, c, d, batch_size,
                        smem, ks_values[0].dtype.itemsize,
                        max_block_dim, max_grid_dim),
                    _find_hyper_parameters(
                        a, c, b, d, batch_size,
                        smem, ks_values[0].dtype.itemsize,
                        max_block_dim, max_grid_dim))
        else:
            hparams = params
        n_hp = len(hparams)
        if params_perm is None:
            # Default hyper-parameters: use the largest tile values.
            hparams_perm = [_find_all_hyper_parameters_perm(
                x.shape[0], batch_size, max_block_dim, max_grid_dim)[0]]
        else:
            hparams_perm = params_perm
        n_hp_perm = len(hparams_perm)

        # Loop over the hyper-parameters.
        n_tests = len(hparams)
        duration = np.zeros((n_tests, n_runs, n_factors + int(perm)))
        dp = []
        msg = ("params must be a list," +
               " params[i] must be a list" +
               " and params[i][j] must be a tuple (matmat and rmatmat).")
        for h in range(n_tests):
            if not isinstance(hparams[h], list):
                raise TypeError(msg)
            read, store = 0, 1
            if perm:
                # Read bit-reversal permutation kernel and compile it.
                pbx, pby, pvsize, knl = _modify_template_bitrev_perm(
                    x.shape[0], batch_size,
                    smem, max_block_dim, max_grid_dim,
                    hparams_perm[h], ks_values[i].dtype,
                    'clh' if is_opencl else 'cuh')
                b_kernel = ''.join(knl)
                if is_opencl:
                    b_program = cl.Program(context, b_kernel).build()
                else:
                    b_program = SourceModule(b_kernel, no_extern_c=True)
            # Loop over the factors (from right to left).
            for i in range(n_factors - 1, -1, -1):
                if not isinstance(hparams[h][i], tuple):
                    raise TypeError(msg)
                # Read kernel.
                if ks_values[i].dtype != x.dtype:
                    x = x.astype(ks_values[i].dtype)
                    warnings.warn(
                        "Cast X to match the dtype of L.ks_values." +
                        " This can incur a loss of performance," +
                        " as-well-as a loss of precision if the dtype" +
                        " of X was initially of higher precision than" +
                        " that of L.ks_values.")
                a, b, c, d = patterns[i]
                hp, rhp, knl, rknl = _modify_template(
                    a, b, c, d, batch_size,
                    smem, max_block_dim, max_grid_dim,
                    hparams[h][i], ks_values[i].dtype,
                    'clh' if is_opencl else 'cuh')
                kernel = ''.join(knl)
                rkernel = ''.join(rknl)

                # Compile kernel.
                if is_opencl:
                    program = cl.Program(context, kernel).build()
                else:
                    # Because of overloading function no_extern_c=True.
                    # Use extern "C" { __global__ void ksmm(...) {...} }.
                    program = SourceModule(kernel, no_extern_c=True)

                # Define the grid.
                out_size = a * b * d
                ntx, nty = hp[0] // hp[3], hp[2] // hp[4]
                if is_opencl:
                    local_work_size = (ntx, nty)
                    global_work_size = (
                        ((batch_size + hp[0] - 1) // hp[0]) * ntx,
                        ((out_size + hp[2] - 1) // hp[2]) * nty)
                else:
                    block = (ntx, nty, 1)
                    grid = ((batch_size + hp[0] - 1) // hp[0],
                            (out_size + hp[2] - 1) // hp[2], 1)

                # The kernel computes K @ X where the input K and X
                # are in row-major format.
                # The output y of the computation is in row-major format.
                # Host to device.
                if not x.flags['C_CONTIGUOUS']:
                    warnings.warn("Cast X to be of C-contiguous type." +
                                  " This can incur a loss of performance.")
                if h == 0 and i == (n_factors - 1):
                    # Multiply most right factor with x.
                    if is_opencl:
                        dp.append(
                            cl.Buffer(
                                context,
                                cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                                hostbuf=x if x.flags['C_CONTIGUOUS'] else np.ascontiguousarray(x)
                            )
                        )
                        for _ in range(2):
                            dp.append(
                                cl.Buffer(context,
                                          cl.mem_flags.READ_WRITE, y.nbytes))
                    else:
                        dp.append(cuda.mem_alloc(x.nbytes))
                        cuda.memcpy_htod(
                            dp[-1], x if x.flags['C_CONTIGUOUS'] else
                            np.ascontiguousarray(x))
                        for _ in range(2):
                            dp.append(cuda.mem_alloc(y.nbytes))
                # Run the kernel.
                for j in range(n_runs):
                    for _ in range(n_repeats):
                        if is_opencl:
                            if perm and i == (n_factors - 1):
                                # Apply bit-reversal permutation to x.
                                knl = cl.Kernel(b_program, 'bitrev_perm')
                                knl.set_args(dp_perm, dp[0], dp[1],
                                             np.uint32(batch_size))
                                event = cl.enqueue_nd_range_kernel(
                                    queue, knl,
                                    (((batch_size + pvsize * pbx - 1)
                                      // (pvsize * pbx)) * pbx,
                                     ((x.shape[0] + pby - 1) // pby) * pby, 1),
                                    (pbx, pby, 1))
                                event.wait()
                                complete = cl.command_execution_status.COMPLETE
                                if event.command_execution_status != complete:
                                    raise Exception(
                                        "OpenCL command execution" +
                                        " status is not complete.")
                                duration[h, j, -1] += 1e-9 * (
                                    event.profile.end - event.profile.start)
                                read, store = 1, 2
                            # Kronecker-sparse multiplication.
                            knl = cl.Kernel(program, 'ksmm')
                            knl.set_args(buf_val[i], dp[read], dp[store],
                                         np.uint32(a), np.uint32(b),
                                         np.uint32(c), np.uint32(d),
                                         np.uint32(batch_size))
                            # Record kernel duration using OpenCL event.
                            event = cl.enqueue_nd_range_kernel(
                                queue, knl, global_work_size, local_work_size)
                            event.wait()
                            complete = cl.command_execution_status.COMPLETE
                            if event.command_execution_status != complete:
                                raise Exception("OpenCL command execution" +
                                                " status is not complete.")
                            duration[h, j, i] += 1e-9 * (event.profile.end
                                                         - event.profile.start)
                        else:
                            if perm and i == (n_factors - 1):
                                # Apply bit-reversal permutation to x.
                                knl = b_program.get_function('bitrev_perm')
                                start, end = cuda.Event(), cuda.Event()
                                start.record()
                                knl(dp_perm, dp[0], dp[1],
                                    np.uint32(batch_size),
                                    block=(pbx, pby, 1),
                                    grid=((batch_size +
                                           pvsize * pbx - 1) // (pvsize * pbx),
                                          (x.shape[0] + pby - 1) // pby, 1))
                                context.synchronize()
                                end.record()
                                end.synchronize()
                                duration[h, j, -1] += 1e-3 * end.time_since(
                                    start)
                                read, store = 1, 2
                            # Kronecker-sparse multiplication.
                            knl = program.get_function('ksmm')
                            # Record kernel duration using CUDA event.
                            start, end = cuda.Event(), cuda.Event()
                            start.record()
                            knl(buf_val[i], dp[read], dp[store],
                                np.uint32(a), np.uint32(b),
                                np.uint32(c), np.uint32(d),
                                np.uint32(batch_size),
                                block=block,
                                grid=grid)
                            context.synchronize()
                            end.record()
                            end.synchronize()
                            duration[h, j, i] += 1e-3 * end.time_since(start)
                # print(f"test {h}/{n_tests} factor={i} {n_runs}x{n_repeats}",
                #       duration[h, j, i])
                if read == 0:
                    read, store = 1, 2
                else:
                    read, store = store, read
            # Get the output after multiplication
            # with the most left factor.
            if h == (n_tests - 1) and i == 0:
                if is_opencl:
                    event = cl.enqueue_copy(queue, y, dp[read])
                    event.wait()
                    complete = cl.command_execution_status.COMPLETE
                    if event.command_execution_status != complete:
                        raise Exception("OpenCL command execution" +
                                        " status is not complete.")
                else:
                    cuda.memcpy_dtoh(y, dp[read])
                    context.synchronize()
        if is_opencl:
            for i in range(3):
                dp[i].release()
        else:
            for i in range(3):
                dp[i].free()
            context.synchronize()
        del dp
        if max_out_size == output_size:
            return y, duration
        else:
            return y[:output_size, :], duration

    y, duration = _kx(x, patterns,
                      d_values, context, perm, dp_bitrev_idx)
    if x.ndim == 1:
        y = y.ravel()
    np.divide(duration,
              n_repeats * (1 if x.ndim == 1 else x.shape[1]), out=duration)

    for i in range(len(d_values)):
        if is_opencl:
            d_values[i].release()
        else:
            d_values[i].free()
            context.synchronize()
    if perm:
        if is_opencl:
            dp_bitrev_idx.release()
        else:
            dp_bitrev_idx.free()
            context.synchronize()

    if not is_opencl:
        context.pop()
    del d_values, dp_bitrev_idx, context

    return y, duration


def save(L: LazyLinOp, name: str):
    """
    Save the instance ``L`` of :class:`LazyLinOp`
    returned by ``L = ksm(...)`` or ``L = ksd(...)`` function.
    Save the result of the factorization
    in a json file ``name + '.json'``.

    Args:
        L: ``LazyLinOp``
            The ``LazyLinOp`` ``L`` to save.
        name: ``str``
            Name of the file.

    .. seealso::
        - :func:`load`.

    Examples:
        >>> import scipy as sp
        >>> import numpy as np
        >>> from lazylinop.butterfly import Chain, ksd, load, save
        >>> H = sp.linalg.hadamard(8)
        >>> x = np.random.randn(8)
        >>> chain = Chain.square_dyadic(H.shape)
        >>> L = ksd(H, chain)
        >>> save(L, "hadamard_8x8")
        >>> L_ = load("hadamard_8x8")
        >>> y = L @ x
        >>> y_ = L_ @ x
        >>> np.allclose(y, y_)
        True
    """
    if not islazylinop(L):
        raise Exception("L must be an instance of LazyLinOp class.")
    # Save result of factorization in a json file.
    data = {}
    for i in range(len(L.ks_values)):
        data["factor" + str(i)] = {}
        if is_torch_array(L.ks_values[i]):
            data["factor" + str(i)]['package'] = 'torch'
        elif isinstance(L.ks_values[i], np.ndarray):
            data["factor" + str(i)]['package'] = 'numpy'
        else:
            data["factor" + str(i)]['package'] = 'none'
        # Store current factor in a dict.
        data["factor" + str(i)]['ks_patterns'] = L.ks_patterns[i]
        data["factor" + str(i)][
            'ks_values_real'] = L.ks_values[i].real.tolist()
        if 'complex' in str(L.ks_values[i].dtype):
            data["factor" + str(i)][
                'ks_values_imag'] = L.ks_values[i].imag.tolist()
        data["factor" + str(i)]['dtype'] = str(L.ks_values[i].dtype)
        data["factor" + str(i)]['params'] = L.params[i]
        data["factor" + str(i)]['backend'] = L.backend
    with open(name + '.json', 'w') as f:
        json.dump(data, f, indent=1)


def load(name: str):
    """
    Load the :class:`.LazyLinOp` ``L`` from file ``name.json``.
    The file ``name.json`` has been created by :func:`save`.

    Args:
        name: ``str``
            Name of the ``.json`` file where to load ``L``.

    Returns:
        ``L`` is a :class:`.LazyLinOp`
        that corresponds to the product of ``n_patterns``
        :class:`.LazyLinOp` each one returned by :func:`ksm`.
        If file does not exist, return ``None``.

    .. seealso::
        - :func:`save`.

    Examples:
        >>> import scipy as sp
        >>> import numpy as np
        >>> from lazylinop.butterfly import Chain, ksd, load, save
        >>> H = sp.linalg.hadamard(8)
        >>> x = np.random.randn(8)
        >>> chain = Chain.square_dyadic(H.shape)
        >>> A = ksd(H, chain)
        >>> save(A, "hadamard_8x8")
        >>> A_ = load("hadamard_8x8")
        >>> y = A @ x
        >>> y_ = A_ @ x
        >>> np.allclose(y, y_)
        True
    """
    try:
        L, ks_patterns = None, []
        with open(name + '.json', 'r') as f:
            data = json.load(f)
            # Loop over the Kronecker-sparse factors.
            ks_values, params, backend = [], [], []
            for k in data.keys():
                if 'complex' in str(data[k]['dtype']):
                    ks_values.append(
                        np.asarray(data[k]['ks_values_real']).astype(
                            data[k]['dtype']) +
                        (1j * np.asarray(data[k]['ks_values_imag'])).astype(
                            data[k]['dtype']))
                else:
                    ks_values.append(
                        np.asarray(data[k]['ks_values_real']).astype(
                            data[k]['dtype']))
                params.append(data[k]['params'])
                backend.append(data[k]['backend'])
                ks_patterns.append(data[k]['ks_patterns'])
            L = ksm(ks_values, params, backend[0])
            L.ks_values = ks_values
        return L
    except IOError:
        raise IOError(f"Did not find {name}.json.")


def plot(L, name: str = None):
    """
    Plot ``L.ks_values`` on a logarithmic scale.
    If ``ks_values`` is complex
    plot ``xp.sqrt(ks_values * xp.conj(ks_values))``.
    Matplotlib package must be installed.

    Args:
        name: ``str``
            Save the plot in both PNG file ``name + '.png'``
            and SVG file ``name + '.svg'``.
            Default value is ``None`` (it only draws
            the ``L.ks_values``).

    Examples:
        >>> from lazylinop.butterfly import dft
        >>> from lazylinop.butterfly import plot
        >>> N = 16
        >>> L = dft(N)
        >>> plot(L)
    """

    if not hasattr(L, "ks_values"):
        warnings.warn("L does not have ks_values attribute," +
                      " do nothing.")
        return 0

    xp = array_namespace(L.ks_values[0])

    import matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.colors as clr
    from matplotlib.patches import Rectangle
    from matplotlib.collections import PatchCollection
    plt.rcParams.update({"font.size": 16})
    plt.rcParams.update({"lines.linewidth": 8})
    plt.rcParams.update({"lines.markersize": 6})
    # plt.rcParams.update({"legend.fontsize": 4})

    cmap = plt.get_cmap("rainbow")

    n = len(L.ks_values)
    _device = L.ks_values[0].device
    s, t = n, 1
    X, Y = 0, 0
    min_ksv = xp.full(len(L.ks_values), 0.0, device=_device)
    max_ksv = xp.full(len(L.ks_values), 0.0, device=_device)
    for i, k in enumerate(L.ks_values):
        a, b, c, d = k.shape
        X += a * c * d + 1
        Y = max(Y, a * b * d)
        if 'complex' in str(k.dtype):
            min_ksv[i] = xp.min(xp.sqrt(xp.real(k * xp.conj(k))))
            max_ksv[i] = xp.max(xp.sqrt(xp.real(k * xp.conj(k))))
        else:
            min_ksv[i] = xp.min(k)
            max_ksv[i] = xp.max(k)
    # To avoid divide by zero.
    min_ksv = xp.min(min_ksv)
    max_ksv = xp.max(max_ksv)
    # Handle the case ks_values entries are all the same.
    if xp.absolute(max_ksv - min_ksv) < (
            10.0 * xp.finfo(max_ksv.dtype).eps):
        max_ksv = min_ksv
        norm = 1.0
    else:
        norm = xp.pow(xp.log2(max_ksv - min_ksv), -1)

    px = 1 / plt.rcParams['figure.dpi']
    # fig = plt.figure("draw", figsize=(640 * px, 480 * px))
    # plt.gca().set_aspect('equal')
    fig = plt.figure("draw", figsize=(s * 250 * px, t * 250 * px))
    abox = [0.05, 0.01, 0.9, 0.98]
    ax = fig.add_axes(
        abox,
        xlabel="",
        ylabel="",
        title="",
        xlim=(0, X),
        ylim=(0, t * Y),
        xscale="linear",
        yscale="linear",
    )
    ax.set_aspect('equal')
    plt.axis('off')

    # Loop over the patterns.
    cum = 0
    for p in range(s):
        for q in range(t):
            if p * t + q >= n:
                break
            a, b, c, d = L.ks_values[p * t + q].shape
            x, y = a * c * d, a * b * d
            ax.text(cum + x, (t - q) * Y,
                    s=f"({a}, {b}, {c}, {d})", ha='right', va='top')
            ax.text(cum + x, (t - q) * Y - y,
                    s=f"({a * b * d}, {a * c * d})",
                    ha='right', va='bottom')
            # Borders
            pc = PatchCollection([Rectangle((cum, (t - q) * Y - y), x, y)],
                                 facecolor='white',
                                 alpha=1.0, edgecolor='black')
            ax.add_collection(pc)
            # ks_values
            is_complex = 'complex' in str(L.ks_values[p * t + q].dtype)
            rs = [None] * (a * b * c * d)
            vs = xp.empty(a * b * c * d,
                          dtype=min_ksv.dtype, device=_device)
            for i in range(a):
                for j in range(b):
                    for k in range(c):
                        for l in range(d):
                            row = i * b * d + j * d + l
                            col = i * c * d + k * d + l
                            idx = i * b * c * d + j * c * d + k * d + l
                            rs[idx] = Rectangle(
                                (cum + col, (t - q) * Y - row - 1), 1, 1)
                            v = L.ks_values[p * t + q][i, j, k, l]
                            if is_complex:
                                v = xp.sqrt(xp.real(v * xp.conj(v)))
                            if min_ksv == max_ksv:
                                vs[idx] = 0.5
                            elif v <= min_ksv:
                                vs[idx] = 0.0
                            elif v >= max_ksv:
                                vs[idx] = 1.0
                            else:
                                vs[idx] = xp.log2(v - min_ksv) * norm
            pc = PatchCollection(rs, facecolor=cmap(vs.tolist()), alpha=1.0)
            ax.add_collection(pc)
            cum += x + 1

    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    if name is None:
        plt.show()
    else:
        plt.savefig(f"{name}.png", dpi='figure',
                    transparent=True, bbox_inches='tight')
        plt.savefig(f"{name}.svg", dpi='figure',
                    transparent=True, bbox_inches='tight')
        fig.clf()
        plt.close("draw")
