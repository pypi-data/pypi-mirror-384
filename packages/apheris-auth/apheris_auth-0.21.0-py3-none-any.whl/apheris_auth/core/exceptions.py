class ApherisException(Exception):
    pass


class AccessDenied(ApherisException):
    """
    Raised when trying to access forbidden endpoints or objects.
    """


class ServerError(ApherisException):
    """
    Raised when something is broken in the API server code.
    """


class ObjectNotFound(ApherisException):
    """
    Raised when trying to access an object that does not exist.
    """


class BadRequest(ApherisException):
    """
    Raised when request sent to the API is malformed.
    """


class Unauthorized(ApherisException):
    """
    Raised when request lacks valid authentication credentials for the target resource.
    """


class ConnectionError(ApherisException):
    """
    Raised when a connection fails.
    """


class MissingConfiguration(ApherisException):
    """
    Raised when the configuration file or its keys are not found.
    """


class EmptySessionInfo(ApherisException):
    """
    Raised when the loaded session info from credentials file is empty
    """

    pass


class SSOLoginFailed(ApherisException):
    """
    Raised when for any reason the sso login is not successful
    """

    pass


class NotSSOSession(ApherisException):
    """
    Raised when for any reason the sso login is not successful
    """

    pass


class SSOLogoutFailed(ApherisException):
    """
    Raised when for any reason the sso login is not successful
    """

    pass


class AlreadyLoggedOut(ApherisException):
    pass


class AllCallbackPortsInUse(ApherisException):
    pass


class FallbackFlow(ApherisException):
    pass
