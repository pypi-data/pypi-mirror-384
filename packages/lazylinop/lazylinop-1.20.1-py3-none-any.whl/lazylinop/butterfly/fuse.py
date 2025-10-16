# -*- coding-utf8 -*-
import numpy as np
from lazylinop.butterfly import ksm
from lazylinop.wip.butterfly.utils import clean
from array_api_compat import array_namespace, device


def fuse(t1, t2):
    r"""
    Fuse two 4D arrays of ``ks_values`` ``t1, t2`` of shape
    $\left(a_1,~b_1,~c_1,~d_1\right)$ and $\left(a_2,~b_2,~c_2,~d_2\right)$.
    The resulting 4D array of ``ks_values`` ``t`` is of shape
    $\left(a_1,~\frac{b_1d_1}{d_2},~\frac{a_2c_2}{a_1},~d_2\right)$
    and satisfies ``(ksm(t1) @ ksm(t2)).toarray() == ksm(t).toarray()``.

    Args:
        t1, t2: 4D arrays
            - First ``ks_values`` of shape $\left(a_1,~b_1,~c_1,~d_1\right)$.
            - Second ``ks_values`` of shape $\left(a_2,~b_2,~c_2,~d_2\right)$.
            The dimensions must satisfy:

            - $a_1c_1d_1=a_2b_2d_2$
            - $a_1$ divides $a_2$
            - $d_2$ divides $d_1$
            otherwize an ``Exception`` is returned.

    Returns:
        The resulting ``ks_values`` ``t`` is a 4D array of shape
        $\left(a_1,~\frac{b_1d_1}{d_2},~\frac{a_2c_2}{a_1},~d_2\right)$.

    .. seealso::
        - :py:func:`ksm`.

    Examples:
        >>> import numpy as np
        >>> from lazylinop.butterfly import ksm, fuse
        >>> a1, b1, c1, d1 = 2, 2, 2, 4
        >>> a2, b2, c2, d2 = 4, 2, 2, 2
        >>> v1 = np.random.randn(a1, b1, c1, d1)
        >>> v2 = np.random.randn(a2, b2, c2, d2)
        >>> v = fuse(v1, v2)
        >>> v.shape
        (2, 4, 4, 2)
        >>> L = ksm(v)
        >>> L1 = ksm(v1)
        >>> L2 = ksm(v2)
        >>> x = np.random.randn(L.shape[1])
        >>> np.allclose(L @ x, L1 @ L2 @ x)
        True
    """
    if len(t1.shape) != 4 or len(t2.shape) != 4:
        raise Exception("t1 and t2 must be 4D NumPy arrays.")
    a1, b1, c1, d1 = t1.shape
    a2, b2, c2, d2 = t2.shape
    # Valid and chainable?
    if a1 * c1 * d1 != a2 * b2 * d2:
        raise Exception("a1 * c1 * d1 must be equal to a2 * b2 * d2.")
    if a2 % a1 != 0:
        raise Exception("a1 must divide a2.")
    if d1 % d2 != 0:
        raise Exception("d2 must divide d1.")
    M, N = a1 * b1 * d1, a2 * c2 * d2
    # Resulting ks_values.
    a, b, c, d = a1, (b1 * d1) // d2, (a2 * c2) // a1, d2
    dtype = (t1[0, 0, 0, :1] * t2[0, 0, 0, :1]).dtype
    xp = array_namespace(t1)
    _device = device(t1)
    ks_values = xp.zeros((a, b, c, d), dtype=dtype,
                         device=device(t1))
    # Loop over M rows.
    for row in range(M):
        # Map between 2d and 4d representations.
        # First ks_values
        # row = i1 * b1 * d1 + j1 * d1 + l1
        i1 = row // (b1 * d1)
        j1 = (row - i1 * b1 * d1) // d1
        l1 = row - i1 * b1 * d1 - j1 * d1
        # Loop over the column of the first factor/the
        # row of the second factor.
        # Increment is d1.
        # Start from the super-block row // (b1 * d1) plus offset row % d1.
        # No offset for d1=1.
        # Loop over c1 * d1 columns by step d1 of the first factor.
        for t in range(i1 * c1 * d1 + row % d1, (i1 + 1) * c1 * d1, d1):
            k1 = (t - i1 * c1 * d1) // d1
            _i2 = t // (b2 * d2)
            tmp1 = t1[i1, j1, k1, l1]
            # Loop over the column of the second factor.
            # Increment is d2.
            # Start from the super-block t // (b2 * d2) plus offset t % d2.
            # No offset for d2=1.
            #
            # Loop over c2 * d2 columns by step d2 of the second factor.
            # Therefore, the number of iterations of the algorithm is
            # M * ((c1 * d1) // d1) * ((c2 * d2) // d2)
            # = a1 * b1 * d1 * ((c1 * d1) // d1) * ((c2 * d2) // d2)
            # = a1 * b1 * d1 * c1 * c2
            # = b1 * a2 * b2 * d2 * c2
            # Number of iterations of direct matrix multiplication is
            # M * K * N
            # = (a1*b1*d1)*(a1*c1*d1)*(a2*c2*d2)
            # The ratio is
            # (a1*b1*d1*c1*c2) / (a1*b1*d1*a1*c1*d1*a2*c2*d2)
            # = 1/(a1*d1*a2*d2)
            cols = xp.arange(_i2 * c2 * d2 + t % d2, (_i2 + 1) * c2 * d2, d2,
                             device=_device)
            # Map between 2d and 4d representations.
            # Second ks_values
            # col = i2 * c2 * d2 + k2 * d2 + l2
            i2 = cols // (c2 * d2)
            j2 = (t - i2 * b2 * d2) // d2
            k2 = (cols - i2 * c2 * d2) // d2
            l2 = cols - i2 * c2 * d2 - k2 * d2
            # Map between 2d and 4d representations
            # of the resulting ks_values.
            # row = i * b * d + j * d + l
            # col = i * c * d + k * d + l
            i = row // (b * d)
            j = (row - i * b * d) // d
            # Each element of k is unique.
            k = (cols - i * c * d) // d
            # assert len(np.where(k < 0)[0]) == 0
            # assert len(np.unique(k)) == len(k)
            l = row - i * b * d - j * d
            ks_values[i, j, k, l] += tmp1 * t2[i2, j2, k2, l2]
    return ks_values
