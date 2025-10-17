"""Module containing the CustomException class"""

from typing import Any

class CustomException(Exception):
    """
    The base class for all custom exceptions

    If no arguments are provided at instantiation, the default error message is used.
    Otherwise, the provided argument is used as the error message.
    """

    def __init__(self, *args, **kwargs):
        if self.__class__ == CustomException:
            raise NotImplementedError()

        if args:
            if not isinstance(args[0], str):
                # needs to be imported here to prevent circular import
                # pylint: disable-next=cyclic-import, import-outside-toplevel
                from abllib.error._general import WrongTypeError
                raise WrongTypeError("Expected error message to be of type str")
            super().__init__(*args, **kwargs)
        else:
            # exception was raised without args
            super().__init__(self.default_messages[0], **kwargs)

    default_messages: dict[int, str]

    @classmethod
    def with_values(cls, *args: Any):
        """Instantiate the given exception with the given args"""

        if cls == CustomException:
            raise NotImplementedError()

        index = len(args)
        if index not in cls.default_messages:
            raise AttributeError(f"{cls} does not support error messages created with {index} arguments")

        message = cls.default_messages[index]
        message = message.format(*args)
        return cls(message)

    def __init_subclass__(cls):
        if 0 not in cls.default_messages:
            # needs to be imported here to prevent circular import
            # pylint: disable-next=cyclic-import, import-outside-toplevel
            from abllib.error._general import MissingDefaultMessageError
            raise MissingDefaultMessageError.with_values(cls)

        for key in cls.default_messages.keys():
            if not isinstance(key, int):
                raise TypeError()
        for val in cls.default_messages.values():
            if not isinstance(val, str):
                raise TypeError()

        if hasattr(cls, "default_message"):
            # TODO: handle legacy classes, as default_message is deprecated
            pass
