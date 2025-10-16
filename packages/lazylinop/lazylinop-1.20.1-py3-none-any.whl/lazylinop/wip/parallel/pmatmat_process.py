from lazylinop import LazyLinOp
from multiprocessing import cpu_count, Process, Queue
from .pmatmat_thread import _share_work
import numpy as np
import warnings


def pmatmat_multiprocess(L, nworkers=None, use_matvec=False,
                         procs_created_once=False):
    """
    Implements :py:func:`.pmatmat` using Python `multiprocessing
    <https://docs.python.org/3/library/multiprocessing.html>`_.

    Args:
        L:
            see :py:func:`.pmatmat`
        nworkers:
            see :py:func:`.pmatmat`
        use_matvec:
            see :py:func:`.pmatmat`
        procs_created_once: (bool)
            If ``True``, processes are created beforehand and then
            consume/compute multiplications on the fly.
            Otherwise (``False``) processes are created each time a
            multiplication is calculated.  ``procs_created_once=True``
            hardly outperforms ``False`` case because it needs to make
            IPC (Inter-Process Communication) to send slices of ``A``
            (if we compute ``L @ A``) to processes created
            beforehand. In case of ``procs_created_once=False`` ``A`` is
            auto-shared by process forking (without any copy) but the resulting
            slices of multiplication still imply a need for IPC.
    """
    if procs_created_once:
        return PMCreatedOnceProcessLazyLinOp(L, nworkers,
                                             use_matvec=use_matvec)
    else:
        return PMProcessLazyLinOp(L, nworkers, use_matvec=use_matvec)


class PMProcessLazyLinOp(LazyLinOp):
    """
    TODO
    """

    def __init__(self, L, nworkers=None, use_matvec=False):
        """
            It can parallelize proceeding alternatively as follows:
                1. Parallelize a pre-defined matmat per blocks of columns.
                2. Define a parallelized matmat using a pre-defined matvec.

            .. Warning:: Using the method 1 or 2 does not go without
            consequence on the computing performance. In most cases
            method 1 should be more efficient.

            Python Process-es (multiprocessing package) are used for
            parallelization.

        """
        self.L = L
        super().__init__(L.shape,
                         matmat=lambda X:
                         pmatmat_process(L, X, nworkers,
                                         use_matvec=use_matvec),
                         rmatmat=lambda Y:
                         pmatmat_process(L.H, Y, nworkers,
                                         use_matvec=use_matvec))

    def terminate(self):
        # just for compatibility with PMCreatedOnceProcessLazyLinOp
        # (TODO: it should be made by class inheritance).
        pass


def matmat_matvec(L, A, q, offset):
    if len(A.shape) == 1 or (len(A.shape) == 2 and A.shape[1] <= 1):
        out = L @ A
    else:
        # Determine the dtype of the output.
        print(L.shape, A.shape)
        tmp = L @ A[:, 0]
        out = np.empty((L.shape[0], A.shape[1]), dtype=tmp.dtype)
        np.copyto(out[:, 0], tmp)
        for j in range(1, A.shape[1]):
            out[:, j] = L @ A[:, j]
    if q is None:
        return out
    else:
        q.put([out, offset])


def matmat_block(L, A, q, offset):
    out = L @ A
    if q is None:
        return out
    else:
        q.put([out, offset])


def select_matmat_func(use_matvec=False):
    if use_matvec:
        return matmat_matvec
    else:
        return matmat_block


def pmatmat_process(L, A, nprocs=None, use_matvec=False):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        matmat = select_matmat_func(use_matvec=use_matvec)
        if nprocs is None:
            nprocs = cpu_count()
        nprocs = min(nprocs, cpu_count())
        # Determine the dtype of the output.
        # FIXME: implementation is not efficient.
        tmp = L @ A[:, 0]
        out = np.empty((L.shape[0], A.shape[1]), dtype=tmp.dtype)
        w_offsets, w_njobs = _share_work(nprocs, A.shape[1])
        procs = [0 for _ in range(nprocs)]
        q = Queue()
        # create nprocs-1 additional
        # the current one will work too but directly here
        for i in range(nprocs-1):
            start = w_offsets[i]
            end = start + w_njobs[i]
            procs[i] = Process(target=matmat,
                               args=(L, A[:, start:end], q, start))
            procs[i].start()
        start = w_offsets[nprocs-1]
        end = start + w_njobs[nprocs-1]
        out[:, start:end] = matmat(L, A[:, start:end], None, start)
        for i in range(nprocs-1):
            LA_slice = q.get()
            offset = LA_slice[1]
            slice_len = LA_slice[0].shape[1]
            out[:, offset:offset+slice_len] = LA_slice[0]
        q.close()
        return out


class PMCreatedOnceProcessLazyLinOp(LazyLinOp):
    """
    Same as PMProcessLazyLinOp but processes created once and for all
    (waiting for new multiplications to compute).
    It follows then model Producer-consumer on each matmat request.
    """

    def __init__(self, L, nworkers=None, use_matvec=False):
        self.L = L
        if nworkers is None:
            nworkers = cpu_count()
        nworkers = min(nworkers, cpu_count())
        procs = [0 for _ in range(nworkers)]
        procs_H = [0 for _ in range(nworkers)]
        q_in = Queue()
        q_out = Queue()
        self.procs = procs
        self.procs_H = procs_H
        self.q_in = q_in
        self.q_out = q_out
        q_in_H = Queue()
        q_out_H = Queue()
        self.procs = procs
        self.q_in_H = q_in_H
        self.q_out_H = q_out_H
        for i in range(nworkers):
            procs[i] = Process(target=process_consume, args=(L, q_in, q_out,
                                                             use_matvec))
            procs[i].start()

            procs_H[i] = Process(target=process_consume, args=(L.H, q_in_H,
                                                               q_out_H,
                                                               use_matvec))
            procs_H[i].start()
        super().__init__(L.shape,
                         matmat=lambda X:
                         process_produce(L, X, procs, q_in, q_out),
                         rmatmat=lambda Y:
                         process_produce(L.H, Y, procs_H, q_in_H, q_out_H))

    def __del__(self):
        self.terminate()

    def terminate(self):
        for p in self.procs:
            p.terminate()
        for p in self.procs_H:
            p.terminate()


def process_produce(L, A, procs, q_in, q_out):
    nprocs = len(procs)
    # Determine the dtype of the output.
    # FIXME: implementation is not efficient.
    tmp = L @ A[:, 0]
    out = np.empty((L.shape[0], A.shape[1]), dtype=tmp.dtype)
    w_offsets, w_njobs = _share_work(nprocs, A.shape[1])
    for i in range(nprocs):
        start = w_offsets[i]
        end = start + w_njobs[i]
        q_in.put([A[:, start:end], start])
    for i in range(nprocs):
        LA_slice = q_out.get()
        offset = LA_slice[1]
        slice_len = LA_slice[0].shape[1]
        out[:, offset:offset+slice_len] = LA_slice[0]
    return out


def process_consume(L, q_in, q_out, use_matvec):
    # coverage note: cannot be accounted because it
    # runs in another process
    # I tried option --concurrency=multiprocessing but it
    # didn't work (even with conf. file and updated version: 7.5.1)
    # see https://coverage.readthedocs.io/en/7.5.1/config.html#run-concurrency
    matmat = select_matmat_func(use_matvec=use_matvec)
    while mm_info := q_in.get():
        A, offset = mm_info
        matmat(L, A, q_out, offset)
