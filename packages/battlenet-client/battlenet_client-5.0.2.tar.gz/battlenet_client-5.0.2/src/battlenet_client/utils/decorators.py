"""Defines the decorators used in this package

Functions:
   verify_region

Misc Variables:
    __version__
    __author__

Author: David "Gahd" Couples
License: GPL v3
Copyright: February 24, 2022
"""
import functools

from .exceptions import BNetGrantError


__version__ = '1.1.0'
__author__ = 'David \'Gahd\' Couples'


def verify_grant_type(target_grant_types=None):
    """ Verfies the grant type is valid

    Args:
        target_grant_types (list of str): list of grant types that are valid

    Raises:
        BNetGrantError: when the grant type is not valid
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if hasattr(self, 'grant_type') and self.grant_type not in target_grant_types:
                raise BNetGrantError(f"Invalid grant type: {self.grant_type}")
            return func(self, *args, **kwargs)
        return wrapper

    if callable(target_grant_types):
        return decorator(target_grant_types)
    else:
        return decorator
