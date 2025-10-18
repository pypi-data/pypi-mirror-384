"""
get_min_max function definition
"""

import numpy


def get_min_max(d: numpy.ndarray, delta: float) -> tuple:

    """
    Get minimum and maximum values for colour mapping
    args...
        d: 2D NumPy array of values to be colour mapped
        delta: Offset to use instead if the values are the same
    """

    dfi = d[numpy.isfinite(d)]
    if dfi.size > 0:
        min_val = dfi.min()
        max_val = dfi.max()
    else:
        max_val = min_val = 0
    if max_val == min_val:
        max_val += delta

    return min_val, max_val
