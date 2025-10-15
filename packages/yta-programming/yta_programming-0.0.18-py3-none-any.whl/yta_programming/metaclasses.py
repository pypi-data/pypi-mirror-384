"""
Module to include classes that must be
inherited as metaclasses like this example
below:

`class Colors(metaclass = _GetAttrReturnsNoneMetaClass):`
"""


class _GetAttrReturnsNoneMetaClass(type):
    """
    Meta class to be used when we don't want
    to receive an exception if accessing to a
    non-existing attribute but getting None
    instead.

    Useful for some classes we will use as
    static classes, like Colors, that is just
    a holder of color values built dynamically
    so if one of the values doesn't exist, we
    just get None as it is not defined.
    """

    def __getattr__(
        self,
        name: str
    ):
        """
        Accessing to any property that doesn't exist
        will return None instead of raising an 
        Exception.
        """
        return None