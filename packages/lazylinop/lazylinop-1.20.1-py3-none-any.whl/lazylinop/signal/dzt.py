import numpy as np
from lazylinop import LazyLinOp
from lazylinop.signal import dft


def dzt(N, a: int = 1):
    r"""
    Returns a :class:`.LazyLinOp` ``L`` for the Discrete Zak Transform (DZT).
    :octicon:`alert-fill;1em;sd-text-danger` The parameter ``a`` must
    divide input length ``N``.

    .. math::

        \begin{equation}
        Z_x^a\left(n, k\right)=\frac{1}{\sqrt{a}}\sum_{l=0}^ax\left(n+lL\right)e^{-2j\pi\frac{kl}{a}}
        \end{equation}

    Shape of ``L`` is $(N,~N)$.

    ``L`` is orthonormal, and the :class:`.LazyLinOp`
    for the inverse DZT is ``L.H``.

    Args:
        N: ``int``
            Size of the input ($N > 0$).

        a: ``int``, optional
            The parameter ``a`` must divide input length ``N``.
            Default is 1.

    Returns:
        :class:`.LazyLinOp` DZT

    Examples:
        >>> from lazylinop.signal import dzt
        >>> import numpy as np
        >>> Z = dzt(32, 1)
        >>> x = np.random.randn(32)
        >>> y = Z @ x
        >>> x_ = Z.H @ y
        >>> np.allclose(x_, x)
        True

    References:
        [1] H. Bölcskei and F. Hlawatsch. Discrete Zak transforms, polyphase
            transforms, and applications. IEEE Trans. Signal Process.,
            45(4):851--866, april 1997.

    .. seealso::
        `Zak transform (Wikipedia) <https://en.wikipedia.org/
        wiki/Zak_transform>`_,
        `LTFAT <https://ltfat.org/doc/gabor/zak.html>`_.
    """

    if not isinstance(a, int):
        raise TypeError("a must be an integer.")

    if a < 1:
        raise ValueError("a must be > 0.")

    if (N % a) != 0:
        raise ValueError("a must divide N.")

    L = N // a

    def _matvec(x):
        # Because of the reshape of x, DZT is simply:
        # return (dft(a) @ x.reshape(a, L)).flatten('F')
        return (dft(a) @ x.reshape(a, L)).T.reshape(-1)

    def _rmatvec(x):
        # return (dft(a).H @ x.reshape(a, L, order='F')).flatten('C')
        return (dft(a).H @ x.reshape(L, a).T).reshape(-1)

    return LazyLinOp(
        shape=(N, N),
        matvec=lambda x: _matvec(x),
        rmatvec=lambda x: _rmatvec(x))
