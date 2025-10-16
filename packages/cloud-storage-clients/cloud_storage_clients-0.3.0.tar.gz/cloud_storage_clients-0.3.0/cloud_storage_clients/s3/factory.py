from cloud_storage_clients.connector import Connector
from cloud_storage_clients.s3.client import S3Client


class S3ClientFactory:
    def __init__(self, default_region_name: str | None = None):
        self.default_region_name = default_region_name

    def __call__(self, connector: Connector, credentials: dict | None):
        return S3Client(connector, credentials, self.default_region_name)
