from lazylinop import LazyLinOp
import numpy as np
from warnings import warn
try:
    from mpi4py import MPI
    from mpi4py.util.dtlib import from_numpy_dtype
except Exception:
    warn('mpi4py is not installed, the module mpilop won\'t work')


class MPILop(LazyLinOp):
    """
    Implements a :class:`.LazyLinOp` based on MPI to compute the multiplication
    (``matmat`` and ``rmatmat``).

    This operator basically distributes slices of the underlying matrix to MPI
    processes that compute their part of the multiplication, then the
    multiplication result slices are aggregated by the rank-0 MPI
    process.

    .. note::

        This operator is not to be confound with :py:func:`.pmatmat_mpi`.
        Besides, the function ``pmatmat_mpi`` should not be used to parallelize
        furthermore a :py:class:`.MPILop`.


    **See also**: :py:func:`.pmatmat`.
    """

    def __init__(self, shape, mat_npz, mat_dtype, bcast_op=True):
        """
        MPILop constructor.

        Args:
            shape:
                the shape of the operator (must match mat_npz array,
                it is needed because only 0-rank MPI process will read the
                file).
            mat_npz:
                the file (in npz format) to load the array from.
            mat_dtype:
                the dtype corresponding to mat_npz (it is needed because only
                0-rank MPI process will read the file).
            bcast_op:
                True (default) to broadcast the the multiplication operand of
                the operator to all MPI processes (from the rank-0 process) and
                False to load it locally for each process (typically, if only
                the 0-rank process gets the operand, for example through a
                prompt that a user fills with any info that defines the
                operand, you'll use bcast_op==True.
                Otherwise if all processes have access to the operand, no need
                to broadcast it).

        .. note::

            This operator should be used with OpenMP enabled or it
            won't be efficient to compute the distributed multiplication.
            Mixing multithreading (from NumPy) with multiprocessing is
            often counterproductive.


        Example:
            >>> # disable OpenMP before all things
            >>> from os import environ
            >>> environ['OMP_NUM_THREADS'] = '1'
            >>> from lazylinop.wip import MPILop
            >>> shape = (15, 20)
            >>> import numpy as np
            >>> M = np.random.rand(*shape)
            >>> np.savez('M.npz', M)
            >>> MPILop(shape, 'M.npz', np.dtype('float64'), bcast_op=False)
            <15x20 MPILop with unspecified dtype>

        **See also** bm_np_mul.py_ and bm_mpilop.py_ for valuable examples and
        :ref:`mpilop_bench`.

        .. _bm_np_mul.py: _static/bm_np_mul.py
        .. _bm_mpilop.py: _static/bm_np_mul.py
        """
        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        self.bcast_op = bcast_op
        if rank == 0:
            npz = np.load(mat_npz, allow_pickle=True)
            M = npz[list(npz.keys())[0]]
            if M.shape != shape:
                raise ValueError("shape and M.shape must be"
                                 " equal: "+str(shape)+", "+str(M.shape))
        else:
            M = None
        super(MPILop, self).__init__(shape,
                                     matmat=lambda M:
                                     self.mpi_matmat(M,
                                                     bcast_op=bcast_op,
                                                     ncols=M.shape[1] if M
                                                     is not None and
                                                     M.ndim > 1 else 1,
                                                     axis=0, op_ndim=M.ndim),
                                     rmatmat=lambda M:
                                     self.mpi_matmat(M,
                                                     bcast_op=bcast_op,
                                                     ncols=M.shape[1] if M
                                                     is not None and
                                                     M.ndim > 1 else 1,
                                                     axis=1, op_ndim=M.ndim,
                                                     conj=True))

        self.comm = comm
        self.rank = rank
        self.mpi_size = comm.Get_size()
        self.L = M
        self.Ls = None
        self.LHs = None
        self.slot_inds = [np.empty((self.mpi_size+1), dtype='int')
                          for _ in range(2)]
        self.n_per_slot = [0, 0]
        # slice for this MPI slot for L (idx 0), and L.H (idx 1):
        self.Ls = [None, None]
        # Because LazyLinOp.dtype is always None.
        self._dtype_from_op = mat_dtype

    def _init_distributed_mat(self, axis=0, conj=False):
        (self.Ls[axis], self.n_per_slot[axis],
         self.slot_inds[axis], sendcounts) = \
                scatter_mat(self.comm,
                            self.L,
                            self._dtype_from_op,
                            self.shape,
                            axis=axis,
                            conj=conj)

    def mpi_matmat(self, M, ncols=1, bcast_op=True, axis=0, op_ndim=1,
                   conj=False):
        """
        Multiplies self by a numpy array M.


        Args:
            M: the vector to multiply by.
            ncols: the number of column of M (it is necessary because nonzero
            rank processes ignore the shape of M).
            axis: if axis == 0 self@M is computed, if axis == 1 self.H@M.
            bcast_op: if True then M is broadcasted to all MPI slots, otherwise
            they use their local vector.
            op_ndim: the number of dimensions of M, it might be 1 or 2 (it is
            necessary as for ncols).

        Return:
            The result of self @ M (only on rank-0 process).
        """
        if self.Ls[axis] is None:
            self._init_distributed_mat(axis=axis, conj=conj)

        if self.rank == 0 and self.bcast_op:
            M = np.ascontiguousarray(M)

        comm = self.comm
        rank = self.rank
        size = self.mpi_size
        shape = self.shape

        slot_inds = self.slot_inds[axis]
        Ls = self.Ls[axis]

        if rank > 0 and bcast_op:
            M = np.empty((shape[(axis+1) % 2], ncols), dtype=Ls.dtype)

        if bcast_op:
            comm.Bcast(M, root=0)
        Ls = Ls.reshape(-1, shape[(axis+1) % 2])
        rs = Ls @ M

        if rank == 0:
            r = np.empty((shape[axis], ncols), rs.dtype)
        else:
            r = None
        sendcounts = [int(slot_inds[r+1]-slot_inds[r])*ncols
                      for r in range(size)]
        comm.Gatherv(rs, [r, tuple(sendcounts), slot_inds[:-1]*ncols,
                          from_numpy_dtype(rs.dtype)])

        return r if op_ndim > 1 or r is None else r.ravel()


def scatter_mat(comm, M, Mdtype, Mshape, axis=0, conj=True):
    """
    Scatter array M to from 0-rank MPI node to others.

    Args:
        comm: mpi comm (e.g. COMM_WORLD)
        M: the array matrix to scatter.
        Mdtype: dtype of the matrix ``M``.
        Mshape: shape of the matrix ``M``.
        axis: scatter M (axis 0) or M.T (axis 1).
        conj: if True scatter M.conj() or M.T.conj().
    """
    if M is not None:
        # TODO: handle other dtypes
        if axis == 0:
            M = np.ascontiguousarray(M)
        elif axis == 1:
            M = np.asfortranarray(M)
        else:
            raise ValueError('axis must be 0 or 1')
    # else rank > 0

    shape = Mshape
    rank = comm.Get_rank()
    size = comm.Get_size()

    n_per_slot = shape[axis] // size
    rem = shape[axis] - n_per_slot * size
    slot_inds = np.empty((size+1), dtype='int')
    slot_inds[0] = 0
    for i in range(1, len(slot_inds)):
        slot_inds[i] = slot_inds[i-1] + n_per_slot + (1 if i <= rem else 0)

    orders = ['C', 'F']
    s = shape[(axis+1) % 2]
    sendcounts = [int(slot_inds[r+1]-slot_inds[r]) * s for r in range(size)]
    Ms = np.empty((sendcounts[rank]), dtype=Mdtype)
    comm.Scatterv([M.ravel(order=orders[axis]) if M is not None else None,
                   sendcounts,
                   slot_inds[:size] * s,  # offset in data for each proc
                   from_numpy_dtype(Ms.dtype)],
                  Ms)
    return Ms.conj() if axis == 1 and conj else \
        Ms, n_per_slot, slot_inds, sendcounts
