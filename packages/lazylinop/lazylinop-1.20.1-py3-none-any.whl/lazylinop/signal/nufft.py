import numpy as np
try:
    import cupy as cp
except ModuleNotFoundError:
    cp = None
try:
    import torch
except ModuleNotFoundError:
    torch = None
from lazylinop import LazyLinOp
from lazylinop.basicops import indexer
from lazylinop.signal import fft
from array_api_compat import (
    array_namespace, device, is_numpy_array,
    is_cupy_array, is_torch_array)
from scipy.special import jv, lambertw
from warnings import warn


def _direct(s, f, x, isign: int = -1):
    r"""
    Naive implementation of NUFFT.

    Args:
        s: 1d array
            Samples $s_j\in\left[0,~1\right]$.
        f: 1d array
            Frequencies $\omega_k\in\left[0,~N\right]$.
            ``s`` and ``f`` must have the same length.
        x: 1d array
            1d array signal.
        isign: ``int``
            Sign in the exponential.
            Default value is $-1$.
    """
    xp = array_namespace(x)
    N = x.shape[0]
    arg = isign * 2j * xp.pi
    _cplx = 'torch' in str(xp.__package__) and 'complex' not in str(x.dtype)
    return (
        xp.exp(
            arg * (f.reshape(-1, 1) @ s.reshape(1, -1))) @ (
                x + 0j if _cplx
                else x
            )
    ) / xp.sqrt(xp.asarray([N], device=device(x)))


def nufft(N: int, samples=None, frequencies=None,
          backend: str = 'lazylinop', eps: float = 1e-6):
    r"""
    Returns a :class:`.LazyLinOp` ``L`` for the
    Non-Uniform Discrete Fourier Transform (NUFFT).

    Shape of ``L`` is $(N,~N)$.

    In general, ``L.H`` is not the inverse NUFFT (as the
    generic NUFFT is not orthonormal).

    ``L = nufft(N, None, None)`` (default) is functionally
    equivalent to the Fast-Fourier-Transform operator and
    returns ``F = fft(N)``.

    The nonuniform Discrete Fourier Transform is defined
    (for possibly nonuniform samples $s_n$ and possibly
    nonuniform frequencies $\omega_k$) as:

    .. math::

        \begin{equation}
        y_k\equiv\left(\omega_k\right)~\text{where}~y\left(\omega\right)=\frac{1}{\sqrt{N}}\sum_{n=0}^{N-1}x_ne^{-2\pi is_n\omega}\text{,}~\forall\omega\in\left[0,~N\right]
        \end{equation}

    Args:
        N: ``int``
            Size of the input ($N > 0$).
        samples: 1d array
            Samples $s_n\in\left[0,~1\right[$ must be real.
            The size of ``samples`` must be $N$.
            Default value is ``None`` (uniform samples
            $s_n=\frac{n}{N}$ with $0\le n\lt N$).
        frequencies: 1d array
            Frequencies $\omega_k\in\left[0,~N\right[$ must be real.
            The size of ``frequencies`` must be $N$.
            Default value is ``None`` (uniform frequencies
            $\omega_k=k$ with $0\le k\lt N$).
        backend: ``str``, optional
            Three different implementations are available:

            - ``'lazylinop'`` is the default value.
              The underlying implementation is based on
              :ref:`[1] <nufft>` and :py:class:`.LazyLinOp`'s
              pre-built operators.
            - ``'finuftt'`` uses encapsulation of `fiNUFFT Python
              package <https://finufft.readthedocs.io/en/latest/>`_.
            - ``'direct'`` uses direct computation of NUFFT.
              In the case of small $N$ there is no need for
              a fast algorithm.
              ``eps`` argument has no effect for ``backend='direct'``.
        eps: ``float``, optional
            Precision to achieve (see :ref:`[1] <nufft>` and
            `fiNUFFT Python package <https://finufft.
            readthedocs.io/en/latest/>`_ for more details).
            Default value is ``1e-6``.
            It has not effect for ``backend='direct'``.

    Returns:
        :class:`.LazyLinOp` NUFFT

    Examples:
        >>> from lazylinop.signal import nufft
        >>> import numpy as np
        >>> N = 32
        >>> x = np.random.randn(N)
        >>> samples = np.random.rand(N)
        >>> k = 4
        >>> F = nufft(N, samples, None)
        >>> y = F @ x
        >>> # Naive implementation of NUFFT-II.
        >>> z = np.sum(x * np.exp(-2j * np.pi * k * samples)) / np.sqrt(N)
        >>> np.allclose(y[k], z)
        True

    .. _nufft:

        **References:**

        [1] A Nonuniform Fast Fourier Transform Based on Low Rank Approximation.
        Diego Ruiz-Antolin and Alex Townsend
        SIAM Journal on Scientific Computing 2018 40:1, A529-A547
    """

    if backend not in ['direct', 'finufft', 'lazylinop']:
        raise ValueError("backend must be either" +
                         " 'direct', 'finufft' or 'lazylinop'.")

    if samples is not None and frequencies is not None:
        xp = array_namespace(samples)
        type = 3
    elif samples is not None and frequencies is None:
        xp = array_namespace(samples)
        type = 2
    elif samples is None and frequencies is not None:
        xp = array_namespace(frequencies)
        type = 1
    else:
        return fft(N)

    if samples is not None:
        if 'complex' in str(samples.dtype):
            raise TypeError("samples must be real.")
        if samples.shape[0] != N:
            raise Exception("samples size must be N.")
    if frequencies is not None:
        if 'complex' in str(frequencies.dtype):
            raise TypeError("frequencies must be real.")
        if frequencies.shape[0] != N:
            raise Exception("frequencies size must be N.")

    if frequencies is not None and (
            xp.min(xp.real(frequencies)) < 0 or
            xp.max(xp.real(frequencies)) > N):
        raise Exception("frequencies must be in the interval [0, N].")
    if samples is not None and (
            xp.min(xp.real(samples)) < 0.0 or
            xp.max(xp.real(samples)) > 1.0):
        raise Exception("samples must be in the interval [0, 1).")

    if backend == 'direct':
        # N is small: use direct computation of NUFFT.
        if type == 1:
            _s = xp.arange(
                N, dtype=frequencies.dtype, device=device(frequencies)) / N
            return LazyLinOp(
                shape=(N, N),
                matmat=lambda x: _direct(_s, frequencies, x, -1),
                rmatmat=lambda x: _direct(frequencies / N, N * _s, x, 1)
            )
        elif type == 2:
            _f = xp.arange(
                N, dtype=samples.dtype, device=device(samples))
            return LazyLinOp(
                shape=(N, N),
                matmat=lambda x: _direct(samples, _f, x, -1),
                rmatmat=lambda x: _direct(_f / N, N * samples, x, 1)
            )
        elif type == 3:
            return LazyLinOp(
                shape=(N, N),
                matmat=lambda x: _direct(samples, frequencies, x, -1),
                rmatmat=lambda x: _direct(frequencies / N, N * samples, x, 1)
            )

    if backend == 'finufft':
        # finufft does not support torch tensors.
        # If namespace is torch convert tensor to CuPy array.
        # If device is cpu convert to NumPy array.
        kwargs = {}
        if 'numpy' in str(xp.__package__):
            from finufft import nufft1d1, nufft1d3
        elif 'torch' in str(xp.__package__):
            warn("backend='finufft' uses cupy.from_dlpack" +
                 " to convert PyTorch tensor to CuPy array.")
            str_d = str(device(
                samples if samples is not None else frequencies))
            if 'cpu' in str_d:
                from finufft import nufft1d1, nufft1d3
            elif 'cuda' in str_d:
                _device_id = int(str_d.replace("cuda:", ""))
                kwargs = {"gpu_device_id": _device_id}
                cp.cuda.runtime.setDevice(_device_id)
                from cufinufft import nufft1d1, nufft1d3
        elif 'cupy' in str(xp.__package__):
            _device = (samples if samples is not None
                       else frequencies).device
            kwargs = {"gpu_device_id": _device.id}
            from cufinufft import nufft1d1, nufft1d3
        if 'torch' in str(xp.__package__):
            def _cupy2torch(c):
                return torch.from_dlpack(c)

            def _torch2cupy(t):
                if 'cpu' in str(device(t)):
                    return np.from_dlpack(t)
                elif 'cuda' in str(device(t)):
                    return cp.from_dlpack(t)
        else:
            def _cupy2torch(c):
                return c

            def _torch2cupy(t):
                return t
        # finufft does not normalize by sqrt(N).
        # finutt expects complex input but floating-point
        # precision for the samples and frequencies.
        norm = _torch2cupy(xp.pow(xp.sqrt(xp.asarray(
            [N], dtype=(frequencies if samples is None else samples).dtype,
            device=device(frequencies if samples is None else samples))), -1))
        if type == 1:
            # finufft omega are in the interval [0, N].
            # FIXME: use nufft1d1 instead of nufft1d3.
            # f_k = sum(x[j] * exp(+/- i * w[k] * s[j]), j)
            xx = _torch2cupy(xp.asarray(
                2.0 * xp.pi / N,
                dtype=(frequencies if samples is None else samples).dtype,
                device=device(frequencies if samples is None else samples)))
            seq = _torch2cupy(xp.arange(
                N, dtype=frequencies.dtype, device=device(frequencies)))
            _f = _torch2cupy(frequencies)
            # finufft source strengths shape is (n_tr, N).
            return LazyLinOp(
                shape=(N, N),
                matvec=lambda x: _cupy2torch(nufft1d3(
                    xx * seq, _torch2cupy(x) + 0j, _f,
                    out=None, eps=eps, isign=-1,
                    **kwargs) * norm),
                rmatvec=lambda x: _cupy2torch(nufft1d3(
                    xx * _f, _torch2cupy(x) + 0j, seq,
                    out=None, eps=eps, isign=1,
                    **kwargs) * norm)
            )
        elif type == 2:
            # finufft samples are in the interval [0, 2 * pi].
            xx = _torch2cupy(
                xp.asarray(2.0 * xp.pi,
                           dtype=samples.dtype, device=device(samples)))
            seq = xx * _torch2cupy(
                xp.arange(
                    N, dtype=samples.dtype, device=device(samples)))
            _s = _torch2cupy(samples)
            # finufft source strengths shape is (n_tr, N).
            return LazyLinOp(
                shape=(N, N),
                matvec=lambda x: _cupy2torch(
                    nufft1d1(xx * _s, _torch2cupy(x) + 0j,
                             n_modes=2 * N, out=None,
                             eps=eps, isign=-1,
                             **kwargs) * norm)[N:],
                rmatvec=lambda x: _cupy2torch(
                    nufft1d3(seq, _torch2cupy(x) + 0j, _s,
                             out=None, eps=eps, isign=1,
                             **kwargs) * norm)
            )
        elif type == 3:
            # finufft samples are in the interval [-pi, pi].
            # finufft omega are in the interval [0, N].
            # f_k = sum(x[j] * exp(+/- i * w[k] * s[j]), j)
            xx = _torch2cupy(
                xp.asarray(2.0 * xp.pi, dtype=samples.dtype,
                           device=device(samples)))
            _s = xx * _torch2cupy(samples)
            _f = _torch2cupy(frequencies)
            # finufft source strengths shape is (n_tr, N).
            return LazyLinOp(
                shape=(N, N),
                matvec=lambda x: _cupy2torch(
                    nufft1d3(_s, _torch2cupy(x) + 0j, _f,
                             out=None, eps=eps, isign=-1,
                             **kwargs) * norm),
                rmatvec=lambda x: _cupy2torch(
                    nufft1d3(_f, _torch2cupy(x) + 0j, _s,
                             out=None, eps=eps, isign=1,
                             **kwargs) * norm)
            )

    # Use pre-built LazyLinOp's to build NUFFT.
    if type == 1:
        return _nufft(N, None, frequencies, eps)
    elif type == 2:
        # NUFFT-II corresponds to a transposed NUFFT-I.
        return _nufft(N, samples, None, eps)
        # return _nufft(N, None, N * samples, eps)
    elif type == 3:
        # Compute e and t (see Ref.[1] for more details).
        e = xp.asarray(
            xp.round(frequencies),
            dtype=xp.int if 'torch' in str(xp.__package__) else 'int',
            device=device(frequencies))
        t = e - N * (e // N)
        # Computation of NUFFT-III uses NUFFT-II:
        # From definition we have (see Ref.[1] for more details):
        # y_k    = sum(x_k * exp(-2 * pi * im * s_j * w_k), j)
        # N_{jk} = exp(-2 * pi * im * s_j * w_k)
        #        = exp(-2 * pi * im * s_j * (w_k - e_k)) *
        #          exp(-2 * pi * im * s_j * e_k)
        #        = exp(-2 * pi * im * s_j * (w_k - e_k)) *
        #          exp(-2 * pi * im * s_j * (e_k - t_k)) *
        #          exp(-2 * pi * im * s_j * t_k)
        #        = exp(-2 * pi * im * s_j * (w_k - e_k)) *
        #          exp(-2 * pi * im * s_j * (e_k - t_k)) *
        #          N2_{jk}
        # where e_k = round(w_k, N) corresponds to equispaced
        # frequencies and t_k = mod(round(w_k, N), N).
        # A o B o NUFFT-II where o is the Hadamard product.
        F_2 = indexer(
            N, t.tolist()) @ _nufft(N, samples, None, eps)
        # Chebyshev expansion (see Ref.[1] for more details).
        err = frequencies - e
        gamma = xp.linalg.norm(err, xp.inf)
        np_gamma = 5.0 * np.asarray(gamma.tolist())
        # Rank value.
        if gamma > eps:
            tmp = (np_gamma * np.exp(
                lambertw([np.log(140 / eps) / np_gamma], k=0)))[0]
            _rank = max(3, int(np.ceil(np.real([tmp]))[0]))
            err_gamma = err / gamma
        else:
            _rank = 1
            err_gamma = err
        # Compute vectors uA and vA.
        exp_err = xp.exp(-1j * xp.pi * err)
        arg = np.asarray((-0.5 * gamma * xp.pi).tolist())
        _vA = (2 * samples - 1).reshape(1, -1)
        # Pre-compute Chebyshev polynomial T_p.
        T_p = []
        for p in range(_rank):
            if p == 0:
                T_p.append(xp.full(N, 1, dtype=err.dtype,
                                   device=device(err)))
            elif p == 1:
                T_p.append(err_gamma)
            else:
                T_p.append(2 * err_gamma * T_p[p - 1] - T_p[p - 2])
        # Loop over rank to compute u_r and v_r.
        uA = xp.zeros((_rank, N),
                      dtype=(exp_err * T_p[0]).dtype, device=device(err))
        vA = xp.zeros((_rank, N), dtype=err.dtype, device=device(err))
        for r in range(_rank):
            for p in range(_rank):
                # First term is halved, see Ref.[1] for more details.
                _halved = 0.5 if p == 0 else 1.0
                if abs(p - r) % 2 == 0:
                    a_pr = 4.0 * (1j ** r) * (
                        jv([0.5 * (p + r)], arg) * jv([0.5 * (r - p)], arg))[0]
                    uA[r] += _halved * a_pr * exp_err * T_p[p]
            if r == 0:
                vA[r] = xp.full((1, N), 1, dtype=err.dtype, device=device(err))
            elif r == 1:
                vA[r] = _vA
            else:
                vA[r] = 2 * _vA * vA[r - 1] - vA[r - 2]
        # The first term is halved (see Ref.[1] for more details).
        vA[0] *= 0.5

        # # Taylor expansion (see Ref.[1] for more details).
        # _vA = (-2.0j * xp.pi * samples).reshape(1, -1)
        # uA, vA = xp.pow(err, 0).reshape(1, -1), xp.pow(_vA, 0).reshape(1, -1)
        # for r in range(1, _rank):
        #     uA = xp.vstack((uA, uA[r - 1] * err))
        #     vA = xp.vstack((vA, vA[r - 1] * _vA / r))

        # Compute B = uB_0 @ vB_0^T + uB_1 @ vB_1^T.
        # See Ref.[1] for more details.
        _rankB = 1 if xp.all(
            xp.logical_or((e - t) == N, (e - t) == 0)) else 2
        if _rankB == 1:
            uB = xp.full((1, N), 1.0, dtype=err.dtype, device=device(err))
            vB = xp.full((1, N), 1.0, dtype=err.dtype, device=device(err))
        else:
            uB = xp.vstack(
                (uB[0] - ((e - t) / N).reshape(1, -1),
                 ((e - t) / N).reshape(1, -1)))
            vB = xp.vstack(
                (vB[0], xp.exp(-2.0j * xp.pi * samples).reshape(1, -1)))
        # Store pre-compute diag operators.
        # Compute A o B = sum(uA_i @ vA_i^T, i) o sum(uB_j @ vB_j^T, j)
        #               = sum((uA_i @ vA_i^T) o (uB_j @ vB_j^T), i, j)
        #               = sum(diag(uA_i) @ (uB_j @ vB_j^T) @ diag(vA_i), i, j)
        #               = sum((uA_i o uB_j) @ (vB_j o vA_i)^T, i, j)
        # Compute (A o B) o F_2
        # = sum((uA_i o uB_j) @ (vB_j o vA_i)^T, i, j) o F_2
        # = sum(((uA_i o uB_j) @ (vB_j o vA_i)^T) o F_2, i, j)
        # = sum(diag(uA_i o uB_j) @ F_2 @ diag(vB_j o vA_i), i, j)
        D = {'u': {}, 'v': {}}
        for i in ['u', 'v']:
            D[i] = {'mul': {}, 'rmul': {}}

        def _matmat(x, adjoint: bool = False):

            xp = array_namespace(x)
            # Get pre-computed u_r, v_r or
            # compute it according to x.
            mul = 'rmul' if adjoint else 'mul'
            for i in ['u', 'v']:
                if 'numpy' in str(xp):
                    lib = 'numpy'
                elif 'cupy' in str(xp):
                    lib = 'cupy'
                elif 'torch' in str(xp):
                    lib = 'torch'
                if lib not in D[i][mul].keys():
                    D[i][mul][lib] = {}
            # Get dtype and device of x.
            _dtype, _device = (x + 0j).dtype, device(x)
            str_t, str_d = str(_dtype), str(_device)
            for i in ['u', 'v']:
                if str_t not in D[i][mul][lib].keys():
                    D[i][mul][lib][str_t] = {}
                if str_d not in D[i][mul][lib][str_t].keys():
                    D[i][mul][lib][str_t][str_d] = {}
            # Cast u and/or v if needed.
            _D = {'u': None, 'v': None}
            for i in ['u', 'v']:
                # if not bool(D[i][mul][lib][str_t][str_d]):
                if D[i][mul][lib][str_t][str_d] == {}:
                    for r in range(_rank):
                        for j in range(_rankB):
                            if i == 'u':
                                D[i][mul][lib][str_t][str_d][
                                    f"{r}-{j}"] = (
                                        xp.asarray(
                                            uA[r] * uB[j],
                                            copy=True, dtype=_dtype,
                                            device=_device
                                        ) if mul == 'mul' else
                                        xp.asarray(
                                            uA[r] * uB[j],
                                            copy=True, dtype=_dtype,
                                            device=_device
                                        ).T.conj()
                                    ).reshape(-1, 1)
                            elif i == 'v':
                                D[i][mul][lib][str_t][str_d][
                                    f"{r}-{j}"] = (
                                        xp.asarray(
                                            vB[j] * vA[r],
                                            copy=True, dtype=_dtype,
                                            device=_device
                                        ) if mul == 'mul' else
                                        xp.asarray(
                                            vB[j] * vA[r],
                                            copy=True, dtype=_dtype,
                                            device=_device
                                        ).T.conj()
                                    ).reshape(-1, 1)
                _D[i] = D[i][mul][lib][str_t][str_d]

            y = None
            for r in range(_rank):
                for j in range(_rankB):
                    k = f"{r}-{j}"
                    if adjoint:
                        dy = _D['v'][k] * (F_2.H @ (_D['u'][k] * x))
                    else:
                        dy = _D['u'][k] * (F_2 @ (_D['v'][k] * x))
                    if r == 0 and j == 0:
                        y = dy
                    else:
                        y += dy
            return y

        return LazyLinOp(
            shape=(N, N),
            matmat=lambda x: _matmat(x, False),
            rmatmat=lambda x: _matmat(x, True)
        )


def _nufft(N: int, samples, frequencies, eps: float):
    """
    NUFFT-I and NUFFT-II helper function.
    """

    if samples is not None:
        type = 2
        xp = array_namespace(samples)
    elif frequencies is not None:
        type = 1
        xp = array_namespace(frequencies)
    else:
        raise Exception("_nufft expects type to be either 1 or 2.")

    # Pre-compute u and v vectors.
    # Arbitrarily distributed points?
    # Compute s and t (see Ref.[1] for more details).
    s, err = None, None
    if type == 1:
        s = xp.asarray(
            xp.round(frequencies),
            dtype=xp.int if 'torch' in str(xp.__package__) else 'int',
            device=device(frequencies))
        err = frequencies - s
    elif type == 2:
        s = xp.asarray(
            xp.round(N * samples),
            dtype=xp.int if 'torch' in str(xp.__package__) else 'int',
            device=device(samples))
        err = N * samples - s
    else:
        raise Exception("_nufft expects type to be either 1 or 2.")
    t = s - N * (s // N)
    equispaced = xp.allclose(
        t, xp.arange(N, dtype=t.dtype, device=device(t)), rtol=0.0, atol=1e-3)

    # samples is None.
    # From definition we have:
    # y_k    = sum(x_k * exp(-2 * pi * im * (j / N) * w_k), j)
    # N_{jk} = exp(-2 * pi * im * (j / N) * w_k)
    #        = exp(-2 * pi * im * (j / N) * (w_k - e_k)) * F_{jk}
    # frequencies is None:
    # From definition we have:
    # y_k    = sum(x_k * exp(-2 * pi * im * s_j * k), j)
    # M_{jk} = exp(-2 * pi * im * s_j * k)
    #        = exp(-2 * pi * im * N * s_j * (k / N))
    #        = exp(-2 * pi * im * (k / N) * w_j)
    #        = N_{kj}

    # Chebyshev expansion (see Ref.[1] for more details).
    gamma = xp.linalg.norm(err, xp.inf)
    np_gamma = 5.0 * np.asarray(gamma.tolist())
    # Rank value.
    if gamma > eps:
        tmp = (np_gamma * np.exp(
            lambertw([np.log(140 / eps) / np_gamma], k=0)))[0]
        _rank = max(3, int(np.ceil(np.real([tmp]))[0]))
        err_gamma = err / gamma
    else:
        _rank = 1
        err_gamma = err

    exp_err = xp.exp(-1j * xp.pi * err)
    w = xp.arange(N, device=device(err))
    arg = np.asarray((-0.5 * gamma * xp.pi).tolist())
    _vr = (2.0 / N) * w - 1.0
    ur, vr, T_p = [], [], []
    # Pre-compute Chebyshev polynomial T_p.
    for p in range(_rank):
        if p == 0:
            T_p.append(xp.full(N, 1, dtype=err.dtype,
                               device=device(err)))
        elif p == 1:
            T_p.append(err_gamma)
        else:
            T_p.append(2 * err_gamma * T_p[p - 1] - T_p[p - 2])
    # Loop over rank to compute u_r and v_r.
    for r in range(_rank):
        ur.append(xp.full(N, 0, dtype=(exp_err * T_p[0]).dtype,
                          device=device(err)))
        for p in range(_rank):
            # First term is halved, see Ref.[1] for more details.
            _halved = 0.5 if p == 0 else 1.0
            if abs(p - r) % 2 == 0:
                a_pr = 4.0 * (1j ** r) * (
                    jv([0.5 * (p + r)], arg) * jv([0.5 * (r - p)], arg))[0]
                ur[r] += _halved * a_pr * exp_err * T_p[p]
        if r == 0:
            vr.append(xp.full(N, 1, dtype=err.dtype,
                              device=device(err)))
        elif r == 1:
            vr.append(_vr)
        else:
            vr.append(2 * _vr * vr[r - 1] - vr[r - 2])
    # The first term is halved (see Ref.[1] for more details).
    vr[0] *= 0.5

    # # Taylor expansion (see Ref.[1] for more details).
    # _vr = (-2.0j * xp.pi / N) * xp.arange(N, device=device(err))
    # ur = [xp.full(N, 1, dtype=err.dtype, device=device(err))]
    # vr = [xp.full(N, 1, dtype=_vr.dtype, device=device(_vr))]
    # for r in range(1, _rank):
    #     ur.append(ur[r - 1] * err)
    #     vr.append(vr[r - 1] * _vr / r)

    # Pre-compute LazyLinOp.
    if equispaced:
        F = fft(N)
    else:
        F = indexer(N, t.tolist()) @ fft(N)
    D = {'u': {}, 'v': {}}
    for i in ['u', 'v']:
        D[i] = {'mul': {}, 'rmul': {}}

    def _matmat(x, adjoint: bool = False):

        xp = array_namespace(x)
        # Get dtype and device of x.
        _dtype, _device = (x + 0j).dtype, device(x)
        str_t, str_d = str(_dtype), str(_device)
        # Get pre-computed u_r, v_r or
        # compute it according to x.
        mul = 'rmul' if adjoint else 'mul'
        for i in ['u', 'v']:
            if 'numpy' in str(xp):
                lib = 'numpy'
            elif 'cupy' in str(xp):
                lib = 'cupy'
            elif 'torch' in str(xp):
                lib = 'torch'
            if lib not in D[i][mul].keys():
                D[i][mul][lib] = {}
            if str_t not in D[i][mul][lib].keys():
                D[i][mul][lib][str_t] = {}
        # Cast u and/or v if needed.
        _D = {'u': None, 'v': None}
        for i in ['u', 'v']:
            if str_d not in D[i][mul][lib][str_t].keys():
                D[i][mul][lib][str_t][str_d] = None
            if D[i][mul][lib][str_t][str_d] is None:
                if adjoint:
                    D[i][mul][lib][str_t][str_d] = [
                        xp.asarray(
                            ur[r] if i == 'u' else vr[r],
                            copy=True, dtype=_dtype,
                            device=_device
                        ).conj().reshape(-1, 1)
                        for r in range(_rank)]
                else:
                    D[i][mul][lib][str_t][str_d] = [
                        xp.asarray(
                            ur[r] if i == 'u' else vr[r],
                            copy=True, dtype=_dtype,
                            device=_device
                        ).reshape(-1, 1)
                        for r in range(_rank)]
            _D[i] = D[i][mul][lib][str_t][str_d]

        y = None
        for r in range(_rank):
            if type == 2:
                # NUDFT-I is equivalent to a transposed NUDFT-II.
                if adjoint:
                    dy = _D['u'][r] * (F.T.H @ (_D['v'][r] * x))
                else:
                    dy = _D['v'][r] * (F.T @ (_D['u'][r] * x))
            elif type == 1:
                if adjoint:
                    dy = _D['v'][r] * (F.H @ (_D['u'][r] * x))
                else:
                    dy = _D['u'][r] * (F @ (_D['v'][r] * x))
            if r == 0:
                y = dy
            else:
                y += dy
        return y

    return LazyLinOp(
        shape=(N, N),
        matmat=lambda x: _matmat(x, False),
        rmatmat=lambda x: _matmat(x, True)
    )
