# -*- coding: utf-8 -*-

from lazylinop import LazyLinOp
from gc import collect


try:
    import pyopencl as cl
except (ImportError, ModuleNotFoundError):
    cl = None
try:
    import pycuda.driver as cuda
    import pycuda._driver as _cuda
    from pycuda.tools import clear_context_caches
except:  # ImportError:
    cuda = None
    _cuda = None


def clean(L: LazyLinOp):
    """
    Release (OpenCL) or free (CUDA) device
    pointers :class:`.LazyLinOp` ``L`` returned
    by either ``ksm(...)`` or ``ksd(...)``.
    Once you compute ``y = L @ x`` and you do not
    need ``L`` anymore, use ``clean(L)`` to clean memory
    and to delete ``L``.

    Args:
        L: ``LazyLinOp``
            Clean device pointers from ``L`` and delete it.
    """
    if hasattr(L, 'device_pointers'):
        # Backend 'numpy' and 'scipy' do not need device pointers.
        for i in range(len(L.device_pointers)):
            if _cuda is not None and \
               isinstance(L.device_pointers[i], _cuda.DeviceAllocation):
                L.device_pointers[i].free()
                # https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html#stream-ordered-memory-allocator-intro
                # L.context.synchronize()
            elif cl is not None and \
                 isinstance(L.device_pointers[i], cl.Buffer):
                L.device_pointers[i].release()
            else:
                pass
        del L.device_pointers
    del L


def del_all_contexts():
    """
    Delete all contexts.
    """
    from lazylinop.butterfly.ksm import contexts
    n_contexts = len(contexts)
    for i in range(n_contexts):
        if cuda is not None and \
           isinstance(contexts[n_contexts - 1 - i], cuda.Context):
            contexts[n_contexts - 1 - i].push()
            contexts[n_contexts - 1 - i].synchronize()
            contexts[n_contexts - 1 - i].pop()
            contexts[n_contexts - 1 - i].detach()
            del contexts[n_contexts - 1 - i]
    if cuda is not None:
        clear_context_caches()
    collect()
    contexts = []
