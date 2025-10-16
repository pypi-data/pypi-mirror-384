from lazylinop import LazyLinOp
from lazylinop.utils import _iscxsparse
from scipy.sparse import issparse, csr_matrix as szeros
import array_api_compat


def eye(M, N=None, k=0):
    """
    Returns the :class:`.LazyLinOp` ``L`` for eye
    (identity matrix and variants).

    Args:
        M: ``int``
            Number of rows.
        N: ``int``, optional
             Number of columns. Default is ``M``.
        k: ``int``, optional
             Diagonal to place ones on.

             - zero for the main diagonal (default),
             - positive integer for an upper diagonal,
             - negative integer for a lower diagonal.

    Example:
        >>> import lazylinop as lz
        >>> le1 = lz.eye(5)
        >>> le1
        <5x5 LazyLinOp with unspecified dtype>
        >>> le1.toarray(dtype='float')
        array([[1., 0., 0., 0., 0.],
               [0., 1., 0., 0., 0.],
               [0., 0., 1., 0., 0.],
               [0., 0., 0., 1., 0.],
               [0., 0., 0., 0., 1.]])
        >>> le2 = lz.eye(5, 2)
        >>> le2
        <5x2 LazyLinOp with unspecified dtype>
        >>> le2.toarray(dtype='int')
        array([[1, 0],
               [0, 1],
               [0, 0],
               [0, 0],
               [0, 0]])
        >>> le3 = lz.eye(5, 3, 1)
        >>> le3
        <5x3 LazyLinOp with unspecified dtype>
        >>> le3.toarray(dtype='int')
        array([[0, 1, 0],
               [0, 0, 1],
               [0, 0, 0],
               [0, 0, 0],
               [0, 0, 0]])
        >>> le4 = lz.eye(5, 3, -1)
        >>> le4
        <5x3 LazyLinOp with unspecified dtype>
        >>> le4.toarray(dtype='int')
        array([[0, 0, 0],
               [1, 0, 0],
               [0, 1, 0],
               [0, 0, 1],
               [0, 0, 0]])

        .. seealso::
            `scipy.sparse.eye <https://docs.scipy.org/doc/scipy/reference/
            generated/scipy.sparse.eye.html>`_,
            `numpy.eye <https://numpy.org/devdocs/reference/generated/
            numpy.eye.html>`_.
    """
    def matmat(x, M, N, k):
        # x is always 2d
        # if eye is the identity just return x
        if k == 0 and M == N:
            if array_api_compat.is_torch_array(x):
                return array_api_compat.torch.clone(x)
            else:
                return x.copy()
        if issparse(x):
            x = x.tocsr()
            y = szeros((M, x.shape[1]), dtype=x.dtype)
        elif _iscxsparse(x):
            x = x.tocsr()
            from cupyx.scipy.sparse import csr_matrix
            y = csr_matrix((M, x.shape[1]), dtype=x.dtype)
        else:
            xp = array_api_compat.array_namespace(x)
            y = xp.zeros((M, x.shape[1]), dtype=x.dtype, device=x.device)
        # Return 0 array if -k <= M or k >= N.
        if k < 0 and abs(k) < M:
            abs_k = abs(k)
            minmn = min(M - abs_k, N)
            y[abs_k:(abs_k + minmn), :] = x[:minmn, :]
        elif k == 0:
            if M > N:
                y[:N, :] = x
            else:
                y = x[:M, :]
        elif k > 0 and k < N:
            minmn = min(M, N - k)
            y[:minmn, :] = x[k:(k + minmn), :]
        # else y = zeros
        return y

    N = N if N is not None else M
    return LazyLinOp((M, N), matmat=lambda x: matmat(x, M, N, k),
                     rmatmat=lambda x: matmat(x, N, M, -k))
