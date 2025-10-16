import numbers
import numpy as np
from functools import partial
from collections.abc import Iterable
import array_api_compat
from array_api_compat import is_torch_array, is_numpy_array
from lazylinop.utils import is_array, array_xnamespace


def islazylinop(op):
    return isinstance(op, LazyLinOp)


def aslazylinop(op):
    if islazylinop(op):
        return op
    elif is_array(op):
        return ArrayBasedLazyLinOp(op)
    elif hasattr(op, "shape") and hasattr(op, "matvec"):
        args = {}
        if hasattr(op, "matmat"):
            args.update({"matmat": op.matmat})
        else:
            args.update({"matvec": op.matvec})
        if hasattr(op, "rmatmat"):
            args.update({"rmatmat": op.rmatmat})
        elif hasattr(op, "rmatvec"):
            args.update({"rmatvec": op.rmatvec})
        elif hasattr(op, "H"):
            args.update({"rmatmat": lambda x: op.H @ x})
        return LazyLinOp(op.shape, **args)
    else:
        raise TypeError(
            f"'{op}' object of type '{type(op)}' cannot be converted to LazyLinOp"
        )


class _MetaLazy(type):
    def __call__(cls, *args, **kwargs):
        L = super().__call__(*args, **kwargs)
        L._post_init()
        return L


class LazyLinOp(metaclass=_MetaLazy):
    """
    The ``LazyLinOp`` class.

    .. admonition:: The lazy principle
        :class: admonition note

        The evaluation of any defined operation on a ``LazyLinOp`` is
        delayed until a multiplication by a matrix/vector or a call of
        :py:func:`LazyLinOp.toarray` is made.


    .. admonition:: Two ways to instantiate
        :class: admonition note

        - Using :py:func:`lazylinop.aslazylinop` or
        - Using this constructor (:py:func:`lazylinop.LazyLinOp`) to define
          ``matmat``, ``matvec`` functions.

    .. admonition:: Available operations
        :class: admonition note

        ``+`` (addition), ``-`` (subtraction),
        ``@`` (matrix product), ``*`` (scalar multiplication),
        ``**`` (matrix power for square operators),
        indexing, slicing and others.
        For a nicer introduction you might look at `these tutorials
        <https://faustgrp.gitlabpages.inria.fr/lazylinop/tutorials.html>`_.

    .. admonition:: Recursion limit
        :class: admonition warning

        Repeated "inplace" modifications of a :py:class:`LazyLinOp`
        through any operation like a concatenation
        (``op = vstack((op, anything))``)
        are subject to a :py:class:`RecursionError` if the number of recursive
        calls exceeds :py:func:`sys.getrecursionlimit`. You might change this
        limit if needed using :py:func:`sys.setrecursionlimit`.
    """

    def __init__(
        self,
        shape,
        matvec=None,
        matmat=None,
        rmatvec=None,
        rmatmat=None,
        *args,
        **kwargs,
    ):
        """
        A ``LazyLinOp`` instance is defined by a shape and at least
        functions ``matvec`` or ``matmat`` and ``rmatvec`` or ``rmatmat``.

        Parameters
        ----------
            shape: (``tuple[int, int]``)
                 Operator $L$ dimensions $(M, N)$.
            matvec: (callable)
                 Returns $y = L * v$ with $v$ a vector of size $N$.
                 $y$ size is $M$ with the same number of dimension(s) as $v$.
            rmatvec: (callable)
                 Returns $y = L^H * v$ with $v$ a vector of size $M$.
                 $y$ size is $N$ with the same number of dimension(s) as $v$.
            matmat: (callable)
                 Returns $L * V$.
                 The output matrix shape is $(M, K)$.
            rmatmat: (``callable``)
                 Returns $L^H * V$.
                 The output matrix shape is $(N, K)$.

        .. admonition:: Auto-implemented operations
            :class: admonition note

            - If only ``matvec`` is defined and not ``matmat``, an
              automatic naive ``matmat`` will be defined upon the given
              ``matvec`` but note that it might be suboptimal (in which
              case a ``matmat`` is useful).
              The same applies for ``rmatvec`` and ``rmatmat``.
            - No need to provide the implementation of the multiplication by a
              :class:`LazyLinOp`, or a numpy array with ``ndim > 2`` because
              both of them are auto-implemented. For the latter operation,
              it is computed as in `numpy.__matmul__ <https://numpy.org/
              doc/stable/reference/generated/numpy.matmul.html>`_.


        Return:
            ``LazyLinOp``

        Example:
            >>> # In this example we create a LazyLinOp
            >>> # for the DFT using the fft from scipy
            >>> import numpy as np
            >>> from scipy.fft import fft, ifft
            >>> from lazylinop import LazyLinOp
            >>> fft_mm = lambda x: fft(x, norm='ortho')
            >>> fft_rmm = lambda x: ifft(x, norm='ortho')
            >>> n = 16
            >>> F = LazyLinOp((n, n), matvec=fft_mm, rmatvec=fft_rmm)
            >>> x = np.random.rand(n)
            >>> y = F @ x
            >>> np.allclose(y, fft(x, norm='ortho'))
            True
            >>> np.allclose(x, F.H @ y)
            True

        .. seealso::
            `SciPy linear Operator
            <https://docs.scipy.org/doc/scipy/reference/generated/
            scipy.sparse.linalg.LinearOperator.html>`_.
            :py:func:`LazyLinOp.check`
            `scipy fft
            <https://docs.scipy.org/doc/scipy/reference/generated/
            scipy.fft.fft.html>`_
        """
        try:
            self._shape = tuple(np.asarray(shape).tolist())
        except TypeError:
            raise TypeError("LazyLinOp shape must be a tuple of two integers")

        self.matvec, self.rmatvec, self.matmat, self.rmatmat = (
            matvec,
            rmatvec,
            matmat,
            rmatmat,
        )

    def _post_init(self):
        # Check shape validity
        try:
            assert (
                isinstance(self.shape, tuple)
                and len(self.shape) == 2
                and isinstance(self.shape[0], int)
                and isinstance(self.shape[1], int)
            )
        except AssertionError:
            raise TypeError("LazyLinOp shape must be a tuple of two integers")

        # Check if an implementation of matvec or matmat is provided
        if not (callable(self.matvec) or callable(self.matmat)):
            raise TypeError(
                "At least a matvec or a matmat callable function must be passed to the constructor."
            )

        # Check if an implementation of rmatvec or rmatmat is provided
        if not hasattr(self, "rmatvec"):
            self.rmatvec = None
        if not hasattr(self, "rmatmat"):
            self.rmatmat = None
        if not (callable(self.rmatvec) or callable(self.rmatmat)):
            raise TypeError(
                "At least a rmatvec or a rmatmat callable function must be defined."
            )

        def _default_matvec(x, matmat_fn):
            xp = array_xnamespace(x)
            return xp.reshape(matmat_fn(xp.reshape(x, (-1, 1))), (-1,))

        # Use default_matmat/matvec implementation if not provided
        def _default_matmat(X, matvec_fn):
            # Compute the first column to get the output dtype and shape
            tmp_out = matvec_fn(X[:, 0]).reshape(
                -1,
            )
            xp = array_xnamespace(tmp_out)
            args = {}
            if "numpy" in str(xp.__package__):
                device = 'cpu'
                args.update({"order": "F"})
            else:
                device = tmp_out.device
            out = xp.empty(
                (tmp_out.shape[0], X.shape[1]), dtype=tmp_out.dtype,
                device=device, **args
            )
            out[:, 0] = tmp_out

            for i in range(1, X.shape[1]):
                out[:, i] = matvec_fn(X[:, i]).reshape(
                    -1,
                )
            return out

        if not self.matmat:
            self.matmat = partial(_default_matmat, matvec_fn=self.matvec)
        if not self.rmatmat:
            self.rmatmat = partial(_default_matmat, matvec_fn=self.rmatvec)

        if not self.matvec:
            self.matvec = partial(_default_matvec, matmat_fn=self.matmat)
        if not self.rmatvec:
            self.rmatvec = partial(_default_matvec, matmat_fn=self.rmatmat)

        # Wrap matvec/matmat/rmatvec/rmatmat in a function that check provided argument
        def _check_matfn(x, orig_fn, expected_size, expected_dim):
            if not is_array(x):
                raise TypeError("matvec/matmat() argument must be an array")
            if expected_dim == 1:
                if not (x.ndim == 1 or x.ndim == 2 and x.shape[1] == 1):
                    raise ValueError("matvec() argument array must be a vector")
            elif expected_dim != x.ndim:
                raise ValueError("matmat() argument array must be a matrix")
            if expected_size != x.shape[0]:
                raise ValueError(
                    f"LazyLinOp matvec/matmat: dimension mismatch (expected {expected_size}, got {x.shape[0]})"
                )
            return orig_fn(x)

        self.matvec = partial(
            _check_matfn,
            orig_fn=self.matvec,
            expected_size=self.shape[1],
            expected_dim=1,
        )
        self.rmatvec = partial(
            _check_matfn,
            orig_fn=self.rmatvec,
            expected_size=self.shape[0],
            expected_dim=1,
        )
        self.matmat = partial(
            _check_matfn,
            orig_fn=self.matmat,
            expected_size=self.shape[1],
            expected_dim=2,
        )
        self.rmatmat = partial(
            _check_matfn,
            orig_fn=self.rmatmat,
            expected_size=self.shape[0],
            expected_dim=2,
        )

        # Add auxilliary function
        self.check = lambda *args, **kwargs: check(self, *args, **kwargs)
        self.transpose = lambda: self.T

    def __repr__(self):
        return (
            (f"<{self.shape[0]}x{self.shape[1]} {type(self).__name__}")
            + (
                " with unspecified dtype"
                if self.dtype is None
                else f" with dtype={self.dtype}"
            )
            + ">"
        )

    # Operators

    def __pos__(self):
        """
        Returns the positive ::py:class:`LazyLinOp` of self (it is self)

        Example:
            >>> from lazylinop import aslazylinop
            >>> import numpy as np
            >>> M = np.random.rand(10, 12)
            >>> lM = aslazylinop(M)
            >>> +lM
            <10x12 ArrayBasedLazyLinOp with dtype=float64>
        """
        return self

    def __neg__(self):
        """
        Returns the negative ::py:class:`LazyLinOp` of self.

        Example:
            >>> from lazylinop import aslazylinop
            >>> import numpy as np
            >>> M = np.random.rand(10, 12).astype('float32')
            >>> lM = aslazylinop(M)
            >>> x = np.random.randn(12)
            >>> np.allclose(-lM @ x, -(lM @ x))
            True
        """
        return LazyLinOp(
            self.shape,
            matmat=lambda x: -self.matmat(x),
            rmatmat=lambda x: -self.rmatmat(x),
        )

    def __add__(self, other):
        """
        Returns the LazyLinOp for self + other.

        Other must be a LazyLinOp with same shape, or a scalar
        """
        if isinstance(other, numbers.Number):
            from lazylinop import ones

            return self + other * ones(self.shape)

        elif islazylinop(other):
            if other.shape != self.shape:
                raise ValueError("Dimensions must agree")
            return LazyLinOp(
                self.shape,
                matmat=lambda x: self.matmat(x) + other.matmat(x),
                rmatmat=lambda x: self.rmatmat(x) + other.rmatmat(x),
            )

        else:
            raise TypeError("Cannot only add a LazyLinOp object or a scalar")

    def __radd__(self, other):
        return self + other

    def __sub__(self, other):
        """
        Returns the LazyLinOp for self - other
        """
        return self + (-other)

    def __rsub__(self, other):
        return -self + other

    def __mul__(self, other):
        """
        Returns the LazyLinOp for self * s.

        Args:
            s: a scalar.

        """
        if isinstance(other, numbers.Number):
            return LazyLinOp(
                self.shape,
                matmat=lambda x: self.matmat(x) * other,
                rmatmat=lambda x: self.rmatmat(x) * other,
            )
        elif is_array(other):
            raise TypeError(
                "Ambiguous use of '*' operator: For matrix product, use '@'. For element-wise multiplication by a vector, use LazyLinOp 'diag' operator"
            )
        elif islazylinop(other):
            raise TypeError(
                "Ambiguous use of '*' operator: For LazyLinop composition, use '@'."
            )
        else:
            raise TypeError("Cannot multiply by a non-scalar object")

    def __truediv__(self, other):
        """
        Returns the LazyLinOp for self / s.

        Args:
            s: a scalar.

        """
        return self * (1 / other)

    def __pow__(self, n):
        """
        Returns the :py:class:`LazyLinOp` for the n-th power of ``self``.

        - ``L**n == L @ L @ ... @ L`` (n-1 multiplications).

        Args:
            n: a positive integer

        Raises:
            The :py:class:`.LazyLinOp` is not square.

        Example:
            >>> from lazylinop import aslazylinop
            >>> import numpy as np
            >>> M = np.random.rand(10, 10).astype('float32')
            >>> lM = aslazylinop(M)
            >>> lM
            <10x10 ArrayBasedLazyLinOp with dtype=float32>
            >>> np.allclose((lM**2).toarray(), M @ M)
            True
        """
        if not isinstance(n, int):
            raise TypeError("Can only raise to an integer exponent")
        elif n < 0:
            raise ValueError("Can only raise to a positive exponent")
        elif self.shape[0] != self.shape[1]:
            raise Exception("Cannot apply power to a non-square LazyLinOp")
        else:
            from lazylinop import eye

            L = eye(self.shape[0])
            for _ in range(n):
                L = self @ L
            return L

    def __matmul__(self, other):
        """
        Computes self @ op.

        Args:
            op: a compatible array or LazyLinOp

        Returns:
            If op is an array compatible object, the function returns
            (``self @ op``) as such an array. Otherwise
            it returns the :class:`LazyLinOp` for the multiplication
            ``self @ op``.

        """
        if islazylinop(other):
            if self.shape[1] != other.shape[0]:
                raise ValueError(
                    f"LazyLinOp matmul: dimension mismatch ({self.shape} incompatible with {other.shape})"
                )
            return LazyLinOp(
                (self.shape[0], other.shape[1]),
                matmat=lambda x: self.matmat(other.matmat(x)),
                rmatmat=lambda x: other.rmatmat(self.rmatmat(x)),
            )
        elif is_array(other):
            other_shape_idx = 0 if other.ndim <= 2 else -2
            if self.shape[1] != other.shape[other_shape_idx]:
                raise ValueError(
                    f"LazyLinOp matmul: dimension mismatch ({self.shape} incompatible with {other.shape})"
                )
            if other.ndim == 1:
                return self.matvec(other)
            elif other.ndim == 2:
                return self.matmat(other)
            elif other.ndim > 2:
                if is_numpy_array(other):
                    vmatmat = np.vectorize(
                        lambda A, B: A.matmat(B), excluded=[0], signature="(q,r)->(p,r)"
                    )
                else:
                    # FIXME missing implementation?
                    raise NotImplementedError(
                        "Multiplication by a tensor is only supported by numpy array"
                    )
                return vmatmat(self, other)
        raise TypeError(
            "LazyLinOp '@' can only be applied to 1D or 2D arrays, or to other LazyLinOp"
        )

    def __rmul__(self, other):
        """
        Returns the LazyLinOp for s * self.

        Args:
            s: a scalar.

        """
        return self * other

    # Necessary for right matmul with numpy arrays.
    __array_ufunc__ = None

    def __rmatmul__(self, other):
        """
        Returns op @ self.

        Args:
            op: an object compatible with self for this binary operation.

        Returns:
            a :class:`LazyLinOp` or an array depending on op type.

        .. seealso::
            :py:func:`LazyLinOp.__matmul__`
        """
        if is_array(other) and other.ndim <= 2:
            xp = array_xnamespace(other)
            return xp.conj((self.H @ xp.conj(other.T)).T)
        raise TypeError("Only 1D or 2D arrays can apply '@' to a LazyLinOp")

    # Attributes

    @property
    def mT(self):
        """
        The :py:class:`LazyLinOp` transpose.
        """
        return self.T

    @property
    def ndim(self):
        """
        The number of dimensions of the :class:`LazyLinOp`
        (it is always 2).
        """
        return 2

    @property
    def shape(self):
        """
        The shape (``tuple[int, int]``) of the :class:`LazyLinOp`.
        """
        return self._shape

    @property
    def dtype(self):
        """
        Data type of the ``LazyLinOp`` (default is ``None``).
        Only used for LazyLinops created from arrays
        ``L = aslazylinop(array)``, in which case
        ``L.dtype = array.dtype``.
        All other lazylinops have ``dtype = None``.
        """
        return None

    @property
    def size(self):
        """
        The :py:class:`LazyLinOp` size (as the product of its dimension).
        """
        return self.shape[0] * self.shape[1]

    @property
    def T(self):
        """
        The :py:class:`LazyLinOp` transpose.
        """
        return self.conj().H

    @property
    def H(self):
        """
        The :py:class:`LazyLinOp` adjoint/transconjugate.
        """
        return LazyLinOp(
            (self.shape[1], self.shape[0]),
            matmat=lambda x: self.rmatmat(x),
            rmatmat=lambda x: self.matmat(x),
        )

    # Other methods

    def _getitem_left(self, index):
        # FIXME : move low level part of slicer here
        from lazylinop.basicops import slicer, indexer

        if isinstance(index, Iterable):
            return indexer(self.shape[0], index) @ self
        elif isinstance(index, slice):
            return slicer(self.shape[0], index.start, index.stop, index.step) @ self
        elif isinstance(index, int):
            return slicer(self.shape[0], index, index + 1) @ self
        else:
            raise TypeError(f"Cannot index using {type(index)} objects")

    def _getitem_right(self, index):
        # FIXME : move low level part of slicer here
        from lazylinop.basicops import slicer, indexer

        if isinstance(index, Iterable):
            return (indexer(self.shape[1], index) @ self.T).T
        elif isinstance(index, slice):
            return (
                slicer(self.shape[1], index.start, index.stop, index.step) @ self.T
            ).T
        elif isinstance(index, int):
            return (slicer(self.shape[1], index, index + 1) @ self.T).T
        else:
            raise TypeError("Cannot index using {type(key2)} objects")

    def __getitem__(self, indices, /):
        """
        Returns slicing/indexing or the LazyLinOp (e.g. `self[indices]`)

        Args:
            indices:
                a single or a pair of index object (integer, iterable, slice or ellipsis)

        """
        if isinstance(indices, (list, tuple)):
            if len(indices) > 2:
                raise ValueError("Indexing is only supported along 1 or 2 dimensions")
            i0 = indices[0]
            i1 = indices[1] if len(indices) > 1 else None
        else:
            i0 = indices
            i1 = None

        res = self
        if not (
            i0 is Ellipsis or isinstance(i0, slice) and i0 == slice(None, None, None)
        ):
            res = res._getitem_left(i0)
        # check op order as res type may have been changed
        if i1 is not None and i1 is not Ellipsis:
            res = res._getitem_right(i1)

        return res

    # Additional methods

    @property
    def real(self):
        """
        Returns the :py:class:`LazyLinOp` real part.
        """
        return (self + self.conj()) / 2

    @property
    def imag(self):
        """
        Returns the :py:class:`LazyLinOp` imaginary part.
        """
        return (self - self.conj()) / 2j

    def conj(self):
        """
        Returns the :py:class:`LazyLinOp` conjugate.
        """

        xp = array_xnamespace

        return LazyLinOp(
            self.shape,
            matmat=lambda x: xp(x).conj(self.matmat(xp(x).conj(x))),
            rmatmat=lambda x: xp(x).conj(self.rmatmat(xp(x).conj(x))),
        )

    def toarray(self, dtype: str = None, array_namespace=None, device: str = None):
        """
        Returns self as an array

        Internally, it computes ``self @ array_namespace.eye(self.shape[1], dtype=dtype)``, with array_namespace and dtype depending on arguments.

        with smallest possible ``dtype`` and returns self as a
        NumPy/CuPy array or torch tensor.
        ``dtype`` of the output ``y`` depends on
        the :class:`LazyLinOp` instance ``self``.

        Args:
            dtype: ``str``, optional
                The ``dtype`` used eye() in eye()

                Default value is ``None`` and will select the
                smallest possible dtype.

                Note that ``dtype`` of the returned array depends on
                the :class:`LazyLinOp` instance ``self``.
            array_namespace: ``namespace``, optional
                The type of the return array, as an array API namespace (numpy, torch, cupy, …)

                  Default is ``None``, which would use numpy
            device: ``str``, optional
                The ``device`` where the returned array will be computed

                Default value is ``None``, the array will reside on CPU

                Note: ``device`` has no effect if ``array_namespace`` is not
                equal to ``'torch'``.

        Examples:
            >>> import numpy as np
            >>> from lazylinop import aslazylinop
            >>> L = aslazylinop(np.eye(2, dtype='int'))
            >>> L.toarray(array_namespace=np, dtype='float')
            array([[1., 0.],
                   [0., 1.]])
        """
        if array_namespace is None:
            import array_api_compat.numpy as xp
        else:
            if hasattr(array_api_compat, array_namespace.__name__):
                xp = getattr(array_api_compat, array_namespace.__name__)
            else:
                xp = array_namespace

        if dtype is None:
            if "torch" in str(xp):
                for t in [
                    xp.float32,
                    xp.float64,
                    xp.complex64,
                    xp.complex128,
                    xp.float16,
                    xp.bfloat16,
                    xp.int32,
                    xp.int64,
                    xp.int16,
                    xp.int8,
                    xp.uint8,
                    xp.bool,
                ]:
                    try:
                        self @ xp.eye(self.shape[1], 1, dtype=t, device=device)
                        eye_dtype = t
                        break
                    except RuntimeError:
                        pass
            else:
                eye_dtype = "int8"
        else:
            eye_dtype = dtype

        return self @ xp.eye(self.shape[1], dtype=eye_dtype, device=device)


class ArrayBasedLazyLinOp(LazyLinOp):
    """
    ``ArrayBasedLazyLinOp`` class.

    Specialization of LazyLinOp when the underlaying linear operator
    is an array-based Matrix.

    It provide more efficient versions of some LazyLinOp operations, in
    particular for indexing and toarray().
    """

    def __init__(self, M, shape=None):
        """
        Create an ``ArrayBasedLazyLinOp`` instance.

        Parameters
        ----------
            M: (Array or a ``callable``)
                 The uderlaying array or a callable that returns the array.
                 The array must represent a matrix and must have 2 dimensions
                 (if 1-D array is provided, it will converted as a single column matrix)
            shape: (``tuple[int, int]``)
                 Only used and required when M is a callable. In this case, M evaluation is
                 defered, it is necessary to provide the shape in advance for proper
                 LazyLinOp object definition

        Return:
            ``ArrayBasedLazyLinOp``

        Example:
            >>> M = np.arange(12).reshape(3, 4)
            >>> L = ArrayBasedLazyLinOp(M)
            >>> L
            <3x4 ArrayBasedLazyLinOp with dtype=int64>
            >>> L.toarray() is M
            True
            >>> # Other example where the evaluation of M+M is defered
            >>> # (dtype is not kwown before matrix is evaluated)
            >>> L = ArrayBasedLazyLinOp(lambda: M+M, shape=M.shape)
            >>> L
            <3x4 ArrayBasedLazyLinOp with unspecified dtype>
            >>> x = np.random.randn(L.shape[1])
            >>> np.allclose(L@x, (M+M)@x)
            True
        """
        self._mat = None
        if callable(M):
            self._get_mat = M
            if shape is None:
                raise TypeError(
                    "ArrayBasedLazyLinOp() requires shape parameter if the provided array is a callable"
                )
            super().__init__(
                shape=shape,
                matmat=lambda X: self._M @ X,
                rmatmat=lambda X: array_xnamespace(X).conj(self._M.T) @ X,
            )

        else:
            self._mat_init(M)
            super().__init__(
                shape=self._M.shape,
                matmat=lambda X: self._M @ X,
                rmatmat=lambda X: array_xnamespace(X).conj(self._M.T) @ X,
            )

    def _mat_init(self, M):
        if M.ndim < 2:
            xp = array_xnamespace(M)
            M = xp.reshape(M, (1, -1))

        if M.ndim != 2:
            raise ValueError("LazyLinOp must be based on array with ndim <= 2")

        self._mat = M

    @property
    def _M(self):
        if self._mat is None:
            self._mat_init(self._get_mat())
        return self._mat

    # def __repr__(self):
    #     return (
    #         f"<{self.shape[0]}x{self.shape[1]} {type(self).__name__}(shape={tuple(self.shape)} with dtype {self.dtype})"
    #     )

    @property
    def dtype(self):
        if self._mat is None:
            return None
        # We convert torch dtype to preserve scipy LinearOperator compatibility
        if is_torch_array(self._M):
            return self._M[0, 0].numpy(force=True).dtype
        return self._M.dtype

    def __getitem__(self, s):
        return ArrayBasedLazyLinOp(self._M[s])  # FIXME: use lazy eval w/ shape

    def __neg__(self):
        return ArrayBasedLazyLinOp(lambda: -self._M, shape=self.shape)

    @property
    def T(self):
        return ArrayBasedLazyLinOp(
            lambda: self._M.T, shape=(self.shape[1], self.shape[0])
        )

    @property
    def H(self):
        xp = array_xnamespace(self._M)
        if xp.isdtype(self._M.dtype, "complex floating"):
            return ArrayBasedLazyLinOp(
                lambda: xp.conj(self._M).T, shape=(self.shape[1], self.shape[0])
            )
        else:
            return self.T

    @property
    def real(self):
        xp = array_xnamespace(self._M)
        return ArrayBasedLazyLinOp(lambda: xp.real(self._M), shape=self.shape)

    @property
    def imag(self):
        xp = array_xnamespace(self._M)
        return ArrayBasedLazyLinOp(lambda: xp.imag(self._M), shape=self.shape)

    def toarray(self, dtype: str = None, array_namespace=None, device: str = None):

        if dtype is None:
            dtype = self._M.dtype
        if array_namespace is None:
            array_namespace = array_xnamespace(self._M)
        else:
            if hasattr(array_api_compat, array_namespace.__name__):
                array_namespace = getattr(array_api_compat, array_namespace.__name__)

        return array_namespace.asarray(self._M, dtype=dtype, device=device)


def check(self, array_namespace=np, dtype: str = "float64", device=None):
    r"""
    Verifies validity assertions on any :py:class:`LazyLinOp`.

    **Notations**:

    - Let ``op`` a :py:class:`LazyLinOp`,
    - ``u``, ``v`` vectors such that ``u.shape[0] == op.shape[1]``
      and ``v.shape[0] == op.shape[0]``,
    - ``X``, ``Y`` 2d-arrays such that ``X.shape[0] == op.shape[1]``
      and ``Y.shape[0] == op.shape[0]``.

    The function verifies:

        - Consistency of operator/adjoint product shape:

            1.

                a. ``(op @ u).shape == (op.shape[0],)``,
                b. ``(op.H @ v).shape == (op.shape[1],)``,
            2.

                a. ``(op @ X).shape == (op.shape[0], X.shape[1])``,
                b. ``(op.H @ Y).shape == (op.shape[1], Y.shape[1])``,

        - Consistency of operator & adjoint products:

            3. ``(op @ u).conj().T @ v == u.conj().T @ op.H @ v``

        - Consistency of operator-by-matrix & operator-by-vector products:

            4. ``op @ X`` is equal to the horizontal concatenation of all
               ``op @ X[:, j]`` ($0 \le j  < X.shape[1]$).

               (it implies also that ``(op @ X).shape[1] == X.shape[1]``,
               as previously verified in 2.a)

        - Consistency of adjoint-by-matrix & adjoint-by-vector products:

            5. ``op.H @ Y`` is equal to the horizontal concatenation of all
               ``op.H @ Y[:, j]`` ($0 \le j  < Y.shape[1]$).

               (it implies also that ``(op.H @ Y).shape[1] == Y.shape[1]``,
               as previously verified in 2.b)

        - Linearity:

            6. ``op @ (a1 * u1 + a2 * u2) == a1 * (op @ u1) + a2 * (op @ u2)``.

        - Device:

            7. ``array_api_compat.device(x) == array_api_compat.device(op @ x)

    Raises:
        - ``Exception("Operator shape[0] and operator-by-vector
          product shape must agree")`` (assertion 1.a)
        - ``Exception("Operator shape[1] and adjoint-by-vector
          product shape must agree")`` (assertion 1.b)
        - ``Exception("Operator-by-matrix product shape and
          operator/input-matrix shape must agree")`` (assertion 2.a)
        - ``Exception("Operator-by-matrix & operator-by-vector
          products must agree")`` (assertion 2.b)
        - ``Exception("Operator and adjoint products do not match")``
          (assertion 3)
        - ``Exception("Operator-by-matrix & operator-by-vector
          products must agree")`` (assertion 4)
        - ``Exception("Adjoint-by-matrix product shape and
          adjoint/input-matrix shape must agree")`` (assertion 5)


    .. admonition:: Computational cost
        :class: warning

        This function has a computational cost of several
        matrix products.
        It shouldn't be used into an efficient implementation but
        only to test a :py:class:`.LazyLinOp` implementation is
        valid.

    .. admonition:: Necessary condition but not sufficient
        :class: admonition-note

        This function is able to detect an inconsistent :class:`.LazyLinOp`
        according to the assertions above but it cannot ensure a
        particular operator computes what someone is excepted this operator
        to compute.
        In other words, the operator can be consistent but not correct at
        the same time. Thus, this function is not enough by itself to write
        unit tests for an operator, complementary tests are necessary.

    Args:
        self: (:py:class:`LazyLinOp`)
            Operator to test.
        array_namespace: ``namespace``, optional
            Namespace of the input to test ``self``.

            - NumPy namespace (default value).
            - CuPy namespace.
            - PyTorch namespace.
            - ``None`` NumPy/CuPy and PyTorch namespaces.
        dtype: ``str``, optional
            dtype of the input that will be used
            to test ``self``.
        device: optional
            Use device ``device`` to run ``self.check(...)``.
            Default value is ``None``.

    Example:
        >>> import numpy as np
        >>> from numpy.random import rand
        >>> from lazylinop import aslazylinop, LazyLinOp
        >>> M = rand(12, 14)
        >>> # numpy array M is OK as a LazyLinOp
        >>> aslazylinop(M).check(array_namespace=np)
        >>> # the next LazyLinOp is not
        >>> L2 = LazyLinOp((6, 7), matmat=lambda x: np.ones((6, 7)), rmatmat=lambda x: np.zeros((7,6)))
        >>> L2.check(array_namespace=np) # doctest:+ELLIPSIS
        Traceback (most recent call last):
            ...
        Exception: ...

    .. seealso::
        :py:func:`aslazylinop`,
        :py:class:`LazyLinOp`
    """

    import array_api_compat

    _array_namespace = array_xnamespace
    _device = array_api_compat.device
    _size = array_api_compat.size

    def _randx(M, N=None, xp=np, dtype: str = "float", device=None):
        if "numpy" in str(xp.__package__):
            _randn = xp.random.randn
        elif "torch" in str(xp.__package__):
            _randn = xp.randn
            _dtype = xp.from_numpy(np.random.randn(3).astype(dtype)).dtype
        elif "cupy" in str(xp.__package__):
            _randn = xp.random.randn
        else:
            raise Exception("Unknown array namespace.")
        n = 1 if N is None else N
        if dtype == "complex":
            tmp = _randn(M, n) + 1j * _randn(M, n)
        else:
            tmp = _randn(M, n)
        if "torch" in str(xp.__package__):
            tmp = tmp.to(dtype=_dtype, device=device)
        elif "cupy" in str(xp.__package__):
            with xp.cuda.Device(device):
                tmp = tmp.astype(dtype)
        else:
            tmp = tmp.astype(dtype)
        return tmp.reshape(-1) if n == 1 else tmp

    # Loop over NumPy/CuPy and PyTorch input.
    if array_namespace is None:
        import array_api_compat.numpy as xp1
        import array_api_compat.cupy as xp2
        import array_api_compat.torch as xp3

        xps = [xp1, xp2, xp3]
    else:
        xps = [array_namespace]
    for p in xps:
        # Random vectors and matrices.
        u = _randx(self.shape[1], xp=p, dtype=dtype, device=device)
        v = _randx(self.shape[0], xp=p, dtype=dtype, device=device)
        X = _randx(self.shape[1], 3, xp=p, dtype=dtype, device=device)
        Y = _randx(self.shape[0], 3, xp=p, dtype=dtype, device=device)
        a = _randx(1, xp=p, dtype=dtype, device=device)[0]
        a2 = _randx(1, xp=p, dtype=dtype, device=device)[0]
        u2 = _randx(self.shape[1], xp=p, dtype=dtype, device=device)
        xp = _array_namespace(u)
        # CuPy default device.
        if "cupy" in str(xp.__package__) and device is not None:
            xp.cuda.runtime.setDevice(device)
        if "torch" in str(xp.__package__):
            # Check against torch tensor.
            # Torch does not support multiplication of
            # two tensors with different dtype.
            try:
                z = self @ u
            except RuntimeError:
                print(
                    "Torch does not support multiplication of"
                    + " two tensors with different dtype:"
                    + f" do not check against {u.dtype}."
                )
                continue
        # Check device
        self_u = self @ u
        self_v = self.H @ v
        if _device(self_u) != _device(u):
            raise Exception("y = op @ x and x are not on the same device.")
        # Check operator - vector product dimension
        if self_u.shape != (self.shape[0],):
            raise Exception(
                "Operator shape[0] and operator-by-vector product shape must agree"
            )
        # Check operator adjoint - vector product dimension
        if self_v.shape != (self.shape[1],):
            raise Exception(
                "Operator shape[1] and adjoint-by-vector product shape must agree"
            )
        # Check operator - matrix product consistency
        AX = self @ X
        if AX.shape != (self.shape[0], X.shape[1]):
            raise Exception(
                "Operator-by-matrix product shape and"
                " operator/input-matrix shape must agree"
            )
        for i in range(X.shape[1]):
            if not xp.allclose(AX[:, i], self @ X[:, i]):
                raise Exception(
                    "Operator-by-matrix & operator-by-vector products must agree"
                )
        # Check operator transpose/adjoint dimensions
        AY = self.H @ Y
        if AY.shape != (self.shape[1], Y.shape[1]) or (self.T @ Y).shape != (
            self.shape[1],
            Y.shape[1],
        ):
            raise Exception(
                "Adjoint-by-matrix product shape and"
                " adjoint/input-matrix shape must agree"
            )

        # Check operator adjoint on matrix product
        for i in range(Y.shape[1]):
            if not xp.allclose(AY[:, i], self.H @ Y[:, i]):
                raise Exception(
                    "Adjoint-by-matrix & adjoint-by-vector products must agree"
                )
        del AY
        # Dot test to check forward - adjoint consistency
        if "torch" in str(xp.__package__):
            # Torch does not support multiplication of
            # two tensors with different dtype.
            # fft of float tensor returns complex tensor.
            promote = xp.promote_types(self_u.dtype, self_v.dtype)
            if not xp.allclose(
                (self_u.conj().T @ v.to(dtype=self_u.dtype)).to(dtype=promote),
                (u.conj().T.to(dtype=self_v.dtype) @ self_v).to(dtype=promote),
            ):
                raise Exception("Operator and adjoint products do not match")
        else:
            if not xp.allclose(self_u.conj().T @ v, u.conj().T @ self_v):
                raise Exception("Operator and adjoint products do not match")
        # Check linearity op @ (a * u + a2 * u2) = a * op @ u + a2 * op @ u2.
        y = self @ (a * u + a2 * u2)
        z = a * self_u + a2 * (self @ u2)
        if not xp.allclose(y, z):
            raise Exception("Operator is not linear.")
