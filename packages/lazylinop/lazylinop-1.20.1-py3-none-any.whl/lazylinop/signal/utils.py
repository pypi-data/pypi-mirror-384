import numpy as np
from lazylinop import slicer


def chunk(N, size, hop=1, start=0, stop=None):
    """Returns a :class:`.LazyLinOp` that extracts chunks from
    a signal of size N.

    This operator returns the concatenation of regularly spaced chunks
    of ``size`` elements from the provided signal. The spacing between
    consecutive chunks is of ``hop`` elements of the original signal.
    If ``start`` and/or ``stop`` is provided, the first chunk starts at the ``start``
    element of the signal (and subsequents chunks are also shifted)
    and stops at the ``stop`` element.

    Args:
        size: ``int``
            Size of each chunk.
        hop: ``int``, optional
            Number of elements in the original signal between two chunks.
            Default is 1.
        start: ``int``, optional
            Index of the element in the original signal where chunking starts.
            Default is 0.
        stop: ``int``, optional
            Index of the element (excluded) in the original signal where chunking stops.
            Default is None, meaning that chunkins stops at the end of the signal.

    Returns:
        The chunk :class:`.LazyLinOp` of shape $(M,N)$, where
        $M=size \times Nchunks$ with $Nchunks$ the number of chunks.

    .. _chunk_format
    Chunk description
    ------------------
        .. image:: _static/chunk.svg
            :width: 400px
            :height: 400px

    Examples:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> N = 10
        >>> x = np.arange(N)
        >>> x
        array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        >>> # extract chunks of 5 elements every 2 element
        >>> lz.signal.chunk(N, 5, 2) @ x
        array([0, 1, 2, 3, 4, 2, 3, 4, 5, 6, 4, 5, 6, 7, 8])
    """

    if size <= 0 or size > N:
        raise ValueError("size must be strictly positive and lower than N.")
    if hop <= 0:
        raise ValueError("hop must be strictly positive.")

    if not isinstance(start, int):
        raise ValueError("start must be an integer")
    if stop is not None and not isinstance(stop, int):
        raise ValueError("stop must be an integer")

    # FIXME: also support negative values for start/stop?
    if start < 0 or start > N-1:
        raise ValueError("start must be positive and lower than N-1")
    if stop is not None and (stop <= start or stop > N):
        raise ValueError("stop must be higher than start and lower than N")

    return slicer(N,
                  np.arange(start, (stop or N + 1) - size, hop),
                  np.arange(start+size, stop or N + 1, hop)
                  )


def downsample(N, step, start=0, stop=None):
    """Returns a :class:`.LazyLinOp` that downsamples
    a signal x of size N.

    This operator performs decimation on provided signal,
    where the result contains elements selected every ``step``
    elements in the original signal, starting at ``start`` up to
    ``stop``, if provided.

    When ``L = downsample(N, step, start, stop)``, computing ``y = L @ x``
    is equivalent to ``y = x[start:stop:step]``.

    Args:
        N: ``int``
            Length of the input vector.
        step: ``int``
            The stride to use for selecting elements in the original signal.
        start: ``int``, optional
            Index of the element in the original signal where decimation starts.
            Default is 0.
        stop: ``int``, optional
            Index of the element (excluded) in the original signal where decimation stops.
            Default is None, meaning that chunkins stops at the end of the signal.

    Returns:
        The downsample :class:`.LazyLinOp`.

    Examples:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> N = 10
        >>> x = np.arange(N)
        >>> x
        array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        >>> # Downsample every 2 element, starting at the third
        >>> lz.signal.downsample(N, 2, 3) @ x
        array([3, 5, 7, 9])
    """
    return decimate(N, step, start, stop)


def decimate(N, step, start=0, stop=None):
    """Returns a :class:`.LazyLinOp` that decimates/subsamples
    a signal x of size N.

    This operator performs decimation on provided signal,
    where the result contains elements selected every ``step``
    elements in the original signal, starting at ``start`` up to
    ``stop``, if provided.

    When ``L = decimate(N, step, start, stop)``, computing ``y = L@x``
    is equivalent to ``y = x[start:stop:step]``.

    Args:
        N: ``int``
            Length of the input vector.
        step: ``int``
            The stride to use for selecting elements in the original signal.
        start: ``int``, optional
            Index of the element in the original signal where decimation starts.
            Default is 0.
        stop: ``int``, optional
            Index of the element (excluded) in the original signal where decimation stops.
            Default is None, meaning that chunkins stops at the end of the signal.

    Returns:
        The decimate :class:`.LazyLinOp`.

    Examples:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> N = 10
        >>> x = np.arange(N)
        >>> x
        array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        >>> # decimate every 2 element, starting at the third
        >>> lz.signal.decimate(N, 2, 3) @ x
        array([3, 5, 7, 9])
    """
    if step <= 0 or step > N:
        raise ValueError("step must be strictly positive and lower than N.")

    if not isinstance(start, int):
        raise ValueError("start must be an integer")
    if stop is not None and not isinstance(stop, int):
        raise ValueError("stop must be an integer")

    if start < 0 or start > N-1:
        raise ValueError("start must be positive and lower than N-1")
    if stop is not None and (stop <= start or stop > N):
        raise ValueError("stop must be higher than start and lower than N")

    return slicer(N, start=start, stop=stop, step=step)


def overlap_add(N: int, size: int, overlap: int = 1):
    """
    Returns a :class:`.LazyLinOp` ``L`` for overlap-add linear operator.

    Such an operator L applies to an input signal x with ``N`` elements,
    where ``N`` must be a multiple of ``size``, and is considered as the
    concatenation of $N/size$ chunks of ``size`` elements.

    The output ``y = L@x`` results from the addition of these chunks with overlap:
    The first ``overlap`` elements of a block $i+1$ with last ``overlap``
    elements of block $i$. Blocks size is given by ``size``.

    Shape of L is $(M, N)$ with $M = N - overlap \times ( N/size - 1)$

    Args:
        N: ``int``
            Size of the input.
        size: ``int``
            Block size. Must divide N.
        overlap: ``int``
            Size of the overlap between blocks. Must be strictly positive,
            and smaller than the block size ``size``.

    Returns:
        :class:`.LazyLinOp`

    .. _overlap_add_format
    Overlap-add description
    -----------------------
        .. image:: _static/overlap_add.svg
            :width: 400px
            :height: 400px

    Examples:
        >>> from lazylinop.signal import overlap_add
        >>> import numpy as np
        >>> x = np.full(5, 1.0)
        >>> # Do nothing because input size is equal to window
        >>> L = overlap_add(5, 5, overlap=1)
        >>> np.allclose(L @ x, x)
        True
        >>> x = np.full(6, 1.0)
        >>> L = overlap_add(6, 2, overlap=1)
        >>> L @ x
        array([1., 2., 2., 1.])
    """

    if size <= 0:
        raise ValueError("size must be strictly positive.")
    if (N % size) != 0:
        raise Exception("size must divide N.")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be positive and lower than size.")

    return chunk(N - (N // size - 1) * overlap, size, size-overlap).T
