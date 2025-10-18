from json import JSONDecodeError
from typing import Union

from requests import Response

from ...core.log import logger


class TimeoutOccurred(Exception):
    """No response within timeout interval."""

    def __init__(self, timeout: float):
        super().__init__(
            f"User authentication was not received within {timeout} seconds."
        )


class GrantNotProvided(Exception):
    """Grant was not provided."""

    def __init__(self, grant_name: str, dictionary_without_grant: dict):
        super().__init__(f"{grant_name} not provided within {dictionary_without_grant}.")


class InvalidGrantRequest(Exception):
    """
    If the request failed client authentication or is invalid, the authorization server
    returns an error response as described in:
    https://tools.ietf.org/html/rfc6749#section-5.2
    """

    # https://tools.ietf.org/html/rfc6749#section-5.2
    request_errors = {
        "invalid_request": "The request is missing a required parameter, includes an unsupported parameter value (other than grant type), repeats a parameter, includes multiple credentials, utilizes more than one mechanism for authenticating the client, or is otherwise malformed.",  # noqa E501
        "invalid_client": 'Client authentication failed (e.g., unknown client, no client authentication included, or unsupported authentication method).  The authorization server MAY return an HTTP 401 (Unauthorized) status code to indicate which HTTP authentication schemes are supported.  If the client attempted to authenticate via the "Authorization" request header field, the authorization server MUST respond with an HTTP 401 (Unauthorized) status code and include the "WWW-Authenticate" response header field matching the authentication scheme used by the client.',  # noqa E501
        "invalid_grant": "The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client.",  # noqa E501
        "unauthorized_client": "The authenticated client is not authorized to use this authorization grant type.",  # noqa E501
        "unsupported_grant_type": "The authorization grant type is not supported by the authorization server.",  # noqa E501
        "invalid_scope": "The requested scope is invalid, unknown, malformed, or exceeds the scope granted by the resource owner.",  # noqa E501
    }

    # https://tools.ietf.org/html/rfc6749#section-4.2.2.1
    # https://tools.ietf.org/html/rfc6749#section-4.1.2.1
    browser_errors = {
        "invalid_request": "The request is missing a required parameter, includes an invalid parameter value, includes a parameter more than once, or is otherwise malformed.",  # noqa E501
        "unauthorized_client": "The client is not authorized to request an authorization code or an access token using this method.",  # noqa E501
        "access_denied": "The resource owner or authorization server denied the request.",  # noqa E501
        "unsupported_response_type": "The authorization server does not support obtaining an authorization code or an access token using this method.",  # noqa E501
        "invalid_scope": "The requested scope is invalid, unknown, or malformed.",  # noqa E501
        "server_error": "The authorization server encountered an unexpected condition that prevented it from fulfilling the request. (This error code is needed because a 500 Internal Server Error HTTP status code cannot be returned to the client via an HTTP redirect.)",  # noqa E501
        "temporarily_unavailable": "The authorization server is currently unable to handle the request due to a temporary overloading or maintenance of the server.  (This error code is needed because a 503 Service Unavailable HTTP status code cannot be returned to the client via an HTTP redirect.)",  # noqa E501
    }

    def __init__(self, response: Union[Response, dict]):
        super().__init__(InvalidGrantRequest.to_message(response))

    @staticmethod
    def to_message(response: Union[Response, dict]) -> str:
        """
        Handle response as described in:
            * https://tools.ietf.org/html/rfc6749#section-5.2
            * https://tools.ietf.org/html/rfc6749#section-4.1.2.1
            * https://tools.ietf.org/html/rfc6749#section-4.2.2.1
        """
        if isinstance(response, dict):
            return InvalidGrantRequest.to_oauth2_message(
                response, InvalidGrantRequest.browser_errors
            )

        try:
            return InvalidGrantRequest.to_oauth2_message(
                response.json(), InvalidGrantRequest.request_errors
            )
        except JSONDecodeError:
            return response.text

    @staticmethod
    def to_oauth2_message(content: dict, errors: dict) -> str:
        """
        Handle content as described in:
            * https://tools.ietf.org/html/rfc6749#section-5.2
            * https://tools.ietf.org/html/rfc6749#section-4.1.2.1
            * https://tools.ietf.org/html/rfc6749#section-4.2.2.1
        """

        def _pop(key: str) -> str:
            value = content.pop(key, None)
            if value and isinstance(value, list):
                value = value[0]
            return value

        if "error" in content:
            error = _pop("error")
            known_error = errors.get(error)
            if not known_error:
                logger.error(
                    f"While performing Single sign-on with company account, "
                    f"an unknown error was received, details: {error}"
                )
                return "Unknown error, please try to login again."
            logger.error(
                f"While performing Single sign-on with company account, "
                f"an unknown error was received, details: {_pop('error_description')}"
            )
            error_description = _pop("error_description") or known_error
            message = f"{error}: {error_description}"
            if "error_uri" in content:
                message += f"\nMore information can be found on {_pop('error_uri')}"
            if content:
                message += f"\nAdditional information: {content}"
        else:
            message = f"{content}"
        return message


class StateNotProvided(Exception):
    """State was not provided."""

    def __init__(self, dictionary_without_state: dict):
        super().__init__(f"state not provided within {dictionary_without_state}.")
