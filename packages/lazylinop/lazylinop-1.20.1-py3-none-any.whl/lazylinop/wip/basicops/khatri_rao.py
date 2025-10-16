from lazylinop import aslazylinop, islazylinop, LazyLinOp
from lazylinop.basicops import kron
import numpy as np
import scipy as sp


def khatri_rao(A, B, column: bool = True, backend: str = 'auto'):
    r"""
    Returns a :class:`.LazyLinOp` ```L`` for the Khatri-Rao product.
    Khatri-Rao product is a column-wise Kronecker product we denote $K_c$
    while the row-wise product is $K_r$.
    If $A$ and $B$ are two matrices then $K_c(A,~B)^T = K_r(A^T,~B^T)$.
    Therefore, we easily get the adjoint of the column-wize Khatri-Rao product.
    If matrix $A$ shape is $(M,~N)$ and shape of $B$ is $(P,~N)$,
    the shape of the Khatri-Rao product $K_c$ is $(MP,~N)$.
    The function does not explicitly compute the matrix.
    It uses the trick $K_c(A,~B)x = vec(Bdiag(x)A.T)$ where $x$ is a
    vector of length $N$ and $diag(x)$ a diagonal matrix of size $N^2$.

    Shape of ``L`` is $(MP,~N)$.

    Args:
        A: ``np.ndarray`` or ``LazyLinOp``
            First matrix, it can be :class:`.LazyLinOp` or NumPy array.
        B: ``np.ndarray`` or ``LazyLinOp``
            Second matrix, it can be :class:`.LazyLinOp` or NumPy array.
        column: ``bool``, optional

            - ``True`` (default) computes Khatri-Rao product column-wize.
            - ``False`` computes row-wize product.
        backend: ``str``, optional

            - 'scipy' uses SciPy Khatri-Rao product.
              It does not work for row-wise product.
              :octicon:`megaphone;1em;sd-text-danger` If ``A`` or ``B``
              is a :class:`.LazyLinOp`, the backend computes dense matrix
              before to compute Khatri-Rao product. It could be very slow.
            - 'lazylinop' uses Khatri-Rao vector product trick.
            - 'auto' uses the best backend.

    Returns:
        :class:`.LazyLinOp`

    Examples:
        >>> import numpy as np
        >>> import scipy as sp
        >>> from lazylinop.wip.basicops import khatri_rao
        >>> A = np.full((2, 2), 1)
        >>> B = np.eye(3, 2, k=0)
        >>> x = np.random.rand(2)
        >>> K = khatri_rao(A, B)
        >>> S = sp.linalg.khatri_rao(A, B)
        >>> np.allclose(K @ x, S @ x)
        True

    .. seealso::
        - `scipy.linalg.khatri_rao <https://docs.scipy.org/
          doc/scipy/reference/generated/scipy.linalg.khatri_rao.html>`_,
        - `Wikipedia <https://en.wikipedia.org/
          wiki/Khatri%E2%80%93Rao_product>`_.
    """

    Ma, Na = A.shape[0], A.shape[1]
    Mb, Nb = B.shape[0], B.shape[1]

    if not column and Ma != Mb:
        raise ValueError("number of rows differs.")

    if column and Na != Nb:
        raise ValueError("number of columns differs.")

    shape = (Ma * Mb, Na) if column else (Ma, Na * Nb)

    # Compute number of operations for lazylinop (B @ diag(x) @ A.T)
    # and for SciPy and return the best backend.
    def _nops(A, B, x, backend):
        if backend != 'auto':
            return backend
        # x is always 2d
        m, k = B.shape
        k, n = x.shape[0], x.shape[0]
        n, p = A.T.shape
        batch_size = x.shape[1]
        tmp1 = A.shape[0] * B.shape[0] * A.shape[1]
        tmp2 = (k ** 2 + m * p) * batch_size
        return 'lazylinop' if tmp1 > tmp2 else 'scipy'

    # Because NumPy/SciPy uses parallel computation of the @
    # there is no reasons to define a matvec and run batch of
    # matvec in parallel as matmat.
    def _matmat(A, B, x, column):
        # x is always 2d
        Ma, Na = A.shape[0], A.shape[1]
        Mb, Nb = B.shape[0], B.shape[1]
        if islazylinop(x):
            x = np.eye(x.shape[0], M=x.shape[0], k=0) @ x
        batch_size = x.shape[1]
        dtype = x.dtype
        if A.dtype is not None:
            dtype = np.promote_types(dtype, A.dtype)
        if B.dtype is not None:
            dtype = np.promote_types(dtype, B.dtype)
        Y = np.empty(
            (Ma * Mb if column else Ma, batch_size),
            dtype=dtype
        )
        if column:
            # We use K_c(A, B) @ x = vec(B @ diag(x) @ A^T)
            # and a ravel with order='F' (does not work with Numba).
            for i in range(batch_size):
                m, k = B.shape
                k, n = x.shape[0], x.shape[0]
                n, p = A.T.shape
                ltor = m * k * n + m * n * p
                rtol = m * k * p + k * n * p
                # Save diagonal matrix creation.
                if i == 0:
                    D = np.diag(x[:, i])
                else:
                    np.fill_diagonal(D, val=x[:, i])
                # Minimize the number of operations.
                if ltor < rtol:
                    Y[:, i] = ((B @ D) @ A.T).ravel(order='F')
                else:
                    Y[:, i] = (B @ (D @ A.T)).ravel(order='F')
        else:
            lA = aslazylinop(A)
            lB = aslazylinop(B)
            offset = 0
            for r in range(Ma):
                K = kron(lA[r, :], lB[r, :])
                Y[offset:(offset + K.shape[0]), :] = K @ x
                offset += K.shape[0]
        return Y

    # We use K_c(A, B)^T = K_r(A^T, B^T) to compute the adjoint.
    return LazyLinOp(
        shape=shape,
        matmat=lambda x: sp.linalg.khatri_rao(
            np.eye(A.shape[0], M=A.shape[0], k=0) @ A if islazylinop(A) else A,
            np.eye(B.shape[0], M=B.shape[0], k=0) @ B if islazylinop(B) else B
        ) @ x if column and _nops(A, B, x, backend) == 'scipy'
        else _matmat(A, B, x, column),
        rmatmat=lambda x: _matmat(A.T.conj(), B.T.conj(), x, not column)
    )
