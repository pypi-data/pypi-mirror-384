"""
There is a new @singleton decorator that is supposed
to work like this and create a singleton instance.
"""

from yta_programming.metaclasses import SingletonMeta, SingletonABCMeta


__all__ = [
    'SingletonMeta',
    'SingletonABCMeta'
]