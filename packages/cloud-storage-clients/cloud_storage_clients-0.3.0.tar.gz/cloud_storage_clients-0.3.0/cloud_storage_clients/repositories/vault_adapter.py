import abc
from dataclasses import dataclass

import hvac
import hvac.adapters
import hvac.exceptions


class VaultAdapter(abc.ABC):
    """This class can be implemented to connect to a Vault secrets manager.
    It will be used by a VaultCredentialRepository to access and retrieve secrets holding connectors credentials.
    """

    @abc.abstractmethod
    def get_secrets(self, vault_key: str):
        pass

    @abc.abstractmethod
    def update_secrets(self, vault_key: str, secret_data: dict):
        pass

    @abc.abstractmethod
    def delete_secrets(self, vault_key: str):
        pass


@dataclass
class SecretCredentials:
    role_id: str
    secret_id: str


@dataclass
class TokenCredentials:
    token: str


class DefaultVaultAdapter(VaultAdapter):
    def __init__(
        self,
        url: str,
        *,
        vault_client: hvac.Client | None = None,
        credentials: SecretCredentials | TokenCredentials | None = None,
        unseal_keys: list[str] | None = None,
        hvac_client_verify: bool = True,
        secret_mount: str | None = None,
        hvac_adapter: type[hvac.adapters.Adapter] = hvac.adapters.JSONAdapter,
    ):
        self.url = url
        self.hvac_client_verify = hvac_client_verify
        self.secret_mount = secret_mount or ""
        self.credentials = credentials
        self.unseal_keys = unseal_keys

        if vault_client:
            self.client = vault_client
        elif credentials is not None:
            self.client = hvac.Client(
                url=url,
                verify=hvac_client_verify,
                adapter=hvac_adapter,
            )
        else:
            raise RuntimeError(
                "Please give a vault client or credentials as VaultSecret or VaultToken"
            )

        if isinstance(credentials, TokenCredentials):
            self.client.token = credentials.token

    def get_secrets(self, vault_key: str) -> dict:
        self._unseal_and_login()
        return self.client.secrets.kv.v2.read_secret(
            path=vault_key, mount_point=self.secret_mount
        )["data"]["data"]

    def update_secrets(self, vault_key: str, secret_data: dict):
        self._unseal_and_login()
        self.client.secrets.kv.v2.create_or_update_secret(
            path=vault_key,
            secret=secret_data,
            mount_point=self.secret_mount,
        )

    def delete_secrets(self, vault_key: str):
        self._unseal_and_login()
        self.client.secrets.kv.v2.delete_metadata_and_all_versions(
            path=vault_key,
            mount_point=self.secret_mount,
        )

    def _unseal_and_login(self):
        if self.client.sys.is_sealed() and self.unseal_keys:
            for unseal_key in self.unseal_keys:
                self.client.sys.submit_unseal_key(unseal_key)
        if not self.client.is_authenticated():
            self._login()

    def _login(self):
        if isinstance(self.credentials, TokenCredentials):
            self.client.token = self.credentials.token
        elif isinstance(self.credentials, SecretCredentials):
            self.client.auth.approle.login(
                role_id=self.credentials.role_id,
                secret_id=self.credentials.secret_id,
            )
        else:
            raise RuntimeError("Vault Client not authenticated.")
