import numpy as np
import scipy as sp
from lazylinop import LazyLinOp
from lazylinop.basicops import eye
from lazylinop.basicops import mpad
from lazylinop.basicops import vstack
from lazylinop.basicops import anti_eye, slicer
from lazylinop.signal import fft
from lazylinop.signal.utils import chunk
import sys
from array_api_compat import (
    array_namespace, is_cupy_array, is_torch_array)
try:
    from cupyx.scipy.fft import dstn as cpx_dstn
    from cupyx.scipy.fft import idstn as cpx_idstn
except:
    pass
sys.setrecursionlimit(100000)


def dst(N, type: int = 2, backend: str = 'scipy'):
    r"""
    Returns a :class:`.LazyLinOp` ``L`` for the Direct Sine Transform (DST).

    Shape of ``L`` is $(N,~N)$.

    ``L`` is orthonormal, and the :class:`.LazyLinOp`
    for the inverse DST is ``L.T``.

    The function provides two backends: SciPy and Lazylinop.

    Args:
        N: ``int``
            Size of the input (N > 0).

        type: ``int``, optional
            1, 2, 3, 4 (I, II, III, IV).
            Defaut is 2.
            See `SciPy DST <https://docs.scipy.org/doc/scipy/
            reference/generated/
            scipy.fft.dst.html#scipy-fft-dst>`_ and
            `CuPy DST <https://docs.cupy.dev/en/latest/reference/
            generated/cupyx.scipy.fft.dst.html#cupyx.scipy.fft.dst>`_
            for more details.

        backend: str, optional
            - ``'scipy'`` (default) uses ``(cupyx).scipy.fft.dst``
              to compute the DST depending on the input array.
            - ``'lazylinop'`` Uses a composition of basic Lazylinop operators
              to compute the DST (:func:`.fft`, :func:`.vstack` etc.).

    Returns:
        :class:`.LazyLinOp`

    Example:
        >>> from lazylinop.signal import dst as lz_dst
        >>> from scipy.fft import dst as sp_dst
        >>> import numpy as np
        >>> x = np.random.randn(32)
        >>> F = lz_dst(32)
        >>> y = F @ x
        >>> np.allclose(y, sp_dst(x, norm='ortho'))
        True
        >>> # compute the inverse DST
        >>> x_ = F.T @ y
        >>> np.allclose(x_, x)
        True

    .. seealso::
       - `DST (Wikipedia) <https://en.wikipedia.org/wiki/
         Discrete_sine_transform>`_,
       - `SciPy DST <https://docs.scipy.org/doc/scipy/,
         reference/generated/ scipy.fft.dst.html#scipy-fft-dst>`_,
       - `SciPy inverse DST <https://docs.scipy.org/doc/scipy/reference/
         generated/scipy.fft.idst.html>`_,
       - `CuPy DST <https://docs.cupy.dev/en/latest/reference/
         generated/cupyx.scipy.fft.dst.html#cupyx.scipy.fft.dst>`_
       - :func:`.dct`
    """
    return _dst_helper(N, type, None, 'ortho', None, True, backend)


def _dst_helper(N, type: int = 2, n: int = None, norm: str = 'ortho',
                workers: int = None, orthogonalize: bool = None,
                backend: str = 'scipy'):
    r"""
    Returns a :class:`.LazyLinOp` for the Direct Sine Transform (DST).


    Operator dimensions: $n \times N$ (or $N \times N$ if ``n=None``).

    The function provides two backends: SciPy and Lazylinop.

    To compute the inverse DST, simply use ``dst(...).inv()``
    (see example below).
    It works for any ``norm`` and ``orthogonalize`` configuration.
    For more details about the precise calculation you can consult
    :ref:`dst_inverse_computation`.

    Args:
        N: ``int``
            Size of the input (N > 0).

        type: ``int``, optional
            1, 2, 3, 4 (I, II, III, IV).
            Defaut is 2.
            See `SciPy DST <https://docs.scipy.org/doc/scipy/
            reference/generated/
            scipy.fft.dst.html#scipy-fft-dst>`_  and
            `CuPy DST <https://docs.cupy.dev/en/latest/reference/
            generated/cupyx.scipy.fft.dst.html#cupyx.scipy.fft.dst>`_
            for more details.

        n: ``int``, optional
            Length of the output / size of the DCT.

            - If ``n < N``, crop the input before DCT.

            - If ``n > N``, zero-pad the input before DCT.

            - If ``n=None`` or equivalent ``n=N``, no cropping/padding.

        norm: ``str``, optional
            Normalization mode:

                - ``norm='ortho'`` (default): normalization with scale
                  factor $1/\sqrt{2n}$ or $1/\sqrt{2(n+1)}$ if ``type=1``.

                - ``norm=None``: no normalization.

                - ``norm='1/(2n)'``: the operator is scaled by $1/(2n)$
                  or $1/(2(n+1))$ if ``type=1``.

                See below the table for conversion to SciPy DST ``norm``
                argument.

                The operator is orthogonal iff ``orthogonalize=True``,
                ``norm='ortho'`` and $N = n$ (square operator).
                See ``orthogonalize`` doc for more details.

        workers: int, optional
            Number of workers (default ``None`` means ``os.cpu_count()``) to
            use for parallel computation if input has multiple columns.
            Works only for ``backend='scipy'``.

            See `SciPy DST <https://docs.scipy.org/doc/scipy/
            reference/generated/
            scipy.fft.dst.html#scipy-fft-dst>`_ for more details.

        orthogonalize: bool, optional
            Orthogonalization scaling.

            Default is ``None`` (equivalent to ``True`` if ``norm='ortho'``,
            ``False`` otherwise).

            - ``orthogonalize=True``:

                - type II: output ``y[n-1]`` is scaled by
                  ${1 / \sqrt{2}}$.
                - type III: input ``x[n-1]`` is scaled by
                  ${\sqrt{2} / 2}$.

            - ``orthogonalize=False``: no additional scaling of any
              input/output entry.

            For types I and IV: no additional scaling whatever is
            ``orthogonalize``.

            See ``norm`` argument and `SciPy DST
            <https://docs.scipy.org/doc/scipy/reference/generated/
            scipy.fft.dst.html#scipy-fft-dst>`_ for more details.

        backend: str, optional
            - ``'scipy'`` (default) uses ``scipy.fft.dst`` to compute the DST.
            - ``'lazylinop'`` uses building-blocks to compute the DST
              (Lazylinop :func:`.fft`, :func:`.vstack` etc.).

    Returns:
        :class:`.LazyLinOp`

    .. admonition:: Correspondence to `scipy.fft.dst <https://docs.scip
                    y.org/doc/scipy/reference/generated/scipy.fft.dst.
                    html>`_/`idst
                    <https://docs.scipy.org/doc/scipy/reference/
                    generated/scipy.fft.idst.html>`_ norm argument:
        :class: admonition note

        +------------------------------+-----------------------------+
        |                    **Forward operator**                    |
        +------------------------------+-----------------------------+
        |       Lazylinop              |        SciPy                |
        +------------------------------+-----------------------------+
        |    ``dst(N, norm=None) @ x`` | ``dst(x, norm='backward')`` |
        +------------------------------+-----------------------------+
        | ``dst(N, norm='ortho') @ x`` | ``dst(x, norm='ortho')``    |
        +------------------------------+-----------------------------+
        | ``dst(N, norm='1/(2n)') @ x``| ``dst(x, norm='forward')``  |
        +------------------------------+-----------------------------+

        +------------------------------+------------------------------+
        |                    **Transpose operator**                   |
        +-------------------------------+-----------------------------+
        |       Lazylinop               |        SciPy                |
        +-------------------------------+-----------------------------+
        | ``dst(N, norm=None).T @ y``   | ``idst(y, norm='forward')`` |
        +-------------------------------+-----------------------------+
        |``dst(N, norm='ortho').T @ y`` | ``idst(y, norm='ortho')``   |
        +-------------------------------+-----------------------------+
        |``dst(N, norm='1/(2n)').T @ y``| ``idst(y, norm='backward')``|
        +-------------------------------+-----------------------------+

    .. seealso::
       - `Wikipedia <https://en.wikipedia.org/wiki/Discrete_sine_transform>`_,
       - `SciPy DST <https://docs.scipy.org/doc/scipy/,
         reference/generated/ scipy.fft.dst.html#scipy-fft-dst>`_,
       - `SciPy inverse DST <https://docs.scipy.org/doc/scipy/reference/
         generated/scipy.fft.idst.html>`_,
       - `CuPy DST <https://docs.cupy.dev/en/latest/reference/
         generated/cupyx.scipy.fft.dst.html#cupyx.scipy.fft.dst>`_
       - :func:`.dct`
    """
    from .dct import LazyLinOpDCST
    _check_norm(norm)

    if orthogonalize is None and norm == 'ortho':
        orthogonalize = True

    if backend == 'scipy':
        return _scipy_dst(N, type, n, norm, workers, orthogonalize)

    # Length of the output
    M = N if n is None else n

    if (N <= 1 or M <= 1) and type == 1:
        raise Exception("DST I: N and n must be > 1.")
    if N < 1 or M < 1:
        raise Exception("N and n must be >= 1.")

    if type == 1:
        # L @ x is equivalent to
        # sp.fft.dst(x, 1, n, 0, norm, False, 1, orthogonalize)
        # up to a scale factor depending on norm.
        S1 = slicer(2 * (M + 1), 1, M+1)
        F = fft(2 * (M + 1)) * np.sqrt(2 * (M + 1))
        L = S1 @ F @ vstack((eye(M + 2, M, k=-1),
                             -anti_eye(M)))
    elif type == 2:
        # L @ x is equivalent to
        # sp.fft.dst(x, 2, n, 0, norm, False, 1, orthogonalize)
        # up to a scale factor depending on norm.
        # Append -flip(x) to the original input x.
        # Interleave with zeros such that the first element is zero.
        # Compute the DFT of length 4 * M and keep first M elements.
        S1 = slicer(4 * M, 1, M+1)
        F = fft(4 * M) * np.sqrt(4 * M)
        P = mpad(1, 2 * M, 1, ('before'))
        L = S1 @ F @ P @ vstack((eye(M, M, k=0),
                                 -anti_eye(M)))
        if orthogonalize:
            # Divide last element of the output by sqrt(2).
            L = _mult_xi(M, [M - 1], [1.0 / np.sqrt(2.0)]) @ L
    elif type == 3:
        # L @ x is equivalent to
        # sp.fft.dst(x, 3, n, 0, norm, False, 1, orthogonalize)
        # up to a scale factor depending on norm.
        # type 3 is transpose of type 2 if last element
        # of x is multiplied by 1 / 2 if not orthogonalize,
        # sqrt(2) / 2 if orthogonalize.
        S1 = slicer(4 * M, 1, M+1)
        F = fft(4 * M) * np.sqrt(4 * M)
        P = mpad(1, 2 * M, 1, ('before'))
        L = (S1 @ F @ P @ vstack((eye(M, M, k=0),
                                  -anti_eye(M)))).T
        Q = _mult_xi(M, [M - 1],
                     [0.5 * (np.sqrt(2.0) if orthogonalize else 1.0)])
        L = L @ Q
    elif type == 4:
        # L @ x is equivalent to
        # sp.fft.dst(x, 4, n, 0, norm, False, 1, orthogonalize)
        # up to a scale factor depending on norm.
        # Append flip(x), -x and -flip(x) to the original input x.
        # Interleave with zeros such that the first element is zero.
        # Compute the DFT of length 8 * M and keep M odd elements.
        S1 = chunk(8 * M, size=1, hop=2, start=1, stop=2*M+1)
        F = fft(8 * M) * np.sqrt(8 * M)
        P = mpad(1, 4 * M, 1, ('before'))
        L = 0.5 * (
            S1 @ F @ P @ vstack(
                (
                    vstack((eye(M, M, k=0),
                            anti_eye(M))),
                    vstack((-eye(M, M, k=0),
                            -anti_eye(M)))
                )
            )
        )
    else:
        raise ValueError("type must be either 1, 2, 3 or 4.")

    if M != N:
        # Pad with zero or truncate the input
        L = L @ eye(M, N, k=0)

    if norm == 'ortho':
        scale = [
            np.sqrt(2 * (L.shape[0] + 1)),
            np.sqrt(2 * L.shape[0]),
            np.sqrt(2 * L.shape[0]),
            np.sqrt(2 * L.shape[0])
        ]
    elif norm == '1/(2n)':
        scale = [
            2 * (L.shape[0] + 1),
            2 * L.shape[0],
            2 * L.shape[0],
            2 * L.shape[0]
        ]
    # else: norm is None

    # Use a function to apply scale factor
    # and orthogonalize if True.
    def _matmat(L, x):
        _dtype_sanitized_x(x, 'dst')
        y = -(L @ x).imag
        if norm in ['ortho', '1/(2n)']:
            y /= scale[type - 1]
        return y

    L_ = LazyLinOpDCST(
        shape=(L.shape[0], N),
        matmat=lambda x: _matmat(L, x),
        rmatmat=lambda x: _matmat(L.T, x),
        dtype=None  # 'float'
    )

    _store_inv_info(L_, N, M, norm, type, orthogonalize)

    return L_


def _scipy_dst(N, type: int = 2, n: int = None, norm: str = 'ortho',
               workers: int = None, orthogonalize: bool = None):
    """
    Returns a LazyLinOp that encapsulates SciPy DST of size N.
    If the input array is a batch of vectors,
    apply DST per column.
    """
    from .dct import LazyLinOpDCST
    # Length of the output
    M = N if n is None else n

    # norm already validated by dst()

    # now set matching norm arguments for scipy
    # that allows L.toarray().T to be equal to L.T.toarray()
    # see orthogonalize == False case in _rmatmat
    sp_norm, sp_norm_inv = _scipy_norm(norm)
    n_workers = -1 if workers is None else workers

    if (not np.isscalar(type) or type - np.floor(type) != 0
       or type < 1 or type > 4):
        raise ValueError("type must be either 1, 2, 3 or 4.")

    # Pad or truncate the input with the help of lazylinop.
    # Therefore, do not modify sp.fft.(i)dct(n) argument n=None.
    pad_crop_lz = eye(M, N, k=0) if M != N else None

    def _matmat(x):
        if is_torch_array(x):
            raise TypeError("backend='scipy' expects CuPy or NumPy arrays.")
        _dtype_sanitized_x(x, 'dst')
        # x is always 2d
        if pad_crop_lz is not None:
            x = pad_crop_lz @ x
        if is_cupy_array(x):
            return cpx_dstn(x, type, (None), 0, sp_norm, False)
        else:
            return sp.fft.dstn(x, type, (None), 0, sp_norm,
                               False, n_workers, orthogonalize=orthogonalize)

    # define rmatmat pre/post-idst function needed for orthogonalize=None
    if not orthogonalize and type == 2:
        pre_idst = lambda x: _mult_xi(x.shape[0],  # noqa: F811, E731
                                      [x.shape[0]-1], [2]) @ x
    else:
        pre_idst = lambda x: x  # noqa: F811, E731

    if not orthogonalize and type == 3:
        post_idst = lambda y: _mult_xi(y.shape[0],  # noqa: F811, E731
                                       [y.shape[0]-1], [0.5]) @ y
    else:
        post_idst = lambda y: y  # noqa: F811, E731

    def _rmatmat(x):
        # x is always 2d
        if is_torch_array(x):
            raise TypeError("backend='scipy' expects CuPy or NumPy arrays.")
        _dtype_sanitized_x(x, 'dst')
        x = pre_idst(x)
        if is_cupy_array(x):
            y = cpx_idstn(x, type, (None), 0, sp_norm_inv, False)
        else:
            y = sp.fft.idstn(x, type, (None), 0, sp_norm_inv, False,
                             n_workers, orthogonalize=orthogonalize)
        y = post_idst(y)
        if pad_crop_lz is not None:
            y = pad_crop_lz.T @ y
        return y

    L = LazyLinOpDCST(
        shape=(M, N),
        matmat=lambda x: _matmat(x),
        rmatmat=lambda x: _rmatmat(x),
        dtype=None  # 'float'
    )

    _store_inv_info(L, N, M, norm, type, orthogonalize)

    return L


def _mult_xi(N, idx, a):
    """Constructs a LazyLinOp that multiplies some of the elements
    of an input array by a factor and left unchanged the others.

    Args:
        N: int
            Length of the input array.
        idx: list
            List of indices.
        a: list
            List of factors.

    Returns:
        LazyLinOp
    """

    if len(idx) == 0 or len(a) == 0:
        raise Exception("idx and a must have one element at least.")
    if len(idx) != len(a):
        raise Exception("idx and a must have the same length.")

    def _matmat(x):
        # x is always 2d
        xp = array_namespace(x)
        if is_torch_array(x):
            y = xp.clone(x)
        else:
            y = x.copy()
        for i, v in enumerate(idx):
            y[v, :] *= a[i]
        return y

    return LazyLinOp(
        shape=(N, N),
        matmat=lambda x: _matmat(x),
        rmatmat=lambda x: _matmat(x)
    )


def _dtype_sanitized_x(x, func):
    if 'complex' in str(x.dtype):
        # do not use np.iscomplex
        # x can not be a numpy array
        # (e.g. x a scipy mat)
        raise ValueError(str(func)+" is a real function but x is not real")
    return x


_valid_norms = ['ortho', None, '1/(2n)']


def _check_norm(norm):
    if norm not in _valid_norms:
        raise ValueError("norm must be either 'ortho'," +
                         " '1/(2n)' or None.")
    return norm


def _scipy_norm(lz_norm):
    # determine *fft, i*fft norm arguments
    # form lz norm argument
    if lz_norm is None:
        sp_norm = 'backward'
        sp_norm_inv = 'forward'
    elif lz_norm == '1/(2n)':
        sp_norm = 'forward'
        sp_norm_inv = 'backward'
    else:  # lz_norm is 'ortho'
        assert lz_norm == 'ortho'
        sp_norm = sp_norm_inv = 'ortho'
    return sp_norm, sp_norm_inv


def _store_inv_info(L, N, M, norm, type, orthogonalize):
    # keep information for inversion
    L.scale = 2 * (M + 1) if type == 1 else 2 * M
    L.norm = norm
    L.orthogonalize = orthogonalize

    if not orthogonalize and type in [2, 3]:
        if type == 2:
            L.pre_adj = _mult_xi(M, [M-1], [0.5])
        else:  # type == 3:
            if N >= M:
                L.post_adj = _mult_xi(N, [M-1], [2])
