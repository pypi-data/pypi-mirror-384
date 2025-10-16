from lazylinop import LazyLinOp
import numpy as np
from warnings import warn
from .pmatmat_thread import _share_work

try:
    from mpi4py import MPI
except Exception:
    warn('mpi4py is not installed, pmatmat_mpi won\'t work')
from lazylinop.wip.parallel.mpilop import scatter_mat

# coverage note: as far as I know MPI code cannot be
# monitored by coverage, so the coverage is wrongly low


def pmatmat_mpi(L, use_matvec=False, scatter_A=False):
    """
    Implements :py:func:`.pmatmat` using MPI (`mpi4py
    <https://mpi4py.readthedocs.io/en/stable/mpi4py.html>`_)

    Args:
        L:
            see :py:func:`.pmatmat`
        nworkers:
            see :py:func:`.pmatmat`
        use_matvec:
            see :py:func:`.pmatmat`
        scatter_A: (bool)
            If ``True``, the array ``A`` is scattered to MPI slots/cores by
            slices from 0-rank MPI slot which should be the only one to know
            the full ``A``. This represents an extra cost, that's why the
            option is ``False`` by default.

    """
    return PMMPILazyLinOp(L, use_matvec=use_matvec, scatter_X=scatter_A)


class PMMPILazyLinOp(LazyLinOp):

    def __init__(self, L, nworkers=None, use_matvec=False, scatter_X=False):
        """
            It can parallelize proceeding alternatively as follows:
                1. Parallelize a pre-defined matmat per blocks of columns.
                2. Define a parallelized matmat using a pre-defined matvec.

            .. Warning:: Using the method 1 or 2 does not go without
            consequence on the computing performance. In most cases
            method 1 should be more efficient.

            MPI (mpi4py) is used for parallelization.

        """
        self.L = L
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        super().__init__(L.shape,
                         matmat=lambda X:
                         self._pmatmat_mpi(L, X,
                                           use_matvec=use_matvec,
                                           scatter_X=scatter_X),
                         rmatmat=lambda Y:
                         self._pmatmat_mpi(L.H, Y,
                                           use_matvec=use_matvec,
                                           scatter_X=scatter_X))

    def _pmatmat_mpi(self, L, X, use_matvec=False, scatter_X=False):
        comm = self.comm
        rank = comm.Get_rank()
        # size = comm.Get_size()
        if scatter_X:
            Xcols, gncols, slot_inds, sendcounts = scatter_mat(comm, X,
                                                               X.dtype,
                                                               X.shape,
                                                               axis=1)
            ncols = sendcounts[rank] // X.shape[0]
            Xcols = Xcols.reshape(-1, ncols, order='F')
        else:
            # X is available locally to all slots
            w_offsets, w_njobs = _share_work(comm.Get_size(), X.shape[1])
            Xcols = X[:, w_offsets[rank]:w_offsets[rank+1]]
            ncols = Xcols.shape[1]
        if use_matvec:
            # Determine the dtype of the output.
            # FIXME: implementation is not efficient.
            tmp = L @ Xcols[0]
            out = np.empty((L.shape[0], Xcols.shape[1]),
                           dtype=tmp.dtype, order='F')
            # could be parallelized using threads but
            # it is pretty the same to increase the number of MPI slots,
            # isn't it?
            for j in range(Xcols.shape[1]):
                out[:, j] = L @ Xcols[j]
        else:
            out = np.asfortranarray(L @ Xcols)

        if rank == 0:
            res = np.empty((L.shape[0], X.shape[1]), dtype='float64',
                           order='F')
        else:
            res = None

        # TODO: gathering should be factored out as done for scatter_mat
        # TODO: dtype should be anything not just MPI double
#        sendcounts = [out.shape[0] * ncols for i in range(size)]
        sendcounts = comm.gather(np.prod(out.shape), 0)
        if rank == 0:
            assert res.size == np.sum(sendcounts)
        comm.Gatherv(out, [res, sendcounts] if rank == 0 else
                     None)
        if res is not None:
            return res if X.ndim > 1 or res is None else res.ravel()
        return None  # not 0-rank slot
