from yta_constants.regex import GeneralRegularExpression
from yta_validation import PythonValidator

import re


# TODO: Maybe the 'var' filename is not appropriate
class CaseStyleHandler:
    """
    Class to wrap and group the functionalities related
    with the different programming case styles.
    """

    @staticmethod
    def snake_case_to_upper_camel_case(
        snake_str: str
    ):
        """
        Turn the provided 'snake_str' text (that should be like
        'this_is_the_variable_name') into a upper camel case
        name (that would be, for the previous example, 
        'ThisIsTheVariableName').
        """
        if (
            not PythonValidator.is_string(snake_str) or
            not GeneralRegularExpression.SNAKE_CASE.parse(snake_str)
        ):
            raise Exception('The provided "snake_str" parameter is not a valid string.')
        
        return ''.join(
            word.title()
            for word in snake_str.split('_')
        )
    
    @staticmethod
    def snake_case_to_lower_camel_case(
        snake_str: str
    ):
        """
        Turn the provided 'snake_str' text (that should be like
        'this_is_the_variable_name') into a lower camel case
        name (that would be, for the previous example, 
        'thisIsTheVariableName').
        """
        if (
            not PythonValidator.is_string(snake_str) or
            not GeneralRegularExpression.SNAKE_CASE.parse(snake_str)
        ):
            raise Exception('The provided "snake_str" parameter is not a valid string.')

        parts = snake_str.split('_')

        return parts[0] + ''.join(
            word.capitalize()
            for word in parts[1:]
        )

    @staticmethod
    def upper_camel_case_to_snake_case(
        upper_camel_case_str: str
    ):
        """
        Turn the provided 'upper_camel_case_str' string (that
        should be like 'ThisVariable') into a snake case string
        (that would be, for the previous example, 'this_variable).
        """
        if (
            not PythonValidator.is_string(upper_camel_case_str) or
            not GeneralRegularExpression.UPPER_CAMEL_CASE.parse(upper_camel_case_str)
        ):
            raise Exception('The provided "upper_camel_case_str" is not a valid string.')

        return re.sub(r'([a-z])([A-Z])', r'\1_\2', upper_camel_case_str).lower()

    @staticmethod
    def lower_camel_case_to_snake_case(
        lower_camel_case_str: str
    ):
        """
        Turn the provided 'lower_camel_case_str' string (that
        should be like 'thisVariable') into a snake case string
        (that would be, for the previous example, 'this_variable).
        """
        if (
            not PythonValidator.is_string(lower_camel_case_str) or
            not GeneralRegularExpression.LOWER_CAMEL_CASE.parse(lower_camel_case_str)
        ):
            raise Exception('The provided "upper_camel_case_str" is not a valid string.')
        
        return re.sub(r'([a-z])([A-Z])', r'\1_\2', lower_camel_case_str).lower()

# TODO: Implement more conversions