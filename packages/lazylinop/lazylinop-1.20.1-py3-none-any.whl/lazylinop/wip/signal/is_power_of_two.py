def is_power_of_two(n: int) -> bool:
    """return True if integer 'n' is a power of two.

    Args:
        n: int

    Returns:
        bool
    """
    return ((n & (n - 1)) == 0) and n > 0


# if __name__ == '__main__':
#     import doctest
#     doctest.testmod()
