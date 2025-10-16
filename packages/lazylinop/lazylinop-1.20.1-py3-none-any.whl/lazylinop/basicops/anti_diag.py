from lazylinop import LazyLinOp, aslazylinop, islazylinop
from lazylinop.utils import _issparse, _iscxsparse, _istsparse
import numpy as np
from scipy.sparse import issparse
import array_api_compat
from lazylinop.basicops.diag import _pre_compute


def anti_diag(v, k=0, extract_meth='canonical_vectors', extract_batch=1):
    r"""
    Returns a :py:class:`LazyLinOp` ``L`` that extracts an antidiagonal
    or builds an antidiagonal .

    The shape of ``L`` is square and depends on the size of ``v``.

    Args:
        v: (compatible linear operator,  1D ``numpy.ndarray``)
            - If ``v`` is a :py:class:`LazyLinOp` or an array-like compatible
              object, returns a copy of its k-th antidiagonal.
            - If ``v`` is a 1D numpy array, returns a :py:class:`LazyLinOp`
              with ``v`` on the k-th antidiagonal.
              ``L @ x`` returns an error if ``v`` and ``x`` are not
              on the same device where ``L = anti_diag(v, k)``.
        k: ``int``, optional
             The index of antidiagonal, ``0`` (default) for the main
             antidiagonal (the one starting from the upper right corner),
             ``k > 0`` for upper antidiagonals,
             ``k < 0`` for lower antidiagonals below
             (see :py:func:`.anti_eye`).
        extract_meth: ``str``, optional
            The method used to extract the antidiagonal vector. The interest to
            have several methods resides in their difference of memory and
            execution time costs but also on the operator capabilities (e.g.
            not all of them support a CSC matrix as multiplication operand).

            - ``'canonical_vectors'``: use canonical basis vectors $e_i$
              to extract each antidiagonal element of the operator. It takes an
              operator-vector multiplication to extract each antidiagonal
              element.
            - ``'canonical_vectors_csc'``: The same as above but using scipy
              `CSC matrices
              <https://docs.scipy.org/doc/scipy/reference/generated/
              scipy.sparse.csc_matrix.html#scipy.sparse.csc_matrix>`_
              to encode the canonical vectors. The memory cost is
              even smaller than that of ``'canonical_vectors'``.
              However ``v`` must be compatible with CSC
              matrix-vector multiplication.
            - ``'slicing'``: extract antidiagonal elements by slicing rows and
              columns by blocks of shape ``(extract_batch, extract_batch)``.
            - ``'toarray'``: use :func:`LazyLinOp.toarray` to extract
              the antidiagonal after a conversion to a whole numpy array.
        extract_batch: ``int``, optional
            - The size of the batch used for partial antidiagonal extraction in
              ``'canonical_vectors'``, ``'canonical_vectors_csc'`` and
              ``'slicing '`` methods.
               This argument is ignored for ``'toarray'`` method.


        .. admonition:: Antidiagonal extraction cost
            :class: admonition warning

            Even though the ``'toarray'`` method is generally faster if the
            operator is not extremely large it has an important memory cost
            ($O(v.shape[0] \times v.shape[1])$) .
            Hence the default method is ``canonical_vectors`` in order to
            avoid memory consumption.
            However note that this method allows to define a memory-time
            trade-off with the ``extract_batch`` argument. The larger is the
            batch, the faster should be the execution (provided enough memory
            is available).

    Returns:
        The extracted antidiagonal numpy vector or
        the constructed antidiagonal :py:class:`LazyLinOp`.

    Example: (antidiagonal :py:class:`LazyLinOp`)
        >>> import lazylinop.basicops as lz
        >>> import numpy as np
        >>> v = np.arange(1, 6)
        >>> v
        array([1, 2, 3, 4, 5])
        >>> ld1 = lz.anti_diag(v)
        >>> ld1
        <5x5 LazyLinOp with unspecified dtype>
        >>> ld1.toarray('int')
        array([[0, 0, 0, 0, 1],
               [0, 0, 0, 2, 0],
               [0, 0, 3, 0, 0],
               [0, 4, 0, 0, 0],
               [5, 0, 0, 0, 0]])
        >>> ld2 = lz.anti_diag(v, -2)
        >>> ld2
        <7x7 LazyLinOp with unspecified dtype>
        >>> ld2.toarray('int')
        array([[0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 1],
               [0, 0, 0, 0, 0, 2, 0],
               [0, 0, 0, 0, 3, 0, 0],
               [0, 0, 0, 4, 0, 0, 0],
               [0, 0, 5, 0, 0, 0, 0]])
        >>> ld3 = lz.anti_diag(v, 2)
        >>> ld3
        <7x7 LazyLinOp with unspecified dtype>
        >>> ld3.toarray('int')
        array([[0, 0, 0, 0, 1, 0, 0],
               [0, 0, 0, 2, 0, 0, 0],
               [0, 0, 3, 0, 0, 0, 0],
               [0, 4, 0, 0, 0, 0, 0],
               [5, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0]])

    Example: (antidiagonal extraction)
        >>> import lazylinop.basicops as lz
        >>> import numpy as np
        >>> lD = aslazylinop(np.random.rand(10, 12))
        >>> d = lz.anti_diag(lD, -2, extract_meth='toarray', extract_batch=3)
        >>> # verify d is really the antidiagonal of index -2
        >>> d_ = np.diag(np.fliplr(lD.toarray()), -2)
        >>> np.allclose(d, d_)
        True


    .. seealso::
        :py:func:`.diag`
        `numpy.diag
        <https://numpy.org/doc/stable/reference/generated/numpy.diag.html>`_
        `numpy.fliplr
        <https://numpy.org/doc/stable/reference/generated/numpy.fliplr.html>`_
        :func:`.aslazylinop`
    """
    if np.isscalar(extract_batch):
        extract_batch = int(extract_batch)
    if not isinstance(extract_batch, int) or extract_batch < 1:
        raise TypeError('extract_batch must be a strictly positive int')
    te = TypeError("v must be a 1-dim vector (np.ndarray) or a 2d "
                   "array/LinearOperator.")
    if array_api_compat.is_array_api_obj(v) and v.ndim == 1:
        xp = array_api_compat.array_namespace(v)
        # building antidiagonal op
        # v.ndim is 1 here.
        m = v.shape[0] + abs(k)  # xp.size(v) + abs(k)
        # spd is just in case x is sparse in matmat
        spd = [None]  # lazy instantiation

        # Pre-compute v for NumPy/CuPy arrays and torch tensor.
        # vs = _pre_compute(v, True)
        vs = {'matmat': v, 'rmatmat': xp.flip(v.conj(), axis=0)}

        def matmat(x, vs, k):

            if issparse(x):
                import array_api_compat.numpy as xp
            elif _iscxsparse(x):
                import array_api_compat.cupy as xp
            elif _istsparse(x):
                import array_api_compat.torch as xp
            else:
                xp = array_api_compat.array_namespace(x)
            if 'cupy' in str(xp.__package__):
                # FIXME: x.device is not implemented for spmatrix.
                # See cupyx/scipy/sparse/_base.py
                if _iscxsparse(x):
                    # Use v.device.id.
                    # v and x have to be on the same device.
                    lib = f"cupy-{vs.device.id}"
                else:
                    lib = f"cupy-{x.device.id}"
            elif 'numpy' in str(xp.__package__):
                lib = 'numpy'
            elif 'torch' in str(xp.__package__):
                lib = f"torch-{x.device}"

            # x is always 2d
            if _issparse(x):
                # because elementwise mul for scipy sparse
                # matrix is not immediate

                if spd[0] is None:
                    # spd[0] = _sp_anti_diag(vs[lib], k)
                    spd[0] = _sp_anti_diag(vs, k)
                return spd[0] @ x

            # v.ndim is 1 here.
            # v = xp.reshape(vs[lib], (-1, 1))
            v = xp.reshape(vs, (-1, 1))
            sv = v.shape[0]  # xp.size(v)

            if k > 0:
                y = v * x[xp.arange(-1 - k, stop=-1 - k - sv, step=-1)]
                y = xp.vstack((y, xp.zeros((k, x.shape[1]),
                                           dtype=v.dtype, device=v.device)))
            elif k < 0:
                y = v * x[xp.arange(-1, stop=-1 - sv, step=-1)]
                y = xp.vstack((xp.zeros((abs(k), x.shape[1]), dtype=v.dtype,
                                        device=v.device), y))
            else:  # k == 0
                y = v * x[xp.arange(-1, stop=-1 - sv, step=-1)]
            return y
        return LazyLinOp(
            shape=(m, m),
            matmat=lambda x: matmat(x, vs['matmat'], k),
            rmatmat=lambda x: matmat(x, vs['rmatmat'], k))
    elif v.ndim == 2:
        # extraction of op antidiagonal
        op = v
        op = aslazylinop(op)

        if extract_meth == 'toarray' or isinstance(op, np.ndarray):
            return _extract_by_toarray(op, k, te)
        elif extract_meth == 'slicing':
            return _extract_by_slicing(op, *_prepare_extract(op, k),
                                       extract_batch)
        elif extract_meth == 'canonical_vectors':
            return _extract_by_canonical_vecs(op, *_prepare_extract(op, k),
                                              extract_batch)
        elif extract_meth == 'canonical_vectors_csc':
            return _extract_by_canonical_csc_vecs(op, *_prepare_extract(op, k),
                                                  extract_batch)
        elif extract_meth == 'canonical_vectors_csr':
            return _extract_by_canonical_csr_vecs(op, *_prepare_extract(op, k),
                                                  extract_batch)
        else:
            raise ValueError('Extraction method '+str(extract_meth)+' is'
                             ' unknown.')
    else:  # v is 1-dim but not a numpy array or more than 2-dim
        raise te


def _batched_extract_inds_iterator(op, start_i, start_j, dlen, batch_sz):
    i, prev_j = start_i, start_j + 1
    for di in range(0, dlen, batch_sz):
        next_di = min(dlen, di + batch_sz)
        j = max(0, prev_j - batch_sz)
        next_i = min(op.shape[0], i + batch_sz)
        # e_batch_sz <= batch_sz
        # is the effective batch size (because batch_sz might not divide
        # op.shape[1] evenly, then e_batch_sz == op.shape[1] % batch_sz
        e_batch_sz = prev_j - j
        yield (di, i, j, next_di, next_i, prev_j, e_batch_sz)
        i = next_i
        prev_j = j


def _extract_by_slicing(op, d, start_i, start_j, dlen, batch_sz):
    if issparse(op) or islazylinop(op):
        import array_api_compat.numpy as xp
    else:
        xp = array_api_compat.array_namespace(op)
    for di, i, j, next_di, next_i, prev_j, _ in _batched_extract_inds_iterator(
            op, start_i,
            start_j, dlen,
            batch_sz):
        if j > 0:
            d[di:next_di] = xp.diag(
                op[i:next_i, prev_j - 1:j - 1:-1].toarray())
        else:
            d[di:next_di] = xp.diag(op[i:next_i, prev_j - 1::-1].toarray())
    return d


def _extract_by_canonical_vecs(op, d, start_i, start_j, dlen, batch_sz):
    if islazylinop(op):
        # FIXME: what to do if op is a aslazylinop(torch.Tensor)?
        import array_api_compat.numpy as xp
    else:
        xp = array_api_compat.array_namespace(op)
    ej = xp.zeros((op.shape[1], batch_sz))
    for di, i, j, next_di, next_i, prev_j, e_batch_sz in (
        _batched_extract_inds_iterator(
            op, start_i,
            start_j, dlen,
            batch_sz)):
        # use batch_sz canonical vectors for batch columns extraction
        for jj in range(prev_j - 1, max(j - 1, -1), -1):
            ej[jj, prev_j - 1 - jj] = 1
        # extract blocks (columns then rows)
        # and finally the antidiagonal of the block
        # (ej[:, :e_batch_sz] is a group of e_batch_sz canonical vectors)
        d[di:next_di] = xp.diag((op @ ej[:, :e_batch_sz])[i:next_i])
        if next_di != dlen:
            # erase ones for next batch
            for jj in range(prev_j - 1, max(j - 1, -1), -1):
                ej[jj, prev_j - jj - 1] = 0
    return d


def _extract_by_canonical_csc_vecs(op, d, start_i, start_j, dlen, batch_sz):
    return _extract_by_canonical_sparse_vecs(op, d, start_i, start_j, dlen,
                                             batch_sz, 'csc')


def _extract_by_canonical_sparse_vecs(op, d, start_i, start_j, dlen, batch_sz,
                                      scipy_format='csc'):
    from scipy.sparse import csc_matrix, csr_matrix

    def init_scipy_mat(fmt, *args, **kwargs):
        assert fmt.lower() in ['csc', 'csr']
        if fmt.lower() == 'csc':
            return csc_matrix(*args, **kwargs)
        else:  # fmt.lower() == 'csr':
            return csr_matrix(*args, **kwargs)
    ones = [1 for j in range(batch_sz)]
    for di, i, j, next_di, next_i, prev_j, e_batch_sz in (
        _batched_extract_inds_iterator(
            op, start_i,
            start_j, dlen,
            batch_sz)):
        ej_ones_rows = np.arange(prev_j - 1, max(j - 1, -1), -1)
        ej_ones_cols = np.arange(0, e_batch_sz)
        ej_data = ones[:e_batch_sz]
        # ej is a group of e_batch_sz canonical vectors
        ej = init_scipy_mat(scipy_format, (ej_data,
                                           (ej_ones_rows,
                                            ej_ones_cols)),
                            shape=(op.shape[1], e_batch_sz))
        res = (op @ ej)[i:next_i]
        d[di:next_di] = (np.diag(res.toarray()) if issparse(res) else
                         np.diag(res))
    return d


def _extract_by_canonical_csr_vecs(op, d, start_i, start_j, dlen, batch_sz):

    return _extract_by_canonical_sparse_vecs(op, d, start_i, start_j, dlen,
                                             batch_sz, 'csr')


def _extract_by_toarray(op, k, te):
    # op is a LazyLinOp because aslazylinop
    # was called in anti_diag
    return np.diag(op.toarray()[:, -1::-1], k)


def _start_row_col(k, op):
    n = op.shape[1]
    if k >= 0:
        return 0, n - k - 1
    else:
        return - k, n - 1


def _prepare_extract(op, k):
    if k >= op.shape[1] or k <= - op.shape[0]:
        raise ValueError('k is out of bounds.')
    i, j = _start_row_col(k, op)
    dlen = min(op.shape[0] - i, j + 1)
    d = np.empty(dlen, dtype=op.dtype)
    return d, i, j, dlen


def _sp_anti_diag(v, k):
    xp = array_api_compat.array_namespace(v)
    _v_is_torch = array_api_compat.is_torch_array(v)
    if array_api_compat.is_cupy_array(v):
        from cupyx.scipy.sparse import csr_matrix
    elif _v_is_torch:
        from torch import sparse_csr_tensor
    else:
        from scipy.sparse import csr_matrix
    r = v.shape[0]
    if k >= 0:
        m = r + k  # mat m x m
        rows = xp.arange(r)
        trows = xp.hstack((xp.arange(r + 1), xp.full(k, r)))
        cols = xp.arange(m - 1 - k, m - 1 - k - r, -1)
    else:
        m = r - k
        rows = xp.arange(-k, r - k)
        trows = xp.hstack((xp.full(-k, 0), xp.arange(r + 1)))
        cols = xp.arange(m - 1, m - 1 - r, -1)
    if _v_is_torch:
        return sparse_csr_tensor(trows, cols, v, size=(m, m),
                                 dtype=v.dtype, device=v.device)
    else:
        return csr_matrix((v, (rows, cols)), shape=(m, m))
