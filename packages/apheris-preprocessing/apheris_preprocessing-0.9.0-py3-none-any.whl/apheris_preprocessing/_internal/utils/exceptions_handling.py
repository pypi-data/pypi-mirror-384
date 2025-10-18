from typing import List, Optional, Set, Tuple, Union

from apheris_utils.extras_nvflare.logging.util import sanitised_trace


def hide_traceback_decorator(func):
    def safe_error_message_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:

            if isinstance(err, TransformationsException):
                raise err
            else:
                raise TransformationsException(sanitised_trace()) from None

    return safe_error_message_wrapper


class TransformationsException(Exception):
    """Base class for exceptions in transformations module"""

    def __init__(self, message: Optional[str] = None):
        if message is None:
            message = "An error occurred in the transformations module."
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class TransformationsInputTypeException(TransformationsException):
    """Exception raised for a wrong type of input value

    Attributes:
        function_name: name of the function where exception was raised
        argument_name: name of the method argument causing an exception
        argument_type: type of the method argument causing an exception
    """

    def __init__(
        self,
        function_name: str,
        argument_name: str,
        argument_type: type,
    ):
        self.message = (
            f"Unsupported input type {argument_type} "
            f"in {function_name}() for {argument_name}"
        )
        super().__init__(self.message)


class TransformationsFileExtensionNotSupportedException(TransformationsException):
    """Exception is raised for not supported file extension

    Attributes:
        file_extension: input file extension
        supported_file_extensions: list of all supported extensions
    """

    def __init__(
        self,
        file_extension: str,
        supported_file_extensions: List[str],
    ):
        self.message = (
            f"Could not proceed. "
            f"Not supported file extension '{file_extension}'."
            f"List of supported extensions: {supported_file_extensions}"
        )
        super().__init__(self.message)


class TransformationsTypeConversionException(TransformationsException):
    """Exception is raised if conversion of data type is not possible

    Attributes:
        source_data: source data to be converted
        expected_format: type into which source data should be converted
    """

    def __init__(
        self,
        source_data: object,
        expected_format: str,
    ):
        self.message = (
            f"Could not proceed. "
            f"Cannot convert {source_data} data into {expected_format}"
        )
        super().__init__(self.message)


class TransformationsOperationArgumentTypeNotAllowedException(TransformationsException):
    """Exception is raised for operations which are not allowed for privacy reasons
        Raised in case of wrong type of arguments

    Attributes:
        function_name: name of the function where exception was raised
        argument_name: name of the method argument causing an exception
        argument_type: type of the method argument causing an exception
        supported_argument_types: supported types of the method argument
    """

    def __init__(
        self,
        function_name: str,
        argument_name: str,
        argument_type: Union[type, Set[type]],
        supported_argument_types: Union[List[type], Tuple[str], Tuple[type], List[str]],
    ):
        self.message = (
            f"Could not proceed. "
            f"Not allowed argument type for {function_name}(). "
            f"Argument {argument_name} cannot be type {argument_type}. "
            f"Supported types are {supported_argument_types}."
        )
        super().__init__(self.message)


class TransformationsOperationNotAllowedException(TransformationsException):
    """Exception is raised for operations which are not allowed for privacy reasons

    Attributes:
        operation_type: type of the operation causing an exception
        supported_operation_types: supported types of operations
    """

    def __init__(
        self,
        operation_type: type,
        supported_operation_types: List[type],
    ):
        self.message = (
            f"Could not proceed. "
            f"Not allowed operation type {operation_type}."
            f"Supported types are {supported_operation_types}."
        )
        super().__init__(self.message)


class TransformationsNotImplementedException(TransformationsException):
    """Exception is raised for operations which are not yet implemented

    Attributes:
        function_name: name of the function where exception was raised
    """

    def __init__(
        self,
        function_name: str,
        message: Optional[str] = None,
    ):
        self.message = (
            f"Could not proceed with {function_name}. {message}"
            if message
            else (
                f"Could not proceed. "
                f"The operation {function_name}() is not yet implemented."
            )
        )
        super().__init__(self.message)


class TransformationsUnknownCommandException(TransformationsException):
    """Exception is raised for commands which are not recognized

    Attributes:
        function_name: name of the function where exception was raised
    """

    def __init__(
        self,
        function_name: str,
    ):
        self.message = (
            f"Could not proceed. The operation {function_name}() is not recognized."
        )
        super().__init__(self.message)


class TransformationsFailedExecutionException(TransformationsException):
    """Exception is raised for graph execution outcome being None"""

    def __init__(self):
        self.message = "Execution of the compute graph failed. No result is returned."
        super().__init__(self.message)


class TransformationsMissingArgumentException(TransformationsException):
    """Exception is raised when required argument is missing

    Attributes:
        function_name: name of the function where exception was raised
        argument_name: name of the method argument causing an exception
    """

    def __init__(
        self,
        function_name: str,
        argument_name: str,
        mark_as_mandatory: bool = True,
    ):
        prefix = "mandatory " if mark_as_mandatory else ""
        self.message = (
            f"Could not proceed. "
            f"The {prefix}argument {argument_name} is missing for {function_name}()."
        )
        super().__init__(self.message)


class TransformationsNotMatchingNumberOfArgumentsException(TransformationsException):
    """Exception is raised when number of arguments is not matching
        the number of trigger arguments

    Attributes:
        trigger_argument_name: name of the method argument for each of them argument
            needs to be specified
        numbers_of_arguments: not matching numbers of arguments causing an exception
    """

    def __init__(
        self,
        trigger_argument_name: str,
        numbers_of_arguments: List[int],
    ):
        number_of_arguments = " != ".join(map(str, numbers_of_arguments))
        self.message = (
            f"Could not proceed. "
            f"The number of arguments is not matching "
            f"for '{trigger_argument_name}': "
            f"{number_of_arguments}."
        )
        super().__init__(self.message)


class TransformationsInvalidSourceDataException(TransformationsException):
    """Exception is raised when source data is missing information

    Attributes:
        source_data: source data
    """

    def __init__(
        self,
        source_data: object,
    ):
        self.message = f"Could not proceed. Make sure that {source_data} is valid."
        super().__init__(self.message)


class TransformationsInvalidJSONFormatException(TransformationsException):
    """Exception is raised when JSON cannot be decoded"""

    def __init__(
        self,
        message: str,
    ):
        self.message = f"Could not parse JSON. {message}"
        super().__init__(self.message)


class TransformationsModuleCommandNotFoundException(TransformationsException):
    """Exception is raised when NodeCommand object is called on a command
    which is not defined
    """

    def __init__(
        self,
        command: str,
    ):
        self.command = command
        self.message = (
            f"Could not proceed. "
            f"Command {command} is not defined for transformations preprocessing module."
        )
        super().__init__(self.message)


class TransformationsInvalidGraphException(TransformationsException):
    """Exception is raised during execution of the graph when something is
    constructed wrongly."""

    def __init__(self, reason: str, do_that: str):
        self.message = f"The graph is invalid because {reason}. " f"Please {do_that}."
        super().__init__(self.message)


class TransformationDataUnavailableException(TransformationsException):
    """Exception is raised when executing .run() without local file or overwrite,
    and fetching remote dataset failed."""

    def __init__(self, remote_id):
        self.message = f"Tried to access remote data with id {remote_id}, but failed."
        super().__init__(self.message)


class TransformationsWarning(Warning):
    """Base class for warnings in this module"""

    pass


class TransformationsFileExtensionNotDefinedWarning(TransformationsWarning):
    """Warning is raised for missing file extension

    Attributes:
        filepath: file path from which extension was taken
        default_extension: default extension to be applied in case of failure
    """

    def __init__(
        self,
        filepath: str,
        default_extension: str,
    ):
        self.message = (
            f"Filepath '{filepath}' could not be parsed to get the file extension. "
            f"Default extension will be assumed: {default_extension}"
        )
        super().__init__(self.message)

    def __repr__(self):
        return self.message


class TransformationsMissingArgumentWarning(TransformationsWarning):
    """Warning is raised for missing file extension

    Attributes:
        msg: exception message
    """

    def __init__(
        self,
        msg: str,
    ):
        self.message = msg
        super().__init__(self.message)

    def __repr__(self):
        return self.message


class PrivacyException(Exception):
    """
    Raised when a privacy mechanism required by the data provider(s)
    fails to be applied, is violated, or is incompatible
    with the user-chosen settings.
    """


class RestrictedPreprocessingViolation(PrivacyException):
    """
    Raised when a prohibited command is requested to be executed due to
    restricted preprocessing.
    """
