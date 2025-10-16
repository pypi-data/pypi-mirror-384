import numpy as np
from lazylinop import LazyLinOp, aslazylinop
from lazylinop.basicops import hstack, vstack, eye, kron, ones, zeros, anti_eye
from warnings import warn
import array_api_compat
from array_api_compat import is_torch_array, is_cupy_array
try:
    import torch
except ModuleNotFoundError:
    torch = None
import sys
sys.setrecursionlimit(100000)


def pad(op, pad_width, mode='constant', constant_values=0):
    """
    Returns a :class:`.LazyLinOp` ``L`` that acts as a padded version
    of a given compatible linear operator ``op``.

    Args:
        op: (``scipy LinearOperator``, ``LazyLinOperator``, ``numpy array``, ``torch.Tensor``)
            The operator/array to pad.

        pad_width: (``tuple``, ``list``)
            Number of values padded to the edges of each axis.

            - ``((B0, A0), (B1, A1))`` (See Figure `Padding format`).
            - ``(B, A)`` is equivalent to ``((B, A), (B, A))``.
            - ``((B0, ), (B1, ))`` is equivalent to ``((B0, B0), (B1, B1))``.
            - ``(B, )`` is equivalent to ``((B, B), (B, B))``.
            - ``C`` is equivalent to ``((C, C), (C, C))``.

        mode: (``str``)
            - ``'constant'``:
                Pads with a constant value.
            - ``'symmetric'``:
                Pads with the reflection of the vector mirrored along the edge
                of the array.
            - ``'antisymmetric'``:
                Pads with the reflection of the vector mirrored and negated
                along the edge of the array.
            - ``'reflect'``:
                Pads with the reflection of the vector mirrored on the first
                and last values of the vector along each axis.
            - ``'mean'``:
                Pads with the mean value of all the vector along each axis.
            - ``'edge'``:
                Pads with the edge values of :class:`.LazyLinOp`.
            - ``'wrap'``:
                Pads with the wrap of the vector along the axis.
                The first values are used to pad the end and the end values
                are used to pad the beginning.
        constant_values: (``tuple``, ``list``, ``scalar``)
            The padded values for each axis (in ``mode='constant'``).

            - ``((VB0, VA0)``, ``(VB1, VA1))``: padding values before (``VBi``)
              and values after (``VAi``) on each dimension.
              In Figure `Padding format` value ``VBi`` (resp. ``VAi``) goes
              where padding width ``Bi`` (resp.  ``Ai``) is.
            - ``((VB0, VA0))`` is equivalent to ``((VB0, VA0), (VB0, VA0))``.
            - ``(V,)`` or ``V`` is equivalent to ``((V, V), (V, V))``.
            - ``((VB0,), (VB1,))`` is equivalent to
              ``((VB0, VB0), (VB1, VB1))``.

    .. _padding_format
    Padding format (for an operator ``op``)
    --------------
        .. image:: _static/pad_width.svg
            :width: 400px
            :height: 400px

    Example ``mode='constant'``:
        >>> import lazylinop as lz
        >>> import numpy as np
        >>> A = np.arange(18 * 2).reshape((18, 2))
        >>> A
        array([[ 0,  1],
               [ 2,  3],
               [ 4,  5],
               [ 6,  7],
               [ 8,  9],
               [10, 11],
               [12, 13],
               [14, 15],
               [16, 17],
               [18, 19],
               [20, 21],
               [22, 23],
               [24, 25],
               [26, 27],
               [28, 29],
               [30, 31],
               [32, 33],
               [34, 35]])
        >>> lpA = lz.pad(A, (2, 3))
        >>> lpA
        <23x7 LazyLinOp with unspecified dtype>
        >>> lpA.toarray().astype(int)
        array([[ 0,  0,  0,  0,  0,  0,  0],
               [ 0,  0,  0,  0,  0,  0,  0],
               [ 0,  0,  0,  1,  0,  0,  0],
               [ 0,  0,  2,  3,  0,  0,  0],
               [ 0,  0,  4,  5,  0,  0,  0],
               [ 0,  0,  6,  7,  0,  0,  0],
               [ 0,  0,  8,  9,  0,  0,  0],
               [ 0,  0, 10, 11,  0,  0,  0],
               [ 0,  0, 12, 13,  0,  0,  0],
               [ 0,  0, 14, 15,  0,  0,  0],
               [ 0,  0, 16, 17,  0,  0,  0],
               [ 0,  0, 18, 19,  0,  0,  0],
               [ 0,  0, 20, 21,  0,  0,  0],
               [ 0,  0, 22, 23,  0,  0,  0],
               [ 0,  0, 24, 25,  0,  0,  0],
               [ 0,  0, 26, 27,  0,  0,  0],
               [ 0,  0, 28, 29,  0,  0,  0],
               [ 0,  0, 30, 31,  0,  0,  0],
               [ 0,  0, 32, 33,  0,  0,  0],
               [ 0,  0, 34, 35,  0,  0,  0],
               [ 0,  0,  0,  0,  0,  0,  0],
               [ 0,  0,  0,  0,  0,  0,  0],
               [ 0,  0,  0,  0,  0,  0,  0]])
        >>> lpA2 = lz.pad(A, ((2, 3), (4, 1)))
        >>> lpA2
        <23x7 LazyLinOp with unspecified dtype>
        >>> lpA2.toarray().astype('int')
        array([[ 0,  0,  0,  0,  0,  0,  0],
               [ 0,  0,  0,  0,  0,  0,  0],
               [ 0,  0,  0,  0,  0,  1,  0],
               [ 0,  0,  0,  0,  2,  3,  0],
               [ 0,  0,  0,  0,  4,  5,  0],
               [ 0,  0,  0,  0,  6,  7,  0],
               [ 0,  0,  0,  0,  8,  9,  0],
               [ 0,  0,  0,  0, 10, 11,  0],
               [ 0,  0,  0,  0, 12, 13,  0],
               [ 0,  0,  0,  0, 14, 15,  0],
               [ 0,  0,  0,  0, 16, 17,  0],
               [ 0,  0,  0,  0, 18, 19,  0],
               [ 0,  0,  0,  0, 20, 21,  0],
               [ 0,  0,  0,  0, 22, 23,  0],
               [ 0,  0,  0,  0, 24, 25,  0],
               [ 0,  0,  0,  0, 26, 27,  0],
               [ 0,  0,  0,  0, 28, 29,  0],
               [ 0,  0,  0,  0, 30, 31,  0],
               [ 0,  0,  0,  0, 32, 33,  0],
               [ 0,  0,  0,  0, 34, 35,  0],
               [ 0,  0,  0,  0,  0,  0,  0],
               [ 0,  0,  0,  0,  0,  0,  0],
               [ 0,  0,  0,  0,  0,  0,  0]])
        >>> # the same with arbitrary values
        >>> pw = ((2, 3), (4, 1))
        >>> cv = ((-1, -2), (-3, -4))
        >>> lpA3 = lz.pad(A, pw, constant_values=cv)
        >>> lpA3
        <23x7 LazyLinOp with unspecified dtype>
        >>> lpA3.toarray().astype('int')
        array([[-3, -3, -3, -3, -1, -1, -4],
               [-3, -3, -3, -3, -1, -1, -4],
               [-3, -3, -3, -3,  0,  1, -4],
               [-3, -3, -3, -3,  2,  3, -4],
               [-3, -3, -3, -3,  4,  5, -4],
               [-3, -3, -3, -3,  6,  7, -4],
               [-3, -3, -3, -3,  8,  9, -4],
               [-3, -3, -3, -3, 10, 11, -4],
               [-3, -3, -3, -3, 12, 13, -4],
               [-3, -3, -3, -3, 14, 15, -4],
               [-3, -3, -3, -3, 16, 17, -4],
               [-3, -3, -3, -3, 18, 19, -4],
               [-3, -3, -3, -3, 20, 21, -4],
               [-3, -3, -3, -3, 22, 23, -4],
               [-3, -3, -3, -3, 24, 25, -4],
               [-3, -3, -3, -3, 26, 27, -4],
               [-3, -3, -3, -3, 28, 29, -4],
               [-3, -3, -3, -3, 30, 31, -4],
               [-3, -3, -3, -3, 32, 33, -4],
               [-3, -3, -3, -3, 34, 35, -4],
               [-3, -3, -3, -3, -2, -2, -4],
               [-3, -3, -3, -3, -2, -2, -4],
               [-3, -3, -3, -3, -2, -2, -4]])



        zero-padded DFT example:
            >>> import lazylinop as lz
            >>> from lazylinop.signal import fft
            >>> e = lz.eye(5)
            >>> pe = lz.pad(e, (0, 3))
            >>> pfft = fft(8) @ pe

        Example ``mode='symmetric'``, ``mode='reflect'``:
            >>> import lazylinop as lz
            >>> a = np.arange(25).reshape(5, 5)
            >>> sp_a = lz.pad(a, (2, 1), mode='symmetric')
            >>> print(sp_a)
            <8x8 LazyLinOp with unspecified dtype>
            >>> sp_a.toarray().astype('int')
            array([[ 6,  5,  5,  6,  7,  8,  9,  9],
                   [ 1,  0,  0,  1,  2,  3,  4,  4],
                   [ 1,  0,  0,  1,  2,  3,  4,  4],
                   [ 6,  5,  5,  6,  7,  8,  9,  9],
                   [11, 10, 10, 11, 12, 13, 14, 14],
                   [16, 15, 15, 16, 17, 18, 19, 19],
                   [21, 20, 20, 21, 22, 23, 24, 24],
                   [21, 20, 20, 21, 22, 23, 24, 24]])
            >>> sp_a2 = lz.pad(a, ((1, 1), (2, 1)), mode='symmetric')
            >>> print(sp_a2)
            <7x8 LazyLinOp with unspecified dtype>
            >>> sp_a2.toarray().astype('int')
            array([[ 1,  0,  0,  1,  2,  3,  4,  4],
                   [ 1,  0,  0,  1,  2,  3,  4,  4],
                   [ 6,  5,  5,  6,  7,  8,  9,  9],
                   [11, 10, 10, 11, 12, 13, 14, 14],
                   [16, 15, 15, 16, 17, 18, 19, 19],
                   [21, 20, 20, 21, 22, 23, 24, 24],
                   [21, 20, 20, 21, 22, 23, 24, 24]])
            >>> rp_a = lz.pad(a, (2, 1), mode='reflect')
            >>> print(rp_a)
            <8x8 LazyLinOp with unspecified dtype>
            >>> rp_a.toarray().astype('int')
            array([[12, 11, 10, 11, 12, 13, 14, 13],
                   [ 7,  6,  5,  6,  7,  8,  9,  8],
                   [ 2,  1,  0,  1,  2,  3,  4,  3],
                   [ 7,  6,  5,  6,  7,  8,  9,  8],
                   [12, 11, 10, 11, 12, 13, 14, 13],
                   [17, 16, 15, 16, 17, 18, 19, 18],
                   [22, 21, 20, 21, 22, 23, 24, 23],
                   [17, 16, 15, 16, 17, 18, 19, 18]])
            >>> rp_a2 = lz.pad(a, ((1, 1), (2, 1)), mode='reflect')
            >>> print(rp_a2)
            <7x8 LazyLinOp with unspecified dtype>
            >>> rp_a2.toarray().astype('int')
            array([[ 7,  6,  5,  6,  7,  8,  9,  8],
                   [ 2,  1,  0,  1,  2,  3,  4,  3],
                   [ 7,  6,  5,  6,  7,  8,  9,  8],
                   [12, 11, 10, 11, 12, 13, 14, 13],
                   [17, 16, 15, 16, 17, 18, 19, 18],
                   [22, 21, 20, 21, 22, 23, 24, 23],
                   [17, 16, 15, 16, 17, 18, 19, 18]])


        Example ``mode='mean'``:
            >>> import lazylinop as lz
            >>> a = np.arange(25).reshape(5, 5)
            >>> mp_a = lz.pad(a, (2, 1), mode='mean')
            >>> print(mp_a)
            <8x8 LazyLinOp with unspecified dtype>
            >>> mp_a.toarray()
            array([[12., 12., 10., 11., 12., 13., 14., 12.],
                   [12., 12., 10., 11., 12., 13., 14., 12.],
                   [ 2.,  2.,  0.,  1.,  2.,  3.,  4.,  2.],
                   [ 7.,  7.,  5.,  6.,  7.,  8.,  9.,  7.],
                   [12., 12., 10., 11., 12., 13., 14., 12.],
                   [17., 17., 15., 16., 17., 18., 19., 17.],
                   [22., 22., 20., 21., 22., 23., 24., 22.],
                   [12., 12., 10., 11., 12., 13., 14., 12.]])
            >>> mp_a2 = lz.pad(a, ((1, 1), (2, 1)), mode='mean')
            >>> print(mp_a2)
            <7x8 LazyLinOp with unspecified dtype>
            >>> mp_a2.toarray()
            array([[12., 12., 10., 11., 12., 13., 14., 12.],
                   [ 2.,  2.,  0.,  1.,  2.,  3.,  4.,  2.],
                   [ 7.,  7.,  5.,  6.,  7.,  8.,  9.,  7.],
                   [12., 12., 10., 11., 12., 13., 14., 12.],
                   [17., 17., 15., 16., 17., 18., 19., 17.],
                   [22., 22., 20., 21., 22., 23., 24., 22.],
                   [12., 12., 10., 11., 12., 13., 14., 12.]])

        Example ``mode='edge'``:
            >>> import lazylinop as lz
            >>> a = np.arange(25).reshape(5, 5)
            >>> ep_a = lz.pad(a, (2, 1), mode='edge')
            >>> print(ep_a)
            <8x8 LazyLinOp with unspecified dtype>
            >>> y = ep_a.toarray().astype('int')
            >>> y
            array([[ 0,  0,  0,  1,  2,  3,  4,  4],
                   [ 0,  0,  0,  1,  2,  3,  4,  4],
                   [ 0,  0,  0,  1,  2,  3,  4,  4],
                   [ 5,  5,  5,  6,  7,  8,  9,  9],
                   [10, 10, 10, 11, 12, 13, 14, 14],
                   [15, 15, 15, 16, 17, 18, 19, 19],
                   [20, 20, 20, 21, 22, 23, 24, 24],
                   [20, 20, 20, 21, 22, 23, 24, 24]])
            >>> z = np.pad(a, (2, 1), mode='edge')
            >>> np.allclose(y, z)
            True
            >>> ep_a2 = lz.pad(a, ((1, 1), (2, 1)), mode='edge')
            >>> print(ep_a2)
            <7x8 LazyLinOp with unspecified dtype>
            >>> ep_a2.toarray().astype('int')
            array([[ 0,  0,  0,  1,  2,  3,  4,  4],
                   [ 0,  0,  0,  1,  2,  3,  4,  4],
                   [ 5,  5,  5,  6,  7,  8,  9,  9],
                   [10, 10, 10, 11, 12, 13, 14, 14],
                   [15, 15, 15, 16, 17, 18, 19, 19],
                   [20, 20, 20, 21, 22, 23, 24, 24],
                   [20, 20, 20, 21, 22, 23, 24, 24]])

        Example ``mode='wrap'``:
            >>> import lazylinop as lz
            >>> a = np.arange(25).reshape(5, 5)
            >>> wp_a = lz.pad(a, (2, 1), mode='wrap')
            >>> print(wp_a)
            <8x8 LazyLinOp with unspecified dtype>
            >>> wp_a.toarray().astype('int')
            array([[18, 19, 15, 16, 17, 18, 19, 15],
                   [23, 24, 20, 21, 22, 23, 24, 20],
                   [ 3,  4,  0,  1,  2,  3,  4,  0],
                   [ 8,  9,  5,  6,  7,  8,  9,  5],
                   [13, 14, 10, 11, 12, 13, 14, 10],
                   [18, 19, 15, 16, 17, 18, 19, 15],
                   [23, 24, 20, 21, 22, 23, 24, 20],
                   [ 3,  4,  0,  1,  2,  3,  4,  0]])
            >>> wp_a2 = lz.pad(a, ((1, 1), (2, 1)), mode='wrap')
            >>> print(wp_a2)
            <7x8 LazyLinOp with unspecified dtype>
            >>> wp_a2.toarray().astype('int')
            array([[23, 24, 20, 21, 22, 23, 24, 20],
                   [ 3,  4,  0,  1,  2,  3,  4,  0],
                   [ 8,  9,  5,  6,  7,  8,  9,  5],
                   [13, 14, 10, 11, 12, 13, 14, 10],
                   [18, 19, 15, 16, 17, 18, 19, 15],
                   [23, 24, 20, 21, 22, 23, 24, 20],
                   [ 3,  4,  0,  1,  2,  3,  4,  0]])

        .. seealso::
            `numpy.pad <https://numpy.org/doc/stable/reference/generated/
            numpy.pad.html>`_,
            :func:`.aslazylinop`
    """

    msg = "Invalid pad_width, see documentation for more details."
    if isinstance(pad_width, int):
        pw = ((pad_width, pad_width), (pad_width, pad_width))
    elif isinstance(pad_width, tuple) and len(pad_width) == 1:
        pw = ((pad_width[0], pad_width[0]), (pad_width[0], pad_width[0]))
    elif len(pad_width) == 2 and isinstance(pad_width[0], int) and \
       isinstance(pad_width[1], int):
        pw = ((pad_width[0], pad_width[1]), (pad_width[0], pad_width[1]))
    elif len(pad_width) == 2 and isinstance(pad_width[0], tuple) and \
         isinstance(pad_width[1], tuple):
        if len(pad_width[0]) == 1:
            b = (pad_width[0][0], pad_width[0][0])
        else:
            b = (pad_width[0][0], pad_width[0][1])
        if len(pad_width[1]) == 1:
            a = (pad_width[1][0], pad_width[1][0])
        else:
            a = (pad_width[1][0], pad_width[1][1])
        pw = (b, a)
    else:
        raise Exception(msg)
    for i in range(2):
        for j in range(2):
            if not isinstance(pw[i][j], int):
                raise Exception(msg)

    msg = "Invalid constant_values, see documentation for more details."
    if isinstance(constant_values, int):
        cv = ((constant_values, constant_values),
              (constant_values, constant_values))
    elif isinstance(constant_values, tuple) and len(constant_values) == 1:
        cv = ((constant_values[0], constant_values[0]),
              (constant_values[0], constant_values[0]))
    elif len(constant_values) == 2 and isinstance(constant_values[0], int) and \
       isinstance(constant_values[1], int):
        cv = ((constant_values[0], constant_values[1]),
              (constant_values[0], constant_values[1]))
    elif len(constant_values) == 2 and isinstance(constant_values[0], tuple) and \
         isinstance(constant_values[1], tuple):
        if len(constant_values[0]) == 1:
            b = (constant_values[0][0], constant_values[0][0])
        else:
            b = (constant_values[0][0], constant_values[0][1])
        if len(constant_values[1]) == 1:
            a = (constant_values[1][0], constant_values[1][0])
        else:
            a = (constant_values[1][0], constant_values[1][1])
        cv = (b, a)
    else:
        raise Exception(msg)
    for i in range(2):
        for j in range(2):
            if not isinstance(cv[i][j], int):
                raise Exception(msg)

    if mode == 'constant':
        P = aslazylinop(op)
        # Pad axis=0.
        # Before.
        M, N = P.shape
        b, a = pw[0]
        if b > 0:
            if cv[0][0] != 0:
                P = vstack((cv[0][0] * ones((b, N)), P))
            else:
                P = vstack((zeros((b, N)), P))
        # After.
        if a > 0:
            if cv[0][1] != 0:
                P = vstack((P, cv[0][1] * ones((a, N))))
            else:
                P = vstack((P, zeros((a, N))))
        # Pad axis=1.
        # Before.
        M, N = P.shape
        b, a = pw[1]
        if b > 0:
            if cv[1][0] != 0:
                P = hstack((cv[1][0] * ones((M, b)), P))
            else:
                P = hstack((zeros((M, b)), P))
        # After.
        if a > 0:
            if cv[1][1] != 0:
                P = hstack((P, cv[1][1] * ones((M, a))))
            else:
                P = hstack((P, zeros((M, a))))
    elif mode == 'symmetric':
        lop = aslazylinop(op)
        M, N = lop.shape
        bn = (pw[0][0] // M, pw[1][0] // N)
        be = (pw[0][0] % M, pw[1][0] % N)
        an = (pw[0][1] // M, pw[1][1] // N)
        ae = (pw[0][1] % M, pw[1][1] % N)
        # Pad axis=0.
        P = aslazylinop(op)
        # Before
        flip = True
        for _ in range(bn[0]):
            # Symmetric copy?
            P = vstack((anti_eye(M) @ lop if flip else lop, P))
            flip ^= True
        # be elements (according to mode).
        if be[0] > 0:
            P = vstack((eye(be[0], M, k=M - be[0]) @ (
                anti_eye(M) @ lop if flip else lop), P))
        # After
        flip = True
        for _ in range(an[0]):
            # Symmetric copy?
            P = vstack((P, anti_eye(M) @ lop if flip else lop))
            flip ^= True
        # ae elements (according to mode).
        if ae[0] > 0:
            P = vstack((P, eye(ae[0], M) @ (
                anti_eye(M) @ lop if flip else lop)))
        # Pad axis=1.
        lop = aslazylinop(P)
        M, N = lop.shape
        # Before
        flip = True
        for _ in range(bn[1]):
            # Symmetric copy?
            P = hstack((lop @ anti_eye(N) if flip else lop, P))
            flip ^= True
        # be elements (according to mode).
        if be[1] > 0:
            P = hstack(((lop @ anti_eye(N) if flip else lop) @ eye(be[1], N, k=N - be[1]).T, P))
        # After
        flip = True
        for _ in range(an[1]):
            # Symmetric copy?
            P = hstack((P, lop @ anti_eye(N) if flip else lop))
            flip ^= True
        # ae elements (according to mode).
        if ae[1] > 0:
            P = hstack((P, (
                lop @ anti_eye(N) if flip else lop) @ eye(ae[1], N).T))
    elif mode == 'antisymmetric':
        lop = aslazylinop(op)
        M, N = lop.shape
        bn = (pw[0][0] // M, pw[1][0] // N)
        be = (pw[0][0] % M, pw[1][0] % N)
        an = (pw[0][1] // M, pw[1][1] // N)
        ae = (pw[0][1] % M, pw[1][1] % N)
        # Pad axis=0.
        P = aslazylinop(op)
        # Before
        flip = True
        for _ in range(bn[0]):
            # Symmetric copy?
            P = vstack((-anti_eye(M) @ lop if flip else lop, P))
            flip ^= True
        # be elements (according to mode).
        if be[0] > 0:
            P = vstack((eye(be[0], M, k=M - be[0]) @ (
                -anti_eye(M) @ lop if flip else lop), P))
        # After
        flip = True
        for _ in range(an[0]):
            # Symmetric copy?
            P = vstack((P, -anti_eye(M) @ lop if flip else lop))
            flip ^= True
        # ae elements (according to mode).
        if ae[0] > 0:
            P = vstack((P, eye(ae[0], M) @ (
                -anti_eye(M) @ lop if flip else lop)))
        # Pad axis=1.
        lop = aslazylinop(P)
        M = lop.shape[0]
        # Before
        flip = True
        for _ in range(bn[1]):
            # Symmetric copy?
            P = hstack((-anti_eye(M) @ lop if flip else lop, P))
            flip ^= True
        # be elements (according to mode).
        if be[1] > 0:
            P = hstack(((lop @ -anti_eye(M) if flip else lop) @ eye(be[1], M, k=M - be[1]).T, P))
        # After
        flip = True
        for _ in range(an[1]):
            # Symmetric copy?
            P = hstack((P, -anti_eye(M) @ lop if flip else lop))
            flip ^= True
        # ae elements (according to mode).
        if ae[1] > 0:
            P = hstack((P, (
                lop @ -anti_eye(M) if flip else lop) @ eye(ae[1], M).T))
    elif mode == 'periodic' or mode == 'wrap':
        lop = aslazylinop(op)
        M, N = lop.shape
        bn = (pw[0][0] // M, pw[1][0] // N)
        be = (pw[0][0] % M, pw[1][0] % N)
        an = (pw[0][1] // M, pw[1][1] // N)
        ae = (pw[0][1] % M, pw[1][1] % N)
        # Pad axis=0
        # Because mode is periodic, we just have to copy/paste.
        if (bn[0] + an[0]) == 0:
            P = aslazylinop(op)
        else:
            P = kron(ones((bn[0] + 1 + an[0], 1)), lop)
        if be[0] > 0:
            P = vstack([(eye(be[0], M, k=M - be[0]) @ lop), P])
        if ae[0] > 0:
            P = vstack([P, eye(ae[0], M) @ lop])
        # Pad axis=1
        lop = aslazylinop(P)
        M, N = lop.shape
        # Before
        for _ in range(bn[1]):
            P = hstack((lop, P))
        # be elements (according to mode).
        if be[1] > 0:
            P = hstack((lop @ eye(be[1], N, k=N - be[1]).T, P))
        # After
        for _ in range(an[1]):
            P = hstack((P, lop))
        # ae elements (according to mode).
        if ae[1] > 0:
            P = hstack((P, lop @ eye(ae[1], N).T))
    elif mode == 'reflect':
        M, N = op.shape
        if M == 1 or N == 1:
            raise ValueError("op.shape must be > 1.")
        lop = aslazylinop(op)
        M, N = lop.shape
        bn = (pw[0][0] // (M - 1), pw[1][0] // (N - 1))
        be = (pw[0][0] % (M - 1), pw[1][0] % (N - 1))
        an = (pw[0][1] // (M - 1), pw[1][1] // (N - 1))
        ae = (pw[0][1] % (M - 1), pw[1][1] % (N - 1))
        # Pad axis=0.
        P = aslazylinop(op)
        # Before
        flip = True
        for _ in range(bn[0]):
            # Reflected copy.
            P = vstack((anti_eye(M - 1, M) @ lop if flip
                        else eye(M - 1, M) @ lop, P))
            flip ^= True
        # be elements (according to mode).
        if be[0] > 0:
            P = vstack((anti_eye(be[0], M, k=M - 1 - be[0]) @ lop if flip
                        else eye(be[0], M, k=M - 1 - be[0]) @ lop, P))
        # After
        flip = True
        for _ in range(an[0]):
            # Reflected copy.
            P = vstack((P, anti_eye(M - 1, M, k=1) @ lop if flip
                        else eye(M - 1, M, k=1) @ lop))
            flip ^= True
        # ae elements (according to mode).
        if ae[0] > 0:
            P = vstack((P, anti_eye(ae[0], M, k=1) @ lop if flip
                        else eye(ae[0], M, k=1) @ lop))
        # Pad axis=1.
        lop = aslazylinop(P)
        M, N = lop.shape
        # Before
        flip = True
        for _ in range(bn[1]):
            # Reflected copy.
            P = hstack((lop @ anti_eye(N - 1, N).T if flip
                        else lop @ eye(N - 1, N).T, P))
            flip ^= True
        # be elements (according to mode).
        if be[1] > 0:
            P = hstack((lop @ anti_eye(be[1], N, k=N - 1 - be[1]).T if flip
                        else lop @ eye(be[1], N, k=N - 1 - be[1]).T, P))
        # After
        flip = True
        for _ in range(an[1]):
            # Reflected copy.
            P = hstack((P, lop @ anti_eye(N - 1, N, k=1).T if flip
                        else lop @ eye(N - 1, N, k=1).T))
            flip ^= True
        # ae elements (according to mode).
        if ae[1] > 0:
            P = hstack((P, lop @ anti_eye(ae[1], N, k=1).T if flip
                        else lop @ eye(ae[1], N, k=1).T))
    elif mode == 'edge':
        # Pad axis=0.
        lop = aslazylinop(op)
        M, N = lop.shape
        P = aslazylinop(op)
        # Edge before.
        if pw[0][0] > 0:
            P = vstack((
                kron(ones((pw[0][0], 1)), eye(1, M) @ lop), lop))
        # Edge after.
        if pw[0][1] > 0:
            P = vstack((
                P, kron(ones((pw[0][1], 1)), eye(1, M, k=M - 1) @ lop)))
        # Pad axis=1.
        lop = aslazylinop(P)
        M, N = lop.shape
        # Edge before.
        if pw[1][0] > 0:
            P = hstack((
                kron(ones((1, pw[1][0])), lop @ eye(N, 1)), P))
        # Edge after.
        if pw[1][1] > 0:
            P = hstack((
                P, kron(ones((1, pw[1][1])), lop @ eye(N, 1, k=-(N - 1)))))
    elif mode == 'mean':
        # Pad axis=0.
        lop = aslazylinop(op)
        M, N = lop.shape
        P = aslazylinop(op)
        # Mean before.
        if pw[0][0] > 0:
            P = vstack((
                kron(ones((pw[0][0], 1)), 1 / M * ones((1, M)) @ lop), lop))
        # Mean after.
        if pw[0][1] > 0:
            P = vstack((
                P, kron(ones((pw[0][1], 1)), 1 / M * ones((1, M)) @ lop)))
        # Pad axis=1.
        lop = aslazylinop(P)
        M, N = lop.shape
        # Mean before.
        if pw[1][0] > 0:
            P = hstack((
                kron(ones((1, pw[1][0])), lop @ (1 / N * ones((N, 1)))), P))
        # Mean after.
        if pw[1][1] > 0:
            P = hstack((
                P, kron(ones((1, pw[1][1])), lop @ (1 / N * ones((N, 1))))))
    else:
        raise Exception("mode must be either 'constant', 'symmetric', 'antisymmetric',"
                        + " 'wrap', 'periodic', 'reflect', 'edge' or 'mean'.")
    return P


def mpad(L: int, X: int, n: int = 1, add: str = 'after'):
    """Returns a :py:class:`LazyLinOp` to zero-pad each signal block.

    If you apply this operator to a vector of length L * X the output will have
    a length (L + n) * X.

    Args:
        L: int
            Block size
        X: int
            Number of blocks.
        n: int, optional
            Add n zeros to each block.
        add: str, optional
            If ``add='after'`` add ``n`` zeros after the block.
            If ``add='before'`` add ``n`` zeros before the block.
            Default value is ``'after'``.

    Returns:
        LazyLinOp

    Examples:
        >>> import lazylinop as lz
        >>> import numpy as np
        >>> x = np.full(3, 1.0)
        >>> x
        array([1., 1., 1.])
        >>> lz.mpad(1, 3, 1) @ x
        array([1., 0., 1., 0., 1., 0.])
        >>> lz.mpad(1, 3, 1, add='before') @ x
        array([0., 1., 0., 1., 0., 1.])
    """

    if n <= 0:
        return eye(X * L, X * L, k=0)

    if add == 'after':
        return kron(eye(X), eye(L + n, L))
    elif add == 'before':
        return kron(eye(X), eye(n + L, L, k=-n))
    else:
        raise Exception("add must be either after or before.")
