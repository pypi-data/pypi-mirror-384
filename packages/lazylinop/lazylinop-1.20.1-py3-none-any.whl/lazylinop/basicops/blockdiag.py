from lazylinop import LazyLinOp
import array_api_compat


def block_diag(*ops):
    """
    Returns a :class:`.LazyLinOp` ``L`` that acts as the block-diagonal
    concatenation of compatible linear operators ``ops``.

    Args:
        ops:
            Operators (:class:`.LazyLinOp`-s or other compatible
            linear operators) to concatenate block-diagonally.

    Returns:
        The resulting block-diagonal :class:`.LazyLinOp`.

    Example:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> from lazylinop import aslazylinop
        >>> import scipy
        >>> nt = 10
        >>> d = 64
        >>> v = np.random.rand(d)
        >>> terms = [np.random.rand(64, 64) for _ in range(10)]
        >>> ls = lz.block_diag(*terms) # ls is the block diagonal LazyLinOp
        >>> np.allclose(scipy.linalg.block_diag(*terms), ls.toarray())
        True

    .. seealso::
        `scipy.linalg.block_diag <https://docs.scipy.org/doc/scipy/reference/
        generated/scipy.linalg.block_diag.html>`_,
        :func:`.aslazylinop`
    """

    n_ops = len(ops)

    nrows, ncols = 0, 0
    for i in range(n_ops):
        nrows += ops[i].shape[0]
        ncols += ops[i].shape[1]

    def _matmat(x, adjoint):
        xp = array_api_compat.array_namespace(x)
        h = int(adjoint)
        # Compute first column to determine the dtype.
        cum_y, cum_x = 0, 0
        for i, L in enumerate(ops):
            m, n = L.shape[h], L.shape[1 - h]
            if i == 0:
                y0 = (L.T.conj() if adjoint
                      else L) @ x[cum_x:(cum_x + n), :1]
            else:
                y0 = xp.vstack((y0,
                                (L.T.conj() if adjoint
                                 else L) @ x[cum_x:(cum_x + n), :1]))
            cum_y += m
            cum_x += n
        if x.shape[1] == 1:
            # Batch size is 1.
            return y0
        # Compute the batch.
        cum_y, cum_x = 0, 0
        y = xp.empty((ncols if adjoint
                      else nrows, x.shape[1]), dtype=y0.dtype,
                     device=array_api_compat.device(x))
        y[:, :1] = y0
        for i, L in enumerate(ops):
            m, n = L.shape[h], L.shape[1 - h]
            y[cum_y:(cum_y + m), 1:] = (L.T.conj() if adjoint
                                        else L) @ x[cum_x:(cum_x + n), 1:]
            cum_y += m
            cum_x += n
        return y

    return LazyLinOp(
        shape=(nrows, ncols),
        matmat=lambda x: _matmat(x, False),
        rmatmat=lambda x: _matmat(x, True)
    )
