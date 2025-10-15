"""
Use `SingletonMeta`, is the best option by now.
"""
import functools


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

class _SingletonWrapper:
    """
    Singleton wrapper class that creates instances
    for each decorated class.
    """

    def __init__(
        self,
        cls
    ):
        self.__wrapped__ = cls
        self._instance = None

        functools.update_wrapper(self, cls)

    def __call__(
        self,
        *args,
        **kwargs
    ):
        """
        Get a single instance of decorated class.
        """
        if self._instance is None:
            self._instance = self.__wrapped__(*args, **kwargs)

        return self._instance

