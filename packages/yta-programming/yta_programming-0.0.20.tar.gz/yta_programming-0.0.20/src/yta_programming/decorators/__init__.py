"""
This whole 'decorators' module has to be refactored
because the structure is not clear...
"""
from yta_programming.decorators.singleton import _SingletonWrapper


class ClassPropertyDescriptor(object):
    """
    This class is based on this topic:
    - https://stackoverflow.com/a/5191224
    """

    def __init__(
        self,
        fget,
        fset = None
    ):
        self.fget = fget
        self.fset = fset

    def __get__(
        self,
        obj,
        cls = None
    ):
        if cls is None:
            cls = type(obj)
        return self.fget.__get__(obj, cls)()

    def __set__(
        self,
        obj,
        value
    ):
        if not self.fset:
            raise AttributeError("can't set attribute")
        type_ = type(obj)
        return self.fset.__get__(obj, type_)(value)

    def setter(
        self,
        func
    ):
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self.fset = func
        return self

def classproperty(
    func
):
    """
    Decorator to implement a class property.
    """
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    return ClassPropertyDescriptor(func)


def singleton(
    cls: type
):
    """
    Singleton decorator that return a wrapper object
    that, when called, returns a single instance of
    the decorated class. For unit testing, use the
    '__wrapped__' attribute to access the class
    directly.
    """
    return _SingletonWrapper(cls)

def singleton_old(  
    cls
):
    """
    (!) This decorator cannot be used with a base
    class that is inherited, it should be used 
    with the children classes.

    Decorator to implement a singleton class by
    making sure only one instance is returned each
    time the class is instantiated.

    You just need to use the decorator on top of
    the class you want to be singleton and you are
    ready to use it.

    How to declare and instantiate:

    ```
    @singleton_old
    class Singleton:
        pass

    s1 = Singleton()
    ```
    """
    instances = {}
    
    def get_instance(
        *args,
        **kwargs
    ):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)

        return instances[cls]
    
    return get_instance