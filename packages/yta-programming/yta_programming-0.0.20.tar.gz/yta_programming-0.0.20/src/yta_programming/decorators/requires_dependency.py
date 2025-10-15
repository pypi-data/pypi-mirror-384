from typing import Union


def requires_dependency(
    module: str,
    library_name: Union[str, None] = None,
    package_name: Union[str, None] = None
):
    """
    A decorator to include a library/module as optional
    but required to be able to do some functionality.
    Those libraries will not be included as main 
    dependencies in the poetry file, but will appear as
    optional.

    The parameters:
    - `module`: The name with the library is imported
    in the project.
    - `library_name`: The name of the project in which
    you are using it (the one the 'pyproject.toml' file
    belongs to).
    - `package_name`: The name you need to use when
    installing (that is also set as optional in the
    .toml file).

    Example of use:
    - `@requires_dependency('PIL', 'yta_file', 'pillow')`

    You must declare those libraries within the
    'pyproject.toml' file like this:

    `[tool.poetry.group.optional]
    optional = true
    [tool.poetry.group.optional.dependencies]
    faster_whisper = ">=1.0.2,<2.0.0"`
    """
    def decorator(
        func
    ):
        def wrapper(
            *args,
            **kwargs
        ):
            try:
                __import__(module)
            except ImportError:
                message = f'The function "{func.__name__}" needs the "{module}" installed.'

                message = (
                    f'{message} You can install it with this command: pip install {library_name}[{package_name}]'
                    if package_name else
                    message
                )

                raise ImportError(message)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# TODO: This is not actually a decorator but it
# is used for a similar purpose than the one 
# above
class OptionalClass:
    """
    Class to be used when trying to create a class
    attribute that is based on an optional library,
    which means a library that is optional in the
    `pyproject.toml` file and its functionality can
    be used only if installed, but its not necessary
    at all in that module.

    This is useful when you have a main library that
    includes some optional modules and you want to
    add the functionality of those optional modules
    but keeping then as optional, so you put the
    extra modules as optional libraries but add the
    classes here as optional.

    Example:
    ```
    class NumpyResizer: # in normal numpy module
        shortcut = OptionalClass('cv2', 'yta_numpy', 'opencv-python', 'yta_numpy.resizer.Resizer')
    ```
    """

    def __init__(
        self,
        module: str,
        # TODO: Why None accepted (?)
        library_name: Union[str, None] = None,
        package_name: Union[str, None] = None,
        import_path: Union[str, None] = None
    ):
        """
        The parameters:
        - `module`: The name with the library is imported
        in the project.
        - `library_name`: The name of the project in which
        you are using it (the one the 'pyproject.toml' file
        belongs to).
        - `package_name`: The name you need to use when
        installing (that is also set as optional in the
        .toml file).
        - `import_path`: The import path you would use to
        import that class to be used in the code.

        Example of use:
        - `OptionalClass('yta_numpy_resizer', 'yta_numpy', 'yta_numpy_resizer', 'yta_numpy.resizer.Resizer')`
        """
        self.module: str = module
        self.library_name: str = library_name
        self.package_name: Union[str, None] = package_name
        self.import_path = import_path
        self._cls = None

    def _load_class(self):
        if self._cls is not None:
            return self._cls

        try:
            #xmodule = __import__(self.module)
            module = __import__(self.import_path)
            #module = importlib.import_module(self.import_path)
        except ImportError as e:
            message = f'The class "{self.import_path}" needs the "{self.module}" installed.'

            message = (
                f'{message} You can install it with this command: pip install {self.library_name}[{self.package_name}]'
                if self.package_name else
                message
            )

            raise ImportError(message)

        # Skip first name (module name)
        for part in self.class_path.split('.')[1:]:
            module = getattr(module, part)

        self._cls = module

        return module

    def __call__(
        self,
        *args,
        **kwargs
    ):
        """
        To instantiate the class as if it was the real one.
        """
        return self._load_class()(*args, **kwargs)

    def __getattr__(
        self,
        name
    ):
        """
        Access to the static or class attributes of the real
        one.
        """
        return getattr(self._load_class(), name)
