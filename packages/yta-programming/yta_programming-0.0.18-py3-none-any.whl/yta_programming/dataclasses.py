from yta_validation import PythonValidator
from typing import Union
from dataclasses import dataclass

import inspect


@dataclass
class MethodParameter:
    """
    The representation of a parameter found in a
    method signature, indicating if it was what 
    we consider an optional parameter or a 
    mandatory one based on its default value.
    """

    name: str
    """
    The name of the parameter.
    """
    type: any
    """
    The type of the parameter.
    """
    default_value: any
    """
    The default value of the parameter.
    """

    def __init__(
        self,
        name: str,
        type: any,
        default_value: any
    ):
        self.name = name
        # TODO: The type, that comes from '.annotation' has
        # to be reconsidered as it is quite special
        self.type = type
        self.default_value = default_value

    @property
    def is_default_value_empty(
        self
    ) -> bool:
        """
        Check if the default value is empty (no value
        associated) or  not.
        """
        return self.default_value is inspect._empty
    
    @property
    def is_optional(
        self
    ) -> bool:
        """
        Check if the parameter is optional (its default
        value is None).
        """
        return self.default_value is None
    
    @property
    def is_mandatory(
        self
    ) -> bool:
        """
        Check if the parameter is mandatory (its default
        value is not None).
        """
        return not self.is_optional
    
    @property
    def as_dict(
        self
    ) -> dict:
        """
        Get the parameter as a dict with its 'name' as
        the key and the instance as the value.

        'name' : self
        """
        return {
            self.name: self
        }
    
@dataclass
class MethodParameters:
    """
    List of parameters that exist in a function
    or method signature, to be able to handle
    them easy and detect which ones are mandatory
    or optional and more stuff.
    """

    parameters: list[MethodParameter]
    """
    The parameters found in the method signature.
    """

    def __init__(
        self,
        parameters: list[MethodParameter]
    ):
        if (
            not PythonValidator.is_list(parameters) or
            any(
                not PythonValidator.is_instance_of(item, MethodParameter)
                for item in parameters
            )
        ):
            raise Exception('The provided "parameters" parameter is not a list of MethodParameter instances or at least one of the elements is not a MethodParameter instance.')

        self.parameters = parameters
        
    @property
    def mandatory(
        self
    ) -> 'MethodParameters':
        """
        Get the parameters that are mandatory as a new
        instance of a MethodParameters class containing
        only those ones.

        This is a new instance that doesn't modify the
        original one.
        """
        return MethodParameters(self.mandatory_as_list)
    
    @property
    def optional(
        self
    ) -> 'MethodParameters':
        """
        Get the parameters that are optional as a new
        instance of a MethodParameters class containing
        only those ones.

        This is a new instance that doesn't modify the
        original one.
        """
        return MethodParameters(self.optional_as_list)

    @property
    def mandatory_as_list(
        self
    ) -> list[MethodParameter]:
        """
        Get the parameters that are mandatory as a list
        of MethodParameter instances.
        """
        return [
            parameter
            for parameter in self.parameters
            if parameter.is_mandatory
        ]
    
    @property
    def optional_as_list(
        self
    ) -> list[MethodParameter]:
        """
        Get the parameters that are optional as a list
        of MethodParameter instances.
        """
        return [
            parameter
            for parameter in self.parameters
            if parameter.is_optional
        ]
    
    @property
    def mandatory_keys(
        self
    ) -> list[str]:
        """
        Get the keys of the parameters that are considered
        mandatory.
        """
        return [
            parameter.name
            for parameter in self.mandatory_as_list
        ]
    
    @property
    def optional_keys(
        self
    ) -> list[str]:
        """
        Get the keys of the parameters that are considered
        optional.
        """
        return [
            parameter.name
            for parameter in self.optional_as_list
        ]
    
    @property
    def keys(
        self
    ) -> list[str]:
        """
        Get the keys of all the parameters.
        """
        return self.mandatory_keys + self.optional_keys
    
    @property
    def as_dict(
        self
    ) -> dict[str, MethodParameter]:
        """
        Get the parameters as a dictionary in which the
        parameter names are the keys and the values are
        MethodParameter instances.
        """
        if (
            not hasattr(self, '_as_dict') or
            self._as_dict is None
        ):
            self._as_dict = {
                parameter.name: parameter
                for parameter in self.parameters
            }

        return self._as_dict
    
    def get(
        self,
        name: str
    ) -> Union[MethodParameter, None]:
        """
        Get the parameter with the given 'name' if
        existing, or None if not.
        """
        return self.as_dict.get(name, None)
    
    def has(
        self,
        name: str
    ) -> bool:
        """
        Check if the parameter with the given 'name' 
        exist or not.
        """
        return name in self.as_dict
    
    def remove(
        self,
        name: str
    ) -> 'Parameters':
        """
        Remove the parameter with the provided 'name' if
        existing.
        """
        self.parameters = [
            parameter
            for parameter in self.parameters
            if parameter.name != name
        ]

        # We force it to be recalculated
        self._as_dict = None

        return self

EMPTY = inspect._empty
"""
Basic python empty value class. This class is obtained
when a variable has no value set.
"""