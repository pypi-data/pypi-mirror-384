from lazylinop import LazyLinOp
from multiprocessing import cpu_count
from threading import Thread
import numpy as np


def pmatmat_multithread(L, nworkers=None, use_matvec=False):
    """
    Implements :py:func:`.pmatmat` using Python threads (`threading
    <https://docs.python.org/3/library/threading.html>`_ package)
    for parallelization.

    .. Warning:: Please note that GIL_ can slow down significantly the
        computation depending on how ``L.matmat``/``matvec`` is implemented.
        In case GIL issues cannot be avoided you might use process-based
        methods of :py:func:`.pmatmat`.

    Args:
        L:
            see :py:func:`.pmatmat`
        nworkers:
            see :py:func:`.pmatmat`
        use_matvec:
            see :py:func:`.pmatmat`

    .. _GIL: https://wiki.python.org/moin/GlobalInterpreterLock

    Returns:
        A thread parallelized :py:class:`.LazyLinOp`.

    """
    return PMThreadLazyLinOp(L, nworkers, use_matvec=use_matvec)


class PMThreadLazyLinOp(LazyLinOp):
    """
    TODO
    """

    def __init__(self, L, nworkers=None, use_matvec=False):
        """
        """
        self.L = L
        super().__init__(L.shape,
                         matmat=lambda X:
                         pmatmat_thread(L, X, nworkers,
                                        use_matvec=use_matvec),
                         rmatmat=lambda Y:
                         pmatmat_thread(L.H, Y, nworkers,
                                        use_matvec=use_matvec))


def _share_work(nworkers, njobs):
    """
    Workload balance computing function helper.

    Args:
        nworkers: number of workers.
        njobs: number of jobs to be done by workers.

    Returns: (w_offsets, w_njobs)
        w_joffets: the worker job offsets, w_offsets[j] is the
        starting job of worker j. w_offsets[nworkers] == njobs.
        w_njobs: the worker number of assigned jobs. The worker j
        is in charge of jobs w_offsets[j] to
        w_offsets[j]+w_njobs[j]-1.
    """
    # spread jobs evenly to workers
    w_njobs = np.array([njobs // nworkers for _ in range(nworkers)],
                       dtype='int')
    rem = njobs - w_njobs[0] * nworkers
    # spread remaining jobs to first workers
    w_njobs[:rem] += 1  # rem < nworkers
    # compute job offsets from w_njobs
    w_offsets = list(w_njobs)
    for i in range(1, nworkers):
        w_offsets[i] += w_offsets[i-1]
    w_offsets = [0] + w_offsets
    return (w_offsets, w_njobs)


def pmatmat_thread(L, A, nthreads=None, use_matvec=False):
    if use_matvec:
        def matmat(L, A, out, offset):
            for j in range(A.shape[1]):
                out[:, offset+j] = L @ A[:, j]
    else:
        def matmat(L, A, out, offset):
            out[:, offset:offset+A.shape[1]] = L @ A
    if nthreads is None:
        nthreads = cpu_count()
    nthreads = min(nthreads, cpu_count())
    # We need to determine the dtype of the output.
    # FIXME: implementation is not efficient.
    tmp = L @ A[:, 0]
    out = np.empty((L.shape[0], A.shape[1]), dtype=tmp.dtype)
    w_offsets, w_njobs = _share_work(nthreads, A.shape[1])
    ths = [0 for _ in range(nthreads)]
    for i in range(nthreads):
        start = w_offsets[i]
        end = start + w_njobs[i]
        ths[i] = Thread(target=matmat, args=(L, A[:, start:end], out, start))
        ths[i].start()
    for i in range(nthreads):
        ths[i].join()
    return out
