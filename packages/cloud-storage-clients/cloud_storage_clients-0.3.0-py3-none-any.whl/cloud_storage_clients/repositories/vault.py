from cloud_storage_clients.connector import Connector
from cloud_storage_clients.exceptions import RepositoryError
from cloud_storage_clients.repositories import vault_adapter
from cloud_storage_clients.repositories.credentials import CredentialRepository


class VaultCredentialRepository(CredentialRepository):
    """
    This repository can be used to read credentials through a (Vault)[https://www.vaultproject.io/] secrets manager.
    It needs a VaultAdapter, that you need to instantiate and give to constructor.
    A VaultAdapter class should implement at least get_secrets(vault_key: str).

    By default, this repository will build a vault key from given connector id and add a prefix to it.
    """

    def __init__(self, adapter: vault_adapter.VaultAdapter, prefix: str | None = None):
        self.prefix = prefix or ""
        self.adapter = adapter

    def get_credentials(self, connector: Connector) -> dict:
        vault_key = self.build_vault_key(connector)
        try:
            return self.adapter.get_secrets(vault_key)
        except Exception as e:
            raise RepositoryError(
                f"Could not retrieve credentials of connector {connector.key} from Vault"
            ) from e

    def update_credentials(self, connector: Connector, secret_data: dict) -> dict:
        vault_key = self.build_vault_key(connector)
        try:
            return self.adapter.update_secrets(vault_key, secret_data)
        except Exception as e:
            raise RepositoryError(
                f"Could not update credentials of connector {connector.key} from Vault"
            ) from e

    def delete_credentials(self, connector: Connector) -> dict:
        vault_key = self.build_vault_key(connector)
        try:
            return self.adapter.delete_secrets(vault_key)
        except Exception as e:
            raise RepositoryError(
                f"Could not delete credentials of connector {connector.key} from Vault"
            ) from e

    def build_vault_key(self, connector: Connector):
        vault_path = connector.key

        if self.prefix:
            vault_path = f"{self.prefix}/{vault_path}"

        return vault_path
