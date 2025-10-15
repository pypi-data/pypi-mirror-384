from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

from loguru import logger

try:
    from azure.data.tables import TableServiceClient
except Exception:  # pragma: no cover
    TableServiceClient = None  # type: ignore


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AzureTableService:
    connection_string: Optional[str] = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    def _get_client(self) -> "TableServiceClient":
        if not self.connection_string:
            raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING not configured")
        if TableServiceClient is None:
            raise RuntimeError("azure-data-tables not installed; install to use table operations")
        clean = self.connection_string.strip().strip('"').strip("'")
        return TableServiceClient.from_connection_string(conn_str=clean)

    def ensure_table(self, table_name: str) -> None:
        client = self._get_client()
        try:
            client.create_table_if_not_exists(table_name=table_name)
        except Exception as e:
            logger.warning("ensure_table(%s) warning: %s", table_name, e)

    def put_entity(self, table_name: str, entity: Dict[str, Any]) -> Dict[str, Any]:
        client = self._get_client()
        table = client.get_table_client(table_name)
        res = table.create_entity(entity=entity)
        logger.info(
            "Inserted entity into %s: PK=%s RK=%s",
            table_name,
            entity.get("PartitionKey"),
            entity.get("RowKey"),
        )
        return {"etag": getattr(res, "etag", None), "ts": _now_iso()}

    def upsert_entity(self, table_name: str, entity: Dict[str, Any]) -> Dict[str, Any]:
        client = self._get_client()
        table = client.get_table_client(table_name)
        res = table.upsert_entity(entity=entity, mode="merge")
        logger.info(
            "Upserted entity into %s: PK=%s RK=%s",
            table_name,
            entity.get("PartitionKey"),
            entity.get("RowKey"),
        )
        return {"etag": getattr(res, "etag", None), "ts": _now_iso()}

    def delete_entity(self, table_name: str, partition_key: str, row_key: str) -> bool:
        client = self._get_client()
        table = client.get_table_client(table_name)
        try:
            table.delete_entity(partition_key=partition_key, row_key=row_key)
            logger.info("Deleted entity in %s (%s/%s)", table_name, partition_key, row_key)
            return True
        except Exception as exc:
            logger.error("Failed to delete entity in %s: %s", table_name, exc)
            return False

    def query(self, table_name: str, filter_query: str) -> Iterable[Dict[str, Any]]:
        client = self._get_client()
        table = client.get_table_client(table_name)
        for entity in table.query_entities(filter=filter_query):
            yield dict(entity)

