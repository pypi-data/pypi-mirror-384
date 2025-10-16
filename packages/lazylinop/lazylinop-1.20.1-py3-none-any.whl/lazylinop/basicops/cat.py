from lazylinop.utils import array_xnamespace
from lazylinop import LazyLinOp


def concat(ops, axis=0):
    def _hstack(op1, op2):
        if op1.shape[0] != op2.shape[0]:
            raise ValueError(
                "Cannot concatenate operators with different 2nd dimension shape along axis 1"
            )
        return LazyLinOp(
            (op1.shape[0], op1.shape[1] + op2.shape[1]),
            matmat=lambda x: op1 @ x[: op1.shape[1]] + op2 @ x[op1.shape[1] :],
            rmatmat=lambda x: concat([op1.H, op2.H], axis=0) @ x,
        )

    def _vstack(op1, op2):
        if op1.shape[1] != op2.shape[1]:
            raise ValueError(
                "Cannot concatenate operators with different 1st dimension shape along axis 0"
            )
        xp = array_xnamespace
        return LazyLinOp(
            (op1.shape[0] + op2.shape[0], op1.shape[1]),
            matvec=lambda x: xp(x).hstack([op1 @ x, op2 @ x]),
            matmat=lambda x: xp(x).vstack([op1 @ x, op2 @ x]),
            rmatmat=lambda x: concat([op1.H, op2.H], axis=1) @ x,
        )

    if axis == 0:
        _xstack = _vstack
    elif axis == 1:
        _xstack = _hstack
    else:
        raise ValueError("axis must be 0 or 1")
    out = ops[0]
    for op in ops[1:]:
        out = _xstack(out, op)
    return out


def hstack(ops):
    """
    Concatenates linear operators horizontally.

    Args:
        ops: (``tuple`` of compatible linear operators)
            For any pair ``i, j < len(ops)``, ``ops[i].shape[0] ==
            ops[i].shape[0]``.

    Returns:
        A concatenation :class:`LazyLinOp`.

    Example:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> from lazylinop import islazylinop
        >>> A = np.ones((10, 10))
        >>> B = lz.ones((10, 2))
        >>> lcat = lz.hstack((A, B))
        >>> islazylinop(lcat)
        True
        >>> np.allclose(lcat.toarray(), np.hstack((A, B.toarray())))
        True

    .. seealso::

        :func:`vstack`,
        `numpy.hstack,
        <https://numpy.org/doc/stable/reference/generated/numpy.hstack.html>`_
        :func:`.aslazylinop`
    """
    return concat(ops, axis=1)


def vstack(ops):
    """
    Concatenates linear operators horizontally.

    Args:
        ops: (``tuple`` of compatible linear operators)
            For any pair ``i, j < len(ops)``, ``ops[i].shape[1] ==
            ops[i].shape[1]``.

    Returns:
        A concatenation :class:`LazyLinOp`.

    Example:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> from lazylinop import islazylinop
        >>> A = np.ones((10, 10))
        >>> B = lz.ones((2, 10))
        >>> lcat = lz.vstack((A, B))
        >>> islazylinop(lcat)
        True
        >>> np.allclose(lcat.toarray(), np.vstack((A, B.toarray())))
        True

    .. seealso::
        :func:`hstack`
        `numpy.vstack
        <https://numpy.org/doc/stable/reference/generated/numpy.vstack.html>`_
        :func:`.aslazylinop`

    """
    return concat(ops, axis=0)
