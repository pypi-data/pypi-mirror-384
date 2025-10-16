"""
Module for polynomial related :py:class:`.LazyLinOp`-s.

It provides "polynomial for :py:class:`.LazyLinOp`" functions for which
the polynomial variable is itself a linear operator (especially a
:py:class:`.LazyLinOp`). This allows to build a :py:class:`.LazyLinOp`
``M=p(L)`` when ``p`` is an instance of a polynomial class inherited
from NumPy polynomial package and matrix representation of
:py:class:`.LazyLinOp` ``L`` is square.

Below are the provided classes:

    - :py:class:`.Polynomial` inherited from `NumPy Polynomial <https:/
      /numpy.org/doc/stable/reference/generated/
      numpy.polynomial.polynomial.Polynomial.html>`_,
    - :py:class:`.Chebyshev`, inherited from `NumPy Chebyshev <https:/
      /numpy.org/doc/stable/reference/generated/
      numpy.polynomial.chebyshev.Chebyshev.html>`_,
    - :py:class:`.Hermite`, inherited from `NumPy Hermite <https:/
      /numpy.org/doc/stable/reference/generated/
      numpy.polynomial.hermite.Hermite.html>`_,
    - :py:class:`.HermiteE`, inherited from `NumPy HermiteE <https:/
      /numpy.org/doc/stable/reference/generated/
      numpy.polynomial.hermite_e.HermiteE.html>`_,
    - :py:class:`.Laguerre`, inherited from `NumPy Laguerre <https:/
      /numpy.org/doc/stable/reference/generated/
      numpy.polynomial.laguerre.Laguerre.html>`_,
    - :py:class:`.Legendre`, inherited from `NumPy Legendre <https:/
      /numpy.org/doc/stable/reference/generated/
      numpy.polynomial.legendre.Legendre.html>`_.

Below are the provided functions:

    - :py:func:`.xpoly` that returns an instance of a polynomial class
      inherited from NumPy polynomial classes.
      It could be (specified by :py:func:`xpoly(coef, kind=...)`):

      - ``'chebyshev'`` which is specialized for Chebyshev polynomials.
      - ``'hermite'`` which is specialized for Hermite
        "physicists" polynomials.
      - ``'hermite_e'`` which is specialized for Hermite
        "probabilists" polynomials.
      - ``'laguerre'`` which is specialized for Laguerre polynomials.
      - ``'legendre'`` which is specialized for Legendre polynomials.
      - ``'roots'`` which defines the polynomial from its roots.
    - :py:func:`.power` for the n-th power of any linear operator.

With ``p1`` and ``p2`` two polynomial instances return by
:py:func:`xpoly(coef1, kind1)` and :py:func:`xpoly(coef2, kind2)`, one can:

    - add/substract (if ``kind1=kind2``: ``(p1 + p2)(L)``, ``(p1 - p2)(L)``
      with ``L`` the polynomial variable). Evaluating and applying the
      polynomials on the fly is also possible: ``(p1 + p2)(L) @ x``.
    - The same is possible to multiply (``*``), divide (``//``) and modulo
      (``%``) two polynomials (``(p1 * p2)(L)``, ``(p1 // p2)(L)``,
      ``(p1 % p2)(L)``.
    - And compose two polynomials: ``(p1(p2))(L)`` whatever
      ``kind1`` and ``kind2``.
    - :octicon:`megaphone;1em;sd-text-danger` Of note, matrix representation
      of instance ``L`` of :py:class:`.LazyLinOp` must be square.
    - :octicon:`info;1em;sd-text-success` If ``p`` is in monomial form
      evaluation of ``p(L) @ x`` uses the
      `Horner's method <https://en.wikipedia.org/wiki/Horner%27s_method>`_,
      `Clenshaw algorithm <https://en.wikipedia.org/wiki/Clenshaw_algorithm>`_
      otherwise.
    - :octicon:`pin;1em;sd-text-danger` Of note, duration of
      ``(p1(p2))(L) @ x`` and duration of ``p1(p2(L)) @ x`` might differ
      when the number of polynomial coefficients is large.

.. admonition:: More details about implementation and features

   The :py:func:`xpoly` returns an instance of internal classes that extend
   NumPy polynomial classes
   `Polynomial <https://numpy.org/doc/stable/reference/generated/
   numpy.polynomial.polynomial.Polynomial.html>`_,
   `Chebyshev <https://numpy.org/doc/stable/reference/generated/
   numpy.polynomial.chebyshev.Chebyshev.html>`_,
   `Hermite <https://numpy.org/doc/stable/reference/generated/
   numpy.polynomial.hermite.Hermite.html>`_,
   `HermiteE <https://numpy.org/doc/stable/reference/generated/
   numpy.polynomial.hermite_e.HermiteE.html>`_,
   `Laguerre <https://numpy.org/doc/stable/reference/generated/
   numpy.polynomial.laguerre.Laguerre.html>`_,
   `Legendre <https://numpy.org/doc/stable/reference/generated/
   numpy.polynomial.legendre.Legendre.html>`_.

   They override the method :py:meth:`__call__` to implement the polynomial
   evaluation and calculate on the fly the available operations.
   Under the hood evaluation is called depending on the polynomial form.
.. To compute n-th power of a LazyLinOp use :py:func:`power` or
   create :py:class:`Poly` instance such that only n-th coefficient
   is equal to one while the others are equal to zero.
"""
import numpy as np
from numpy.polynomial import Polynomial as P
from numpy.polynomial import Chebyshev as T
from numpy.polynomial import Hermite as H
from numpy.polynomial import HermiteE as HE
from numpy.polynomial import Laguerre as La
from numpy.polynomial import Legendre as Le
from lazylinop import islazylinop, LazyLinOp, aslazylinop


def xpoly(coef, domain: list = [-1.0, 1.0], window: list = [-1.0, 1.0],
          symbol: str = 'x', kind: str = 'monomial'):
    r"""Return instance amongst :py:class:`numpy.polynomial.Polynomial`,
    :py:class:`numpy.polynomial.Chebyshev`,
    :py:class:`numpy.polynomial.Hermite`,
    :py:class:`numpy.polynomial.HermiteE`,
    :py:class:`numpy.polynomial.Laguerre`
    or :py:class:`numpy.polynomial.Legendre` according to kind.
    ``xpoly`` is the extended function for polynomial creation of any
    kind without using the specialized polynomial classes directly.
    Under the hood, the function create instance depending on the kind
    :code:`'chebyshev'`, :code:`'hermite'`, :code:`'hermite_e'`,
    :code:`'laguerre'`, :code:`'legendre'`, :code:`'monomial'` or
    :code:`'roots'` of the polynomial you ask for.
    It is pretty simple and you can construct a polynomial as you
    would do with a `NumPy polynomial <https://numpy.org/doc/stable/
    reference/routines.polynomials.classes.html>_`.

    Args:
        coef: list or 1d array
            List of coefficients :math:`\lbrack c_0,c_1,\cdots,c_n\rbrack`
            if :code:`kind!='roots'`:

            .. math::

                \begin{equation}
                p(L)=\sum_{i=0}^nc_iQ_i(L)
                \end{equation}

            List of roots :math:`\lbrack r_0,r_1,\cdots,r_n,c_n\rbrack`
            (where :code:`c_n` is the leading coefficients)
            if :code:`kind='roots'`:

            .. math::

                \begin{equation}
                p(L)=c_n\prod_{i=0}^n(L-r_iId)
                \end{equation}

        .. domain: list, optional
            See `NumPy documentation <https://numpy.org/doc/stable/reference/
            generated/numpy.polynomial.polynomial.Polynomial.html#
            numpy.polynomial.polynomial.Polynomial>`_ for more details.
        .. window: list, optional
            See `NumPy documentation <https://numpy.org/doc/stable/reference/
            generated/numpy.polynomial.polynomial.Polynomial.html#
            numpy.polynomial.polynomial.Polynomial>`_ for more details.
        .. symbol: str, optional
            See `NumPy documentation <https://numpy.org/doc/stable/reference/
            generated/numpy.polynomial.polynomial.Polynomial.html#
            numpy.polynomial.polynomial.Polynomial>`_ for more details.
        kind: str, optional
            Representation of the polynomial.
            It could be 'monomial' (default), 'chebyshev',
            'hermite' physicists polynomials,
            'hermite_e' probabilists polynomials, 'laguerre',
            'legendre' and 'roots'.
            If kind is 'roots', coef is considered to be
            the roots of the polynomial. Leading coefficient is the
            last element :code:`coef[:-1]` of coef argument while the first
            values are the roots of the polynomial.
            Because of the expression :math:`(L - r_0Id)\cdots (L - r_nId)`
            coefficient :math:`c_n` of the highest power :math:`c_nL^n`
            is always 1.

    Raises:
        ValueError
            coef size must be > 0.
        Exception
            coef must be a 1d array.
        ValueError
            kind must be either monomial, cheb, herm,
            herme, lag, leg or roots.

    Examples:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> p1 = lz.polynomial.xpoly([1.0, 2.0, 1.0], kind='monomial')
        >>> p2 = lz.polynomial.xpoly([-1.0, -1.0, 1.0], kind='roots')
        >>> np.allclose(p1.coef, p2.coef)
        True

    .. seealso::
        `numpy.polynomial package
        <https://numpy.org/doc/stable/reference/routines.polynomials.html>`_.
    """
    if type(coef) is list:
        coef = np.asarray(coef)
    if coef.shape[0] < 1:
        raise ValueError("coef size must be > 0.")
    if coef.ndim != 1:
        raise Exception("coef must be a 1d array.")

    if kind == 'monomial':
        return Polynomial(coef, domain, window, symbol, fromRoots=False)
    elif kind == 'chebyshev':
        return Chebyshev(coef, domain, window, symbol)
    elif kind == 'hermite':
        return Hermite(coef, domain, window, symbol)
    elif kind == 'hermite_e':
        return HermiteE(coef, domain, window, symbol)
    elif kind == 'laguerre':
        return Laguerre(coef, domain, window, symbol)
    elif kind == 'legendre':
        return Legendre(coef, domain, window, symbol)
    elif kind == 'roots':
        if coef.shape[0] == 1:
            return Polynomial(coef, domain, window, symbol, fromRoots=False)
        else:
            return Polynomial(coef, domain, window, symbol, fromRoots=True)
    else:
        raise ValueError("kind must be either monomial, chebyshev," +
                         " hermite, hermite_e," +
                         " laguerre, legendre or roots.")


def _is_lazylinop_poly(p):
    return isinstance(p, (Polynomial, Chebyshev, Hermite,
                          HermiteE, Laguerre, Legendre))


def _compose(p, op):
    """Returns the composition p(op).

    Args:
        p: :py:class:`.Poly`, :py:class:`.Chebyshev`, :py:class:`.Hermite`,
        :py:class:`.HermiteE`, :py:class:`.Laguerre` or :py:class:`.Legendre`
        op: :py:class:`.Poly`, :py:class:`.Chebyshev`, :py:class:`.Hermite`,
        :py:class:`.HermiteE`, :py:class:`.Laguerre` or :py:class:`.Legendre`

    Raises:
        TypeError: op or p is not of a valid lazylinop polynomial class.

    .. seealso::
        `numpy.polynomial package
        <https://numpy.org/doc/stable/reference/routines.polynomials.html>`_.
    """
    if not _is_lazylinop_poly(p):
        raise TypeError('p is not a valid lazylinop polynomial')
    if _is_lazylinop_poly(op):
        # composition by numpy super class of op
        tmp = op.__class__.__bases__[0].__call__(p, op)  # np polynomial
        # then convert to lazylinop poly
        return op.__class__(tmp.coef, domain=tmp.domain, window=tmp.window)
    else:
        raise TypeError('op is not valid lazylinop polynomial')


class Polynomial(P):
    """This class implements a polynomial class derived from
    :py:class:`numpy.polynomial.Polynomial` and so relies on NumPy polynomial
    package to manipulate polynomials.

    See :py:mod:`lazylinop.polynomial` for an introduction to implemented
    operations and their basic use.
    """

    def __init__(self, coef, domain: list = [-1.0, 1.0],
                 window: list = [-1.0, 1.0], symbol: str = 'x',
                 fromRoots: bool = False):
        r"""__init__(self, coef, fromRoots: bool = False)

        Init instance of Poly.

        :octicon:`alert-fill;1em;sd-text-danger` Be aware that
        :code:`Poly(fromRoots=True)(L)` returns
        :math:`p(L)=c_n\prod_{i=0}^n(L-r_iId)` and not
        :math:`p(x)=\prod_{i=0}^n(x-r_i)` like
        `NumPy polyvalfromroots <https://docs.scipy.org/doc/numpy-1.9.3/
        reference/generated/numpy.polynomial.polynomial.polyvalfromroots.html>`_.

        Args:
            coef: list
                List of coefficients :math:`\lbrack c_0,c_1,\cdots,c_n\rbrack`
                if :code:`fromRoots=False`.
                Polynomial of :py:class:`.LazyLinOp` ``L`` is:

                .. math::

                    \begin{equation}
                    p(L)=\sum_{i=0}^nc_iL^i
                    \end{equation}

                List of roots :math:`\lbrack r_0,r_1,\cdots,r_n,c_n\rbrack`
                (where :code:`c_n` is the leading coefficients)
                if :code:`fromRoots=True`.
                Polynomial of :py:class:`.LazyLinOp` ``L`` is:

                .. math::

                    \begin{equation}
                    p(L)=c_n\prod_{i=0}^n(L-r_iId)
                    \end{equation}

            .. domain: list, optional
                See `NumPy documentation <https://numpy.org/doc/stable/
                reference/generated/
                numpy.polynomial.polynomial.Polynomial.html#
                numpy.polynomial.polynomial.Polynomial>`_ for more details.
            .. window: list, optional
                See `NumPy documentation <https://numpy.org/doc/
                stable/reference/generated/
                numpy.polynomial.polynomial.Polynomial.html#
                numpy.polynomial.polynomial.Polynomial>`_ for more details.
            .. symbol: str, optional
                See `NumPy documentation <https://numpy.org/doc/
                stable/reference/generated/
                numpy.polynomial.polynomial.Polynomial.html#
                numpy.polynomial.polynomial.Polynomial>`_ for more details.
            fromRoots: bool, optional
                - If ``False`` uses polynomial coefficients.
                - If ``True`` uses polynomial roots.
                  Last element :code:`coef[-1]` of :code:`coef`
                  is the leading coefficient.

        Examples:
            >>> import numpy as np
            >>> import lazylinop as lz
            >>> p1 = lz.polynomial.Polynomial([1, 2, 1], fromRoots=False)
            >>> p2 = lz.polynomial.Polynomial([-1, -1, 1], fromRoots=True)
            >>> np.allclose(p1.coef, p2.coef)
            True

        .. seealso::
            `numpy.polynomial package
            <https://numpy.org/doc/stable/reference/routines.polynomials.html>`_.
        """
        coef = np.asarray(coef)
        if fromRoots is False or coef.shape[0] == 1:
            # If coef.shape is (1, ) there is only leading coefficient
            self.roots = None
            self.leading_coef = coef[-1]
            P.__init__(self, coef, domain, window, symbol)
        else:
            self.roots = coef[:-1]
            self.leading_coef = coef[-1]
            # Last element coef[-1] of coef is the leading coefficient.
            # np.polynomial.polynomial.polyfromroots does not use it.
            P.__init__(self,
                       np.polynomial.polynomial.polyfromroots(self.roots),
                       domain, window, symbol)

    def __call__(self, op):
        r"""
        Thanks to Python :py:meth:`__call__` instance behaves like function.
        If op is a LazyLinOp, return polynomial of op applied to input array.
        If op is a :py:class:`numpy.polynomial.Polynomial`,
        :py:class:`numpy.polynomial.Chebyshev`,
        :py:class:`numpy.polynomial.Hermite`,
        :py:class:`numpy.polynomial.HermiteE`,
        :py:class:`numpy.polynomial.Laguerre` or
        :py:class:`numpy.polynomial.Legendre` instance, return a poly instance.

        Args:
            op: :py:class:`numpy.polynomial.Polynomial`,
            :py:class:`numpy.polynomial.Chebyshev`,
            :py:class:`numpy.polynomial.Hermite`,
            :py:class:`numpy.polynomial.HermiteE`,
            :py:class:`numpy.polynomial.Laguerre` or
            :py:class:`numpy.polynomial.Legendre` instance

        Raises:
            TypeError
                Unexpected op.

        Examples:
            >>> import numpy as np
            >>> import lazylinop as lz
            >>> p = lz.polynomial.Polynomial([1.0, 2.0, 3.0])
            >>> L = lz.eye(3, 3, k=0)
            >>> islazylinop(p(L))
            True
            >>> x = np.random.randn(3)
            >>> np.allclose(6.0 * x, p(L) @ x)
            True

        .. seealso::
            `numpy.polynomial package
            <https://numpy.org/doc/stable/reference/routines.polynomials.html>`_.
        """
        if islazylinop(op):
            if self.roots is None:
                return _polyval(op, self.coef)
            else:
                return self.leading_coef * _polyvalfromroots(op, self.roots)
        elif _is_lazylinop_poly(op):
            return _compose(self, op)
        else:
            raise TypeError('Unexpected op.')


class Chebyshev(T):
    """This class implements a Chebyshev polynomial class derived from
    :py:class:`numpy.polynomial.Chebyshev` and so relies on NumPy polynomial
    package to manipulate polynomials.

    See :py:mod:`lazylinop.polynomial` for an introduction to implemented
    operations and their basic use.
    """

    def __init__(self, coef, domain: list = [-1.0, 1.0],
                 window: list = [-1.0, 1.0], symbol: str = 'x'):
        r"""Init instance of Chebyshev.

        Args:
            coef: list
                List of Chebyshev
                coefficients :math:`\lbrack c_0,c_1,\cdots,c_n\rbrack`.
                Polynomial of :py:class:`.LazyLinOp` ``L`` is:

                .. math::

                    \begin{equation}
                    p(L)=\sum_{i=0}^nc_iT_i(L)
                    \end{equation}

            .. domain: list, optional
                See `NumPy documentation <https://numpy.org/doc/stable/
                reference/generated/
                numpy.polynomial.chebyshev.Chebyshev.html#
                numpy.polynomial.chebyshev.Chebyshev>`_ for more details.
            .. window: list, optional
                See `NumPy documentation <https://numpy.org/doc/
                stable/reference/generated/
                numpy.polynomial.chebyshev.Chebyshev.html#
                numpy.polynomial.chebyshev.Chebyshev>`_ for more details.
            .. symbol: str, optional
                See `NumPy documentation <https://numpy.org/doc/
                stable/reference/generated/
                numpy.polynomial.chebyshev.Chebyshev.html#
                numpy.polynomial.chebyshev.Chebyshev>`_ for more details.

        Examples:
            >>> from lazylinop.polynomial import Chebyshev
            >>> t = Chebyshev([1.0, 2.0, 3.0])
            >>> (t + t).coef
            array([2., 4., 6.])

        .. seealso::
            `numpy.polynomial package
            <https://numpy.org/doc/stable/reference/routines.polynomials.html>`_.
        """
        T.__init__(self, coef, domain, window, symbol)

    def __call__(self, op):
        """
        Thanks to Python :py:meth:`__call__` instance behaves like function.
        If op is a LazyLinOp, return polynomial of op applied to input array.
        If op is a :py:class:`numpy.polynomial.Polynomial`,
        :py:class:`numpy.polynomial.Chebyshev`,
        :py:class:`numpy.polynomial.Hermite`,
        :py:class:`numpy.polynomial.HermiteE`,
        :py:class:`numpy.polynomial.Laguerre` or
        :py:class:`numpy.polynomial.Legendre` instance, return a poly instance.

        Args:
            op: :py:class:`numpy.polynomial.Polynomial`,
            :py:class:`numpy.polynomial.Chebyshev`,
            :py:class:`numpy.polynomial.Hermite`,
            :py:class:`numpy.polynomial.HermiteE`,
            :py:class:`numpy.polynomial.Laguerre` or
            :py:class:`numpy.polynomial.Legendre` instance

        Raises:

        Examples:
            >>> from lazylinop import eye, islazylinop
            >>> from lazylinop.polynomial import Chebyshev
            >>> t = Chebyshev([1.0, 2.0, 3.0])
            >>> L = eye(3, 3, k=0)
            >>> islazylinop(t(L))
            True

        .. seealso::
            `numpy.polynomial package
            <https://numpy.org/doc/stable/reference/routines.polynomials.html>`_.
        """
        if islazylinop(op):
            return _chebval(op, self.coef)
        elif _is_lazylinop_poly(op):
            return _compose(self, op)
        else:
            raise TypeError('Unexpected op.')


class Hermite(H):
    """This class implements a Hermite "physicist" polynomial class derived
    from :py:class:`numpy.polynomial.Hermite` and so relies on NumPy polynomial
    package to manipulate polynomials.

    See :py:mod:`lazylinop.polynomial` for an introduction to implemented
    operations and their basic use.
    """

    def __init__(self, coef, domain: list = [-1.0, 1.0],
                 window: list = [-1.0, 1.0], symbol: str = 'x'):
        r"""Init instance of Hermite.

        Args:
            coef: list
                List of Hermite coefficients
                :math:`\lbrack c_0,c_1,\cdots,c_n\rbrack`.
                Polynomial of :py:class:`.LazyLinOp` ``L`` is:

                .. math::

                    \begin{equation}
                    p(L)=\sum_{i=0}^nc_iH_i(L)
                    \end{equation}

            .. domain: list, optional
                See `NumPy documentation <https://numpy.org/doc/stable/
                reference/generated/
                numpy.polynomial.hermite.Hermite.html#
                numpy.polynomial.hermite.Hermite>`_ for more details.
            .. window: list, optional
                See `NumPy documentation <https://numpy.org/doc/
                stable/reference/generated/
                numpy.polynomial.hermite.Hermite.html#
                numpy.polynomial.hermite.Hermite>`_ for more details.
            .. symbol: str, optional
                See `NumPy documentation <https://numpy.org/doc/
                stable/reference/generated/
                numpy.polynomial.hermite.Hermite.html#
                numpy.polynomial.hermite.Hermite>`_ for more details.

        Examples:
            >>> from lazylinop.polynomial import Hermite
            >>> h = Hermite([1.0, 2.0, 3.0])
            >>> (h + h).coef
            array([2., 4., 6.])

        .. seealso::
            `numpy.polynomial package
            <https://numpy.org/doc/stable/reference/routines.polynomials.html>`_.
        """
        H.__init__(self, coef, domain, window, symbol)

    def __call__(self, op):
        """
        Thanks to Python :py:meth:`__call__` instance behaves like function.
        If op is a LazyLinOp, return polynomial of op applied to input array.
        If op is a :py:class:`numpy.polynomial.Polynomial`,
        :py:class:`numpy.polynomial.Chebyshev`,
        :py:class:`numpy.polynomial.Hermite`,
        :py:class:`numpy.polynomial.HermiteE`,
        :py:class:`numpy.polynomial.Laguerre` or
        :py:class:`numpy.polynomial.Legendre` instance, return a poly instance.

        Args:
            op: LazyLinOp,
            :py:class:`numpy.polynomial.Polynomial`,
            :py:class:`numpy.polynomial.Chebyshev`,
            :py:class:`numpy.polynomial.Hermite`,
            :py:class:`numpy.polynomial.HermiteE`,
            :py:class:`numpy.polynomial.Laguerre` or
            :py:class:`numpy.polynomial.Legendre` instance

        Raises:

        Examples:
            >>> from lazylinop import eye, islazylinop
            >>> from lazylinop.polynomial import Hermite
            >>> h = Hermite([1.0, 2.0, 3.0])
            >>> L = eye(3, 3, k=0)
            >>> islazylinop(h(L))
            True

        .. seealso::
            `numpy.polynomial package
            <https://numpy.org/doc/stable/reference/routines.polynomials.html>`_.
        """
        if islazylinop(op):
            return _hermval(op, self.coef)
        elif _is_lazylinop_poly(op):
            return _compose(self, op)
        else:
            raise TypeError('Unexpected op.')


class HermiteE(HE):
    """This class implements a Hermite "probabilist" polynomial class derived
    from :py:class:`numpy.polynomial.HermiteE` and so relies on NumPy
    polynomial package to manipulate polynomials.

    See :py:mod:`lazylinop.polynomial` for an introduction to implemented
    operations and their basic use.
    """

    def __init__(self, coef, domain: list = [-1.0, 1.0],
                 window: list = [-1.0, 1.0], symbol: str = 'x'):
        r"""Init instance of HermiteE.

        Args:
            coef: list
                List of Hermite coefficients
                :math:`\lbrack c_0,c_1,\cdots,c_n\rbrack`.
                Polynomial of :py:class:`.LazyLinOp` ``L`` is:

                .. math::

                    \begin{equation}
                    p(L)=\sum_{i=0}^nc_iH_i(L)
                    \end{equation}

            .. domain: list, optional
                See `NumPy documentation <https://numpy.org/doc/stable/
                reference/generated/
                numpy.polynomial.hermite_e.HermiteE.html#
                numpy.polynomial.hermite_e.HermiteE>`_ for more details.
            .. window: list, optional
                See `NumPy documentation <https://numpy.org/doc/
                stable/reference/generated/
                numpy.polynomial.hermite_e.HermiteE.html#
                numpy.polynomial.hermite_e.HermiteE>`_ for more details.
            .. symbol: str, optional
                See `NumPy documentation <https://numpy.org/doc/
                stable/reference/generated/
                numpy.polynomial.hermite_e.HermiteE.html#
                numpy.polynomial.hermite_e.HermiteE>`_ for more details.

        Examples:
            >>> from lazylinop import eye, islazylinop
            >>> from lazylinop.polynomial import HermiteE
            >>> h = HermiteE([1.0, 2.0, 3.0])
            >>> (h + h).coef
            array([2., 4., 6.])

        .. seealso::
            `numpy.polynomial package
            <https://numpy.org/doc/stable/reference/routines.polynomials.html>`_.
        """
        HE.__init__(self, coef, domain, window, symbol)

    def __call__(self, op):
        """
        Thanks to Python :py:meth:`__call__` instance behaves like function.
        If op is a LazyLinOp, return polynomial of op applied to input array.
        If op is a :py:class:`numpy.polynomial.Polynomial`,
        :py:class:`numpy.polynomial.Chebyshev`,
        :py:class:`numpy.polynomial.Hermite`,
        :py:class:`numpy.polynomial.HermiteE`,
        :py:class:`numpy.polynomial.Laguerre` or
        :py:class:`numpy.polynomial.Legendre` instance, return a poly instance.

        Args:
            op: :py:class:`numpy.polynomial.Polynomial`,
            :py:class:`numpy.polynomial.Chebyshev`,
            :py:class:`numpy.polynomial.Hermite`,
            :py:class:`numpy.polynomial.HermiteE`,
            :py:class:`numpy.polynomial.Laguerre` or
            :py:class:`numpy.polynomial.Legendre` instance

        Raises:

        Examples:
            >>> from lazylinop import eye, islazylinop
            >>> from lazylinop.polynomial import HermiteE
            >>> h = HermiteE([1.0, 2.0, 3.0])
            >>> L = eye(3, 3, k=0)
            >>> islazylinop(h(L))
            True

        .. seealso::
            `numpy.polynomial package
            <https://numpy.org/doc/stable/reference/routines.polynomials.html>`_.
        """
        if islazylinop(op):
            return _hermval(op, self.coef, False)
        elif _is_lazylinop_poly(op):
            return _compose(self, op)
        else:
            raise TypeError('Unexpected op.')


class Laguerre(La):
    """This class implements a Laguerre polynomial class derived from
    :py:class:`numpy.polynomial.Laguerre` and so relies on NumPy polynomial
    package to manipulate polynomials.

    See :py:mod:`lazylinop.polynomial` for an introduction to implemented
    operations and their basic use.
    """

    def __init__(self, coef, domain: list = [-1.0, 1.0],
                 window: list = [-1.0, 1.0], symbol: str = 'x'):
        r"""Init instance of Laguerre.

        Args:
            coef: list
                List of Laguerre coefficients
                :math:`\lbrack c_0,c_1,\cdots,c_n\rbrack`.
                Polynomial of :py:class:`.LazyLinOp` ``L`` is:

                .. math::

                    \begin{equation}
                    p(L)=\sum_{i=0}^nc_iL_{a,i}(L)
                    \end{equation}

            .. domain: list, optional
                See `NumPy documentation <https://numpy.org/doc/stable/
                reference/generated/
                numpy.polynomial.laguerre.Laguerre.html#
                numpy.polynomial.laguerre.Laguerre>`_ for more details.
            .. window: list, optional
                See `NumPy documentation <https://numpy.org/doc/
                stable/reference/generated/
                numpy.polynomial.laguerre.Laguerre.html#
                numpy.polynomial.laguerre.Laguerre>`_ for more details.
            .. symbol: str, optional
                See `NumPy documentation <https://numpy.org/doc/
                stable/reference/generated/
                numpy.polynomial.laguerre.Laguerre.html#
                numpy.polynomial.laguerre.Laguerre>`_ for more details.

        Examples:
            >>> from lazylinop import eye, islazylinop
            >>> from lazylinop.polynomial import Laguerre
            >>> la = Laguerre([1.0, 2.0, 3.0])
            >>> (la + la).coef
            array([2., 4., 6.])
            >>> L = eye(3, 3, k=0)
            >>> islazylinop(la(L))
            True

        .. seealso::
            `numpy.polynomial package
            <https://numpy.org/doc/stable/reference/routines.polynomials.html>`_.
        """
        La.__init__(self, coef, domain, window, symbol)

    def __call__(self, op):
        """
        Thanks to Python :py:meth:`__call__` instance behaves like function.
        If op is a LazyLinOp, return polynomial of op applied to input array.
        If op is a :py:class:`numpy.polynomial.Polynomial`,
        :py:class:`numpy.polynomial.Chebyshev`,
        :py:class:`numpy.polynomial.Hermite`,
        :py:class:`numpy.polynomial.HermiteE`,
        :py:class:`numpy.polynomial.Laguerre` or
        :py:class:`numpy.polynomial.Legendre` instance, return a poly instance.

        Args:
            op: :py:class:`numpy.polynomial.Polynomial`,
            :py:class:`numpy.polynomial.Chebyshev`,
            :py:class:`numpy.polynomial.Hermite`,
            :py:class:`numpy.polynomial.HermiteE`,
            :py:class:`numpy.polynomial.Laguerre` or
            :py:class:`numpy.polynomial.Legendre` instance

        Raises:

        Examples:
            >>> from lazylinop import eye, islazylinop
            >>> from lazylinop.polynomial import Laguerre
            >>> la = Laguerre([1.0, 2.0, 3.0])
            >>> L = eye(3, 3, k=0)
            >>> islazylinop(la(L))
            True

        .. seealso::
            `numpy.polynomial package
            <https://numpy.org/doc/stable/reference/routines.polynomials.html>`_.
        """
        if islazylinop(op):
            return _lagval(op, self.coef)
        elif _is_lazylinop_poly(op):
            return _compose(self, op)
        else:
            raise TypeError('Unexpected op.')


class Legendre(Le):
    """This class implements a Legendre polynomial class derived from
    :py:class:`numpy.polynomial.Legendre` and so relies on NumPy polynomial
    package to manipulate polynomials.

    See :py:mod:`lazylinop.polynomial` for an introduction to implemented
    operations and their basic use.
    """

    def __init__(self, coef, domain: list = [-1.0, 1.0],
                 window: list = [-1.0, 1.0], symbol: str = 'x'):
        r"""Init instance of Legendre.

        Args:
            coef: list
                List of Legendre coefficients
                :math:`\lbrack c_0,c_1,\cdots,c_n\rbrack`.
                Polynomial of :py:class:`.LazyLinOp` ``L`` is:

                .. math::

                    \begin{equation}
                    p(L)=\sum_{i=0}^nc_iL_{e,i}(L)
                    \end{equation}

            .. domain: list, optional
                See `NumPy documentation <https://numpy.org/doc/stable/
                reference/generated/
                numpy.polynomial.legendre.Legendre.html#
                numpy.polynomial.legendre.Legendre>`_ for more details.
            .. window: list, optional
                See `NumPy documentation <https://numpy.org/doc/
                stable/reference/generated/
                numpy.polynomial.legendre.Legendre.html#
                numpy.polynomial.legendre.Legendre>`_ for more details.
            .. symbol: str, optional
                See `NumPy documentation <https://numpy.org/doc/
                stable/reference/generated/
                numpy.polynomial.legendre.Legendre.html#
                numpy.polynomial.legendre.Legendre>`_ for more details.

        Examples:
            >>> from lazylinop import eye, islazylinop
            >>> from lazylinop.polynomial import Legendre
            >>> le = Legendre([1.0, 2.0, 3.0])
            >>> (le + le).coef
            array([2., 4., 6.])
            >>> L = eye(3, 3, k=0)
            >>> islazylinop(le(L))
            True

        .. seealso::
            `numpy.polynomial package
            <https://numpy.org/doc/stable/reference/routines.polynomials.html>`_.
        """
        Le.__init__(self, coef, domain, window, symbol)

    def __call__(self, op):
        """
        Thanks to Python :py:meth:`__call__` instance behaves like function.
        If op is a LazyLinOp, return polynomial of op applied to input array.
        If op is a :py:class:`numpy.polynomial.Polynomial`,
        :py:class:`numpy.polynomial.Chebyshev`,
        :py:class:`numpy.polynomial.Hermite`,
        :py:class:`numpy.polynomial.HermiteE`,
        :py:class:`numpy.polynomial.Laguerre` or
        :py:class:`numpy.polynomial.Legendre` instance.

        Args:
            op: LazyLinOp,
            :py:class:`numpy.polynomial.Polynomial`,
            :py:class:`numpy.polynomial.Chebyshev`,
            :py:class:`numpy.polynomial.Hermite`,
            :py:class:`numpy.polynomial.HermiteE`,
            :py:class:`numpy.polynomial.Laguerre` or
            :py:class:`numpy.polynomial.Legendre` instance

        Raises:

        Examples:
            >>> from lazylinop import eye, islazylinop
            >>> from lazylinop.polynomial import Legendre
            >>> le = Legendre([1.0, 2.0, 3.0])
            >>> L = eye(3, 3, k=0)
            >>> islazylinop(le(L))
            True

        .. seealso::
            `numpy.polynomial package
            <https://numpy.org/doc/stable/reference/routines.polynomials.html>`_.
        """
        if islazylinop(op):
            return _legval(op, self.coef)
        elif _is_lazylinop_poly(op):
            return _compose(self, op)
        else:
            raise TypeError('Unexpected op.')


def _polyval(L, c):
    r"""Constructs a :py:class:`.LazyLinOp` polynomial ``P(L)`` of linear
    operator ``L``.

    ``P(L)`` is equal to :math:`c_0Id+c_1L^1+\cdots +c_nL^n`.

    The Horner's method is used to compute ``P(L) @ X``.

    ``Y = P(L) @ X`` shape is ``(L.shape[0], X.shape[1])``.

    Args:
        L: LazyLinOp
            Linear operator (matrix representation must be square).
        c: 1d array
            List of polynomial coefficients.
            If the size of the 1d array is n + 1 then the largest power of the
            polynomial is n.

    Returns:
        LazyLinOp

    Raises:
        Exception
            Matrix representation of L is not square.
        Exception
            List of coefficients has zero size.
        Exception
            coef must be a 1d array.

    Examples:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> x = np.random.randn(3)
        >>> L = lz.eye(3, 3, k=0)
        >>> y = lz.polynomial._polyval(L, [1.0, 2.0, 3.0]) @ x
        >>> np.allclose(6.0 * x, y)
        True

    .. seealso::
        - `NumPy polynomial class <https://docs.scipy.org/doc//numpy-1.9.3/
          reference/generated/numpy.polynomial.polynomial.polyval.html>`_.
        - :py:func:`polyvalfromroots`.
    """

    if L.shape[0] != L.shape[1]:
        raise Exception("Matrix representation of L is not square.")

    c = np.asarray(c)

    if c.ndim != 1:
        raise Exception("coef must be a 1d array.")

    if c.shape[0] == 0:
        raise Exception("List of coefficients has zero size.")

    def _matmat(L, x, c):
        # x can't be a LazyLinOp here because it's handle before in
        # LazyLinOp.__matmul__
        # x is always 2d
        out = (
            x * c[-1] if c[-1] != 0
            else np.zeros(x.shape,
                          dtype=np.promote_types(c.dtype, x.dtype))
        )
        for i in range(len(c) - 2, -1, -1):
            out = L @ out
            if c[i] != 0:
                out += x * c[i]
        return out

    return LazyLinOp(
        shape=L.shape,
        matmat=lambda x: _matmat(L, x, c),
        rmatmat=lambda x: _matmat(L.T.conj(), x, c)
    )


def _polyvalfromroots(L, r):
    r"""Constructs a :py:class:`.LazyLinOp` polynomial
    ``P(L)`` of linear operator ``L`` from the polynomial roots.

    ``P(L)`` is equal to :math:`(L - r_0Id)(L - r_1)\cdots (L - r_nId)`.

    ``Y = P(L) @ X`` shape is ``(L.shape[0], X.shape[1])``.

    Args:
        L: LazyLinOp
            Linear operator (matrix representation must be square).
        r: 1d array
            List of polynomial roots.

    Returns:
        LazyLinOp

    Raises:
        Exception
            Matrix representation of L is not square.
        Exception
            List of roots has zero size.
        Exception
            roots must be a 1d array.

    Examples:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> x = np.random.randn(3)
        >>> L = lz.eye(3, 3, k=0)
        >>> y = lz.polynomial._polyvalfromroots(L, [1.0, 1.0, 1.0]) @ x
        >>> np.allclose(0.0 * x, y)
        True

    .. seealso::
        - `NumPy polyvalfromroots <https://docs.scipy.org/doc/
          numpy-1.9.3/reference/generated/numpy.polynomial.polynomial.
          polyvalfromroots.html>`_.
        - :py:func:`polyval`.
    """

    if L.shape[0] != L.shape[1]:
        raise Exception("Matrix representation of L is not square.")

    r = np.asarray(r)

    if r.ndim != 1:
        raise Exception("roots must be a 1d array.")

    R = r.shape[0]
    if R == 0:
        raise Exception("List of roots has zero size.")

    def _matmat(roots, L, x):
        # x is always 2d
        Lx = L @ x if roots[-1] == 0 else (L @ x - roots[-1] * x)
        nr = len(roots)

        for i in range(nr - 2, -1, -1):
            r = roots[i]
            Lx = L @ Lx if r == 0.0 else (L @ Lx - r * Lx)

        return Lx

    return LazyLinOp(
        shape=L.shape,
        matmat=lambda x: _matmat(r, L, x),
        rmatmat=lambda x: _matmat(r, L.T.conj(), x)
    )


def _chebval(L, c):
    r"""Constructs a :py:class:`.LazyLinOp` Chebysev polynomial ``P(L)`` of
    linear operator ``L``.

    ``P(L)`` is equal to :math:`c_0Id+c_1T_1(L)+\cdots +c_nT_n(L)`.

    The k-th Chebyshev polynomial can be computed by recurrence:

    .. math::

        \begin{eqnarray}
        T_0(L) &=& 1\\
        T_1(L) &=& L\\
        T_{k+1}(L) &=& 2LT_k(L) - T_{k-1}(L)
        \end{eqnarray}

    The Clenshaw's method is used to compute ``P(L) @ X``.

    ``Y = P(L) @ X`` shape is ``(L.shape[0], X.shape[1])``.


    Args:
        L: LazyLinOp
            Linear operator (matrix representation must be square).
        c: 1d array
            List of Chebyshev polynomial(s) coefficients.
            If the size of the 1d array is n + 1 then the largest power of the
            polynomial is n.

    Returns:
        LazyLinOp

    Raises:
        Exception
            Matrix representation of L is not square.
        Exception
            List of coefficients has zero size.
        Exception
            coef must be a 1d array.

    Examples:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> x = np.random.randn(3)
        >>> L = lz.eye(3, 3, k=0)
        >>> y = lz.polynomial._chebval(L, [1.0, 2.0, 3.0]) @ x
        >>> np.allclose(6.0 * x, y)
        True

    .. seealso::
        - `Wikipedia <https://en.wikipedia.org/wiki/Chebyshev_polynomials>`_,
        - `Polynomial magic web page
          <https://francisbach.com/chebyshev-polynomials/>`_,
        - `NumPy polynomial class <https://docs.scipy.org/doc//numpy-1.9.3/
          reference/generated/numpy.polynomial.chebyshev.chebval.html>`_.
    """

    if L.shape[0] != L.shape[1]:
        raise Exception("Matrix representation of L is not square.")

    c = np.asarray(c)

    if c.shape[0] == 0:
        raise Exception("List of coefficients has zero size.")

    if c.ndim != 1:
        raise Exception("coef must be a 1d array.")

    clenshaw_funcs = [lambda k, L, bk: L @ (2 * bk),  # alpha(k)
                      lambda k: 1,  # beta(k)
                      lambda L, bk: L @ bk]  # phi1(L)

    return LazyLinOp(
        shape=L.shape,
        matmat=lambda x: _matmat_clenshaw(L, c, x, *clenshaw_funcs),
        rmatmat=lambda x: _matmat_clenshaw(L.T.conj(), c, x, *clenshaw_funcs)
    )


def _hermval(L, c, physicist: bool = True):
    r"""Constructs a :py:class:`.LazyLinOp` Hermite (physicist or
    probabilistic) polynomial ``P(L)`` of linear operator ``L``.

    ``P(L)`` is equal to :math:`c_0Id+c_1H_1(L)+\cdots +c_nH_n(L)`.

    The k-th Hermite (physicist) polynomial can be computed by recurrence:

    .. math::

        \begin{eqnarray}
        H_0(L) &=& Id\\
        H_1(L) &=& 2L\\
        H_{k+1}(L) &=& 2LH_k(L) - 2kH_{k-1}(L)
        \end{eqnarray}

    The k-th Hermite (probabilist) polynomial can be computed by recurrence:

    .. math::

        \begin{eqnarray}
        H_0(L) &=& Id\\
        H_1(L) &=& L\\
        H_{k+1}(L) &=& LH_k(L) - kH_{k-1}(L)
        \end{eqnarray}

    The Clenshaw's method is used to compute ``P(L) @ X``.

    ``Y = P(L) @ X`` shape is ``(L.shape[0], X.shape[1])``.


    Args:
        L: LazyLinOp
            Linear operator (matrix representation must be square).
        c: 1d array
            List of Hermite (physicist) polynomial(s) coefficients.
            If the size of the 1d array is n + 1 then the largest power of the
            polynomial is n.
        physicist: bool, optional
            If ``True`` (default) construct Hermite "physicist" polynomial.
            If ``False`` construct Hermite "probabilistic" polynomial.

    Returns:
        LazyLinOp

    Raises:
        Exception
            Matrix representation of L is not square.
        Exception
            List of coefficients has zero size.
        Exception
            coef must be a 1d array.

    Examples:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> x = np.array([1.0, 0.0, 0.0])
        >>> L = lz.eye(3, 3, k=0)
        >>> y = lz.polynomial._hermval(L, [1.0, 2.0, 3.0]) @ x
        >>> z = np.polynomial.hermite.hermval(x[0], [1.0, 2.0, 3.0])
        >>> np.allclose(y[0], z)
        True

    .. seealso::
        - `Wikipedia <https://en.wikipedia.org/wiki/Hermite_polynomials>`_,
        - `NumPy polynomial class <https://docs.scipy.org/doc//numpy-1.9.3/
          reference/generated/numpy.polynomial.hermite.hermval.html>`_.
    """

    if L.shape[0] != L.shape[1]:
        raise Exception("Matrix representation of L is not square.")

    c = np.asarray(c)

    if c.shape[0] == 0:
        raise Exception("List of coefficients has zero size.")

    if c.ndim != 1:
        raise Exception("coef must be a 1d array.")

    if physicist:
        clenshaw_funcs = [
            lambda k, L, bk: L @ (2 * bk),  # alpha(k)
            lambda k: 2 * k,  # beta(k)
            lambda L, bk: L @ (2 * bk)  # phi1(L)
        ]
    else:
        clenshaw_funcs = [
            lambda k, L, bk: L @ bk,  # alpha(k)
            lambda k: k,  # beta(k)
            lambda L, bk: L @ bk  # phi1(L)
        ]

    return LazyLinOp(
        shape=L.shape,
        matmat=lambda x: _matmat_clenshaw(L, c, x, *clenshaw_funcs),
        rmatmat=lambda x: _matmat_clenshaw(L.T.conj(), c, x, *clenshaw_funcs)
    )


def _lagval(L, c):
    r"""Constructs a :py:class:`.LazyLinOp` Laguerre polynomial ``P(L)``
    of linear operator ``L``.

    ``P(L)`` is equal to :math:`c_0Id+c_1L_{a,1}(L)+\cdots+c_nL_{a,n}(L)`.

    The k-th Laguerre polynomial can be computed by recurrence:

    .. math::

        \begin{eqnarray}
        L_{a,0}(L) &=& Id\\
        L_{a,1}(L) &=& Id - L\\
        L_{a,k+1}(L) &=& \frac{(2k + 1 - L)L_{a,k}(L) - kL_{a,k-1}(L)}{k + 1}
        \end{eqnarray}

    The Clenshaw's method is used to compute ``P(L) @ X``.

    ``Y = P(L) @ X`` shape is ``(L.shape[0], X.shape[1])``.


    Args:
        L: LazyLinOp
            Linear operator (matrix representation must be square).
        c: 1d array
            List of Laguerre polynomial(s) coefficients.
            If the size of the 1d array is n + 1 then the largest power
            of the polynomial is n.

    Returns:
        LazyLinOp

    Raises:
        Exception
            Matrix representation of L is not square.
        Exception
            List of coefficients has zero size.
        Exception
            coef must be a 1d array.

    Examples:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> x = np.array([1.0, 0.0, 0.0])
        >>> L = lz.eye(3, 3, k=0)
        >>> y = lz.polynomial._lagval(L, [1.0, 2.0, 3.0]) @ x
        >>> z = np.polynomial.laguerre.lagval(x[0], [1.0, 2.0, 3.0])
        >>> np.allclose(y[0], z)
        True

    .. seealso::
        - `Wikipedia <https://en.wikipedia.org/wiki/Laguerre_polynomials>`_,
        - `NumPy polynomial class <https://docs.scipy.org/doc//numpy-1.9.3/
          reference/generated/numpy.polynomial.laguerre.lagval.html>`_.
    """

    if L.shape[0] != L.shape[1]:
        raise Exception("Matrix representation of L is not square.")

    c = np.asarray(c)

    if c.ndim != 1:
        raise Exception("coef must be a 1d array.")

    if c.shape[0] == 0:
        raise Exception("List of coefficients has zero size.")

    clenshaw_funcs = [
        lambda k, L, bk: ((2 * k + 1) * bk - L @ bk) / (k + 1),  # alpha(k)
        lambda k: k / (k + 1),  # beta(k)
        lambda L, bk: bk - L @ bk  # phi1(L)
                     ]

    return LazyLinOp(
        shape=L.shape,
        matmat=lambda x: _matmat_clenshaw(L, c, x, *clenshaw_funcs),
        rmatmat=lambda x: _matmat_clenshaw(L.T.conj(), c, x, *clenshaw_funcs)
    )


def _legval(L, c):
    r"""Constructs a :py:class:`.LazyLinOp` Legendre polynomial ``P(L)``
    of linear operator ``L``.

    ``P(L)`` is equal to :math:`c_0Id+c_1L_{e,1}(L)+\cdots+c_nL_{e,n}(L)`.

    The k-th Legendre polynomial can be computed by recurrence:

    .. math::

        \begin{eqnarray}
        L_{e,0}(L) &=& Id\\
        L_{e,1}(L) &=& L\\
        L_{e,k+1}(L) &=& \frac{(2k + 1)LL_{e,k}(L) - kL_{e,k-1}(L)}{k + 1}
        \end{eqnarray}

    The Clenshaw's method is used to compute ``P(L) @ X``.

    ``Y = P(L) @ X`` shape is ``(L.shape[0], X.shape[1])``.


    Args:
        L: LazyLinOp
            Linear operator (matrix representation must be square).
        c: 1d array
            List of Legendre polynomial(s) coefficients.
            If the size of the 1d array is n + 1 then the largest power
            of the polynomial is n.

    Returns:
        LazyLinOp

    Raises:
        Exception
            Matrix representation of L is not square.
        Exception
            List of coefficients has zero size.
        Exception
            coef must be a 1d array.

    Examples:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> x = np.array([1.0, 0.0, 0.0])
        >>> L = lz.eye(3, 3, k=0)
        >>> y = lz.polynomial._legval(L, [1.0, 2.0, 3.0]) @ x
        >>> z = np.polynomial.legendre.legval(x[0], [1.0, 2.0, 3.0])
        >>> np.allclose(y[0], z)
        True

    .. seealso::
        - `Wikipedia <https://en.wikipedia.org/wiki/Legendre_polynomials>`_,
        - `NumPy polynomial class <https://docs.scipy.org/doc//numpy-1.9.3/
          reference/generated/numpy.polynomial.legendre.legval.html>`_.
    """

    if L.shape[0] != L.shape[1]:
        raise Exception("Matrix representation of L is not square.")

    c = np.asarray(c)

    if c.ndim != 1:
        raise Exception("coef must be a 1d array.")

    if c.shape[0] == 0:
        raise Exception("List of coefficients has zero size.")

    clenshaw_funcs = [
        lambda k, L, bk: L @ ((2 * k + 1) / (k + 1) * bk),  # alpha(k)
        lambda k: k / (k + 1),  # beta(k)
        lambda L, bk: L @ bk  # phi1(L)
    ]

    return LazyLinOp(
        shape=L.shape,
        matmat=lambda x: _matmat_clenshaw(L, c, x, *clenshaw_funcs),
        rmatmat=lambda x: _matmat_clenshaw(L.T.conj(), c, x, *clenshaw_funcs)
    )


def _matmat_clenshaw(L, c, x, alpha_func, beta_func, phi1_func):
    """
    Clenshaw evaluation of P(L) @ x for any kind of polynomial.

    Args:
        L: (:py:class:`.LazyLinOp`)
            linear operator
        c: (``np.ndarray``)
            coefficients of the polynomial as a 1d-array.
        x: (``np.ndarray``)
            The array to multiply P(L) by.
        alpha_func:
            The function alpha(k, L, bk') that computes alpha(k, L) @ bk'
            (alpha(k, L) is generally alpha(k) * L except for Laguerre).
        beta_func:
            The function (- beta(k)).
        phi1_func:
            The function phi1(L, bk) that computes phi1(L) @ bk.
    """
    # x is always 2d
    if c.shape[0] == 1:
        return c[0] * x
    elif c.shape[0] == 2:
        y = c[0] * x + c[1] * phi1_func(L, x)
        return y
    else:
        # Clenshaw algorithm
        # alpha_k = alpha_func(k) * L
        # beta_k  = beta_func(k)
        # phi0 = eye(N, N)
        # phi1 = L
        # phi_{k + 1} = alpha_k * phi_k + beta_k * phi_{k - 1}
        # b_k = c_k + alpha_k * b_{k + 1} + beta_{k + 1} * b_{k + 2}
        # p(L) = phi_0 * c_0 + phi_1 * b_1 + beta_1 * phi_0 * b_2
        b2 = c[-1] * x
        b1 = c[-2] * x + alpha_func(len(c) - 2, L, b2)
        for k in range(c.shape[0] - 3, 0, -1):
            bk = (
                c[k] * x +
                alpha_func(k, L, b1) -
                ((beta_func(k + 1) * b2) if beta_func(k + 1) != 1 else b2)
            )
            b2 = b1
            b1 = bk
        # phi0 is always 1/Id
        y = c[0] * x + phi1_func(L, b1) - (
            (beta_func(1) * b2) if beta_func(1) != 1 else b2)
        return y


def power(L, n):
    r"""Constructs the n-th power :math:`L^n` of linear operator :math:`L`.
    Matrix representation of :math:`L` must be square.
    :octicon:`alert-fill;1em;sd-text-danger` In some cases
    :code:`power(L,n) @ x` can be least efficient than
    :code:`M=np.power(L.toarray()) @ x`.

    .. note::
        It is equivalent to create an instance from
        :py:func:`xpoly(coef, kind)` such that only n-th coefficient
        is equal to one while the others are equal to zero.

    Args:
        L: LazyLinOp
            Linear operator (e.g. a :py:class:`.LazyLinOp`).
            Matrix representation must be square.
        n: int
            Raise the linear operator to degree n.
            If n is zero, return identity matrix.

    Returns:
        LazyLinOp :math:`L^n`.

    Raises:
        ValueError
            n must be > 0.
        Exception
            Matrix representation of L is not square.

    Examples:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> L = lz.polynomial.power(lz.eye(3, 3, k=0), 3)
        >>> x = np.full(3, 1.0)
        >>> np.allclose(L @ x, x)
        True
        >>> L = lz.polynomial.power(lz.eye(3, 3, k=1), 3)
        >>> # Note that L is in fact zero (nilpotent matrix)
        >>> x = np.full(3, 1.0)
        >>> np.allclose(L @ x, np.zeros(3, dtype=np.float64))
        True

    .. seealso::
        `NumPy power function
        <https://numpy.org/doc/stable/reference/generated/numpy.power.html>`_.
    """
    return aslazylinop(L)**n


# if __name__ == '__main__':
#     import doctest
#     doctest.testmod()
