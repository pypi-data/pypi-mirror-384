# srx-lib-azure

Lightweight wrappers over Azure SDKs used across SRX services.

What it includes:
- Blob: upload/download helpers, SAS URL generation
- Email (Azure Communication Services): simple async sender
- Table: simple CRUD helpers

## Install

PyPI (public):

- `pip install srx-lib-azure`

uv (pyproject):
```
[project]
dependencies = ["srx-lib-azure>=0.1.0"]
```

## Usage

Blob:
```
from srx_lib_azure.blob import AzureBlobService
blob = AzureBlobService()
url = await blob.upload_file(upload_file, "documents/report.pdf")
```

Email:
```
from srx_lib_azure.email import EmailService
svc = EmailService()
await svc.send_notification("user@example.com", "Subject", "Hello", html=False)
```

Table:
```
from srx_lib_azure.table import AzureTableService
store = AzureTableService()
store.ensure_table("events")
store.upsert_entity("events", {"PartitionKey":"p","RowKey":"r","EventType":"x"})
```

## Environment Variables

- Blob & Table: `AZURE_STORAGE_CONNECTION_STRING` (required)
- Email (ACS): `ACS_CONNECTION_STRING`, `EMAIL_SENDER`
- Optional: `AZURE_STORAGE_ACCOUNT_KEY`, `AZURE_BLOB_URL`, `AZURE_SAS_TOKEN`

## Release

Tag `vX.Y.Z` to publish to GitHub Packages via Actions.

## License

Proprietary © SRX
