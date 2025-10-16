from lazylinop import LazyLinOp
import numpy as np


def bitrev(N: int):
    r"""
    Returns a :class:`.LazyLinOp` ``L`` for the bit-reversal permutation.
    :octicon:`alert-fill;1em;sd-text-danger` Size of the signal ``N``
    must be a power of two. Bit-reversal permutation maps each item
    of the sequence ``0`` to ``N - 1`` to the item whose bit
    representation has the same bits in reversed order.

    Args:
        N: ``int``
            Size of the signal.

    Returns:
        :class:`.LazyLinOp`

    Example:
        >>> import numpy as np
        >>> from lazylinop.basicops import bitrev
        >>> x = np.arange(4)
        >>> L = bitrev(4)
        >>> L @ x
        array([0, 2, 1, 3])

    References:
        [1] Fast Bit-Reversal Algorithms, Anne Cathrine Elster.
            IEEE International Conf. on Acoustics, Speech, and
            Signal Processing 1989 (ICASSP'89), Vol. 2,
            pp. 1099-1102, May 1989.

    .. seealso:
        - `Bit-reversal permutation (Wikipedia) <https://en.wikipedia.org/
          wiki/Bit-reversal_permutation>`_.
    """

    if not (((N & (N - 1)) == 0) and N > 0):
        raise ValueError("N must be a power of 2.")

    p = int(np.log2(N))
    H = 1 << (p - 1)
    bitrev_idx = np.empty(N, dtype='int')
    for i in range(N):
        bitrev_idx[i] = i
    bitrev_idx[1] = H
    for i in range(2, N - 1, 2):
        bitrev_idx[i] = bitrev_idx[i // 2] >> 1
        bitrev_idx[i + 1] = bitrev_idx[i] | bitrev_idx[1]

    return LazyLinOp(
        shape=(N, N),
        matmat=lambda x: x[bitrev_idx, :],
        rmatmat=lambda x: x[bitrev_idx, :]
    )
