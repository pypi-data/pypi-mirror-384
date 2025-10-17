"""Module containing custom exceptions for general usage"""

from typing import Any

from abllib.error._custom_exception import CustomException

# pylint: disable=arguments-differ

class ArgumentCombinationError(CustomException):
    """Exception raised when the given combination of arguments is invalid"""

    default_messages = {
        0: "This combination of arguments is invalid"
    }

class CalledMultipleTimesError(CustomException):
    """Exception raised when a single-use function is called twice"""

    default_messages = {
        0: "The function can only be called once"
    }

class DeprecatedError(CustomException):
    """Exception raised when deprecated functionality is used"""

    default_messages = {
        0: "This functionality is deprecated",
        1: "This functionality is deprecated, please use {0} instead"
    }

class DirNotFoundError(CustomException):
    """Exception raised when an expected directory doesn't exist"""

    default_messages = {
        0: "The expected directory doesn't exist",
        1: "The expected directory '{0}' doesn't exist"
    }

class InternalCalculationError(CustomException):
    """Exception raised when an internal calculation resulted in an unacceptable value"""

    default_messages = {
        0: "Internal calculation resulted in an unacceptable value",
        1: "Internal calculation resulted in an unacceptable value {0}"
    }

class InternalFunctionUsedError(CustomException):
    """Exception raised when an internal function was used by an external project"""

    default_messages = {
        0: "This function is only for library-internal use"
    }

class InvalidKeyError(CustomException):
    """Exception raised when the key has an invalid format"""

    default_messages = {
        0: "The key has an invalid format",
        1: "The key '{0}' has an invalid format"
    }

class KeyNotFoundError(CustomException):
    """Exception raised when the key is not found in the storage"""

    default_messages = {
        0: "The requested key could not be found",
        1: "The requested key '{0}' could not be found"
    }

class LockAcquisitionTimeoutError(CustomException):
    """Exception raised when the acquisitgion of a lock timed out"""

    default_messages = {
        0: "The requested lock could not be acquired in time"
    }

class MissingDefaultMessageError(CustomException):
    """Exception raised when an error class is missing the default message"""

    default_messages = {
        0: "The error class is missing a default message. Set it as a class variable in default_messages[0].",
        1: "The error class '{0}' is missing a default message. Set it as a class variable in default_messages[0]."
    }

class MissingInheritanceError(CustomException):
    """Exception raised when a class is expected to inherit from another class"""

    default_messages = {
        0: "The class is missing an inheritance from another class",
        1: "The class is missing an inheritance from {0}",
        2: "The class {1} is missing an inheritance from {0}"
    }

    @classmethod
    def with_values(cls, class_name: Any | type, base_class_name: Any | type):
        if not isinstance(class_name, type):
            class_name = type(class_name)
        if not isinstance(base_class_name, type):
            base_class_name = type(base_class_name)

        return super().with_values(base_class_name, class_name)

class MissingRequiredModuleError(CustomException):
    """Exception raised when a required module is not installed"""

    default_messages = {
        0: "A required module is not installed.",
        1: "The required module '{0}' is not installed."
    }

class NameNotFoundError(CustomException):
    """Exception raised when the name is not found"""

    default_messages = {
        0: "The requested name could not be found",
        1: "The requested name '{0}' could not be found"
    }

class NoneTypeError(CustomException):
    """Exception raised when a value is unexpectedly None"""

    default_messages = {
        0: "Didn't expect None as a value here"
    }

class NotInitializedError(CustomException):
    """Exception raised when an instance is used before it is correctly initialized"""

    default_messages = {
        0: "The instance is not yet initialized correctly"
    }

class RegisteredMultipleTimesError(CustomException):
    """Exception raised when something is registered twice"""

    default_messages = {
        0: "This object is already registered",
        1: "{0} is already registered"
    }

class ReadonlyError(CustomException):
    """Exception raised when a read-only object is changed"""

    default_messages = {
        0: "This object is read-only and cannot be changed",
        1: "{0} is read-only and cannot be changed"
    }

class SingletonInstantiationError(CustomException):
    """Exception raised when a singleton class is instantiated twice"""

    default_messages = {
        0: "The singleton class can only be instantiated once",
        1: "The singleton class {0} can only be instantiated once"
    }

    @classmethod
    def with_values(cls, class_name: Any | type):
        if not isinstance(class_name, type):
            class_name = type(class_name)

        return super().with_values(class_name)

class UninitializedFieldError(CustomException):
    """Exception raised when a subclass doesn't initialize a mandatory field"""

    default_messages = {
        0: "The subclass doesn't initialize a mandatory field",
        1: "The subclass doesn't initialize the mandatory field {0}",
        2: "{0} doesn't initialize the mandatory field {1}"
    }

class WrongTypeError(CustomException):
    """Exception raised when a value wasn't of an expected type"""

    default_messages = {
        0: "Received an unexpected type",
        2: "Expected {1}, not {0}",
        3: "Expected {1} or {2}, not {0}",
        4: "Expected {1}, {2} or {3}, not {0}",
        5: "Expected {1}, {2}, {3} or {4}, not {0}",
        6: "Expected {1}, {2}, {3}, {4} or {5}, not {0}",
    }

    @classmethod
    def with_values(cls, received: Any | type, expected: Any | type | tuple[Any | type]):
        if not isinstance(received, type):
            received = type(received)

        if isinstance(expected, tuple):
            expected = list(expected)
        if not isinstance(expected, list):
            expected = [expected]

        for c, item in enumerate(expected):
            if not isinstance(item, type):
                expected[c] = type(item)

        return super().with_values(received, *expected)
