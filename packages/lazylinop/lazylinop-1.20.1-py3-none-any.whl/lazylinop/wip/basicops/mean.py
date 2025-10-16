from lazylinop import aslazylinop
from lazylinop.basicops import ones
import numpy as np


def mean(op, axis=0, meth='ones'):
    """Computes the arithmetic mean :py:class:`.LazyLinOp` of ``op``
    along the specified axis.

    Args:
        op: :py:class:`.LazyLinOp` or compatible linear operator
           The operator whose mean is computed.
        axis: ``int``, optional
            Axis along which the mean is computed (``0`` or ``1``).
        meth: ``str``
            The method used to compute the mean.

            - ``'ones'``: ``op`` is multiplied by appropriate :py:func:`.ones`.
            - ``'avg'``: :py:func:`.average` is called with same weights for
              every columns/rows.

    Returns:
        :py:class:`.LazyLinOp` for mean of ``op``.

    Example:
        >>> import lazylinop
        >>> import lazylinop.wip.basicops as lz
        >>> lzo = lazylinop.ones((2, 3))
        >>> lzo_m = lz.mean(lzo, axis=0)
        >>> print(lzo_m)
        <1x3 LazyLinOp with unspecified dtype>
        >>> print(lzo_m.toarray())
        [[1. 1. 1.]]
        >>> lzo2 = lzo * 2
        >>> lzo_m2 = lz.mean(lzo2, axis=1)
        >>> print(lzo_m2.toarray())
        [[2.]
         [2.]]

    .. seealso::
        `numpy.mean
        <https://numpy.org/doc/stable/reference/generated/numpy.mean.html>`_,
        :py:func:`.average`,
        :py:func:`.aslazylinop`.
    """
    from lazylinop.wip.basicops import average
    lz_op = aslazylinop(op)
    m, n = lz_op.shape
    ve_axis = ValueError("axis must be 0 or 1")
    if meth == 'ones':
        if axis == 0:
            return 1 / m * (ones((1, m)) @ lz_op)
        elif axis == 1:
            return 1 / n * (lz_op @ ones((n, 1)))
        else:
            raise ve_axis
    elif meth == 'avg':
        return average(lz_op, axis=axis)
    else:
        raise ValueError('Unknown meth')
