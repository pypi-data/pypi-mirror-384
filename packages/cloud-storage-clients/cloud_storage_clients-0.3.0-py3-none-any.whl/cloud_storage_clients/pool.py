from collections.abc import Callable

from cloud_storage_clients.azure.factory import AzureClientFactory
from cloud_storage_clients.cache import ClientCache, DictCache
from cloud_storage_clients.client import Client
from cloud_storage_clients.connector import Connector
from cloud_storage_clients.exceptions import FactoryNotFoundError
from cloud_storage_clients.gcs.factory import GcsClientFactory
from cloud_storage_clients.repositories.credentials import CredentialRepository
from cloud_storage_clients.s3.factory import S3ClientFactory

ClientFactory = Callable[[Connector, dict | None], Client]

DEFAULT_CLIENT_FACTORIES = {
    "azure": AzureClientFactory(3600),
    "google": GcsClientFactory(),
    "s3": S3ClientFactory(),
}


class ClientPool:
    def __init__(
        self,
        default_repository: CredentialRepository = None,
        client_factories: dict[str, ClientFactory] = None,
        cache: ClientCache = None,
    ):
        self.default_repository = default_repository
        self.client_factories = client_factories or DEFAULT_CLIENT_FACTORIES
        self.cache = cache or DictCache()

    def get_client(
        self,
        connector: Connector,
        repository: CredentialRepository | None = None,
        override_cache: bool = False,
    ) -> Client:
        if self.cache and not override_cache:
            client = self.cache.get(connector)
            if client:
                return client

        try:
            factory = self.client_factories[connector.client_type]
        except KeyError:
            raise FactoryNotFoundError(
                f"No factory found for client type {connector.client_type}"
            )

        credentials = self.get_credentials(connector, repository)

        client = factory(connector, credentials)

        if self.cache:
            self.cache.set(connector, client)

        return client

    def register_factory(self, client_type: str, factory: ClientFactory):
        self.client_factories[client_type] = factory

    def get_credentials(
        self, connector: Connector, repository: CredentialRepository | None
    ):
        if repository:
            return repository.get_credentials(connector)
        elif self.default_repository:
            return self.default_repository.get_credentials(connector)
        else:
            return None

    def reset_cache(self, connector: Connector):
        if self.cache:
            self.cache.delete(connector)
