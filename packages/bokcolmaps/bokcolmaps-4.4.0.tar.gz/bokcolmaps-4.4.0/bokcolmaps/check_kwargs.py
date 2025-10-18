"""
check_kwargs function definition
"""

from bokcolmaps.get_common_kwargs import common_kwargs


def check_kwargs(kwargs: dict, extra_kwargs: list=None) -> None:

    """
    Check for invalid kwargs
    args...
        kwargs: list of keyword arguments to check
    kwargs...
        extra_kwargs: list of extra keyword arguments for specific classes
    """

    if extra_kwargs is None:
        extra_kwargs = []

    all_kwargs = common_kwargs + extra_kwargs

    for kwarg in kwargs:
        if kwarg not in all_kwargs:
            raise ValueError('Invalid keyword argument: ' + kwarg)
