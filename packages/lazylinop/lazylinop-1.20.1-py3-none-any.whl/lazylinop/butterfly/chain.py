# -*- coding: utf-8 -*-

from lazylinop.butterfly.GB_param_generate import DebflyGen
import numpy as np
from typing import Union
from sympy import factorint, isprime
from warnings import warn


class Chain():

    def __init__(self, ks_patterns: Union[list, tuple]):
        r"""
        A ``Chain`` instance is built by calling the
        constructor ``Chain(ks_patterns)``.

        Args:
            ks_patterns: ``list``
                List of tuples $((a_l,~b_l,~c_l,~d_l))_{l=1}^n$
                each being called a pattern.
                The tuples $((a_l,~b_l,~c_l,~d_l))_{l=1}^n$ must
                satisfy $a_lc_ld_l=a_{l+1}b_{l+1}d_{l+1}$.

        Attributes:
            ks_patterns: ``list``
                List of patterns $(a_i,~b_i,~c_i,~d_i)$.
            n_patterns: ``int``
                Equal to ``len(ks_patterns)``.
            shape: ``tuple``
                ``shape`` is equal to $(a_1b_1d_1,~a_nc_nd_n)$
                with ``n = n_patterns``.
            chainable: ``bool``
                ``True`` if for each $l$:

                - and $a_l$ divides $a_{l+1}$
                - and $d_{l+1}$ divides $d_l$
                See :ref:`[1] <chain>` for more details.

        Return:
            ``chain`` with ``ks_patterns``, ``n_patterns``, ``shape``
            and ``chainable`` attributes.

        Examples:
            >>> from lazylinop.butterfly import Chain
            >>> chain = Chain([(2, 1, 1, 2), (2, 1, 1, 2)])
            >>> chain.ks_patterns
            [(2, 1, 1, 2), (2, 1, 1, 2)]
            >>> # Concatenation of two chains.
            >>> chain1 = Chain([(1, 2, 2, 4)])
            >>> chain2 = Chain([(4, 2, 2, 1)])
            >>> chain = chain1 @ chain2
            >>> chain.shape
            (8, 8)
            >>> chain.n_patterns
            2
            >>> chain.ks_patterns
            [(1, 2, 2, 4), (4, 2, 2, 1)]

        .. _chain:

            **References:**

            [1] Butterfly Factorization with Error Guarantees.
            L\u00E9on Zheng, Quoc-Tung Le, Elisa Riccietti,
            and R\u00E9mi Gribonval
            https://hal.science/hal-04763712v1/document
        """
        if not isinstance(ks_patterns, (list, tuple)):
            raise TypeError("ks_patterns must be a list or a tuple of tuples.")
        ks_shapes = []
        for k in ks_patterns:
            if not isinstance(k, tuple):
                raise TypeError(
                    "Each element of ks_patterns must be a tuples.")
            a, b, c, d = k
            ks_shapes.append((a * b * d, a * c * d))
        a, b, c, d = ks_patterns[0]
        out = a * b * d
        a, b, c, d = ks_patterns[-1]
        self.__shape = (out, a * c * d)
        self.__ks_shapes = ks_shapes
        self.__n_patterns = len(ks_patterns)
        self.__ks_patterns = ks_patterns
        # Keep track of the rank.
        self.__abcdpq = []
        for k in ks_patterns:
            self.__abcdpq.append((k[0], k[1], k[2], k[3], 1, 1))
        self.__valid = self._is_valid()
        if not self.__valid:
            raise Exception(
                "chain is not valid:"
                + " a_l*c_l*d_l ! = a_{l+1}*c_{l+1}*d_{l+1}.")
        self.__chainable = self._is_chainable()
        self.__rank = 1
        # self.__chain_type = 'custom'

    @property
    def shape(self):
        return self.__shape

    @shape.setter
    def shape(self, value):
        warn("You cannot modify self.shape.")

    @shape.deleter
    def shape(self):
        pass

    @property
    def ks_shapes(self):
        return self.__ks_shapes.copy()

    @ks_shapes.setter
    def ks_shapes(self, value):
        warn("You cannot modify self.ks_shapes.")

    @ks_shapes.deleter
    def ks_shapes(self):
        pass

    @property
    def n_patterns(self):
        return self.__n_patterns

    @n_patterns.setter
    def n_patterns(self, value):
        warn("You cannot modify self.n_patterns.")

    @n_patterns.deleter
    def n_patterns(self):
        pass

    @property
    def ks_patterns(self):
        return self.__ks_patterns.copy()

    @ks_patterns.setter
    def ks_patterns(self, value):
        warn("You cannot modify self.ks_patterns.")

    @ks_patterns.deleter
    def ks_patterns(self):
        pass

    @property
    def abcdpq(self):
        return self.__abcdpq.copy()

    @abcdpq.setter
    def abcdpq(self, value):
        warn("You cannot modify self.abcdpq.")

    @abcdpq.deleter
    def abcdpq(self):
        pass

    @property
    def valid(self):
        return self.__valid

    @valid.setter
    def valid(self, value):
        warn("You cannot modify self.valid.")

    @valid.deleter
    def valid(self):
        pass

    @property
    def chainable(self):
        return self.__chainable

    @chainable.setter
    def chainable(self, value):
        warn("You cannot modify self.chainable.")

    @chainable.deleter
    def chainable(self):
        pass

    @property
    def rank(self):
        return self.__rank

    @rank.setter
    def rank(self, value):
        warn("You cannot modify self.rank.")

    @rank.deleter
    def rank(self):
        pass

    # @property
    # def chain_type(self):
    #     return self.__chain_type
    # @chain_type.setter
    # def chain_type(self, value):
    #     pass
    # @chain_type.deleter
    # def chain_type(self):
    #     pass

    def _is_valid(self):
        r"""
        Check if ``self`` is valid.
        The following conditions must be true:

        - $M=a_0b_0d_0$
        - $a_lc_ld_l=a_{l+1}c_{l+1}d_{l+1}$
        - $N=a_nc_nd_n$
        where $\left(M,~N\right)$ is the shape of the matrix.
        """
        # a_1 * b_1 * d_1 must be equal to the number
        # of rows of the input matrix.
        a, b, c, d = self.ks_patterns[0]
        if a * b * d != self.shape[0]:
            return False
        # a_F * c_F * d_F must be equal to the number
        # of columns of the input matrix.
        F = self.n_patterns
        a, b, c, d = self.ks_patterns[F - 1]
        if a * c * d != self.shape[1]:
            return False
        # Number of columns of the current factor must
        # be equal to the number of rows of the next factor.
        for i in range(F - 1):
            a, b, c, d = self.ks_patterns[i]
            col = a * c * d
            a, b, c, d = self.ks_patterns[i + 1]
            row = a * b * d
            if col != row:
                return False
        return True

    def _is_chainable(self):
        r"""
        Check if ``self`` is chainable.
        The following conditions must be true:

        - $a_l$ divides $a_{l+1}$
        - $d_{l+1}$ divides $d_l$
        See [1] for more details.

        References:
            [1] Butterfly Factorization with Error Guarantees.
            Léon Zheng, Quoc-Tung Le, Elisa Riccietti, and Rémi Gribonval
            https://hal.science/hal-04763712v1/document
        """
        F = self.n_patterns
        for i in range(F - 1):
            a1, b1, c1, d1 = self.ks_patterns[i]
            a2, b2, c2, d2 = self.ks_patterns[i + 1]
            if a2 % a1 != 0 or d1 % d2 != 0:
                return False
        return True

    def mem(self, dtype: str):
        r"""
        Return the memory in bytes of the ``ks_values`` of
        dtype ``dtype`` to be created corresponding to ``self``.

        Args:
            dtype: ``str``
                dtype of the ``ks_values``.

        Examples:
            >>> import numpy as np
            >>> from lazylinop.butterfly import Chain
            >>> sd_chain = Chain.square_dyadic((32, 32))
            >>> sd_chain.ks_patterns
            [(1, 2, 2, 16), (2, 2, 2, 8), (4, 2, 2, 4), (8, 2, 2, 2), (16, 2, 2, 1)]
            >>> sd_chain.mem(np.float32)
            1280
            >>> chain = Chain.monarch((32, 32))
            >>> chain.ks_patterns
            [(1, 4, 4, 8), (4, 8, 8, 1)]
            >>> chain.mem(np.float32)
            1536
        """
        F = self.n_patterns
        mem = 0
        _bytes = np.ones((1, 1), dtype=dtype).dtype.itemsize
        for i in range(F):
            a, b, c, d = self.ks_patterns[i]
            mem += a * b * c * d * _bytes
        return mem

    def fuse(self, i: int):
        r"""
        Fuse ``self.ks_patterns[i]`` $(a_i,~b_i,~c_i,~d_i)$
        with ``self.ks_patterns[i + 1]`` $(a_{i+1},~b_{i+1},~c_{i+1},~d_{i+1})$
        and return a new chain ``chain``.
        The length of ``chain`` is ``self.ns_patterns - 1``.
        The value of ``chain.ks_patterns[i]`` is
        $\left(a_i,~\frac{b_id_i}{d_{i+1}},~\frac{a_{i+1}c_{i+1}}{a_i},~d_{i+1}\right)$.

        Args:
            i: ``int``
                Fuse pattern $i$ with pattern $i+1$.

        Returns:
            A new instance of :class:`Chain` of length ``self.n_patterns - 1``.
        """
        if i >= self.n_patterns:
            raise ValueError("i must be < self.n_patterns.")
        a1, b1, c1, d1 = self.ks_patterns[i]
        a2, b2, c2, d2 = self.ks_patterns[i + 1]
        n = self.n_patterns - 1
        ks_patterns = [None] * n
        # Before the fuse.
        for j in range(i):
            ks_patterns[j] = self.ks_patterns[j]
        # Fuse.
        ks_patterns[i] = (a1, (b1 * d1) // d2, (a2 * c2) // a1, d2)
        # After the fuse.
        for j in range(i + 1, n):
            ks_patterns[j] = self.ks_patterns[j + 1]
        return Chain(ks_patterns)

    def __repr__(self):
        return (
            f"n_patterns={self.n_patterns}\n" +
            f"ks_patterns={self.ks_patterns}\n" +
            f"ks_shapes={self.ks_shapes}\n" +
            f"shape={self.shape}\n" +
            f"chain is valid={self.valid}\n" +
            f"chain is chainable={self.chainable}\n" +
            f"memory(float32)={self.mem(np.float32)} bytes"
        )

    def plot(self, name: str = None):
        """
        Plot ``self.ks_patterns``.
        The colors are randomly chosen.
        Matplotlib package must be installed.

        Args:
            name: ``str``
                Save the plot in both PNG file ``name + '.png'``
                and SVG file ``name + '.svg'``.
                Default value is ``None`` (it only draws
                the ``self.ks_patterns``).

        Examples:
            >>> from lazylinop.butterfly import Chain
            >>> sq_chain = Chain.square_dyadic((32, 32))
            >>> sq_chain.plot("square_dyadic")
            >>> chain = Chain.monarch((32, 32))
            >>> chain.plot("monarch")
        """

        import matplotlib
        import matplotlib.pyplot as plt
        import matplotlib.colors as clr
        from matplotlib.patches import Rectangle
        from matplotlib.collections import PatchCollection
        plt.rcParams.update({"font.size": 16})
        plt.rcParams.update({"lines.linewidth": 8})
        plt.rcParams.update({"lines.markersize": 6})
        # plt.rcParams.update({"legend.fontsize": 4})

        # cmap = plt.get_cmap("Reds")
        cmap = plt.get_cmap("rainbow")

        n = self.n_patterns
        # # Use prime factorization to determine
        # # the size of the grid.
        # nf = []
        # tmp = factorint(n)
        # for k in tmp.keys():
        #     nf.extend([int(k)] * tmp[k])
        # st = []
        # for i in range(len(nf)):
        #     s = int(np.prod(nf[:i]))
        #     t = int(np.prod(nf[i:len(nf)]))
        #     st.append((s, t))
        # diff = n
        # for i, j in st:
        #     if abs(i - j) < diff:
        #         s, t = i, j
        #         diff = abs(i - j)
        # if s < t:
        #     s, t = t, s
        s, t = n, 1
        X, Y = 0, 0
        for k in self.ks_patterns:
            a, b, c, d = k
            X += a * c * d + 1
            Y = max(Y, a * b * d)

        title = ""
        px = 1 / plt.rcParams['figure.dpi']
        # fig = plt.figure("draw", figsize=(640 * px, 480 * px))
        # plt.gca().set_aspect('equal')
        fig = plt.figure("draw", figsize=(s * 250 * px, t * 250 * px))
        abox = [0.05, 0.01, 0.9, 0.98]
        ax = fig.add_axes(
            abox,
            xlabel="",
            ylabel="",
            title=title,
            xlim=(0, X),
            ylim=(0, t * Y),
            xscale="linear",
            yscale="linear",
        )
        ax.set_aspect('equal')
        plt.axis('off')

        # Loop over the patterns.
        cum = 0
        for p in range(s):
            for q in range(t):
                if p * t + q >= n:
                    break
                a, b, c, d = self.ks_patterns[p * t + q]
                x, y = a * c * d, a * b * d
                ax.text(cum + x, (t - q) * Y,
                        s=f"({a}, {b}, {c}, {d})", ha='right', va='top')
                ax.text(cum + x, (t - q) * Y - y,
                        s=f"({a * b * d}, {a * c * d})",
                        ha='right', va='bottom')
                # Borders
                pc = PatchCollection([Rectangle((cum, (t - q) * Y - y), x, y)],
                                     facecolor='white',
                                     alpha=1.0, edgecolor='black')
                ax.add_collection(pc)
                # Support
                rs, vs = [], []
                for i in range(a):
                    for j in range(b):
                        for k in range(c):
                            for l in range(d):
                                row = i * b * d + j * d + l
                                col = i * c * d + k * d + l
                                rs.append(Rectangle(
                                    (cum + col, (t - q) * Y - row - 1), 1, 1))
                                vs.append(np.random.rand())
                pc = PatchCollection(rs, facecolor=cmap(vs),
                                     alpha=1.0)  # , edgecolor='black')
                ax.add_collection(pc)
                cum += x + 1

        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        if name is None:
            plt.show()
        else:
            plt.savefig(f"{name}.png", dpi='figure',
                        transparent=True, bbox_inches='tight')
            plt.savefig(f"{name}.svg", dpi='figure',
                        transparent=True, bbox_inches='tight')
            fig.clf()
            plt.close("draw")

    @classmethod
    def square_dyadic(cls, shape):
        r"""
        Build a square-dyadic chain from shape.

        ``shape`` must satisfy ``shape[0] = shape[1] = N``
        with $N=2^n$ a power of two.
        Number of ``ks_patterns`` is equal to $n$.
        The l-th pattern is given by
        ``(2 ** (l - 1), 2, 2, shape[0] // 2 ** l)`` where
        ``1 <= l <= n``.

        We can draw the square-dyadic decomposition for $N=16$:

        .. image:: _static/square_dyadic.svg

        using:

        .. code-block:: python

            sq_chain = Chain.square_dyadic((16, 16))
            sq_chain.plot()

        Args:
            shape: ``tuple``
                Shape of the input matrix must be $(N,~N)$ with $N=2^n$.
        """
        m, n = shape
        if m != n:
            raise Exception("Matrix must be square shape[0]=shape[1].")
        ok = ((m & (m - 1)) == 0) and m > 0
        ok = ok and (((n & (n - 1)) == 0) and n > 0)
        if not ok:
            raise Exception("shape of the matrix must be power of two.")
        n_patterns = int(np.log2(m))
        ks_patterns = []
        for i in range(1, n_patterns + 1):
            ks_patterns.append((2 ** (i - 1), 2, 2, m // 2 ** i))
        tmp = cls(ks_patterns)
        # tmp.chain_type = 'square dyadic'
        return tmp

    @classmethod
    def monarch(cls, shape, p: int = None, q: int = None):
        r"""
        Build a Monarch chain
        $((1,~p,~q,~\frac{M}{p}),~(q,~\frac{M}{p},~\frac{N}{q},~1))$
        from shape.
        $p$ must divide $M$ and $q$ must divide $N$.
        See :ref:`[1] <monarch>` for more details.

        Args:
            shape: ``tuple``
                Shape of the input matrix $(M,~N)$.
                $M$ and $N$ must not be prime numbers.
            p, q: ``int``, optional
                $p$ must divide $M$ and $q$ must divide $N$.
                If ``p`` (resp. ``q``) is ``None``,
                ``p`` (resp. ``q``) is chosen such $p\simeq\sqrt{m}$
                (resp. $q\simeq\sqrt{n}$).

        Examples:
            >>> from lazylinop.butterfly.chain import Chain
            >>> M, N = 21, 16
            >>> chain = Chain.monarch((M, N))
            >>> chain.ks_patterns
            [(1, 3, 4, 7), (4, 7, 4, 1)]
            >>> M, N = 12, 25
            >>> chain = Chain.monarch((M, N))
            >>> chain.ks_patterns
            [(1, 4, 5, 3), (5, 3, 5, 1)]
            >>> M, N = 12, 16
            >>> chain = Chain.monarch((M, N))
            >>> chain.ks_patterns
            [(1, 4, 4, 3), (4, 3, 4, 1)]
            >>> chain = Chain.monarch((M, N), p=2, q=4)
            >>> chain.ks_patterns
            [(1, 2, 4, 6), (4, 6, 4, 1)]

        .. _monarch:

            **References:**

            [1] Monarch: Expressive structured matrices for efficient and accurate training.
            In International Conference on Machine Learning, pages 4690-4721. PMLR, 2022.
            T. Dao, B. Chen, N. S. Sohomi, A. D. Desai, M. Poli, J. Grogan, A. Liu, A. Rao, A. Rudra, and C. R\u00E9.
        """
        m, n = shape
        if (isprime(m) and m != 2) or (isprime(n) and n != 2):
            raise Exception("shape must not be prime numbers.")
        if (p is not None and m % p != 0) or (q is not None and n % q != 0):
            raise Exception("p must divide m and q must divide n.")
        _p, _q = p, q
        if p is None:
            if m == 1:
                _p = 1
            else:
                mf = []
                tmp = factorint(m)
                for k in tmp.keys():
                    mf.extend([int(k)] * tmp[k])
                s = np.sqrt(m)
                _p = mf[0]
                for i in range(1, len(mf)):
                    if abs(_p * mf[i] - s) < abs(_p - s):
                        _p *= mf[i]
                    else:
                        break
        if q is None:
            if n == 1:
                _q = 1
            else:
                nf = []
                tmp = factorint(n)
                for k in tmp.keys():
                    nf.extend([int(k)] * tmp[k])
                s = np.sqrt(n)
                _q = nf[0]
                for i in range(1, len(nf)):
                    if abs(_q * nf[i] - s) < abs(_q - s):
                        _q *= nf[i]
                    else:
                        break
        ks_patterns = [(1, _p, _q, m // _p), (_q, m // _p, n // _q, 1)]
        tmp = cls(ks_patterns)
        # tmp.chain_type = 'monarch'
        return tmp

    @classmethod
    def wip_non_redundant(cls, shape):
        r"""
        :octicon:`alert-fill;1em;sd-text-danger`
        :octicon:`bug;1em;sd-text-danger`
        This class method is still work-in-progress.

        Build a non redundant chain from ``shape`` using
        Lemma 4.25 from :ref:`[1] <chain>`.
        The function uses a prime factorization $(q_l)_{l=1}^L$ of
        ``M = shape[0]`` and a prime factorization $(p_l)_{l=1}^L$ of
        ``N = shape[0]`` where $L$ is the length of the prime factorization.
        If the two factorization do not have the same length,
        merge the smallest elements of the larger factorization.
        Raise an ``Exception`` if ``shape[0] > 2`` and ``shape[1] > 2``
        are prime numbers.

        Args:
            shape: ``tuple``
                Shape of the input matrix, expect a tuple $(M,~N)$.
                ``M`` is equal to the
                number of rows $a_1b_1d_1$ of the first factor while
                ``N`` is equal to the number of
                columns $a_nc_nd_n$ of the last factor.

        Examples:
            >>> from lazylinop.butterfly import Chain
            >>> sq_chain = Chain.square_dyadic((8, 8))
            >>> sq_chain.ks_patterns
            [(1, 2, 2, 4), (2, 2, 2, 2), (4, 2, 2, 1)]
            >>> nr_chain = Chain.wip_non_redundant((8, 8))
            >>> nr_chain.ks_patterns
            [(1, 2, 2, 4), (2, 2, 2, 2), (4, 2, 2, 1)]
        """
        M, N = shape
        if isprime(M) and isprime(N):
            raise Exception("shape[0] and shape[1] are prime numbers.")
        # Prime factorization of M and N.
        ql = []
        tmp = factorint(M)
        for k in tmp.keys():
            ql.extend([int(k)] * tmp[k])
        pl = []
        tmp = factorint(N)
        for k in tmp.keys():
            pl.extend([int(k)] * tmp[k])
        Lp, Lq = len(pl), len(ql)
        last = False
        if last:
            # Merge last elements.
            while Lp < Lq:
                ql[Lq - 2] = ql[Lq - 2] * ql[Lq - 1]
                ql.pop(Lq - 1)
                Lq -= 1
            while Lq < Lp:
                pl[Lp - 2] = pl[Lp - 2] * pl[Lp - 1]
                pl.pop(Lp - 1)
                Lp -= 1
        else:
            # Merge first elements.
            while Lp < Lq:
                ql[1] = ql[0] * ql[1]
                ql.pop(0)
                Lq -= 1
            while Lq < Lp:
                pl[1] = pl[0] * pl[1]
                pl.pop(0)
                Lp -= 1
        L = len(pl)
        rl = [1] * L
        # Compute ks_patterns.
        # print("pl, ql", pl, ql)
        ks_patterns = []
        for i in range(L):
            if i == 0:
                al = 1
            else:
                al = int(np.prod([pl[j] for j in range(i)]))
            if i == L - 1:
                dl = 1
            else:
                dl = int(np.prod([ql[j] for j in range(i + 1, L)]))
            if i == 0:
                bl = ql[i]
            else:
                bl = ql[i] * rl[i - 1]
            cl = pl[i] * rl[i]
            ks_patterns.append((al, bl, cl, dl))
        tmp = cls(ks_patterns)
        # tmp.chain_type = 'default'
        return tmp

    def __matmul__(self, chain):
        """
        Return the concatenation of two chains.

        Args:
            chain: ``Chain``
                An instance of ``Chain``
                to concatenate with ``self``.

        Returns:
            An instance of ``Chain`` that is the
            concatenation of ``chain`` and ``self``.

        Examples:
            >>> from lazylinop.butterfly import Chain
            >>> chain1 = Chain([(1, 2, 2, 4)])
            >>> chain2 = Chain([(4, 2, 2, 1)])
            >>> chain = chain1 @ chain2
            >>> chain.shape
            (8, 8)
            >>> chain.n_patterns
            2
            >>> chain.ks_patterns
            [(1, 2, 2, 4), (4, 2, 2, 1)]
        """
        M, K = self.shape
        if K != chain.shape[0]:
            raise Exception("self.shape[1] must be equal to chaine.shape[0].")
        return Chain(ks_patterns=self.ks_patterns + chain.ks_patterns)

    def __len__(self):
        """"
        Return length of ``self``.
        """
        return len(self.ks_patterns)
