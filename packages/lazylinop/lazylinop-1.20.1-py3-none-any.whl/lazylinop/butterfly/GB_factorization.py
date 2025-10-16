from warnings import warn
from scipy.sparse.linalg import aslinearoperator
from lazylinop import ArrayBasedLazyLinOp

try:
    import cupy as cp
except ImportError:
    cp = None
try:
    import torch
except ImportError:
    torch = None
try:
    from einops import rearrange

    found_einops = True
except ImportError:
    warn("Did not find einops, therefore use NumPy.")
    found_einops = False
from lazylinop.butterfly.GB_utils import (
    partial_prod_deformable_butterfly_params, Factor)
from lazylinop.linalg.svds import svds
import numpy as np
import os
from array_api_compat import (
    array_namespace, device,
    is_cupy_array, is_numpy_array, is_torch_array)
from lazylinop import islazylinop


if "GB_DISABLE_EINOPS" in dict(os.environ).keys():
    found_einops = os.environ["GB_DISABLE_EINOPS"] == 0
    if not found_einops:
        print("Disable einops.")


def low_rank_project(M, rank: int = 1, svd_backend: str = None):
    """Return low rank approximation by batch SVD.

    Args:
        M: ``cp.array``, ``np.ndarray``, ``torch.Tensor`` or ``list`` of ``LazyLinOp``
            A tensor of order 4 or a list of ``LazyLinOp``,
            performing svd on the two last axis.
        rank: ``int``, optional
            Desired rank (default is 1).
        svd_backend: ``str``, optional
            See :py:func:``svd`` function for more details.
            Default value is ``None``.

    Returns:
        ``(U, Vh)``
    """
    if is_torch_array(M) or is_cupy_array(M):
        U, S, Vh = svds(M, rank=rank, backend=svd_backend)
    elif is_numpy_array(M):
        a, b, _, _ = M.shape
        U, S, Vh = None, None, None
        for i in range(a):
            for j in range(b):
                u, s, vh = svds(
                    M[i, j, :, :], rank=rank, backend=svd_backend)
                if i == 0 and j == 0:
                    U = np.empty((a, b, *u.shape), dtype=u.dtype)
                    S = np.empty((a, b, s.shape[0]), dtype=s.dtype)
                    Vh = np.empty((a, b, *vh.shape), dtype=vh.dtype)
                np.copyto(U[i, j, :, :], u)
                np.copyto(S[i, j, :], s)
                np.copyto(Vh[i, j, :, :], vh)
    elif isinstance(M, list):
        a = len(M)
        b = len(M[0])
        m, n = M[0][0].shape
        if not islazylinop(M[0][0]):
            raise Exception("M must be a list of LazyLinOp.")
        # Because of LazyLinOp use scipy.sparse.svds.
        U, S, Vh = None, None, None
        for i in range(a):
            for j in range(b):
                u, s, vh = svds(
                    M[i][j], rank=rank, backend=svd_backend)
                xp = array_namespace(u)
                if i == 0 and j == 0:
                    U = xp.empty((a, b, *u.shape), dtype=u.dtype,
                                 device=device(u))
                    S = xp.empty((a, b, s.shape[0]), dtype=s.dtype,
                                 device=device(s))
                    Vh = xp.empty((a, b, *vh.shape), dtype=vh.dtype,
                                  device=device(vh))
                U[i, j, :, :] = u[..., :rank]
                S[i, j, :] = s[..., :rank]
                Vh[i, j, :, :] = vh[..., :rank, :]
    else:
        raise Exception(
            "M must be either a torch tensor," +
            " a NumPy/CuPy array or a list of LazyLinOp.")
    xp = array_namespace(S)
    S_sqrt = xp.sqrt(S)
    shape = S_sqrt.size() if is_torch_array(S) else S_sqrt.shape
    if found_einops:
        U = U * rearrange(S_sqrt, "... rank -> ... 1 rank")
        Vh = rearrange(S_sqrt, "... rank -> ... rank 1") * Vh
    else:
        U = U * S_sqrt.reshape(shape[0], shape[1], 1, shape[2])
        Vh = S_sqrt.reshape(shape[0], shape[1], shape[2], 1) * Vh
    return U, Vh


# def torch_svd(A, rank):
#     """
#     Return low rank approximation by finding eigenvalues
#     of a symmetric matrix.
#     Good when one size of a matrix is small.
#     Input:
#     A: a tensor of order 4, performing svd on the two last axis
#     rank: desired rank
#     """
#     if A.dtype == torch.complex64 or A.dtype == torch.complex128:
#         B = torch.matmul(A, A.mH)
#     else:
#         B = torch.matmul(A, A.transpose(-1, -2))

#     sq_S, U = torch.linalg.eigh(B)
#     # print(sq_S[..., -(rank+1):])
#     U = U[..., -rank:]
#     if A.dtype == torch.complex64 or A.dtype == torch.complex128:
#         Vh = torch.matmul(U.mH, A)
#     else:
#         Vh = torch.matmul(U.transpose(-1, -2), A)

#     # print(torch.linalg.norm(torch.matmul(U, Vh) - A))
#     return U, Vh


def dense_to_pre_low_rank_projection(A, b2, c1):
    """Reshape a twiddle to be ready to factorized.

    Args:
        A: ``np.ndarray``, ``torch.tensor`` or ``LazyLinOp``.
            Twiddle.
        b2: ``int``
            Decomposition of the third dimension.
        c1: ``int``
            Decomposition of the fourth dimension.

    Returns:
        Reshaped twiddle (``np.ndarray``, ``torch.tensor``
        or list of ``LazyLinOp``).
    """
    if found_einops and (is_cupy_array(A) or
                         is_torch_array(A) or is_numpy_array(A)):
        return rearrange(
            A,
            "a d (b1 b2) (c1 c2) -> (a c1) (b2 d) b1 c2",
            b2=b2, c1=c1)
    else:
        if is_torch_array(A):
            a, d, b, c = A.size()
        elif is_cupy_array(A) or is_numpy_array(A):
            a, d, b, c = A.shape
        elif islazylinop(A):
            a, d, b, c = 1, 1, *(A.shape)
        b1 = b // b2
        c2 = c // c1
        # LazyLinOp?
        if islazylinop(A):
            # A.reshape(a, d, b1, b2, c) followed by
            # .reshape(a, d, b1, b2, c1, c2)
            # .swapaxes(2, 4)
            # .swapaxes(1, 2)
            # .swapaxes(2, 3)
            # .reshape(a * c1, b2, d, b1, c2)
            # .reshape(a * c1, b2 * d, b1, c2)
            L = []
            for i in range(a * c1):
                L.append([])
                for j in range(b2 * d):
                    L[i].append(
                        A[j:(j + b):b2,
                          (i * c2):((i + 1) * c2)])
            return L
        else:
            return (
                A.reshape(a, d, b1, b2, c)
                .reshape(a, d, b1, b2, c1, c2)
                .swapaxes(2, 4)
                .swapaxes(1, 2)
                .swapaxes(2, 3)
                .reshape(a * c1, b2, d, b1, c2)
                .reshape(a * c1, b2 * d, b1, c2)
            )


def left_to_twiddle(left, c1):
    """Reshape left twiddle.

    Args:
        left: ``np.ndarray`` or ``torch.tensor``.
            Left twiddle.
        c1: ``int``
            Decomposition of the first dimension.

    Returns:
        Reshaped left twiddle (``np.ndarray`` or ``torch.tensor``).
    """
    if found_einops:
        return rearrange(left, "(a c1) d b q -> a d b (c1 q)", c1=c1)
    else:
        tmp, d, b, q = left.shape
        a = tmp // c1
        return (
            left.reshape(a, c1, d, b, q)
            .swapaxes(1, 2)
            .swapaxes(2, 3)
            .reshape(a, d, b, c1 * q)
        )


def right_to_twiddle(right, b2):
    """Reshape right twiddle.

    Args:
        right: ``np.ndarray`` or ``torch.tensor``.
            Left twiddle.
        b2: ``int``
            Decomposition of the second dimension.

    Returns:
        Reshaped right twiddle (``np.ndarray`` or ``torch.tensor``).
    """
    if found_einops:
        return rearrange(right, "a (b2 d) b c -> a d (b b2) c", b2=b2)
    else:
        a, tmp, b, c = right.shape
        d = tmp // b2
        return (
            right.reshape(a, b2, d, b, c)
            .swapaxes(1, 2)
            .swapaxes(2, 3)
            .reshape(a, d, b * b2, c)
        )


def gbf_normalization(l_twiddle, r_twiddle, l_param, r_param,
                      type: str = 'left'):
    """Performing pairwise normalization using QR factorization.

    Args:
        l_twiddle: ``np.ndarray`` or ``torch.tensor``
            Left factor.
        r_twiddle: ``np.ndarray`` or ``torch.tensor``
            Right factor.
        l_param: ``tuple``
            Left GB parameter.
        r_twiddle: ``tuple``
            Right GB parameter.
        type: ``str``, optional
            - left -> normalized column left factor (default),
            - right -> normalized row right factor.

    Returns:
        Two new factors with one of them being
        column (row) normalized (``tuple``).
    """
    a1, b1, c1, d1, p1, q1 = l_param
    a2, b2, c2, d2, p2, q2 = r_param
    if found_einops:
        l_twiddle = rearrange(
            l_twiddle, "a1 d1 b1 (c1 q1) -> (a1 c1) d1 b1 q1", c1=c1
        )
        r_twiddle = rearrange(
            r_twiddle, "a2 d2 (p2 b2) c2 -> a2 (b2 d2) p2 c2", b2=b2
        )
    else:
        a1, d1, b1, tmp = l_twiddle.shape
        q1 = tmp // c1
        l_twiddle = (
            l_twiddle.reshape(a1, d1, b1, c1, q1)
            .swapaxes(2, 3)
            .swapaxes(1, 2)
            .reshape(a1 * c1, d1, b1, q1)
        )
        a2, d2, tmp, c2 = r_twiddle.shape
        p2 = tmp // b2
        r_twiddle = (
            r_twiddle.reshape(a2, d2, p2, b2, c2)
            .swapaxes(2, 3)
            .swapaxes(1, 2)
            .reshape(a2, b2 * d2, p2, c2)
        )
    if type == "left":
        if is_torch_array(l_twiddle):
            l_twiddle, m_twiddle = torch.linalg.qr(l_twiddle)
            r_twiddle = torch.matmul(m_twiddle, r_twiddle)
        elif is_numpy_array(l_twiddle):
            l_twiddle, m_twiddle = np.linalg.qr(l_twiddle)
            r_twiddle = m_twiddle @ r_twiddle
        elif is_cupy_array(l_twiddle):
            l_twiddle, m_twiddle = cp.linalg.qr(l_twiddle)
            r_twiddle = m_twiddle @ r_twiddle
        else:
            # LazyLinOp?
            pass
        if found_einops:
            l_twiddle = rearrange(
                l_twiddle, "(a1 c1) d1 b1 q1 -> a1 d1 b1 (c1 q1)", c1=c1
            )
            r_twiddle = rearrange(
                r_twiddle, "a2 (b2 d2) p2 c2 -> a2 d2 (p2 b2) c2", b2=b2
            )
        else:
            tmp, d1, b1, q1 = l_twiddle.shape
            a1 = tmp // c1
            l_twiddle = (
                l_twiddle.reshape(a1, c1, d1, b1, q1)
                .swapaxes(1, 2)
                .swapaxes(2, 3)
                .reshape(a1, d1, b1, c1 * q1)
            )
            a2, tmp, p2, c2 = r_twiddle.shape
            d2 = tmp // b2
            r_twiddle = (
                r_twiddle.reshape(a2, b2, d2, p2, c2)
                .swapaxes(1, 2)
                .swapaxes(2, 3)
                .reshape(a2, d2, p2 * b2, c2)
            )
    else:
        if is_torch_array(r_twiddle):
            l_twiddle_tp = r_twiddle.permute(0, 1, 3, 2)
            r_twiddle_tp = l_twiddle.permute(0, 1, 3, 2)
            l_twiddle_tp, m_twiddle_tp = torch.linalg.qr(l_twiddle_tp)
            r_twiddle_tp = torch.matmul(m_twiddle_tp, r_twiddle_tp)
        elif is_numpy_array(r_twiddle):
            l_twiddle_tp = r_twiddle.swapaxes(3, 2)
            r_twiddle_tp = l_twiddle.swapaxes(3, 2)
            l_twiddle_tp, m_twiddle_tp = np.linalg.qr(l_twiddle_tp)
            r_twiddle_tp = m_twiddle_tp @ r_twiddle_tp
        elif is_cupy_array(r_twiddle):
            l_twiddle_tp = r_twiddle.swapaxes(3, 2)
            r_twiddle_tp = l_twiddle.swapaxes(3, 2)
            l_twiddle_tp, m_twiddle_tp = cp.linalg.qr(l_twiddle_tp)
            r_twiddle_tp = m_twiddle_tp @ r_twiddle_tp
        else:
            # LazyLinOp?
            pass
        if found_einops:
            l_twiddle = rearrange(
                r_twiddle_tp, "(a1 c1) d1 q1 b1 -> a1 d1 b1 (c1 q1)", c1=c1
            )
            r_twiddle = rearrange(
                l_twiddle_tp, "a2 (b2 d2) c2 p2 -> a2 d2 (p2 b2) c2", b2=b2
            )
        else:
            tmp, d1, q1, b1 = r_twiddle_tp.shape
            a1 = tmp // c1
            l_twiddle = (
                r_twiddle_tp.reshape(a1, c1, d1, q1, b1)
                .swapaxes(1, 4)
                .swapaxes(1, 2)
                .swapaxes(3, 4)
                .reshape(a1, d1, b1, c1 * q1)
            )
            a2, tmp, c2, p2 = l_twiddle_tp.shape
            d2 = tmp // b2
            r_twiddle = (
                l_twiddle_tp.reshape(a2, b2, d2, c2, p2)
                .swapaxes(1, 2)
                .swapaxes(3, 4)
                .swapaxes(2, 3)
                .reshape(a2, d2, p2 * b2, c2)
            )
    return l_twiddle, r_twiddle


def intermediate_factorization(
    start,
    middle,
    end,
    gb_params,
    target,
    normalized_type: str = "L",
    track_epsilon: bool = False,
    svd_backend: str = None
):
    """ Performing one level of hierarchical factorization.

    Args:
        start: ``int``
            Start of the initial interval.
        end: ``int``
            End of the initial interval.
        middle: ``int``
            The separation of the interval start - end.
        gb_params: ``tuple``
            Parameters for butterfly factorizations
        target:
            The target factors.
        normalized_type: ``str``, optional
            Not important for now.
        track_epsilon: ``bool``, optional
            Defaut is False: do not track epsilon.
        svd_backend: ``str``, optional
            See :py:func:``svd`` function for more details.
            Default value is ``None``.

    Returns:
        Two factors (start - mid) and (mid + 1 - end) respecting
        the supports, epsilon (``tuple``).
    """
    param = partial_prod_deformable_butterfly_params(gb_params, start, end)
    param_left = partial_prod_deformable_butterfly_params(
        gb_params, start, middle
    )
    param_right = partial_prod_deformable_butterfly_params(
        gb_params, middle + 1, end
    )
    if is_torch_array(target):
        assert target.size() == (
            param[0],
            param[3],
            param[1] * param[4],
            param[2] * param[5],
        )
    elif is_cupy_array(target) or is_numpy_array(target):
        assert target.shape == (
            param[0],
            param[3],
            param[1] * param[4],
            param[2] * param[5],
        )
    else:
        # LazyLinOp?
        pass

    # Reshape the target twiddle
    target = dense_to_pre_low_rank_projection(
        target, param_right[1], param_left[2])

    # Compute batch SVD
    l_factor, r_factor = low_rank_project(
        target, rank=param_left[-1], svd_backend=svd_backend
    )
    if track_epsilon:
        # ...
        if is_torch_array(target):
            low_rank_errors = torch.linalg.norm(
                target - torch.matmul(l_factor, r_factor), dim=(-1, -2)
            )
            norms = torch.linalg.norm(target, dim=(-1, -2))
        elif is_numpy_array(target):
            low_rank_errors = np.linalg.norm(
                target - l_factor @ r_factor, axis=(-1, -2)
            )
            norms = np.linalg.norm(target, axis=(-1, -2))
        elif is_cupy_array(target):
            low_rank_errors = cp.linalg.norm(
                target - l_factor @ r_factor, axis=(-1, -2)
            )
            norms = cp.linalg.norm(target, axis=(-1, -2))
        else:
            # LazyLinOp?
            low_rank_errors, norms = 0.0, 1.0
        relative_error = low_rank_errors / norms
        if is_torch_array(relative_error):
            epsilon = torch.max(relative_error)
        elif is_numpy_array(relative_error):
            epsilon = np.max(relative_error)
        elif is_cupy_array(relative_error):
            epsilon = cp.max(relative_error)
        else:
            # LazyLinOp?
            epsilon = None
    else:
        epsilon = None

        # return l_factor, r_factor, low_rank_errors
    # l_factor, r_factor = torch_svd(target, rank = param_left[-1])

    # print("Size l_factor: ", l_factor.size())
    # print("Size r_factor: ", r_factor.size())
    # Reshape the factor twiddle
    l_factor = left_to_twiddle(l_factor, param_left[2])

    # print(r_factor.size())
    r_factor = right_to_twiddle(r_factor, param_right[1])

    # if not track_epsilon:
    #     return l_factor, r_factor
    return l_factor, r_factor, epsilon


def GBfactorize(
    matrix,
    gb_params,
    orders,
    normalize: bool = True,
    normalized_type: str = "L",
    track_epsilon: bool = False,
    svd_backend: str = None,
):
    """Return list of factors corresponding to the
    factorization of the matrix.

    Args:
        matrix: ``cp.array``, ``np.ndarray`` or ``torch.tensor``
            Target matrix that will be factorized.
        gb_params: ``tuple``
            The set of parameters describing the
            parameterization of GB factors.
        orders:
            A permutation describing the order of factorization
        normalize: ``bool``, optional
            Normalize (default).
        normalized_type: ``str``, optional
            L is default.
        track_epsilon: ``bool``, optional
            Do not return epsilon (default).
        svd_backend: ``str``, optional
            See :py:func:``svd`` function for more details.
            Default value is ``None``.

    Returns:
        A list of GB factors approximating the target
        matrix (list, epsilon if ``track_epsilon == True``).
    """
    result = [Factor(0, len(gb_params) - 1, matrix)]
    max_epsilon = 0
    for i in orders:
        # Search for the corresponding intermediate factors
        if normalize:
            for index in range(len(result)):
                f = result[index]
                if i > f.end:
                    l_factor, r_factor = gbf_normalization(
                        result[index].factor,
                        result[index + 1].factor,
                        result[index].param_cal(gb_params),
                        result[index + 1].param_cal(gb_params),
                        "left",
                    )
                    result[index].factor = l_factor
                    result[index + 1].factor = r_factor
                    continue
                break
            for index in range(len(result))[::-1]:
                f = result[index]
                if i < f.start:
                    l_factor, r_factor = gbf_normalization(
                        result[index - 1].factor,
                        result[index].factor,
                        result[index - 1].param_cal(gb_params),
                        result[index].param_cal(gb_params),
                        "right",
                    )
                    result[index - 1].factor = l_factor
                    result[index].factor = r_factor
                    continue
                break
        for index in range(len(result)):
            f = result[index]
            if f.start <= i and i < f.end:
                l_factor, r_factor, epsilon = intermediate_factorization(
                    f.start,
                    i,
                    f.end,
                    gb_params,
                    f.factor,
                    normalized_type=normalized_type,
                    track_epsilon=track_epsilon,
                    svd_backend=svd_backend,
                )
                if track_epsilon and epsilon.item() > max_epsilon:
                    max_epsilon = epsilon.item()
                l_element = Factor(f.start, i, l_factor)
                r_element = Factor(i + 1, f.end, r_factor)
                del result[index]
                result.insert(index, l_element)
                result.insert(index + 1, r_element)
                break
    if track_epsilon:
        return result, max_epsilon
    else:
        return result


# def twiddle_mul_twiddle(l_twiddle, r_twiddle, l_param,
#                         r_param, backend: str = 'numpy'):
#     """Compute the product of two compatible twiddles.

#     Args:
#         l_twiddle: ``numpy.array`` or ``torch.tensor``
#             Tensors of order 4.
#         r_twiddle: ``numpy.array`` or ``torch.tensor``
#             Tensors of order 4.
#         backend: ``str``, optional
#             Use numpy (default) or pytorch to compute
#             SVD and QR decompositions.

#     Returns:
#         A tensor of order 4 (twiddle) (``numpy.array``
#         or ``torch.tensor``).
#     """
#     a1, b1, c1, d1, p1, q1 = l_param
#     a2, b2, c2, d2, p2, q2 = r_param
#     if found_einops:
#         l_twiddle = rearrange(
#             l_twiddle, "a1 d1 b1 (c1 q1) -> (a1 c1) d1 b1 q1", c1=c1
#         )
#         r_twiddle = rearrange(
#             r_twiddle, "a2 d2 (p2 b2) c2 -> a2 (b2 d2) p2 c2", b2=b2
#         )
#     else:
#         a1, d1, b1, tmp = l_twiddle.shape
#         q1 = tmp // c1
#         l_twiddle = (
#             l_twiddle.reshape(a1, d1, b1, c1, q1)
#             .swapaxes(2, 3)
#             .swapaxes(1, 2)
#             .reshape(a1 * c1, d1, b1, q1)
#         )
#         a2, d2, tmp, c2 = r_twiddle.shape
#         p2 = tmp // b2
#         r_twiddle = (
#             r_twiddle.reshape(a2, d2, p2, b2, c2)
#             .swapaxes(2, 3)
#             .swapaxes(1, 2)
#             .reshape(a2, b2 * d2, p2, c2)
#         )
#     if backend == 'pytorch' and found_pytorch:
#         result = torch.matmul(l_twiddle.float(), r_twiddle.float())
#     else:
#         result = l_twiddle.astype(np.float64) @ r_twiddle.astype(np.float64)
#     if found_einops:
#         result = rearrange(
#             result, "(a c1) (b2 d) b1 c2 -> a d (b1 b2) (c1 c2)", c1=c1, b2=b2
#         )
#     else:
#         tmp1, tmp2, b1, c2 = result.shape
#         a = tmp1 // c1
#         d = tmp2 // b2
#         result = (
#             result.reshape(a, c1, b2, d, b1, c2)
#             .swapaxes(2, 3)
#             .swapaxes(1, 2)
#             .swapaxes(2, 4)
#             .reshape(a, d, b1 * b2, c1 * c2)
#         )
#     return result


# def twiddle_to_dense(twiddle, backend: str = 'numpy'):
#     """Convert twiddle to the dense form.

#     Args:
#         twiddle: ``np.ndarray`` or ``torch.tensor``
#             Twiddle to convert to dense format.
#         backend: ``str``, optional
#             Use numpy (default) or pytorch to compute
#             SVD and QR decompositions.

#     Returns:
#         Dense form of twiddle (``np.ndarray`` or ``torch.tensor``).
#     """
#     if backend == 'pytorch' and found_pytorch:
#         a, d, b, c = twiddle.size()
#         n = a * d * c
#         output = torch.eye(n)
#     else:
#         a, d, b, c = twiddle.shape
#         n = a * d * c
#         output = np.eye(n)
#     if backend == 'pytorch' and found_pytorch:
#         t = twiddle.view(a * d, b, c)
#         output = (
#             output.reshape(a, c, d, n).permute(0, 2, 1, 3).reshape(a * d, c, n)
#         )
#         output = torch.bmm(t, output)
#         return (
#             output.reshape(a, d, b, n)
#             .permute(0, 2, 1, 3)
#             .reshape(a * d * b, n)
#         )
#     else:
#         t = twiddle.reshape(a * d, b, c)
#         output = (
#             output.reshape(a, c, d, n).swapaxes(1, 2).reshape(a * d, c, n)
#         )
#         output = np.einsum("ijk,ikl->ijl", t, output)
#         return output.reshape(a, d, b, n).swapaxes(1, 2).reshape(a * d * b, n)
