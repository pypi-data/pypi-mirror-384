import os

from cloud_storage_clients.connector import Connector
from cloud_storage_clients.repositories.credentials import CredentialRepository


class EnvCredentialRepository(CredentialRepository):
    """
    EnvCredentialRepository is a repository that reads environment variables and parse them into a dict of credentials.
    It uses the client_type of a connector to look for default expected environment variable of known cloud storages.
    """

    AZURE_CLIENT_TYPES = ["azure"]
    GCS_CLIENT_TYPES = ["gcs", "google"]
    S3_CLIENT_TYPES = ["s3", "aws"]

    AZURE_ACCOUNT_URL = "ACCOUNT_URL"
    AZURE_CLIENT_ID = "CLIENT_ID"
    AZURE_TENANT_ID = "TENANT_ID"
    AZURE_CLIENT_SECRET = "CLIENT_SECRET"

    GCS_PRIVATE_KEY = "PRIVATE_KEY"
    GCS_CLIENT_EMAIL = "CLIENT_EMAIL"

    S3_ACCESS_KEY_ID = "ACCESS_KEY_ID"
    S3_SECRET_ACCESS_KEY = "SECRET_ACCESS_KEY"
    S3_ENDPOINT_URL = "ENDPOINT_URL"
    S3_REGION_NAME = "REGION_NAME"

    def __init__(self, prefix: str = ""):
        self.prefix = prefix

    def get_key(self, env):
        return self.prefix + env

    def getenv(self, env):
        key = self.get_key(env)
        var = os.getenv(key)
        if var is None:
            raise KeyError(f"Variable {key} not found in environment.")
        return var

    def setenv(self, env: str, value: str):
        key = self.get_key(env)
        os.environ[key] = value

    def delenv(self, env):
        key = self.get_key(env)
        try:
            del os.environ[key]
        except KeyError:
            pass

    def get_credentials(self, connector: Connector) -> dict:
        if connector.client_type.lower() in self.S3_CLIENT_TYPES:
            return {
                "access_key_id": self.getenv(self.S3_ACCESS_KEY_ID),
                "secret_access_key": self.getenv(self.S3_SECRET_ACCESS_KEY),
                "region_name": self.getenv(self.S3_REGION_NAME),
                "endpoint_url": self.getenv(self.S3_ENDPOINT_URL),
            }
        elif connector.client_type.lower() in self.AZURE_CLIENT_TYPES:
            return {
                "account_url": self.getenv(self.AZURE_ACCOUNT_URL),
                "client_id": self.getenv(self.AZURE_CLIENT_ID),
                "tenant_id": self.getenv(self.AZURE_TENANT_ID),
                "client_secret": self.getenv(self.AZURE_CLIENT_SECRET),
            }
        elif connector.client_type.lower() in self.GCS_CLIENT_TYPES:
            return {
                "private_key": self.getenv(self.GCS_PRIVATE_KEY),
                "client_email": self.getenv(self.GCS_CLIENT_EMAIL),
            }
        raise NotImplementedError("unknown connector type")

    @staticmethod
    def _assert_keys_coherence(secrets: dict, expected_secret_keys: set):
        secret_keys = set(secrets.keys())
        if not expected_secret_keys.issubset(secret_keys):
            raise KeyError(
                f"Some keys are missing: {expected_secret_keys - secret_keys}"
            )

    def update_credentials(self, connector: Connector, secret_data: dict) -> None:
        if connector.client_type.lower() in self.AZURE_CLIENT_TYPES:
            self._assert_keys_coherence(
                secret_data, {"account_url", "client_id", "tenant_id", "client_secret"}
            )
            self.setenv(self.AZURE_ACCOUNT_URL, secret_data["account_url"])
            self.setenv(self.AZURE_CLIENT_ID, secret_data["client_id"])
            self.setenv(self.AZURE_TENANT_ID, secret_data["tenant_id"])
            self.setenv(self.AZURE_CLIENT_SECRET, secret_data["client_secret"])
        elif connector.client_type.lower() in self.GCS_CLIENT_TYPES:
            self._assert_keys_coherence(secret_data, {"private_key", "client_email"})
            self.setenv(self.GCS_PRIVATE_KEY, secret_data["private_key"])
            self.setenv(self.GCS_CLIENT_EMAIL, secret_data["client_email"])
        elif connector.client_type.lower() in self.S3_CLIENT_TYPES:
            self._assert_keys_coherence(
                secret_data,
                {"access_key_id", "secret_access_key", "region_name", "endpoint_url"},
            )

            self.setenv(self.S3_ACCESS_KEY_ID, secret_data["access_key_id"])
            self.setenv(self.S3_SECRET_ACCESS_KEY, secret_data["secret_access_key"])
            self.setenv(self.S3_REGION_NAME, secret_data["region_name"])
            self.setenv(self.S3_ENDPOINT_URL, secret_data["endpoint_url"])
        else:
            raise NotImplementedError("unknown connector type")

    def delete_credentials(self, connector: Connector) -> None:
        if connector.client_type.lower() in self.S3_CLIENT_TYPES:
            self.delenv(self.S3_ACCESS_KEY_ID)
            self.delenv(self.S3_SECRET_ACCESS_KEY)
            self.delenv(self.S3_REGION_NAME)
            self.delenv(self.S3_ENDPOINT_URL)
        elif connector.client_type.lower() in self.AZURE_CLIENT_TYPES:
            self.delenv(self.AZURE_ACCOUNT_URL)
            self.delenv(self.AZURE_CLIENT_ID)
            self.delenv(self.AZURE_TENANT_ID)
            self.delenv(self.AZURE_CLIENT_SECRET)
        elif connector.client_type.lower() in self.GCS_CLIENT_TYPES:
            self.delenv(self.GCS_PRIVATE_KEY)
            self.delenv(self.GCS_CLIENT_EMAIL)
        else:
            raise NotImplementedError("unknown connector type")
