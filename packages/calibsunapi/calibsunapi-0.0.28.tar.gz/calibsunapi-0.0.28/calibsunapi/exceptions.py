class DocDefaultException(Exception):
    """Subclass exceptions use docstring as default message"""

    def __init__(self, msg=None, *args, **kwargs):
        super().__init__(msg or self.__doc__, *args, **kwargs)


class NoCredentialsError(DocDefaultException):
    """Please provide CALIBSUN_CLIENT_ID and CALIBSUN_CLIENT_SECRET in environment variables or pass values when initializing client."""


class NotAuthenticatedError(DocDefaultException):
    """Not authenticated with Calibsun API. Please provide CALIBSUN_CLIENT_ID and CALIBSUN_CLIENT_SECRET in environment variables or pass values when initializing client."""
