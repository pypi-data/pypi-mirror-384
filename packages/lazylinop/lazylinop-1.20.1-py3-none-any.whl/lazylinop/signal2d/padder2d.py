import sys
from lazylinop.basicops import eye, kron, padder

sys.setrecursionlimit(100000)


def padder2d(in_shape: tuple,
             width: tuple = ((0, 0), (0, 0)),
             mode: str = 'zero'):
    """
    Returns a :class:`.LazyLinOp` ``L`` that extend a 2D signal
    of shape ``in_shape=(M, N)`` (provided in flattened version)
    with either zero, periodic, symmetric, antisymmetric or
    reflect boundary conditions.

    Shape of ``L`` is $(M'N',~MN)$.
    $M'$ and $N'$ are determined by ``width``.
    By default $M'=M$ and $N'=N$.

    After applying the operator as ``y = L @ colvec(X)``, a 2D
    output can be obtained via ``uncolvec(y, out_shape)``
    with ``out_shape = (M', N')``.

    ``padder2d`` use the pre-built :class:`.LazyLinOp` ``padder``
    and the Kronecker vector product trick to compute ``L @ x``.

    Args:
        in_shape: ``tuple``
            Shape of the 2D input array $(M,~N)$.
        width: ``tuple``, optional
            ``width`` argument expects a ``tuple``
            like ``((b_0, a_0), (b_1, a_1))``.
            Number of values padded on both side
            of the first axis is ``(b_0, a_0)``.
            Number of values padded on both side
            of the second axis is ``(b_1, a_1)``.
            ``b_0`` stands for before while ``a_0`` stands for after.
            By default it is equal to ``((0, 0), (0, 0))``.

            The size of the output is $M'N'$ with
            ``M'N' = (b_0 + M + a_0) * (b_1 + N + a_1)``.
        mode: ``str``, optional
            ``'zero'`` (default) or
            ``'wrap'``/``'periodic'`` or
            ``'symm'``/``'symmetric'`` or
            ``'antisymmetric'`` or
            ``'reflect'`` boundary condition.
            See the documentation of the ``.lazylinop.basicops.padder``
            for more details.

    Returns:
        :class:`.LazyLinOp` of shape $(M'N',~MN)$ where
        $M'N' = (b_0 + M + a_0)(b_1 + N + a_1)$.

    Examples:
        >>> from lazylinop.signal2d import padder2d, colvec, uncolvec
        >>> import numpy as np
        >>> M, N = 2, 2
        >>> X = np.arange(4).astype('float').reshape(M, N)
        >>> X
        array([[0., 1.],
               [2., 3.]])
        >>> L = padder2d(X.shape, ((M, M), (N, N)), mode='periodic')
        >>> uncolvec(L @ colvec(X), (3 * M, 3 * N))
        array([[0., 1., 0., 1., 0., 1.],
               [2., 3., 2., 3., 2., 3.],
               [0., 1., 0., 1., 0., 1.],
               [2., 3., 2., 3., 2., 3.],
               [0., 1., 0., 1., 0., 1.],
               [2., 3., 2., 3., 2., 3.]])
        >>> M, N = 3, 2
        >>> X = np.arange(1, 7).astype('float').reshape(M, N)
        >>> X
        array([[1., 2.],
               [3., 4.],
               [5., 6.]])
        >>> L = padder2d(X.shape, ((0, 1), (3, 5)), mode='symmetric')
        >>> uncolvec(L @ colvec(X), (0 + M + 1, 3 + N + 5))
        array([[2., 2., 1., 1., 2., 2., 1., 1., 2., 2.],
               [4., 4., 3., 3., 4., 4., 3., 3., 4., 4.],
               [6., 6., 5., 5., 6., 6., 5., 5., 6., 6.],
               [6., 6., 5., 5., 6., 6., 5., 5., 6., 6.]])

    .. seealso::
        :func:`.lazylinop.basicops.padder`
    """
    if len(in_shape) != 2:
        raise Exception("in_shape expects tuple (M, N).")
    if len(width) != 2:
        raise Exception("width expects tuple" +
                        " ((b_0, a_0), (b_1, a_1)).")

    ba0, ba1 = width[0], width[1]
    if ba0[0] < 0 or ba0[1] < 0 or ba1[0] < 0 or ba1[1] < 0:
        raise ValueError("width must be >= 0.")

    if ba0[0] == 0 and ba0[1] == 0 and ba1[0] == 0 and ba1[1] == 0:
        # Do nothing
        return eye(in_shape[0] * in_shape[1], in_shape[0] * in_shape[1])

    if (
            mode != 'zero' and
            mode != 'wrap' and
            mode != 'periodic' and
            mode != 'symm' and
            mode != 'symmetric' and
            mode != 'antisymmetric' and
            mode != 'reflect'
    ):
        raise ValueError("mode excepts 'wrap', 'periodic'," +
                         " 'symm', 'symmetric', 'antisymmetric'" +
                         " or 'reflect'.")

    # Use padder and kron lazy linear operators to write padder2d
    # Kronecker product trick: vec(A @ X @ B) = kron(B^T, A) @ vec(X)
    return kron(padder(in_shape[1], width[1], mode=mode),
                padder(in_shape[0], width[0], mode=mode))


# if __name__ == '__main__':
#     import doctest
#     doctest.testmod()
