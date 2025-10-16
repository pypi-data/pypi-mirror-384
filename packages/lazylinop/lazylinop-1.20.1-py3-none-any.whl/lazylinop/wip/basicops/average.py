from lazylinop import LazyLinOp, aslazylinop
import numpy as np


def average(op, axis=0, weights=None):
    """Computes the weighted average :class:`.LazyLinOp` of ``op`` along
    the specified axis.


    Args:
        op: :py:class:`.LazyLinOp` or compatible linear operator
           The operator whose average is computed.
        axis: ``int``, optional
            Axis along which the average is computed (``0`` or ``1``).
        weights: ``None`` or ``numpy.ndarray`` (vector of scalars), optional
            - ``weights[i]`` is the weight of the row ``i`` (resp. column
              ``i``) if ``axis=0`` (resp. if ``axis=1``).
            - If ``None`` (default) all columns/rows have the same weight.


    Returns:
        :py:class:`.LazyLinOp` for mean of ``op``.

    Examples:
        >>> import lazylinop as lz
        >>> import lazylinop.wip.basicops as lzb
        >>> lzo1 = lz.ones((2, 3)) * 2
        >>> lzo2 = lz.ones((2, 3)) * 3
        >>> lzo = lz.vstack((lzo1, lzo2))
        >>> w0 = [1, .5, 1.5, 2]
        >>> a1 = lzb.average(lzo, axis=0, weights=w0)
        >>> print(a1)
        <1x3 LazyLinOp with unspecified dtype>
        >>> print(a1.toarray())
        [[2.7 2.7 2.7]]
        >>> np_a1 = np.average(lzo.toarray(), axis=0, weights=w0)
        >>> print(np.allclose(a1.toarray(), np_a1))
        True
        >>> w1 = [1, 2.2, 3]
        >>> a2 = lzb.average(lzo, axis=1, weights=w1)
        >>> print(a2.toarray())
        [[2.]
         [2.]
         [3.]
         [3.]]
        >>> np_a2 = np.average(lzo.toarray(), axis=1, weights=w1)
        >>> print(np.allclose(a2.toarray().ravel(), np_a2))
        True


    .. seealso::
        `numpy.average
        <https://numpy.org/doc/stable/reference/generated/numpy.average.html>`_,
        :py:func:`.mean`,
        :py:func:`.aslazylinop`.
    """
#    from lazylinop.wip.basicops import mean
    lz_op = aslazylinop(op)
#    if weights is None:
#        return mean(lz_op, axis=axis, meth='ones')
    if isinstance(weights, list):
        weights = np.array(weights)

    # ensure weights is a vector of proper shape
    if axis == 0 and weights is not None and len(weights) != lz_op.shape[0]:
        raise ValueError('axis == 0 but len(weights) != op.shape[0]')
    elif axis == 1 and weights is not None and len(weights) != lz_op.shape[1]:
        raise ValueError('axis == 1 but len(weights) != op.shape[1]')

    def _matmat(lz_op, x, adj=False):
        nonlocal weights
        nonlocal axis

        if adj:
            s = (1, lz_op.shape[0]) if axis == 1 else (lz_op.shape[1], 1)
        else:
            s = (lz_op.shape[1], 1) if axis == 1 else (1, lz_op.shape[0])

        if weights is None:
            weights = np.ones(s)
        else:
            weights = weights.reshape(s)

        if adj:
            axis = (axis + 1) % 2

        sum_w = np.sum(weights)

        if sum_w == 0:
            raise ZeroDivisionError("Weights sum to zero,"
                                    " can't be normalized")
        m, n = lz_op.shape
        if axis == 0:
            # whatever is lz_op
            # we can compare the costs
            # of going l2r or r2l
            p = x.shape[1] if x.ndim == 2 else 1
            l2r_c = n * (m + p)
            r2l_c = m * p * (n + 1)
            if l2r_c < r2l_c:
                return 1 / sum_w * ((weights @ lz_op) @ x)
            else:  # r2l
                return 1 / sum_w * (weights @ (lz_op @ x))
        elif axis == 1:
            # from l2r because
            # weights @ x is an outer product
            # that might blow up
            # the memory space
            return 1 / sum_w * ((lz_op @ weights) @ x)

    if axis == 1:
        out_shape = (lz_op.shape[0], 1)
    elif axis == 0:
        out_shape = (1, lz_op.shape[1])
    else:
        raise ValueError("axis must be 0 or 1")
    return LazyLinOp(out_shape, matmat=lambda x: _matmat(lz_op, x),
                     rmatmat=lambda x: _matmat(lz_op.H, x, adj=True))
