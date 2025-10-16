
class Factor:
    """
    Implementation of a tree.
    """

    def __init__(self, start, end, factor):
        """
        The value of a node is a subset of consecutive indices
        {low, ..., high - 1} included in {0, ..., num_factors - 1}.
        :param low: int
        :param high: int
        :param num_factors: int
        """
        self.start = start
        self.end = end
        self.factor = factor

    def param_cal(self, gb_params):
        return partial_prod_deformable_butterfly_params(
            gb_params, self.start, self.end
        )


def partial_prod_deformable_butterfly_params(gb_params, low, high):
    r"""Return closed form expression of partial matrix_product
    of butterfly supports. We name $S_L, \cdots, S_1$ the butterfly
    supports of size $2^L$, represented as binary matrices.
    Then, the method computes the partial matrix
    product $S_{high-1} \cots S_{low}$.

    Args:
        gb_params: ``list``
            List of sizes of factors.
        low: ``int``
            First factor.
        high: ``int``
            Last factor (not included).

    Returns:
        binary matrix (``np.ndarray``)
    """
    params = gb_params[low: high + 1]
    result = [1] * 6
    result[0] = params[0][0]
    result[3] = params[-1][3]
    result[4] = params[0][4]
    result[5] = params[-1][5]
    size_one_middle_h = 1
    size_one_middle_w = 1
    for i in range(high - low + 1):
        b, c = params[i][1:3]
        size_one_middle_h *= b
        size_one_middle_w *= c
    result[1] = size_one_middle_h
    result[2] = size_one_middle_w
    return result


def compatible_chain_gb_params(gb_params):
    if gb_params[0][0] != 1:
        return False
    if gb_params[0][4] != 1:
        return False
    if gb_params[-1][3] != 1:
        return False
    if gb_params[-1][5] != 1:
        return False
    for i in range(len(gb_params) - 1):
        if not compatible_chain_gb_params(gb_params[i], gb_params[i + 1]):
            return False
    return True
