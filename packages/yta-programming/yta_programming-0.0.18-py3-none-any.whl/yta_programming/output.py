from yta_constants.file import FileType, FileExtension
from yta_validation import PythonValidator
from yta_random import Random
from typing import Union


class Output:
    """
    Class to handle the outputs we need for our app
    and force the desired extension if needed.
    """

    def get_filename(
        output_filename: Union[None, str],
        extension: Union[None, FileExtension, FileType, str] = None
    ):
        """
        This method handles the provided 'output_filename' and
        the also given 'extension' to obtain the correct
        filename if needed. This has been created to simplify
        the way we handle the 'output_filename' param when
        working with our different libraries.

        Providing a FileType instance as 'extension' parameter
        will check if the provided 'output_filename' has an
        extension of that file type and preserve it, or use
        the default one if filename extension doesn't fit the
        desired type (or even the filename doesn't have any
        extension). Providing a FileExtension instance as
        'extension' parameter will force that extension for
        the generated output filename.
        """
        # 1. We don't need output and we don't pass output
        if (
            output_filename is None and
            extension is None
        ):
            return None
        
        # 3. We don't need output but we pass output
        if (
            output_filename is not None and
            extension is None
        ):
            # TODO: Maybe validate if extension in str (?)
            return output_filename
        
        # 2. We need output but we don't pass output file
        # 4. We need output and we pass output
        else:
            # Handle extension, as it is set
            if PythonValidator.is_string(extension):
                if FileExtension.is_valid_name_or_value(extension):
                    extension = FileExtension.to_enum(extension)
                elif FileType.is_valid_name_or_value(extension):
                    extension = FileType.to_enum(extension)
                else:
                    raise Exception('The provided "exception" is an invalid string.')
            elif not PythonValidator.is_instance_of(extension, [FileExtension, FileType]):
                raise Exception('The provided "extension" is not a FileExtension nor a FileType instance.')

            output_filename = (
                Random.characters()
                if output_filename is None else
                output_filename
            )

            output_filename = (
                output_filename
                if (
                    PythonValidator.is_instance_of(extension, FileType) and
                    extension.is_filename_valid(output_filename)
                ) else
                extension.get_temp_filename(output_filename)
            )

            return output_filename