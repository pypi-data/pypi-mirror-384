from warnings import warn
from scipy.sparse import issparse, random
import numpy as np
import gc


def check_op(op):
    """
    See :py:func:`LazyLinOp.check_op`.
    """
    from lazylinop import islazylinop, LazyLinOp
    if islazylinop(op):
        if type(op) is not LazyLinOp:
            # TODO: have trust in our own tested LazyLinOp subclasses
            warn("op is a subclass of LazyLinOp and might have broken the"
                 " operator.")
    else:
        raise TypeError("op is not a LazyLinOp")
    op.check()


def _check_op(L, silent=True, ignore_assertions=['A5.3']):
    """
    Asserts that ``L`` is valid (as a :py:class:`LazyLinOp`).

    This function helps to verify that a :py:class:`LazyLinOp` defined using
    the class constructor is valid.

    For ``L`` to be valid it must:

        1. be a :py:class:`LazyLinOp`,
        2. the result of products ``P = L @ X, L.T @ X or L.H @ X`` must
        consist with ``L``, ``X`` and a well defined matrix-product.
        ``P`` must have a consistent ``type(P)``, ``P.dtype``, ``P.shape`` and
        ``P`` value.
        ``X`` can be a 1d and 2d numpy array (and optionally a scipy matrix).

    For more details about the validity of a :py:class:`LazyLinOp` see the
    `specification <./check_op_spec.html>`_.

    Args:
        L: (LazyLinOp)
            The operator to test. It might have been defined by the
            :py:func:`LazyLinOp.__init__` constructor, using
            :py:func:`lazylinop.aslazylinop` or extending the
            :py:class:`LazyLinOp` class.
        silent: (bool)
            if True (default) all informative messages are silenced otherwise
            they are printed.
            If you need to filter warnings too use
            ``warnings.filterwarnings('ignore', 'check_op')``.
        ignore_assertions: (list or None)
            List of assertions to ignore in test of L.
            The identifiers for the assertions are to find
            in `specification <./check_op_spec.html>`_ (e.g.: 'A1.1').
            Defaultly, 'A5.3' is ignored because it is very similar to 'A5.2'.

    Raises:
        ``AssertionError``: if ``L`` is not valid.

    Returns:
       ``None``

    Example:
        >>> from numpy.random import rand
        >>> from lazylinop import aslazylinop
        >>> from lazylinop.check_op import _check_op
        >>> M = rand(12, 14)
        >>> _check_op(aslazylinop(M))

    """
#    warn("Deprecated _check_op, please use check_op. The former will deleted"
#         " soon.")
    ignore_assertions = [] if ignore_assertions is None else ignore_assertions
    from lazylinop import LazyLinOp, islazylinop
    silent or print("Testing your LazyLinOp L...")
    # (A1) type of L:
    assert islazylinop(L) or "A1" in ignore_assertions
    overridden_funcs = []
    verified_meths = [
        f
        for f in dir(LazyLinOp)
        if callable(getattr(LazyLinOp, f))
        or isinstance(getattr(LazyLinOp, f), property)
    ]
    for attr_name in verified_meths:  # dir(LazyLinOp):
        attr = L.__getattribute__(attr_name)
        if (('method' in str(type(attr)) or 'function' in str(type(attr))) and
           'LazyLinOp.'+attr_name not in str(attr)):
            overridden_funcs += [attr_name]
    if len(overridden_funcs) > 0:
        warn("Override detected in LazyLinOp object for function(s): "
             + str(overridden_funcs)+", it might"
             " break something (at your own risk)")
    tested_Ls = [(L, 'L')]
    try:
        L.T.toarray()
    except TypeError as te:
        if str(te) in "'NoneType' object is not callable":
            # rmatmat or rmatvec was not provided by user
            warn("L wasn't defined with a rmatvec/rmatmat function, that's not"
                 " advised as L.T and L.H or left-hand mul Y @ L won't be"
                 " available.")
    else:
        # rmatmat/vec is defined
        tested_Ls += [(L.T, 'L.T'), (L.H, 'L.H')]
    for L_, L_exp in tested_Ls:
        # different to detect erroneous P shape
        X_ncols = 2 if L_.shape[1] != 2 else 3
        silent or print("Testing L_ =", L_exp, "through P = L_ @ X")
        for X, L_must_handle_X in [(np.random.rand(L_.shape[1], X_ncols),
                                    True),
                                   (random(L_.shape[1], X_ncols),
                                    False),
                                   (np.random.rand(L_.shape[1]), True)]:
            silent or print("type(X):", type(X))
            try:
                P = L_ @ X
            except Exception as e:
                if L_must_handle_X:
                    silent or print("L_ @ X raised this exception:", str(e))
                    raise Exception("L_ is defective about the type of X (in"
                                    " L_ @ X). L_ must handle X either it is"
                                    " a 2d or 1d np.ndarray (in the case the"
                                    " dimensions match).")
                else:
                    warn("L_ doesn't handle X of -- not mandatory -- type: " +
                         str(type(X)))
                    del X
                    continue
            # (A2) type of P = L_ @ X:
            assert ((not issparse(X) or issparse(X) and
                     (issparse(P) or isinstance(P, np.ndarray))) or
                    "A2.1" in ignore_assertions)
            assert ((issparse(X) or isinstance(X, np.ndarray) and
                     isinstance(P, np.ndarray)) or "A2.2" in ignore_assertions)
            # (A2) is True,
            # then attributes shape, ndim and dtype are available for P
            # (A3) Shape of P:
            assert P.ndim == X.ndim or "A3.1" in ignore_assertions
            assert P.shape[0] == L_.shape[0] or ("A3.2" in
                                                 ignore_assertions)
            assert (P.ndim == 1 or P.shape[1] == X.shape[1] or 'A3.3' in
                    ignore_assertions)
            # (A4) dtype of P:
            if L_.dtype is None:
                warn("L_ is of undefined dtype, this is not advised.")
            else:
                ref_dtype = np.promote_types(L_.dtype, X.dtype)
                silent or print("ref_dtype:", ref_dtype, "P.type:", P.dtype,
                                "X.dtype:", X.dtype)
                assert (type(np.dtype(P.dtype)) is type(np.dtype(ref_dtype))
                        or ("A4" in ignore_assertions))
            # (A5) equality:
            if issparse(P):
                P = P.toarray()
            # (A5.1)
            assert np.allclose(P, L_.toarray() @ X) or ("A5.1" in
                                                        ignore_assertions)
            # (A5.2)
            if issparse(X):
                X_ = X.toarray()
            else:
                X_ = X
            assert (X_.ndim == 1 or
                    np.all([np.allclose(P[:, j], L_ @ X_[:, j]) for j in
                            range(X_.shape[1])])) or ("A5.2" in
                                                      ignore_assertions)
            assert (X_.ndim == 1 or
                    np.all([np.allclose(P[i, :], L_[i, :] @ X_) for i in
                            range(L_.shape[0])])) or ("A5.3" in
                                                      ignore_assertions)
            del X_
            del X
            del P
            gc.collect()
        silent or print("_L =", L_exp, "passed all tests")
    silent or print("L passed all tests")
