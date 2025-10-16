from scipy.sparse import issparse as sp_issparse
from scipy.sparse.linalg import aslinearoperator
from scipy.linalg import svd as sp_svd
from lazylinop import (ArrayBasedLazyLinOp,
                       islazylinop)
from lazylinop.utils import _istsparse

try:
    import cupy as cp
    import cupyx.scipy.sparse.linalg as cpx_linalg
    from cupyx.scipy.sparse import issparse as cpx_issparse
except ImportError:
    cp = None
try:
    import torch
except ImportError:
    torch = None
import numpy as np
from scipy.sparse.linalg import svds as sp_svds
from array_api_compat import (
    array_namespace, device,
    is_cupy_array, is_numpy_array, is_torch_array)


def svds(M, rank: int, backend: str = None):
    """Partial singular value decomposition of ``M``.

    Args:
        M: ``cp.array``, ``np.ndarray``, ``torch.Tensor``, sparse array/tensor or :py:class:`.LazyLinOp`
            Array or :py:class:`.LazyLinOp` to decompose.
        rank: ``int``
            Compute the first ``rank`` largest magnitude singular values
            *and associated singular vectors*.
        backend: ``str``, optional
            Determined how the SVD is computed: either via a full SVD
            followed by a truncation, or using specialized truncated SVD
            tools that can offer better efficiency.
            Possible choices are:

            - ``None`` (default) to choose SVD backend according to
              the nature of ``M`` (:py:class:`.LazyLinOp` or array) and,
              if applicable, its namespace and/or device.

              - If ``M`` is an array use the full SVD from its namespace
                (``xp = array_namespace(M)`` followed by ``xp.linalg.svd(M)``).
              - If ``M`` is a sparse array or tensor use partial SVD
                from its namespace.
              - If ``M`` is a :py:class:`.LazyLinOp` use SciPy partial SVD.
            - ``'numpy_svd'`` to use NumPy full SVD,
            - ``'scipy_svd'`` to use SciPy full SVD,
            - ``'scipy_svds_<solver>'`` to use SciPy
              ``scipy.sparse.linalg.svds`` where ``'<solver>'`` is either
              ``'arpack'``, ``'lobpcg'`` or ``'propack'``,
            - ``'cupy_svd_x'`` to use CuPy full SVD where ``'x'`` is the device id,
            - ``'cupyx_svds_x'`` to use ``cupyx.scipy.sparse.linalg.svds``
              where ``'x'`` is the device id
              (`see issue <https://github.com/cupy/cupy/issues/9278>`_),
            - PyTorch ``'pytorch_svd_cpu'`` or ``'pytorch_svd_x'``
              to use PyTorch full SVD where ``'x'`` is the CUDA device id,
            - PyTorch ``'pytorch_svds_cpu'`` or ``'pytorch_svds_x'``
              to use PyTorch partial SVD where ``'x'`` is the CUDA device id.

    Returns:
        ``(U, S, Vh)`` arrays corresponding to the
        left singular vectors as columns, the singular values and
        the right singular vectors as rows.

        Shape of ``U`` is ``(L.shape[0], rank)``.

        Shape of ``S`` is ``(rank, )``.

        Shape of ``Vh`` is ``(rank, L.shape[1])``.

        The namespace and device of the singular values and vectors
        are determined as follows:

        - If ``A`` is an array (or ``aslazylinop(array)``) then
          its namespace and device are used
        - otherwize, ``backend`` determines the namespace and device

    Examples:
        >>> from lazylinop.linalg import svds
        >>> from lazylinop.signal import dft
        >>> N = 16
        >>> # Compute the first two largest magnitude singular values
        >>> u, s, vh = svds(dft(16), rank=2, backend='scipy_svd')
        >>> # Two left singular vectors
        >>> u.shape[1] == 2
        True
        >>> # Two singular values
        >>> s.shape[0] == 2
        True
        >>> # Two right singular vectors
        >>> vh.shape[0] == 2
        True

    References:
        - `NumPy svd <https://numpy.org/doc/stable/reference/
          generated/numpy.linalg.svd.html>`_,
        - `SciPy svd <https://docs.scipy.org/doc/scipy/reference/
          generated/scipy.linalg.svd.html>`_,
        - `SciPy svds <https://docs.scipy.org/doc/scipy/reference/
          generated/scipy.sparse.linalg.svds.html>`_,
        - `CuPy svd <https://docs.cupy.dev/en/stable/reference/
          generated/cupy.linalg.svd.html>`_,
        - `CuPy svds <https://docs.cupy.dev/en/stable/reference/
          generated/cupyx.scipy.sparse.linalg.svds.html>`_,
        - `PyTorch svd <https://pytorch.org/docs/stable/
          generated/torch.linalg.svd.html>`_,
        - `PyTorch svds <https://docs.pytorch.org/docs/stable/
          generated/torch.svd_lowrank.html>`_.
    """
    _msg = ("backend must be either None" +
            " 'numpy_svd', 'scipy_svd'," +
            " 'scipy_svds_arpack'," +
            " 'scipy_svds_lobpcg'," +
            " 'scipy_svds_propack'," +
            " 'cupy_svd_x'," +
            " 'cupyx_svds_x'," +
            " 'pytorch_svd_cpu'," +
            " 'pytorch_svd_x'," +
            " 'pytorch_svds_x'.")

    if is_torch_array(M) and backend is None:
        _backend = "pytorch_svd_"
    elif is_cupy_array(M) and backend is None:
        _backend = "cupy_svd_"
    elif is_numpy_array(M) and backend is None:
        _backend = "scipy_svd"
    elif islazylinop(M) and backend is None:
        _backend = "scipy_svds_lobpcg"
    elif sp_issparse(M) and backend is None:
        _backend = "scipy_svds_lobpcg"
    elif cpx_issparse(M) and backend is None:
        _backend = "cupyx_svds_"
    elif _istsparse(M) and backend is None:
        _backend = "pytorch_svds_"
    else:
        _backend = backend

    if (is_torch_array(M) and not _istsparse(M) and
        "pytorch_svd_" in _backend):
        u, s, vh = torch.linalg.svd(M, full_matrices=False)
        return u[..., :rank], s[..., :rank], vh[..., :rank, :]
    elif is_cupy_array(M) and "cupy_svd_" in _backend:
        u, s, vh = cp.linalg.svd(M, full_matrices=False)
        return u[..., :rank], s[..., :rank], vh[..., :rank, :]
    elif (is_cupy_array(M) or
          cpx_issparse(M)) and "cupyx_svds_" in _backend:
        # FIXME: https://github.com/cupy/cupy/issues/9278
        # No solver option.
        _shape = M.shape
        _N = min(_shape[0], _shape[1])
        # FIXME: do we add tol argument to svd function?
        return cpx_linalg.svds(
            M, k=rank, which='LM', ncv=min(_N - 1, 64 * rank),
            maxiter=20 * _N)
    elif is_numpy_array(M) and (_backend == "numpy_svd" or
                                _backend == "scipy_svd" or
                                "scipy_svds_" in _backend):
        if _backend == 'numpy_svd':
            try:
                u, s, vh = np.linalg.svd(M, full_matrices=False)
                return u[..., :rank], s[..., :rank], vh[..., :rank, :]
            except np.linalg.LinAlgError:
                try:
                    # 'gesvd' is MatLab and Octave choice.
                    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.svd.html
                    u, s, vh = sp_svd(M, full_matrices=False, compute_uv=True,
                                      check_finite=False, lapack_driver='gesvd')
                    return u[..., :rank], s[..., :rank], vh[..., :rank, :]
                except np.linalg.LinAlgError:
                    u, s, vh = sp_svd(M, full_matrices=False, compute_uv=True,
                                      check_finite=False, lapack_driver='gesdd')
                    return u[..., :rank], s[..., :rank], vh[..., :rank, :]
        elif _backend == 'scipy_svd':
            u, s, vh = sp_svd(M, full_matrices=False)
            return u[..., :rank], s[..., :rank], vh[..., :rank, :]
        elif "scipy_svds_" in _backend:
            _shape = M.shape
            _N = min(_shape[0], _shape[1])
            _solver = _backend.replace("scipy_svds_", "")
            # FIXME: do we add tol argument to svd function?
            return sp_svds(M, k=rank, which='LM',
                           solver=_solver,
                           ncv=min(_N - 1, 64 * rank),
                           maxiter=20 * _N)
    elif islazylinop(M):
        m, n = M.shape
        if isinstance(M, ArrayBasedLazyLinOp):
            from_aslazylinop = True
            _dtype = M.toarray().dtype
            _device = M.toarray().device
            xp = array_namespace(M.toarray())
        else:
            from_aslazylinop = False
        if from_aslazylinop:
            # FIXME: do not need because of ArrayBasedLazyLinOp.
            # # Consider the case aslazylinop(array/tensor).
            # _y = None
            # if torch is not None and isinstance(_dtype, torch.dtype):
            #     _x = torch.full((M.shape[1], 1), 1,
            #                     dtype=_dtype, device=_device)
            #     _y = M @ _x
            #     if ('float' not in str(_y.dtype) and
            #         'complex' not in str(_y.dtype)):
            #         _y = _y.to(dtype=torch.float32)
            # else:
            #     # FIXME: store namespace when aslazylinop(array)?
            #     try:
            #         # Because of
            #         # RuntimeError: linalg.svd: Expected a floating point or complex tensor as input. Got Long
            #         _x = np.full(
            #             (M.shape[1], 1), 1.0).astype(_dtype)
            #         _y = M @ _x
            #     except:
            #         _y = None
            #     # FIXME: do better than that.
            #     # Check if M @ x returns a CuPy array.
            #     if _y is None:
            #         try:
            #             cp.cuda.runtime.setDevice(_device)
            #             _x = cp.full(
            #                 (M.shape[1], 1), 1).astype(_dtype)
            #             _y = M @ _x
            #         except (NameError, TypeError, ValueError):
            #             _y = None
            # if _y is None:
            #     raise Exception(
            #         "A and backend are incompatible.")
            # xp = array_namespace(_y)
            # _dtype = _y.dtype
            # _device = device(_y)
            pass
        else:
            # Consider the case LazyLinOp.
            if (_backend == 'numpy_svd' or
                _backend == 'scipy_svd' or
                "scipy_svds_" in _backend):
                xp = np
                _dtype = 'float'
                _device = 'cpu'
            elif ("cupy_svd_" in _backend or
                  "cupyx_svds_" in _backend):
                import array_api_compat.cupy as xp
                _dtype = 'float'
                _device = int(_backend.split("_")[-1])
            elif _backend == "pytorch_svd_cpu":
                import array_api_compat.torch as xp
                _dtype = torch.float32
                _device = 'cpu'
            elif "pytorch_svd_" in _backend:
                import array_api_compat.torch as xp
                _dtype = torch.float32
                _device = f"cuda:{_backend.replace('pytorch_svd_', '')}"
            elif _backend == "pytorch_svds_cpu":
                import array_api_compat.torch as xp
                _dtype = torch.float32
                _device = 'cpu'
            elif "pytorch_svds_" in _backend:
                import array_api_compat.torch as xp
                _dtype = torch.float32
                _device = f"cuda:{_backend.replace('pytorch_svds_', '')}"
            else:
                raise Exception(_msg)
        # Compute SVD.
        str_xp = str(xp.__package__)
        if 'torch' in str_xp:
            u, s, vh = xp.linalg.svd(M.toarray(
                array_namespace=xp,
                dtype=None, device=_device), full_matrices=False)
            return u[..., :rank], s[..., :rank], vh[..., :rank, :]
        elif 'cupy' in str_xp:
            if "cupy_svd_" in _backend:
                u, s, vh = xp.linalg.svd(M.toarray(
                    array_namespace=xp,
                    dtype=_dtype, device=_device), full_matrices=False)
                return u[..., :rank], s[..., :rank], vh[..., :rank, :]
            elif "cupyx_svds_" in _backend:
                # FIXME: https://github.com/cupy/cupy/issues/9278
                # No compatibility between SciPy LinearOperator
                # and CuPyx LinearOperator.
                # No solver argument.
                _M = cpx_linalg.LinearOperator(
                    shape=M.shape,
                    matvec=lambda x: M @ x,
                    rmatvec=lambda x: M.H @ x,
                    dtype=M.dtype)
                _shape = _M.shape
                _N = min(_shape[0], _shape[1])
                # FIXME: do we add tol argument to svd function?
                return cpx_linalg.svds(
                    cpx_linalg.aslinearoperator(_M), k=rank, which='LM',
                    ncv=min(_N - 1, 64 * rank), maxiter=20 * _N)
        elif 'numpy' in str_xp:
            _shape = M.shape
            _N = min(_shape[0], _shape[1])
            if "scipy_svds_" in _backend:
                _solver = _backend.replace("scipy_svds_", "")
            else:
                _solver = 'lobpcg'
            # FIXME: do we add tol argument to svd function?
            return sp_svds(aslinearoperator(M), k=rank, which='LM',
                           solver=_solver, ncv=min(_N - 1, 64 * rank),
                           maxiter=20 * _N)
    elif sp_issparse(M):
        _shape = M.shape
        _N = min(_shape[0], _shape[1])
        if _backend is None:
            _solver = 'lobpcg'
        else:
            _solver = _backend.replace("scipy_svds_", "")
        if _solver not in ['arpack', 'lobpcg', 'propack']:
            raise Exception("When M is a SciPy sparse array," +
                            " backend must be either None," +
                            " 'scipy_svds_arpack'," +
                            " 'scipy_svds_lobpcg', or" +
                            " 'scipy_svds_propack'.")
        # FIXME: do we add tol argument to svds function?
        return sp_svds(M, k=rank, which='LM',
                       solver=_solver, ncv=min(_N - 1, 64 * rank),
                       maxiter=20 * _N)
    elif (is_torch_array(M) and not _istsparse(M) and
          "pytorch_svds_" in _backend) or _istsparse(M):
        # FIXME: do we add niter argument to svds function?
        u, s, v = torch.svd_lowrank(M, q=rank, niter=16)
        return u, s, torch.conj(v.T).contiguous()
    else:
        raise Exception(
            "M must be either a torch tensor," +
            " a NumPy/CuPy array, a SciPy sparse array" +
            " or a LazyLinOp" + f" and {_msg}")
