"""
This module provides parallelized matmat (pmatmat) implementations.
"""
from lazylinop import islazylinop
from lazylinop.wip.parallel import pmatmat_multithread
from lazylinop.wip.parallel import pmatmat_multiprocess
from lazylinop.wip.parallel import pmatmat_mpi


def pmatmat(L, method='thread', nworkers=None, use_matvec=False, **kwargs):
    """
    Builds the parallelized :py:class:`.LazyLinOp` version of ``L``.

    ``L``'s ``matmat``/``__matmul__`` is parallelized according to the selected
    ``method``. To compute ``L @ A`` in parallel, the columns of ``A`` are
    "evenly" assigned to several parallel/concurrent workers. Each worker
    computes its part of the product.

    Note that ``L.H``/``L.T`` multiplication is also parallelized in the same
    way.

    For a better understanding and efficient use please see the `pmatmat
    notebook <./notebooks/using_pmatmat.html>`_.


    Args:
        L: :py:class:`.LazyLinOp`
            The operator to parallelize.
        method: ``str``
            - ``'thread'``: see :py:func:`.pmatmat_multithread`
            - ``'process'``: see :py:func:`.pmatmat_multiprocess`
            - ``'mpi'``: see :py:func:`.pmatmat_mpi`
        nworkers: ``int``
            The number of workers used for parallelization.
            Defaultly, this is the number of CPUs/threads available on the
            system (:func:`os.cpu_count`).
            This parameter is ignored for ``'mpi'`` method (it is fixed
            externally by the ``mpiexec``/``mpirun`` command).
        use_matvec: ``bool``
            If ``True`` the ``matvec`` function of ``L`` is used for
            parallelization otherwise only ``matmat`` is used (default).

            For ``use_matvec=True``, a parallelized ``matmat`` is automatically
            defined using ``L``'s pre-defined ``matvec``.
            Each worker makes a series of sequential calls to ``matvec`` in
            parallel (or concurrently) to other workers. The worker calls
            ``matvec`` on columns it has been assigned.

            .. Warning:: ``use_matvec`` does not go without any consequence on
                the computing performance. In most cases method ``False``
                should be more efficient. This is the default method .

        **kwargs: ``unpacked dict``
            Specialized arguments corresponding to the method used.

    .. Warning:: To avoid CPU oversubscribing, it can be useful to disable
        multithreading of underlying libraries.
        For example, NumPy multithreading is disabled by setting
        ``OMP_NUM_THREADS``, ``MKL_NUM_THREADS`` or ``OPENBLAS_NUM_THREADS``
        environment variables to ``'1'`` (it must be done before importing
        NumPy).
        An alternative to environment variables is to use the `threadpoolctl
        <https://pypi.org/project/threadpoolctl/>`_ or `numthreads
        <https://pypi.org/project/numthreads>`_ libraries.

    .. admonition:: SciPy matrices
        :class: note

        The parallelization of ``matmat`` only supports NumPy array operands.
        A way to handle ``L @ S`` with ``S`` a SciPy matrix, is to:
            - first, convert ``S`` to a :class:`.LazyLinOp` ``SL`` (see
              :func:`.aslazylinop`),
            - second, parallelize the :class:`.LazyLinOp` product ``L @ SL``:
              ``pmatmat(L @ SL)``.

    Returns:
        a :py:class:`.LazyLinOp` that is able to compute the
        product ``L @ A`` in parallel according to the chosen ``method``.

    .. warning::

        The example below is not efficient. The only point is to illustrate
        how to basically use the function. For a better understanding and
        efficient use please see the `pmatmat notebook <./notebooks/using
        _pmatmat.html>`_.

    Example:
        >>> from lazylinop import aslazylinop
        >>> from lazylinop.wip.parallel import pmatmat
        >>> shape = (15, 20)
        >>> import numpy as np
        >>> M = np.random.rand(*shape)
        >>> A = np.random.rand(shape[1], 32)
        >>> L = aslazylinop(M)
        >>> pL = pmatmat(L)
        >>> # pL matmat is parallelized using default thread method
        >>> LA = L @ A # seqential mul
        >>> pLA = pL @ A # parallel mul
        >>> np.allclose(pLA, LA)
        True
        >>> np.allclose(pLA, M @ A)
        True

    """
    if not islazylinop(L):
        raise TypeError('L must be a LazyLinOp')
    method = method.lower()
    if method == 'thread':
        pL = pmatmat_multithread(L, nworkers=nworkers, use_matvec=use_matvec,
                                 **kwargs)
    elif method == 'process':
        pL = pmatmat_multiprocess(L, nworkers=nworkers, use_matvec=use_matvec,
                                  **kwargs)
    elif method == 'mpi':
        # nworkers is set externally with MPI command
        pL = pmatmat_mpi(L, use_matvec=use_matvec, **kwargs)
    else:
        raise ValueError('Unsupported method')
    return pL
