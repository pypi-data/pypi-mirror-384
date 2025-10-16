import numpy as np
from sympy import primerange


def random_Euler_sum(n, k):
    """Return k nonnegative integers whose sum equals to n.

    Args:
        n: ``int``
            Target sum.
        k: ``int``
            Number of nonnegative integers.

    Returns:
        ``list``
    """
    result = [0] * k
    sample = np.random.randint(0, k, n)
    for i in sample:
        result[i] = result[i] + 1
    return result


def enumerate_Euler_sum(n, k):
    if k == 1:
        yield (n,)
        return

    for i in range(n + 1):
        for t in enumerate_Euler_sum(n - i, k - 1):
            yield (i,) + t


class DebflyGen:
    def __init__(self, m, n, r):
        self.m = m
        self.n = n
        self.rank = r
        self.divisor_m = []
        self.divisor_n = []
        # Calculate the set of divisor of m
        for i in range(1, m + 1):
            if m % i == 0:
                self.divisor_m.append(i)

        # Calculate the set of divisor of n
        for i in range(1, n + 1):
            if n % i == 0:
                self.divisor_n.append(i)

        self.dp_table = np.zeros((m + 1, n + 1))
        self.dp_table_temp = np.zeros((m + 1, n + 1))
