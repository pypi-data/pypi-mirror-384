import hashlib
import shutil
import tempfile
import warnings
from pathlib import Path
from typing import Optional, Union

import requests

from apheris_auth.core.api import get_client
from apheris_auth.core.exceptions import ObjectNotFound


def download_file(url, file_path):
    """
    Download a file from `url` to `target_dir/file_path` and return the path.
    """

    download_path = Path(file_path)
    download_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with requests.get(url, stream=True) as response_download:
            response_download.raise_for_status()

            with download_path.open("wb") as f:
                shutil.copyfileobj(response_download.raw, f)

        return str(download_path)

    except requests.exceptions.RequestException:
        return None


def compute_hash(file_path: Union[str, Path]) -> str:
    """
    Return the SHA-256 hash of the file at `file_path`.
    """
    h = hashlib.sha256()

    with open(file_path, "rb") as file:
        while True:
            chunk = file.read(h.block_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


class RemoteData:
    """Handle to a Dataset in the Apheris Platform.

    A RemoteData object allows you to </br>
    (1) access locally saved Dummy Data path using the `object_name.dummy_data_path`
    attribute, </br>
    (2) describe the Dataset with the `describe()` function, </br>
    (3) test federated computations on Dummy Data, and </br>
    (4) run federated computations on Real Data. </br>
    """

    def __init__(self, id: str):
        """
        To initialize, specify the unique Dataset id.
        `list_datasets` lists available Datasets and their id's.
        """
        self.id = id
        # Fetch details from API
        self.client = get_client()
        self.dataset_ref = self.client.get_dataset(id)
        self.file_details = self.client.get_dataset_file_details(id)
        # Set details
        self.name = self.dataset_ref.get("name")
        self.organization = self.dataset_ref.get("organization")
        self.node = self.dataset_ref.get("node", {})
        self.owner = self.dataset_ref.get("owner", {})
        self.description = self.dataset_ref.get("description", "")
        # Download dummy
        self.dummy_data_path = self._download_dummy_data()

        # TODO: Should this be set or used via getter/setter?
        self.privacy = None
        self.policies = None

    @staticmethod
    def _get_s3_key_from_full_path(path: str) -> Path:
        """Get keys from paths like s3://bucket_name/keys"""
        return Path("").joinpath(*Path(path).parts[2:])

    def _download_dummy_data(self) -> Optional[str]:
        """Download dummy data from filepath in RemoteData.file_details"""
        dummy_files = self.file_details["data"].get("dummy_data", {}).get("files", {})
        dummy_ref = self.dataset_ref["data"].get("dummy_data", {}).get("files", {})
        if not dummy_files:
            # Try to use dataset_ref data if available
            # (all information will be stored there in the future, won't be necessary)
            dummy_files = dummy_ref
        if dummy_files:
            # TODO: Support for multiple files
            dummy_file_name = list(dummy_files.keys())[0]
            dummy_url = dummy_files[dummy_file_name]
            try:
                dummy_file_s3_path = list(dummy_ref.values())[0]
                dummy_file = self._get_s3_key_from_full_path(dummy_file_s3_path)
            except IndexError:
                dummy_file = Path(self.id, "dummy_data", dummy_file_name)
            # TODO: implement careful caching by updated_at

            expected_dummy_path = get_remote_data_path() / dummy_file

            if expected_dummy_path.is_file() and expected_dummy_path.exists():
                # The expected file already exists. If possible, we want to avoid
                # overwriting the existing file.
                with tempfile.TemporaryDirectory() as tmp_dir:
                    tmp_file_path = Path(tmp_dir) / "tmp_file"
                    tmp_dummy_path = download_file(dummy_url, tmp_file_path)
                    if not tmp_dummy_path:
                        # We display a warning so
                        #   - if dummy data was already locally present user can use it
                        #   - user can perform remote Runs without being blocked by
                        #     RemoteData object's initialization
                        warnings.warn(
                            f"Dummy data cannot be downloaded for RemoteData object "
                            f"with id={self.id}",
                            UserWarning,
                            stacklevel=2,
                        )
                        return None
                    hash_of_downloaded_file = compute_hash(tmp_dummy_path)
                    hash_of_existing_file = compute_hash(expected_dummy_path)
                    if hash_of_downloaded_file == hash_of_existing_file:
                        # The downloaded and the existing file are equal. We do not need
                        # to replace the existing one.
                        pass
                    else:
                        shutil.copy(tmp_dummy_path, expected_dummy_path)
                    dummy_path = expected_dummy_path
            else:
                dummy_path = download_file(dummy_url, expected_dummy_path)
            if dummy_path is not None:
                return str(dummy_path)

        return None

    # Get config for runs

    def _get_local_config(self) -> dict:
        """Return config to start local runs"""
        if not self.dummy_data_path:
            # No dummy data
            raise RuntimeError("Missing dummy data")

        return {
            "id": self.id,
            "node": self.id.split("_")[-2],
            "node_id": self.node.get("id"),
            "aws_account": self.node.get("aws_account"),
            "path": self.dummy_data_path,
            "organization": self.organization,
        }

    def _get_cloud_config(self) -> dict:
        """Return config for remote runs"""

        return {
            "id": self.id,
            "node": self.node.get("name"),
            "node_id": self.node.get("id"),
            "aws_account": self.node.get("aws_account"),
            "organization": self.organization,
        }

    # Policy/Privacy getter/setter

    def get_privacy_policy(self) -> dict:
        """Query the privacy policy for this dataset as defined by the data provider.
        Note: If you have overwritten the privacy policy using ._set_privacy() previously,
        you can retrieve the overwritten value from the attribute .privacy.

        Returns:
            a dictionary with privacy settings such as type and parameters,
            the dictionary can be empty if no privacy protection settings are defined.

        """
        try:
            policy = self.client.get_asset_policy_settings(self.id)
            return policy["privacy"]
        except ObjectNotFound:
            return {}

    def get_permissions(self) -> dict:
        """Query the permissions for this dataset as defined by the data provider.
        Note: If you have overwritten the permissions using ._set_policy() previously,
        you can retrieve the overwritten value from the attribute .policy.

        Returns:
            a dictionary with permissions defined for the current user identity.
        """
        try:
            policy = self.client.get_asset_policy_settings(self.id)
            return policy["permissions"]
        except ObjectNotFound:
            return {}

    def _set_privacy(self, privacy: dict):
        """For testing and exploring privacy options: override privacy options for the
        RemoteData object. It is only possible to set privacy options if the Data
        Provider has required no privacy options, that means it is not possible to reduce
        privacy, just to increase.
        """
        if self.get_privacy_policy():
            raise AssertionError(
                "The dataset already has an asset policy attached. You cannot overwrite "
                "the policy."
            )
        else:
            self.privacy = privacy

    def _set_policy(self, policy: dict):
        """For testing and exploring policy options: override policy options for the
        RemoteData object. Will only have an effect if this is stricter than
        what the Data Provider defined and stored in backend database."""
        self.policies = policy

    # Standards

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other) -> bool:
        return other and self.id == other.id

    def __str__(self) -> str:
        s = (
            f"RemoteData(name='{self.name}', id='{self.id}', owner='{self.owner}', "
            f"organization='{self.organization}')"
        )
        return s

    def __repr__(self) -> str:
        return f"RemoteData(id='{self.id}')"


def get_remote_data_path() -> Path:
    return Path.home() / ".apheris" / "RemoteData"
