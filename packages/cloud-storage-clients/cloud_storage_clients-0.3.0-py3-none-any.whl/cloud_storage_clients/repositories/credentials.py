import abc

from cloud_storage_clients.connector import Connector


class CredentialRepository(abc.ABC):
    """
    `CredentialRepository` are used by `ClientPool` to retrieve credentials for given `Connector`.
    It should implement get_credentials(connector: Connector) that takes a connector as input
    and return a dict containing credentials used to instantiate a `Client` for example.
    """

    @abc.abstractmethod
    def get_credentials(self, connector: Connector) -> dict:
        pass

    @abc.abstractmethod
    def update_credentials(self, connector: Connector, secret_data: dict) -> None:
        pass

    @abc.abstractmethod
    def delete_credentials(self, connector: Connector) -> None:
        pass
