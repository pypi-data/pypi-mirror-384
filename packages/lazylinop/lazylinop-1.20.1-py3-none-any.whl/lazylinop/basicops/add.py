from lazylinop import LazyLinOp


def add(*ops):
    r"""
    Returns a :class:`.LazyLinOp` ``L`` that acts as a sum of
    given compatible linear operators ``ops``.

    Args:
        ops:
            Operators (:class:`.LazyLinOp`-s or other compatible
            linear operators) to sum.

    Returns:
        The :class:`.LazyLinOp` for the sum of ``ops``.

    Examples:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> from lazylinop import aslazylinop
        >>> nt = 10
        >>> d = 8
        >>> v = np.random.rand(d)
        >>> terms = [np.ones((d, d)) for i in range(nt)]
        >>> # terms are all Fausts here
        >>> ls = lz.add(*terms) # ls is the LazyLinOp add of terms
        >>> np_sum = 0
        >>> for i in range(nt): np_sum += terms[i]
        >>> np.allclose(ls @ v, nt * np.ones((d, d)) @ v)
        True

    .. seealso::
        :func:`.aslazylinop`
    """

    def lAx(A, x):
        return A @ x

    def lAHx(A, x):
        return A.T.conj() @ x

    for i, op in enumerate(ops[1:]):
        if op.shape != ops[0].shape:
            raise ValueError('Dimensions must agree')

    def matmat(x, lmul):
        n = len(ops)
        # Fill the output.
        y = lmul(ops[0], x)
        for i in range(1, n):
            y = y + lmul(ops[i], x)
        return y

    return LazyLinOp(ops[0].shape, matmat=lambda x: matmat(x, lAx),
                     rmatmat=lambda x: matmat(x, lAHx))
