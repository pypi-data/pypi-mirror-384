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
from typing import Optional

from .constants import VALID_REGIONS
from .exceptions import BNetRegionNotFoundError, BNetGrantError


__version__ = '1.1.0'
__author__ = 'David \'Gahd\' Couples'


def verify_region(func):
    """Verifies the function's first parameter is a valid region abbreviation

    Raises:
        BNetRegionNotFoundError: when the region (arg[0]) is not a valid region tag
    """
    @functools.wraps(func)
    def wrapper_verify_region(*args, **kwargs):
        if args[0].lower() not in VALID_REGIONS:
            raise BNetRegionNotFoundError('Region not found')

        return func(*args, **kwargs)
    return wrapper_verify_region


def verify_grant_type(target_grant_types=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if hasattr(self, 'grant_type') and self.grant_type not in target_grant_types:
                raise BNetGrantError(f"Invalid grant type: {self.grant_type}")
            #
            return func(self, *args, **kwargs)

        return wrapper

    if callable(target_grant_types):
        return decorator(target_grant_types)
    else:
        return decorator
