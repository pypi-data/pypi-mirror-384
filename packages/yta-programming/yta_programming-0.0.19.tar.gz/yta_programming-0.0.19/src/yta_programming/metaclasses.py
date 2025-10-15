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
    
# TODO: I think this should be the option to use and
# deprecate the SingletonWrapper if confirmed that
# this metaclass is better.
class SingletonMeta(type):
    """
    Singleton meta class to be used by the classes you
    want to be singleton. Here you have an example with
    inheritance:

    ```
    class A(metaclass = SingletonMeta):
        pass

    class B(A):
        pass
    ```

    Instantiating any of these 2 instances, A() or B(),
    will return you the same instance of that class,
    which means that B will be also singleton.
    """
    _instances = {}
    """
    The list of instances of the different classes.
    """

    def __call__(
        cls,
        *args,
        **kwargs
    ):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
            
        return cls._instances[cls]