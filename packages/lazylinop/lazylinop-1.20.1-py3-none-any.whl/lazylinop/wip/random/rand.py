from lazylinop import LazyLinOp
import numpy as np
from numpy.random import RandomState, MT19937, SeedSequence


def rand(shape, dtype='float', seed=None, mode='scalar', bsize=1):
    """
    Returns a new :class:`.LazyLinOp` of random entries (uniform distribution
    into ``[0, 1)``).

    .. admonition:: Free memory cost
        :class: admonition note

        Whatever is the shape of the ``rand``, it has no memory cost
        if ``'scalar'`` mode is used.

    Args:
        shape: (``tuple[int, int]``)
            Shape of the random :class:`.LazyLinOp`.
        dtype: (``str``)
            numpy dtype of the random :class:`.LazyLinOp`.
        mode: (``str``)
            - ``'scalar'``: uses only random scalars, one by one to compute the
              multiplication. Memory cost: one scalar.
            - ``'vector'``: uses only a random vectors, one by one to compute
              the multiplication. Memory cost: one vector of size ``shape[1]``.
            - ``'block'``: computes the multiplication by generating blocks of
              random values (one by one). The size of each block is
              max(``bsize``, shape[1]).
            - ``'array'``: uses a full array of random entries of dimensions
              ``shape`` to compute the multiplication. Memory cost: array of
              dimensions ``shape``.
        seed: (``int``)
            Seed for initialization of the numpy PRNG (Mersenne Twister).

    Example:
        >>> from lazylinop import rand
        >>> lr = rand((4, 5), seed=42)
        >>> lr.toarray()
        array([[0.54199389, 0.61966721, 0.05736978, 0.81190365, 0.86009402],
               [0.62760232, 0.68193335, 0.67527253, 0.48076406, 0.73472516],
               [0.15634112, 0.72853736, 0.21693909, 0.7016948 , 0.96408854],
               [0.27678254, 0.70566135, 0.88665806, 0.61825175, 0.97278719]])


    Returns:
        The random :class:`.LazyLinOp`.

    """
    modes = ['array', 'vector', 'scalar', 'block']
    if mode not in modes:
        raise ValueError("mode must in "+str(modes))

    if seed is None:
        _seed = np.random.get_state()[1][0]
    else:
        _seed = seed

    def _mm(op, shape, adjoint=False):
        out_dtype = np.promote_types(op.dtype, dtype)
        if adjoint:
            out_shape = ((shape[1],  op.shape[1]) if len(op.shape) == 2 else
                         (shape[1],))
        else:
            out_shape = ((shape[0],  op.shape[1]) if len(op.shape) == 2 else
                         (shape[0],))

        rs = RandomState(MT19937(SeedSequence(_seed)))

        if mode == modes[0]:  # array
            if adjoint:
                return _rand_dtype(shape, rs, dtype).T.conj() @ op
            else:
                return _rand_dtype(shape, rs, dtype) @ op
        elif mode == modes[1]:  # vector
            out = np.empty(out_shape, dtype=out_dtype)
            if adjoint:
                for j in range(shape[1]):
                    out[j, :] = _rand_adjoint_vec(shape, op, rs, dtype, j) @ op
                    if j < shape[1] - 1:
                        rs = RandomState(MT19937(SeedSequence(_seed)))
            else:
                for i in range(shape[0]):
                    out[i, :] = _rand_dtype((1, shape[1]), rs, dtype) @ op
        elif mode == modes[3]:  # block
            out = np.empty(out_shape, dtype=out_dtype)
            if adjoint:
                _rand_mm_block_adjoint(shape, op, rs, dtype, out, _seed, bsize)
            else:
                _rand_mm_block(shape, op, rs, dtype, out, bsize)
        else:  # mode == 'scalar'
            out = np.empty(out_shape, dtype=out_dtype)
            if adjoint:
                _rand_mm_scalar_adjoint(shape, op, rs, dtype, out, _seed)
            else:
                _rand_mm_scalar(shape, op, rs, dtype, out)

        return out

    return LazyLinOp(shape, dtype=dtype,
                     matmat=lambda op: _mm(op, shape),
                     rmatmat=lambda op: _mm(op, shape, adjoint=True))


def _rand_dtype(shape, rs, dtype):
    if 'complex' in str(dtype):
        return rs.rand(*shape).astype(dtype) + \
                (1j * rs.rand(*shape)).astype(dtype)
    else:
        return rs.rand(*shape).astype(dtype)


def _rand_mm_scalar(shape, op, rs, dtype, out):
    # assuming seed is set just before call
    for i in range(shape[0]):
        for j in range(shape[1]):
            s = _rand_dtype((1, 1), rs, dtype)
            srow = s * op[j, :]
            if j == 0:
                out[i, :] = srow.ravel()
            else:
                out[i, :] += srow.ravel()


def _rand_mm_scalar_adjoint(shape, op, rs, dtype, out, seed):
    # assuming seed is set just before call
    for k in range(shape[1]):
        for i in range(shape[0]):
            for j in range(shape[1]):
                s = _rand_dtype((1, 1), rs, dtype)
                if j == k:
                    s = s.conj().item()
                    srow = s * op[i, :]
                    if i == 0:
                        out[k, :] = srow.ravel()
                    else:
                        out[k, :] += srow.ravel()
        rs = RandomState(MT19937(SeedSequence(seed)))


def _rand_adjoint_vec(shape, op, rs, dtype, k):
    # assuming seed is set just before call
    vec = np.empty((1, shape[0]), dtype=dtype)
    for i in range(shape[0]):
        for j in range(shape[1]):
            s = _rand_dtype((1, 1), rs, dtype).conj()
            if j == k:
                vec[0, i] = s
    return vec


def _rand_mm_block(shape, op, rs, dtype, out, bsize):
    # assuming seed is set just before call
    bsize = max(shape[1], bsize)
    bnrows = bsize // shape[1]
    bsize = bnrows * shape[1]
    bncols = shape[1]  # == bsize // bnrows
    for i in range(0, shape[0], bnrows):
        ni = min(i + bnrows, shape[0])
        n = ni - i
        b = _rand_dtype((n, bncols), rs, dtype)
        out[i:ni] = b @ op


def _rand_mm_block_adjoint(shape, op, rs, dtype, out, seed, bsize):
    # adjoint is very slow it should be avoided
    # assuming seed is set just before call
    bsize = max(shape[0], bsize)
    bnrows = bsize // shape[0]
    bsize = bnrows * shape[0]
    bncols = shape[0]  # == bsize // bnrows
    block = np.empty((bnrows, bncols), dtype=dtype)
    for j in range(0, shape[1], bnrows):
        nj = min(j + bnrows, shape[1])
        n = nj - j
        for i in range(shape[0]):
            # skip values before
            _rand_dtype((1, j), rs, dtype)
            block[:n, i] = _rand_dtype((1, n), rs, dtype).conj()
            # skip values after
            _rand_dtype((1, shape[1] - nj), rs, dtype)
        out[j:nj] = block[:n, :] @ op
        rs = RandomState(MT19937(SeedSequence(seed)))
