from yta_programming.dataclasses import MethodParameters, MethodParameter
from yta_validation.parameter import ParameterValidator
from typing import Union

import inspect


class ParameterObtainer:
    """
    Class to interact with python methods and classes to obtain
    the parameters those method have. This is useful for any
    dynamic functionality that needs to fill or check if the
    required parameters are passed or not.
    """

    PARAMETER_EMPTY = inspect._empty
    """
    Class that represents an empty parameter default value
    """
    
    @staticmethod
    def get_parameters_from_method(
        method: callable,
        parameters_to_ignore: Union[list[str], None] = []
    ) -> MethodParameters:
        """
        Obtain the parameters of the given 'method' as
        a list of our custom dataclass Parameter, easy
        to handle and to get information from.
        """
        ParameterValidator.validate_mandatory_callable('method', method)
        ParameterValidator.validate_list_of_string('parameters_to_ignore', parameters_to_ignore)
        
        # If arrays are None by any chance, turn into empty arrays
        parameters_to_ignore = (
            []
            if parameters_to_ignore is None else
            parameters_to_ignore
        )

        # We will force these normal parameters to ignore them
        parameters_to_ignore += ['self', 'cls', 'args', 'kwargs']

        return MethodParameters([
            MethodParameter(
                method_parameter.name,
                method_parameter.annotation,
                method_parameter.default
            )
            for method_parameter in inspect.signature(method).parameters.values()
            if method_parameter.name not in parameters_to_ignore
        ])

"""
This code below is nice for testing:
from typing import Union
import inspect

def test_method(text: str, output_filename: Union[str, int, None] = None):
    pass

for parameter in inspect.signature(test_method).parameters:
    print(parameter)

for parameter_value in inspect.signature(test_method).parameters.values():
    print('Este es uno:')
    print(parameter_value.name)
    #print(parameter_value.kind)
    print(parameter_value.annotation)
    print(parameter_value.default)
"""