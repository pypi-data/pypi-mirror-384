from cloud_storage_clients.connector import Connector
from cloud_storage_clients.repositories.credentials import CredentialRepository


class ConstantCredentialRepository(CredentialRepository):
    """This class can be used as a CredentialRepository to always return the same credentials"""

    def __init__(self, credentials: dict):
        self.credentials = credentials

    def get_credentials(self, connector: Connector) -> dict:
        return self.credentials

    def update_credentials(self, connector: Connector, secret_data: dict) -> None:
        self.credentials = secret_data

    def delete_credentials(self, connector: Connector) -> None:
        self.credentials = {}
