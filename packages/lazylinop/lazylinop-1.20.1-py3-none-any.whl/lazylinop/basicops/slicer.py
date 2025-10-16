import numpy as np
from lazylinop import LazyLinOp
import sys
import array_api_compat
from array_api_compat import is_torch_array

sys.setrecursionlimit(100000)

def indexer(N: int, index):
    """Returns a :class:`.LazyLinOp' ``L`` that extracts elements
    from a vector of size N, such that with ``I`` an array of integers
    or booleans:

    ``indexer(N, I) @ x == x[I]``

    Args:
        N: ``int``
            Length of the input.
        index: An ``array``-compatible of integers or booleans.
            If ``index`` is an array of integers, it reprensents the
            indices of the element of the input vector to select.

            If ``index`` in an array of booleans, ``indexer()`` will
            returns the input vector elements whose indices are ``True``
            in ``index``. In that case ``index`` size must be N or 1.

    Returns:
        The indexer :class:`.LazyLinOp`.

    Examples:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> N = 10
        >>> x = np.arange(N)
        >>> x
        array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        >>> # use integers to extract elements
        >>> lz.indexer(N, [2, 1, 1]) @ x
        array([2, 1, 1])
        >>> # use booleans to extract elements
        >>> lz.indexer(N, x > 6) @ x
        array([7, 8, 9])
    """
    index = np.asarray(index)

    if index.dtype == "int":
        if index.ndim != 1:
            raise ValueError("index parameter must be a 1D-array when used with integers")
        if index.size > 0 and np.max(index) > N-1:
            raise ValueError("index parameter indices may not be greater than input dimension")
    elif index.dtype == "bool":
        if index.size == 1:
            index = np.full(N, index)
        if index.ndim > 1:
            raise ValueError("index parameter must be a 0D- or 1D-array when used with booleans")
        if index.size != N:
            raise ValueError("index parameter must have 1 or N elements when used with booleans")
        index = np.flatnonzero(index)
    else:
        raise ValueError("index parameter must be an array of integers or booleans")

    # returns an empty vector as with numpy
    if index.size == 0:
        return slicer(N, 1, 0)

    return slicer(N, index, np.asarray(index)+1, None) #FIXME: probably inefficient


def slicer(N: int, start=None, stop=None, step=None):
    """Returns a :class:`.LazyLinOp' ``L`` that extracts slices
    from a vector of size N, such that with:

    ``y = slicer(N, start, stop, step) @ x``

    y is the vector formed by concatenation of several x slices given by
    each element of start/stop/step parameters, i.e:

    ``y = [ x[start[0]:stop[0]:step[0]] … x[start[i]:stop[i]:step[i]] … ]``

    where ``start[i], stop[i], step[i]`` are interpreted in the same way
    as in usual Python ``slice`` parameters
    (i.e. they can be a positive or negative integer or None).

    If start, stop and step are integers (or None), a single slicing is performed, i.e:

    ``slicer(N, 0, 10, 2) @ x == x[0:10:2]``

    A mix of arrays and integers (or None) may be provided for start/stop/step parameters.
    In that case, each integer parameter is expanded into an array filled with
    its value of the same length as the arrays provided in other parameters.
    (Note: all provided arrays must have the same length)

    .. FIXME: ensure this function is called when L[x:y:z] is applied

    Args:
        N: ``int``
            Length of the input.
        start: ``int`` or ``np.ndarray``
            The slice's first element or slices' list of first elements.
            Each ``start`` element is interpreted in the same way as Python
            ``slice()``'s ``start`` parameter.
            Default is None.
        stop: ``int`` or ``np.ndarray``
            The slice's stop index or slices' list of stop index.
            Each ``stop`` element is interpreted in the same way as Python
            ``slice()``'s ``stop`` parameter.
            Default is None.
        step: ``int`` or ``np.ndarray``
            The slice's stride or slices's list of strides to be used.
            Each ``stop`` element is interpreted in the same way as Python
            ``slice()``'s ``step`` parameter.
            Default is None.

    Returns:
        The slices :class:`.LazyLinOp`.

    Examples:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> N = 10
        >>> x = np.arange(N)
        >>> x
        array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        >>> # use integers to extract a single slice
        >>> lz.basicops.slicer(N, 5, 8) @ x
        array([5, 6, 7])
        >>> # use list to extract multiple slices
        >>> lz.basicops.slicer(N, [0, 5], [2, 8]) @ x
        array([0, 1, 5, 6, 7])
        >>> # pick one every two elements
        >>> lz.basicops.slicer(N, step=2) @ x
        array([0, 2, 4, 6, 8])
        >>> # same example using a batch, in reverse order
        >>> X = np.arange(3*N).reshape((N, 3))
        >>> X
        array([[ 0,  1,  2],
               [ 3,  4,  5],
               [ 6,  7,  8],
               [ 9, 10, 11],
               [12, 13, 14],
               [15, 16, 17],
               [18, 19, 20],
               [21, 22, 23],
               [24, 25, 26],
               [27, 28, 29]])
        >>> lz.basicops.slicer(N, step=-2) @ X
        array([[27, 28, 29],
               [21, 22, 23],
               [15, 16, 17],
               [ 9, 10, 11],
               [ 3,  4,  5]])
        >>> # windows of 5 elements every 2 elements across the vector
        >>> lz.basicops.slicer(N, np.arange(0, 5, 2), np.arange(5, N, 2)) @ x
        array([0, 1, 2, 3, 4, 2, 3, 4, 5, 6, 4, 5, 6, 7, 8])
    """

    start = np.asarray(start)
    stop = np.asarray(stop)
    step = np.asarray(step)

    # We treat empty array as if parameter was None
    if start.size == 0:
        start = np.asarray(None)
    if stop.size == 0:
        stop = np.asarray(None)
    if step.size == 0:
        step = np.asarray(None)

    args = [start, stop, step]

    try:
        assert (s.dtype == "int" or np.all(s is None or isinstance(s, int)) for s in args)
        assert all(s.ndim == 0 or s.ndim == 1 for s in args)
    except AssertionError:
        raise ValueError("start/stop/step parameters must be None, an integer or a 1D-array of integers")

    try:
        assert not np.any(step == 0)
    except AssertionError:
        raise ValueError("step cannot be 0")
    try:
        max_size = max(s.size for s in args)
        if max_size > 1:
            assert all(s.size == max_size or s.size == 1 for s in args)
    except AssertionError:
        raise ValueError("start/stop/step must have the same length or be scalar")

    if start.size == 1:
        start = np.full(max_size, start)
    if stop.size == 1:
        stop = np.full(max_size, stop)
    if step.size == 1:
        step = np.full(max_size, step)

    slices_size = np.empty(max_size, dtype="int")

    for i in range(max_size):
        _start, _stop, _step = slice(start[i], stop[i], step[i]).indices(N)
        slices_size[i] = max(0, (_stop - _start + (_step - (1 if _step > 0 else -1))) // _step)

    total_size = np.sum(slices_size)

    def _matvec(x):
        xp = array_api_compat.array_namespace(x)
        y = xp.empty(total_size, dtype=x.dtype, device=x.device)

        offset = 0
        for i in range(max_size):
            if is_torch_array(x):
                # FIXME: torch does not allow negative step.
                if step[i] is not None and step[i] < 0:
                    y[offset : offset + slices_size[i]] = x[
                        (np.arange(x.shape[0])[start[i] : stop[i] : step[i]]).copy()]
                else:
                    y[offset : offset + slices_size[i]] = x[start[i] : stop[i] : step[i]]
            else:
                y[offset : offset + slices_size[i]] = x[start[i] : stop[i] : step[i]]
            # torch does not allow negative step.
            # array-api-compat does not allow None step.
            # tmp_start = 0 if start[i] is None else start[i]
            # tmp_stop = x.shape[0] if stop[i] is None else stop[i]
            # tmp_step = 1 if step[i] is None else step[i]
            # if tmp_step < 0 and tmp_start != tmp_stop:
            #     tmp_start, tmp_stop = tmp_stop - 1, tmp_start - 1
            # print(tmp_start, tmp_stop, tmp_step)
            # print(xp.arange(tmp_start, stop=tmp_stop, step=tmp_step))
            # y[offset : offset + slices_size[i]] = x[
            #     xp.arange(tmp_start, stop=tmp_stop, step=tmp_step)]
            offset += slices_size[i]

        return y

    def _rmatvec(x):
        xp = array_api_compat.array_namespace(x)
        y = xp.zeros(N, dtype=x.dtype, device=x.device)

        offset = 0
        for i in range(max_size):
            if is_torch_array(x):
                # FIXME: torch does not allow negative step.
                if step[i] is not None and step[i] < 0:
                    y[(np.arange(
                        y.shape[0])[start[i] : stop[i] : step[i]]).copy()
                      ] += x[offset : offset + slices_size[i]]
                else:
                    y[start[i] : stop[i] : step[i]] += x[offset : offset + slices_size[i]]
            else:
                y[start[i] : stop[i] : step[i]] += x[offset : offset + slices_size[i]]
            offset += slices_size[i]

        return y

    return LazyLinOp(
        shape=(total_size, N),
        matvec=lambda x: _matvec(x),
        rmatvec=lambda x: _rmatvec(x),
    )
