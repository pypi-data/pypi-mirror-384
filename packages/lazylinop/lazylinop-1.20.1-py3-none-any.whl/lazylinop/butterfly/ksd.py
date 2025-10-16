# -*- coding: utf-8 -*-

from lazylinop import islazylinop, LazyLinOp
from lazylinop.butterfly.GB_factorization import GBfactorize
from lazylinop.butterfly import Chain, ksm
import numpy as np
from array_api_compat import (
    array_namespace, device, is_array_api_obj,
    is_cupy_array, is_numpy_array, is_torch_array)
from typing import Union


def _balanced_permutation(k):
    if k == 1:
        return [1]
    elif k == 2:
        return [1, 2]
    if k % 2 == 0:
        left_perm = _balanced_permutation((k // 2) - 1)
        right_perm = [
            i + (k + 1) // 2 for i in _balanced_permutation(k // 2)]
        return [k // 2] + left_perm + right_perm
    elif k % 2 == 1:
        left_perm = _balanced_permutation(k // 2)
        right_perm = [
            i + (k + 1) // 2 for i in _balanced_permutation(k // 2)]
        return [k // 2 + 1] + left_perm + right_perm


def ksd(A: Union[np.ndarray, LazyLinOp],
        chain: Chain,
        ortho: bool = True,
        order: str = 'l2r',
        svd_backend: str = None,
        **kwargs):
    r"""
    Returns a :class:`.LazyLinOp`
    corresponding to the (often called "butterfly") factorization of
    ``A`` into Kronecker-sparse factors with sparsity patterns
    determined by a chainable instance ``chain`` of :py:class:`Chain`.

    ``L = ksd(...)`` returns a :class:`.LazyLinOp`
    corresponding to the factorization of ``A`` where
    ``L = ksm(...) @ ksm(...) @ ... @ ksm(...)``.

    .. note::

        ``L.ks_values`` contains the ``ks_values`` of the factorization
        (see :py:func:`ksm` for more details).

    As an example, the DFT matrix is factorized as follows:

    .. code-block:: python3

        M = 16
        # Build DFT matrix using lazylinop.signal.fft function.
        from lazylinop.signal import fft
        V = fft(M).toarray()
        # Use square-dyadic decomposition.
        sd_chain = Chain.square dyadic(V.shape)
        # Multiply the DFT matrix with the bit-reversal permutation matrix.
        from lazylinop.basicops import bitrev
        P = bitrev(M)
        L = ksd(V @ P.T, chain=sd_chain)

    Args:
        A: ``np.ndarray``, ``cp.array``, ``torch.Tensor`` or ``LazyLinOp``
            Matrix or ``LazyLinOp`` to factorize.
            :octicon:`info;1em;sd-text-info` when ``A`` is a
            ``LazyLinOp`` small it is often faster
            to perform ``ksd(A.toarray(), ...)`` than ``ksd(A, ...)``
            if the dense array ``A.toarray()`` fits in memory.
        chain: ``Chain``
            *Chainable* instance of the ``Chain`` class.
            See :class:`.Chain` documentation for more details.
        ortho: ``bool``, optional
            Whether to use orthonormalisation or not during
            the algorithm, see :ref:`[1] <ksd>` for more details.
            Default is ``True``.
        order: ``str``, optional
            Determines in which order partial factorizations
            are performed, see :ref:`[1] <ksd>` for more details.

            - ``'l2r'`` Left-to-right decomposition (default).
            - ``'balanced'``
        svd_backend: ``str``, optional
            See documentation of :py:func:`.linalg.svds`
            for more details.

    Kwargs:
        Additional arguments ``ksm_backend``,
        ``ksm_params`` to pass to :py:func:`ksm` function.
        See :py:func:`ksm` for more details.

    Returns:
        ``L`` is a :class:`.LazyLinOp`
        that corresponds to the product of ``chain.n_patterns``
        :class:`.LazyLinOp` Kronecker-sparse factors.

        The namespace and device of the ``ks_values`` of all factors
        are determined as follows:

        - If ``A`` is an array (or ``aslazylinop(array)``) then
          its namespace and device are used
        - otherwize, ``svd_backend`` determines the namespace and device

    .. seealso::
        - :class:`.Chain`,
        - :func:`ksm`.

    .. _ksd:

        **References:**

        [1] Butterfly Factorization with Error Guarantees.
        Léon Zheng, Quoc-Tung Le, Elisa Riccietti, and Rémi Gribonval
        https://hal.science/hal-04763712v1/document

    Examples:
        >>> import numpy as np
        >>> from lazylinop.butterfly import Chain, ksd
        >>> from lazylinop.basicops import bitrev
        >>> from lazylinop.signal import fft
        >>> N = 256
        >>> M = N
        >>> V = fft(M).toarray()
        >>> chain = Chain.square_dyadic(V.shape)
        >>> # Use bit reversal permutations matrix.
        >>> P = bitrev(N)
        >>> approx = (ksd(V @ P.T, chain) @ P).toarray()
        >>> error = np.linalg.norm(V - approx) / np.linalg.norm(V)
        >>> np.allclose(error, 0.0)
        True
    """

    if not chain.chainable:
        raise Exception("chain is not chainable.")

    if chain.n_patterns < 2:
        raise ValueError("n_patterns must be > 1.")

    if order not in ('l2r', 'balanced'):
        raise ValueError("order must be either 'l2r' or 'balanced'.")

    shape = A.shape

    if 'ksm_backend' not in kwargs.keys():
        kwargs['ksm_backend'] = 'xp'
    if 'ksm_params' not in kwargs.keys():
        kwargs['ksm_params'] = [(None, None)] * chain.n_patterns
    else:
        if not isinstance(kwargs['ksm_params'], list):
            raise Exception("ksm_params must be a list of tuple.")
        n_factors = len(kwargs['ksm_params'])
        if n_factors != chain.n_patterns:
            raise Exception("Length of kwargs['ksm_params'] must be" +
                            " equal to chain.n_patterns.")
        for i in range(n_factors):
            if not isinstance(kwargs['ksm_params'][i], tuple):
                raise Exception("ksm_params must be a list of tuple.")

    if is_numpy_array(A) and (svd_backend is not None and
                              'numpy_svd' not in svd_backend and
                              'scipy_svd' not in svd_backend):
        raise Exception("Because A is a NumPy array, svd_backend must be either" +
                        " 'numpy_svd', 'scipy_svd' or 'scipy_svds_solver'.")

    if is_cupy_array(A) and (svd_backend is not None and
                             'cupy_svd_' not in svd_backend and
                             'cupy_svds_' not in svd_backend):
        raise Exception("Because A is a CuPy array, svd_backend must be either" +
                        " 'cupy_svd_x' or 'cupy_svds_x'.")

    if is_torch_array(A) and (svd_backend is not None and
                             svd_backend != 'pytorch_svd_cpu' and
                             'pytorch_svd_' not in svd_backend):
        raise Exception("Because A is a PyTorch tensor, svd_backend must be either" +
                        " 'pytorch_svd_cpu' or 'pytorch_svd_x'.")

    if is_numpy_array(A) or is_cupy_array(A) or is_torch_array(A):
        A = A.reshape(1, 1, shape[0], shape[1])
        xp = array_namespace(A)
    else:
        # LazyLinOp?
        pass

    # Set architecture for butterfly factorization.
    min_param = chain.ks_patterns

    # Permutation.
    if order == "l2r":
        perm = [i for i in range(chain.n_patterns - 1)]
    elif order == "balanced":
        perm = [i - 1 for i in _balanced_permutation(chain.n_patterns - 1)]
    else:
        raise NotImplementedError("order must be either 'l2r' or 'balanced'")

    # FIXME: p, q compatibility
    min_param = chain.abcdpq

    # Run factorization and return a list of factors.
    factor_list = GBfactorize(A, min_param,
                              perm, ortho,
                              svd_backend=svd_backend)

    if islazylinop(A):
        # Because A is a LazyLinOp,
        # get the array namespace of the factors.
        xp = array_namespace(factor_list[0].factor)
        _device = device(factor_list[0].factor)
    elif is_array_api_obj(A):
        _device = device(A)

    for i, f in enumerate(factor_list):
        a, d, b, c = f.factor.shape
        if is_torch_array(f.factor):
            factor_list[i] = (f.factor).permute(
                0, 2, 1, 3).permute(0, 1, 3, 2).to(device=_device)
        elif is_cupy_array(f.factor) or is_numpy_array(f.factor):
            factor_list[i] = xp.swapaxes(
                xp.swapaxes((f.factor), 2, 1), 3, 2)
        else:
            pass

    L = ksm(factor_list,
            params=kwargs['ksm_params'], backend=kwargs['ksm_backend'])

    return L
