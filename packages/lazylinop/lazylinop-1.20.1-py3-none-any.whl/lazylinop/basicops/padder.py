from lazylinop.basicops import anti_eye, eye, kron, ones, vstack
import numpy as np
from lazylinop import LazyLinOp
import array_api_compat
from array_api_compat import is_torch_array


def padder(N: int, width: tuple = (0, 0), mode: str = 'zero'):
    r"""
    Returns a :class:`.LazyLinOp` ``L`` that extends a signal
    with either zero, periodic, symmetric, antisymmetric or
    reflect boundary conditions.

    Shape of ``L`` is $(M,~N)$. By default $M = N$.

    According to ``mode`` and value of ``width``, ``padder()``
    will add ``width[0] // N`` "copies" of the signal plus
    ``width[0] % N`` elements before and ``width[1] // N``
    "copies" of the signal plus ``width[1] % N`` elements after.

    For an input ``x`` with entries $x_0, x_1, \ldots, x_{N-1}$,
    the output ``y = L @ x`` depends on the ``mode``.

    In the general case, ``width`` is a multiple of input length ``N``:

    - with a periodic boundary condition and ``width = (N, N)``,
      the entries of ``y`` are:

      $x_0, x_1, ..., x_{N-1} | x_0, x_1, ..., x_{N-1} | x_0, x_1, ..., x_{N-1}$

    - with a symmetric boundary condition and ``width = (N, N)``,
      ``y`` has entries:

      $x_{N-1}, ..., x_1, x_0 | x_0, x_1, ..., x_{N-1} | x_{N-1}, ..., x_1, x_0$

    - with an antisymmetric boundary condition and ``width = (N, N)``,
      ``y`` has entries:

      $-x_{N-1}, ..., -x_1, -x_0 | x_0, x_1, ..., x_{N-1} | -x_{N-1}, ..., -x_1, -x_0$

    - with a reflect boundary condition and ``width = (N - 1, N - 1)``,
      the entries of ``y`` are:

      $x_{N-1}, ..., x_1 | x_0, x_1, ..., x_{N-1} | x_{N-2}, x_{N-3}, ..., x_0$

    In the case, ``width`` is lesser than the input length ``N`` we have:

    - with a periodic boundary condition and ``width = (b, a)``,
      ``b < N - 1`` and ``a < N - 1``, the entries of ``y`` are:

      $x_{N-1-b+1}, ..., x_{N-1} | x_0, x_1, ..., x_{N-1} | x_0, ..., x_a$

    - with a symmetric boundary condition and ``width = (b, a)``,
      ``b < N - 1`` and ``a < N - 1``, the entries of ``y`` are:

      $x_b, ..., x_0 | x_0, x_1, ..., x_{N-1} | x_{N-1}, ..., x_{N-1-a+1}$

    - with an antisymmetric boundary condition and ``width = (b, a)``,
      ``b < N - 1`` and ``a < N - 1``, the entries of ``y`` are:

      $-x_b, ..., -x_0 | x_0, x_1, ..., x_{N-1} | -x_{N-1}, ..., -x_{N-1-a+1}$

    - with a reflect boundary condition and ``width = (b, a)``,
      ``1 < b < N - 2`` and ``1 < a < N - 2``, the entries of ``y`` are:

      $x_b, ..., x_1 | x_0, x_1, ..., x_{N-1} | x_{N-2}, ..., x_{N-1-a}$

    :octicon:`pin;1em;sd-text-warning` ``y = L @ X`` with ``X`` a 2D array
    (corresponding to an image) will *only extend* each column of X,
    since this is the normal behaviour of a :class:`.LazyLinOp`.

    Args:
        N: ``int``
            Size of the input.
        width: ``tuple``, optional
            Number of values padded on both side
            of the input ``(before, after)``.
            By default it is equal to ``(0, 0)``.
            The size of the output is ``width[0] + N + width[1]``.
            ``width[0]`` and ``width[1]`` must be greater or
            equal to zero.
        mode: ``str``, optional
            ``zero`` (default), ``'wrap'``/``'periodic'``,
            ``'symm'``/``'symmetric'``, ``'antisymmetric'``
            or ``'reflect'`` boundary condition.

    Returns:
        :class:`.LazyLinOp` of shape $(M,~N)$ where
        $M = before + N + after$ (default is $(3N,~N)$).

    Examples:
        >>> import lazylinop as lz
        >>> import numpy as np
        >>> N = 3
        >>> x = np.arange(1, N + 1).astype(np.float64)
        >>> x
        array([1., 2., 3.])
        >>> L = lz.basicops.padder(N, (N, N - 1))
        >>> L @ x
        array([0., 0., 0., 1., 2., 3., 0., 0.])
        >>> L = lz.basicops.padder(N, (N, N), mode='periodic')
        >>> L @ x
        array([1., 2., 3., 1., 2., 3., 1., 2., 3.])
        >>> L = lz.basicops.padder(N, (N, N), mode='symmetric')
        >>> L @ x
        array([3., 2., 1., 1., 2., 3., 3., 2., 1.])
        >>> L = lz.basicops.padder(N, (1, N), mode='periodic')
        >>> L @ x
        array([3., 1., 2., 3., 1., 2., 3.])
        >>> L = lz.basicops.padder(N, (2, 1), mode='symmetric')
        >>> L @ x
        array([2., 1., 1., 2., 3., 3.])
        >>> L = lz.basicops.padder(N, (N + 2, N + 1), mode='symmetric')
        >>> L @ x
        array([2., 3., 3., 2., 1., 1., 2., 3., 3., 2., 1., 1.])
        >>> L = lz.basicops.padder(N, (N, N), mode='antisymmetric')
        >>> L @ x
        array([-3., -2., -1.,  1.,  2.,  3., -3., -2., -1.])
        >>> L = lz.basicops.padder(N, (N, N), mode='reflect')
        >>> L @ x
        array([2., 3., 2., 1., 2., 3., 2., 1., 2.])
        >>> X = np.array([[0., 3.], [1., 4.], [2., 5.]])
        >>> X
        array([[0., 3.],
               [1., 4.],
               [2., 5.]])
        >>> L = lz.basicops.padder(N, (N + 2, N + 1), mode='symmetric')
        >>> L @ X
        array([[1., 4.],
               [2., 5.],
               [2., 5.],
               [1., 4.],
               [0., 3.],
               [0., 3.],
               [1., 4.],
               [2., 5.],
               [2., 5.],
               [1., 4.],
               [0., 3.],
               [0., 3.]])

    .. seealso::
        :func:`.vstack`, :func:`.hstack`, :func:`.padder2d`
    """
    if N <= 0:
        raise ValueError("N must be strictly positive.")
    if width[0] < 0 or width[1] < 0:
        raise ValueError("width must be >= 0.")

    if width[0] == 0 and width[1] == 0:
        # Nothing to do
        return eye(N, N)

    if mode == 'reflect':
        if N == 1:
            # If the signal length is equal to 1,
            # we just have to copy the value width[0] + width[1] times.
            bn = width[0]
            be = 0
            an = width[1]
            ae = 0
            return ones((width[0] + N + width[1], 1))
        else:
            bn = width[0] // (N - 1)
            be = width[0] % (N - 1)
            an = width[1] // (N - 1)
            ae = width[1] % (N - 1)
    else:
        bn = width[0] // N
        be = width[0] % N
        an = width[1] // N
        ae = width[1] % N

    if mode == 'zero':
        # return eye(width[0] + N + width[1], N, k=-width[0])
        def _matmat(x):
            if is_torch_array(x):
                from torch.nn.functional import pad as torch_pad
                return torch_pad(
                    x, (0, 0, width[0], width[1]),
                    mode='constant', value=0)
            else:
                xp = array_api_compat.array_namespace(x)
                return xp.pad(
                    x, ((width[0], width[1]), (0, 0)),
                    mode='constant', constant_values=0)
        def _rmatmat(x):
            return x[width[0]:(width[0] + N):1]
        return LazyLinOp(
            shape=(width[0] + N + width[1], N),
            matmat=lambda x: _matmat(x),
            rmatmat=lambda x: _rmatmat(x)
        )
    elif mode == 'symmetric' or mode == 'symm':
        ops = []
        L = eye(N)
        # Before
        flip = True
        for i in range(bn):
            if flip:
                # Symmetric copy of the signal.
                L = vstack([anti_eye(N), L])
            else:
                L = vstack([eye(N), L])
            flip ^= True
        # be elements (according to mode) of the signal.
        if be > 0:
            if flip:
                L = vstack([anti_eye(be, N, k=N - be), L])
            else:
                L = vstack([eye(be, N, k=N - be), L])
        # After
        flip = True
        for i in range(an):
            if flip:
                # Symmetric copy of the signal.
                L = vstack([L, anti_eye(N)])
            else:
                L = vstack([L, eye(N)])
            flip ^= True
        # ae elements (according to mode) of the signal.
        if ae > 0:
            if flip:
                L = vstack([L, anti_eye(ae, N)])
            else:
                L = vstack([L, eye(ae, N)])
        return L
    elif mode == 'antisymmetric':
        L = eye(N, N)
        # Before
        flip = True
        for i in range(bn):
            if flip:
                # Antisymmetric copy of the signal.
                L = vstack([-anti_eye(N), L])
            else:
                L = vstack([eye(N, N), L])
            flip ^= True
        # be elements (according to mode) of the signal.
        if be > 0:
            if flip:
                L = vstack([(-eye(be, N, k=N - be) @ anti_eye(N)), L])
            else:
                L = vstack([eye(be, N, k=N - be), L])
        # After
        flip = True
        for i in range(an):
            if flip:
                # Antisymmetric copy of the signal.
                L = vstack([L, -anti_eye(N)])
            else:
                L = vstack([L, eye(N)])
            flip ^= True
        # ae elements (according to mode) of the signal.
        if ae > 0:
            if flip:
                L = vstack([L, -eye(ae, N) @ anti_eye(N)])
            else:
                L = vstack([L, eye(ae, N)])
        return L
    elif mode == 'periodic' or mode == 'wrap':
        # Because mode is periodic, we just have to copy the signal.
        if (bn + an) == 0:
            L = eye(N)
        else:
            L = kron(ones((bn + 1 + an, 1)), eye(N))
        if be > 0:
            L = vstack([eye(be, N, k=N - be), L])
        if ae > 0:
            L = vstack([L, eye(ae, N)])
        return L
    elif mode == 'reflect':
        L = eye(N, N)
        # Before
        flip = True
        for i in range(bn):
            if flip:
                # Reflected copy of the signal.
                L = vstack([(anti_eye(N - 1) @ eye(N - 1, N, k=1)), L])
            else:
                L = vstack([eye(N - 1, N), L])
            flip ^= True
        # be elements (according to mode) of the signal.
        if be > 0:
            if flip:
                L = vstack([(anti_eye(be) @ eye(be, N, k=1)), L])
            else:
                L = vstack([eye(be, N, k=N - 1 - be), L])
        # After
        flip = True
        for i in range(an):
            if flip:
                # Reflected copy of the signal.
                L = vstack([L, anti_eye(N - 1) @ eye(N - 1, N)])
            else:
                L = vstack([L, eye(N - 1, N, k=1)])
            flip ^= True
        # ae elements (according to mode) of the signal.
        if ae > 0:
            if flip:
                L = vstack([L, anti_eye(ae) @ eye(ae, N, k=N - 1 - ae)])
            else:
                L = vstack([L, eye(ae, N, k=1)])
        return L
    else:
        raise ValueError("mode is either 'zero'",
                         " 'periodic' ('wrap')," +
                         " 'symmetric' ('symm')" +
                         " 'antisymmetric' or 'reflect'.")


# if __name__ == '__main__':
#     import doctest
#     doctest.testmod()
