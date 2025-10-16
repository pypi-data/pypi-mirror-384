## cloud-storage-clients

`cloud-storage-clients` is a Python library for having an unique interface over different cloud storage providers.
It can be used to connect a python client to providers.
This package is maintained by [Picsellia](https://fr.picsellia.com/).

This has been conceived for you to override classes.
For example, override VaultRepository if you retrieve credentials in another way.
You can create or override factories of client to add some additional parameters.

## Installation

Add it to your [poetry](https://python-poetry.org/)  environment
```bash
poetry add cloud-storage-clients
```

Or use the package manager [pip](https://pip.pypa.io/en/stable/) to install it.
```bash
pip install cloud-storage-clients
```

## Usage

### Basic client usage to retrieve a specific object name from an S3 bucket
```python
from cloud_storage_clients.connector import Connector
from cloud_storage_clients.s3.client import S3Client

connector = Connector(client_type="s3", bucket="my-bucket")

client = S3Client(connector, {"access_key_id": "access-key", "secret_access_key": "secret-access-key" })

with open("/path/object-name.jpg", "wb") as file:
    response = client.get("object-name.jpg")
    file.write(response.content)

```

### Pool Instanciation
```python
from cloud_storage_clients.connector import Connector
from cloud_storage_clients.s3.factory import S3ClientFactory
from cloud_storage_clients.repositories.vault_adapter import DefaultVaultAdapter, TokenCredentials
from cloud_storage_clients.repositories.vault import VaultCredentialRepository
from cloud_storage_clients.pool import ClientPool

# Login to your Vault by creating a VaultAdapter and its repository
vault_adapter = DefaultVaultAdapter(
    url="http://localhost:7200",
    credentials=TokenCredentials(token="vault_token", unseal_key="unseal_key")
)
repository = VaultCredentialRepository(adapter=vault_adapter)

# Instantiate a ClientPool and add an S3ClientFactory for minio client_type
pool = ClientPool(default_repository=repository)
pool.register_factory("minio", factory=S3ClientFactory())

# Create a connector object
connector = Connector(client_type="minio", bucket="my-bucket")

# Use pool to instantiate a client that have its credentials in Vault
client = pool.get_client(connector)

# Generate a presigned url that an user without access to your bucket can download
presigned_url = client.get_download_url("object-name", 3600).url



```
