from functools import wraps
from typing import TYPE_CHECKING

from calibsunapi.exceptions import NotAuthenticatedError

if TYPE_CHECKING:
    from calibsunapi.client import CalibsunApiClient


def requires_authentication(func):
    @wraps(func)
    def wrapper(self: "CalibsunApiClient", *args, **kwargs):
        if not self.token:
            raise NotAuthenticatedError()
        return func(self, *args, **kwargs)

    return wrapper
