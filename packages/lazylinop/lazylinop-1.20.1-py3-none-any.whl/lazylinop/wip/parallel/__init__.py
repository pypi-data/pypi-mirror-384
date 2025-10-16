"""
Modules for parallelization of :class:`.LazyLinOp`-s.
"""
from .pmatmat_thread import pmatmat_multithread
from .pmatmat_process import pmatmat_multiprocess
from .pmatmat_mpi import pmatmat_mpi
from .pmatmat import pmatmat
from .mpilop import MPILop
