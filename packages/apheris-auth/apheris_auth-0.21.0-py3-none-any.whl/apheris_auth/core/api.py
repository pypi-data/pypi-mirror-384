import functools
import json
from typing import Dict, List

import jwt
import requests

from ..config import settings
from . import auth, exceptions


def create_token_debug_msg(access_token: str) -> str:
    claims = jwt.decode(access_token, options={"verify_signature": False})
    payload = json.dumps(claims, indent=2)
    return f"\nAccess token details used in the unauthorized API call:\n{payload}"


def handle_api_exception(func):
    """
    Decorator to treat exceptions raised by API calls.
    If we know what happened, we add a reason to the response object.
    """

    def _add_reason(response):
        """
        Add the reason for failure to the `response` if available.
        """
        # Only add reason if it was our API
        if response.url.startswith(settings.API_BASE_URL):
            try:
                res = response.json()
            except (json.JSONDecodeError, requests.exceptions.JSONDecodeError):
                details = response.text
            else:
                details = res.get("detail", res)

            if details:
                response.reason = details

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except requests.exceptions.ConnectionError:
            msg = (
                "Failed to connect to the Apheris Platform.\n"
                "Please check your network connection."
            )
            raise exceptions.ConnectionError(msg) from None

        except requests.exceptions.HTTPError as exc:
            # Map to our own exceptions
            if exc.response.status_code == 500:
                ex = exceptions.ServerError
            elif exc.response.status_code == 403:
                ex = exceptions.AccessDenied
            elif exc.response.status_code == 404:
                ex = exceptions.ObjectNotFound
                try:
                    detail = exc.response.json().get("detail")
                    # caller might set a proper reason before raising an error
                    # otherwise it would still be default http.client.responses[404] value
                    if detail and exc.response.reason == "Not Found":
                        exc.response.reason = detail
                except requests.exceptions.InvalidJSONError:
                    pass
            elif exc.response.status_code == 401:
                ex = exceptions.Unauthorized
                msg = "You are not logged in.\nPlease run 'apheris login' in the CLI."
                if auth_header := exc.request.headers.get("Authorization"):
                    try:
                        access_token = auth_header.split()[1]
                    except IndexError:
                        pass
                    else:
                        msg += create_token_debug_msg(access_token)

                exc.response.reason = msg

            elif exc.response.status_code == 400 or exc.response.status_code == 424:
                # apheris API bad request errors contain the details key
                # We may also use other APIs, that don't have details
                ex = exceptions.BadRequest
                _add_reason(exc.response)
            else:
                # Generic error for everything else
                ex = requests.exceptions.HTTPError
                _add_reason(exc.response)

            raise ex(exc.response.reason) from None

    return wrapper


class ApherisAPI:
    """
    Wrapper around the Apheris API.
    """

    def __init__(self) -> None:
        self._session, self._session_type = auth.get_session()

    @handle_api_exception
    def get_dataset(self, dataset_id: str) -> Dict:
        """
        Return information of dataset with `dataset_id` (slug).
        """
        response = self._session.get(settings.API_DATASETS_URL + dataset_id + "/")

        if response.status_code == 403:
            response.reason = (
                f"You do not have permissions to access the dataset `{dataset_id}`."
            )

        if response.status_code == 404:
            response.reason = "No dataset found for id " + dataset_id

        response.raise_for_status()
        return response.json()

    @handle_api_exception
    def get_dataset_file_details(self, dataset_id: str) -> Dict:
        """
        Return file details of the dataset with `dataset_id`.
        """
        # TODO: Return directly with get_dataset from API
        response = self._session.get(f"{settings.API_DATASETS_URL}{dataset_id}/download/")

        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            if settings.VERBOSE:
                print(
                    f"Could not get dataset file details for RemoteData object "
                    f"with id='{dataset_id}': {response.reason}: {response.text}",
                )
            return {"data": {}}

    @handle_api_exception
    def get_datasets(self) -> List[Dict]:
        """
        Return available datasets for the current user.
        """
        response = self._session.get(settings.API_DATASETS_URL)
        response.raise_for_status()

        return response.json()

    @handle_api_exception
    def get_asset_policy_settings(self, dataset_id: str) -> Dict:
        """
        Return the settings (permission and privacy) of an Asset policy of the dataset
        with `dataset_id`.
        """
        response = self._session.get(
            f"{settings.API_ASSET_POLICIES_URL}settings/{dataset_id}/"
        )

        if response.status_code == 403:
            response.reason = (
                "You do not have permissions to view the asset policy for this dataset."
            )

        if response.status_code == 404:
            response.reason = (
                "Asset policy not found. Please verify the ID of the dataset."
            )

        response.raise_for_status()
        return response.json()

    @handle_api_exception
    def get_user_info(self) -> Dict:
        """
        Returns user info payload
        """
        response = self._session.get(f"{settings.API_USER_INFO_URL}")
        response.raise_for_status()
        return response.json()


def get_client() -> ApherisAPI:
    """
    Apheris API client factory.
    """
    return ApherisAPI()
