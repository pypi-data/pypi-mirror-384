from numpy import isscalar, floor
import scipy as sp
from lazylinop import LazyLinOp
from lazylinop.basicops import eye
from lazylinop.basicops import mpad
from lazylinop.basicops import vstack
from lazylinop.basicops import anti_eye, slicer
from lazylinop.signal import fft
from lazylinop.signal.utils import chunk
from lazylinop.signal.dst import (_mult_xi, _dtype_sanitized_x,
                                  _scipy_norm, _check_norm)
import sys
try:
    from cupyx.scipy.fft import dctn as cpx_dctn
    from cupyx.scipy.fft import idctn as cpx_idctn
except:
    pass
from math import sqrt
from array_api_compat import is_cupy_array, is_torch_array
sys.setrecursionlimit(100000)


def dct(N, type: int = 2, backend: str = 'scipy'):
    r"""
    Returns a :class:`.LazyLinOp` ```L`` for the Direct Cosine Transform (DCT).

    Shape of ``L`` is $(N,~N)$.

    ``L`` is orthonormal, and the :class:`.LazyLinOp`
    for the inverse DCT is ``L.T``.

    The function provides two backends: SciPy and Lazylinop.

    Args:
        N: ``int``
            Size of the input (N > 0).

        type: ``int``, optional
            1, 2, 3, 4 (I, II, III, IV).
            Defaut is 2.
            See `SciPy DCT <https://docs.scipy.org/doc/scipy/
            reference/generated/
            scipy.fft.dct.html#scipy-fft-dct>`_ and
            `CuPy DCT <https://docs.cupy.dev/en/latest/reference/
            generated/cupyx.scipy.fft.dct.html>`_ for more details.

        backend: str, optional
            ``'scipy'`` (default) uses ``(cupyx).scipy.fft.dct``
              encapsulation for the underlying computation
              of the DCT.
            - ``'lazylinop'`` uses a composition of basic Lazylinop operators
              to compute the DCT (:func:`.fft`, :func:`.vstack` etc.).

    Returns:
        :class:`.LazyLinOp`

    Example:
        >>> from lazylinop.signal import dct as lz_dct
        >>> from scipy.fft import dct as sp_dct
        >>> import numpy as np
        >>> N = 32
        >>> x = np.random.randn(N)
        >>> F = lz_dct(N)
        >>> y = F @ x
        >>> np.allclose(y, sp_dct(x, norm='ortho'))
        True
        >>> # compute the inverse DCT
        >>> x_ = F.T @ y
        >>> np.allclose(x_, x)
        True
        >>> # To mimick SciPy DCT II norm='ortho' and orthogonalize=False
        >>> from lazylinop.basicops import diag
        >>> v = np.full(N, 1.0)
        >>> v[0] = np.sqrt(2.0)
        >>> y = diag(v) @ F @ x
        >>> z = sp_dct(x, 2, N, 0, 'ortho', False, 1, orthogonalize=False)
        >>> np.allclose(y, z)
        True

    References:
        [1] A Fast Cosine Transform in One and Two Dimensions,
            by J. Makhoul, `IEEE Transactions on acoustics,
            speech and signal processing` vol. 28(1), pp. 27-34,
            :doi:`10.1109/TASSP.1980.1163351` (1980).

    .. seealso::
        - `DCT (Wikipedia) <https://en.wikipedia.org/
          wiki/Discrete_cosine_transform>`_,
        - `SciPy DCT <https://docs.scipy.org/doc/scipy/
          reference/generated/ scipy.fft.dct.html#scipy-fft-dct>`_,
        - `SciPy inverse DCT <https://docs.scipy.org/doc/scipy/
          reference/generated/ scipy.fft.idct.html#scipy-fft-idct>`_,
        - `CuPy DCT <https://docs.cupy.dev/en/latest/reference/
          generated/cupyx.scipy.fft.dct.html>`_,
        - :func:`.dst`
    """
    return _dct_helper(N, type, None, 'ortho', None, True, backend)


def _dct_helper(N, type: int = 2, n: int = None, norm: str = 'ortho',
                workers: int = None, orthogonalize: bool = None,
                backend: str = 'scipy'):
    r"""
    Returns a :class:`.LazyLinOp` for the Direct Cosine Transform (DCT).

    Operator dimensions: $n \times N$ (or $N \times N$ if ``n=None``).

    The function provides two backends: SciPy and Lazylinop.

    To compute the inverse DCT, simply use ``dct(...).inv()``
    (see example below).
    It works for any ``norm`` and ``orthogonalize`` configuration.
    For more details about the precise calculation you can consult
    :ref:`dct_inverse_computation`.

    Args:
        N: ``int``
            Size of the input (N > 0).

        type: ``int``, optional
            1, 2, 3, 4 (I, II, III, IV).
            Defaut is 2.
            See `SciPy DCT <https://docs.scipy.org/doc/scipy/
            reference/generated/
            scipy.fft.dct.html#scipy-fft-dct>`_ for more details.

        n: ``int``, optional
            Length of the output / size of the DCT.

            - If ``n < N``, crop the input before DCT.

            - If ``n > N``, zero-pad the input before DCT.

            - If ``n=None`` or equivalent ``n=N``, no cropping/padding.

        norm: ``str``, optional
            Normalization mode:

                - ``norm='ortho'`` (default): normalization with scale
                  factor $1/\sqrt{2n}$ or $1/\sqrt{2(n-1)}$ if ``type=1``.

                - ``norm=None``: no normalization.

                - ``norm='1/(2n)'``: the operator is scaled by $1/(2n)$
                  or $1/(2(n-1))$ if ``type=1``.

                See below the table for conversion to SciPy DCT ``norm``
                argument.

                The operator is orthogonal iff ``orthogonalize=True``,
                ``norm='ortho'`` and $N = n$ (square operator).
                See ``orthogonalize`` doc for more details.

        workers: ``int``, optional
            Number of workers (default ``None`` means ``os.cpu_count()``) to
            use for parallel computation if input has multiple columns.
            Works only for ``backend='scipy'``.

            See `SciPy DCT <https://docs.scipy.org/doc/scipy/
            reference/generated/
            scipy.fft.dct.html#scipy-fft-dct>`_ for more details.

        orthogonalize: bool, optional
            Orthogonalization scaling.

            Default is ``None`` (equivalent to ``True`` if ``norm='ortho'``,
            ``False`` otherwise).

            - ``orthogonalize=True``:

                - type I: the inputs ``x[0]``, ``x[n-1]`` are
                  scaled by $\sqrt{2}$. Output ``y[0]``,
                  ``y[n-1]`` are scaled by ${1 / \sqrt{2}}$.
                - type II: output ``y[0]`` is scaled by
                  ${1 / \sqrt{2}}$.
                - type III: input ``x[0]`` is scaled by
                  ${\sqrt{2}}$.

            - ``orthogonalize=False``: no additional scaling of any
              input/output entry.

            For type IV: no additional scaling whatever is ``orthogonalize``.


            See ``norm`` argument and `SciPy DCT
            <https://docs.scipy.org/doc/scipy/reference/generated/
            scipy.fft.dct.html#scipy-fft-dct>`_ for more details.

        backend: str, optional
            - ``'scipy'`` (default) uses ``scipy.fft.dct`` to compute the DCT.
            - ``'lazylinop'`` uses building-blocks to compute the DCT
              (Lazylinop :func:`.fft`, :func:`.vstack` etc.).

    Returns:
        :class:`.LazyLinOp`

    .. admonition:: Correspondence to `scipy.fft.dct <https://docs.scip
                    y.org/doc/scipy/reference/generated/scipy.fft.dct.
                    html>`_/`idct
                    <https://docs.scipy.org/doc/scipy/reference/
                    generated/scipy.fft.idct.html>`_ norm argument:
        :class: admonition note

        +------------------------------+-----------------------------+
        |                    **Forward operator**                    |
        +------------------------------+-----------------------------+
        |       Lazylinop              |        SciPy                |
        +------------------------------+-----------------------------+
        |    ``dct(N, norm=None) @ x`` | ``dct(x, norm='backward')`` |
        +------------------------------+-----------------------------+
        | ``dct(N, norm='ortho') @ x`` | ``dct(x, norm='ortho')``    |
        +------------------------------+-----------------------------+
        | ``dct(N, norm='1/(2n)') @ x``| ``dct(x, norm='forward')``  |
        +------------------------------+-----------------------------+

        +------------------------------+------------------------------+
        |                    **Transpose operator**                   |
        +-------------------------------+-----------------------------+
        |       Lazylinop               |        SciPy                |
        +-------------------------------+-----------------------------+
        | ``dct(N, norm=None).T @ y``   | ``idct(y, norm='forward')`` |
        +-------------------------------+-----------------------------+
        |``dct(N, norm='ortho').T @ y`` | ``idct(y, norm='ortho')``   |
        +-------------------------------+-----------------------------+
        |``dct(N, norm='1/(2n)').T @ y``| ``idct(y, norm='backward')``|
        +-------------------------------+-----------------------------+

    .. seealso::
        - `Wikipedia <https://en.wikipedia.org/
          wiki/Discrete_sine_transform>`_,
        - `A fast cosine transform in one and two dimensions
          <https://ieeexplore.ieee.org/document/1163351>`_,
        - `SciPy DCT <https://docs.scipy.org/doc/scipy/
          reference/generated/ scipy.fft.dct.html#scipy-fft-dct>`_,
        - `SciPy inverse DCT <https://docs.scipy.org/doc/scipy/
          reference/generated/ scipy.fft.idct.html#scipy-fft-idct>`_,
        - `CuPy DCT <https://docs.cupy.dev/en/latest/reference/
          generated/cupyx.scipy.fft.dct.html>`_,
        - :func:`.dst`
    """

    _check_norm(norm)

    if orthogonalize is None and norm == 'ortho':
        orthogonalize = True

    if backend == 'scipy':
        return _scipy_dct(N, type, n, norm, workers, orthogonalize)

    # Length of the output
    M = N if n is None else n

    if type == 1:
        # L @ x is equivalent to
        # sp.fft.dct(x, 1, n, 0, norm, False, 1, False)
        # up to a scale factor depending on norm.
        if M < 2:
            raise Exception("DCT I: size of the input must be >= 2.")
        S1 = slicer(2 * (M - 1), 0, M)
        F = fft(2 * (M - 1)) * sqrt(2 * (M - 1))
        L = S1 @ F
        if M > 2:
            S2 = slicer(M, 1, M-1)
            L = L @ vstack((eye(M, M, k=0),
                            anti_eye(M - 2) @ S2))
        if orthogonalize:
            L = L @ _mult_xi(M, [0, M - 1], [sqrt(2.0)] * 2)
            L = _mult_xi(M, [0, M - 1], [1.0 / sqrt(2.0)] * 2) @ L
    elif type == 2:
        # L @ x is equivalent to
        # sp.fft.dct(x, 2, n, 0, norm, False, 1, False)
        # Append flip(x) to the original input x.
        # Interleave with zeros such that the first element is zero.
        # Compute the DFT of length 4 * M and keep first M elements.
        S1 = slicer(4 * M, 0, M)
        F = fft(4 * M) * sqrt(4 * M)
        P = mpad(1, 2 * M, 1, ('before'))
        L = S1 @ F @ P @ vstack((eye(M, M, k=0),
                                 anti_eye(M)))
        if orthogonalize:
            # Divide first element of the output by sqrt(2).
            L = _mult_xi(M, [0], [1.0 / sqrt(2.0)]) @ L
    elif type == 3:
        # L @ x is equivalent to
        # sp.fft.dct(x, 3, n, 0, norm, False, 1, False)
        # up to a scale factor depending on norm.
        # type 3 is transpose of type 2 if first element
        # of x is divided by 2.
        S1 = slicer(4 * M, 0, M)
        F = fft(4 * M) * sqrt(4 * M)
        P = mpad(1, 2 * M, 1, ('before'))
        L = (S1 @ F @ P @ (
            vstack((eye(M),
                    anti_eye(M))))).T @ _mult_xi(M, [0], [0.5])
        if orthogonalize:
            L = L @ _mult_xi(M, [0], [sqrt(2.0)])
    elif type == 4:
        # L @ x is equivalent to
        # sp.fft.dct(x, 4, n, 0, norm, False, 1, False)
        # Append -flip(x), -x and flip(x) to the original input x.
        # Interleave with zeros such that the first element is zero.
        # Compute the DFT of length 8 * M and keep M odd elements.
        S1 = chunk(8 * M, size=1, hop=2, start=1, stop=2*M+1)
        F = fft(8 * M) * sqrt(8 * M)
        P = mpad(1, 4 * M, 1, ('before'))
        L = 0.5 * (
            S1 @ F @ P @ vstack(
                (
                    vstack((eye(M),
                            -anti_eye(M))),
                    vstack((-eye(M),
                            anti_eye(M)))
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
            sqrt(2 * (L.shape[0] - 1)),
            sqrt(2 * L.shape[0]),
            sqrt(2 * L.shape[0]),
            sqrt(2 * L.shape[0])
        ]
    elif norm == '1/(2n)':
        scale = [
            2 * (L.shape[0] - 1),
            2 * L.shape[0],
            2 * L.shape[0],
            2 * L.shape[0]
        ]
    # else: norm is None

    L_ = LazyLinOpDCST(
        shape=(L.shape[0], N),
        matmat=lambda x: (
            (L @ _dtype_sanitized_x(x, 'dct')).real if norm is None
            else (L @ _dtype_sanitized_x(x, 'dct')).real / scale[type - 1]
        ),
        rmatmat=lambda x: ((L.T @ x).real if norm is None
                           else ((L.T @ x).real / scale[type - 1])),
        dtype=None  # 'float'
    )

    _store_inv_info(L_, N, M, norm, type, orthogonalize)

    return L_


def _scipy_dct(N, type: int = 2, n: int = None, norm: str = 'backward',
               workers: int = None, orthogonalize: bool = None):
    """
    Returns a LazyLinOp for the DCT of size N.
    If the input array is a batch of vectors,
    apply DCT per column.

    Args:
        N: int
            Size of the input ($N > 0$).
        type: int, optional
            Defaut is 2.
            See `SciPy DCT <https://docs.scipy.org/doc/scipy/
            reference/generated/
            scipy.fft.dct.html#scipy-fft-dct>`_ for more details.
        n: int, optional
            Default is None.
            See `SciPy DCT <https://docs.scipy.org/doc/scipy/
            reference/generated/
            scipy.fft.dct.html#scipy-fft-dct>`_ for more details.
        norm: str, optional
            Default is 'backward'.
            See `SciPy DCT <https://docs.scipy.org/doc/scipy/
            reference/generated/
            scipy.fft.dct.html#scipy-fft-dct>`_ for more details.
        workers: int, optional
            Default is None
            See `SciPy DCT <https://docs.scipy.org/doc/scipy/
            reference/generated/
            scipy.fft.dct.html#scipy-fft-dct>`_ for more details.
        orthogonalize: bool, optional
            Default is None.
            See `SciPy DCT <https://docs.scipy.org/doc/scipy/
            reference/generated/
            scipy.fft.dct.html#scipy-fft-dct>`_ for more details.

    Returns:
        LazyLinOp

    Raises:
        ValueError
            norm must be either 'ortho', '1/(2n)' or None.
        ValueError
            type must be either 1, 2, 3 or 4.

    .. seealso::
        `SciPy DCT <https://docs.scipy.org/doc/scipy/
        reference/generated/ scipy.fft.dct.html#scipy-fft-dct>`_.
        `SciPy DCTn <https://docs.scipy.org/doc/scipy/reference/
        generated/scipy.fft.dctn.html>`_.
    """

    # Length of the output
    M = N if n is None else n

    # norm already validated by dct()

    # now set matching norm arguments for scipy
    # that allows L.toarray().T to be equal to L.T.toarray()
    # see orthogonalize == False case in _rmatmat
    sp_norm, sp_norm_inv = _scipy_norm(norm)

    n_workers = -1 if workers is None else workers

    if (not isscalar(type) or type - floor(type) != 0
        or type < 1 or type > 4):
        raise ValueError("type must be either 1, 2, 3 or 4.")

    # Pad or truncate the input with the help of lazylinop.
    # Therefore, do not modify sp.fft.(i)dct(n) argument n=None.
    pad_crop_lz = eye(M, N, k=0) if M != N else None

    def _matmat(x):
        # x is always 2d
        if is_torch_array(x):
            raise TypeError("backend='scipy' expects CuPy or NumPy arrays.")
        _dtype_sanitized_x(x, 'dct')
        if pad_crop_lz is not None:
            x = pad_crop_lz @ x
        if is_cupy_array(x):
            return cpx_dctn(x, type, (None), 0, sp_norm, False)
        else:
            return sp.fft.dctn(x, type, (None), 0, sp_norm, False, n_workers,
                               orthogonalize=orthogonalize)

    # define rmatmat pre/post-idct function needed for orthogonalize=None
    pre_idct = lambda x: x  # noqa: F811, E731
    if not orthogonalize:
        if type == 1:
            pre_idct = lambda x: _mult_xi(x.shape[0],  # noqa: F811, E731
                                          [0, x.shape[0]-1], [2] * 2) @ x
        elif type == 2:
            pre_idct = lambda x: _mult_xi(x.shape[0],  # noqa: F811, E731
                                          [0], [2]) @ x

    post_idct = lambda y: y  # noqa: F811, E731
    if not orthogonalize:
        if type == 1:
            post_idct = lambda y: _mult_xi(y.shape[0],  # noqa: F811, E731
                                           [0, y.shape[0]-1], [1 / 2] * 2) @ y
        elif type == 3:
            post_idct = lambda y: _mult_xi(y.shape[0],  # noqa: F811, E731
                                           [0], [1 / 2]) @ y

    def _rmatmat(x):
        # x is always 2d
        if is_torch_array(x):
            raise TypeError("backend='scipy' expects CuPy or NumPy arrays.")
        _dtype_sanitized_x(x, 'dct')
        x = pre_idct(x)
        if is_cupy_array(x):
            y = cpx_idctn(x, type, (None), 0, sp_norm_inv, False)
        else:
            y = sp.fft.idctn(x, type, (None), 0, sp_norm_inv, False,
                             n_workers, orthogonalize=orthogonalize)
        y = post_idct(y)
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


def _store_inv_info(L, N, M, norm, type, orthogonalize):
    # keep information for inversion
    L.scale = 2 * (M-1) if type == 1 else 2 * M
    L.norm = norm
    L.orthogonalize = orthogonalize

    if not orthogonalize and type < 4:
        if type == 1:
            L.pre_adj = _mult_xi(M, [0, M - 1], [.5] * 2)
            L.post_adj = _mult_xi(N, [0], [2])
            # post_adj[-1, -1] = 2
        elif type == 2:
            L.pre_adj = _mult_xi(M, [0], [.5])
        else:  # type == 3:
            L.post_adj = _mult_xi(N, [0], [2])


class LazyLinOpDCST(LazyLinOp):

    def inv(L):
        norm = L.norm
        scale = L.scale
        if norm == 'ortho':
            L_out = L.H
        elif norm == '1/(2n)':
            L_out = scale * L.H
        else:
            assert norm is None
            L_out = 1 / scale * L.H
        if hasattr(L, 'pre_adj'):
            L_out = L_out @ L.pre_adj
        if hasattr(L, 'post_adj'):
            L_out = L.post_adj @ L_out
        return L_out
