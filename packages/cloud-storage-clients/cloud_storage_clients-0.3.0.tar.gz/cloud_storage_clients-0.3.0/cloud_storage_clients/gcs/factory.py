from cloud_storage_clients.connector import Connector
from cloud_storage_clients.gcs.client import GcsClient


class GcsClientFactory:
    def __call__(self, connector: Connector, credentials: dict | None):
        return GcsClient(connector, credentials)
