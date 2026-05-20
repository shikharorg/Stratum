from __future__ import annotations

import abc

from app.models.connector import Connector


class BaseConnector(abc.ABC):
    def __init__(self, connector: Connector, credentials: dict) -> None:
        self._connector = connector
        self._credentials = credentials

    @abc.abstractmethod
    async def fetch_items(self) -> list[dict]: ...

    @abc.abstractmethod
    async def format_item(self, item: dict) -> dict: ...

    @abc.abstractmethod
    async def handle_webhook(self, payload: dict) -> list[dict]: ...

    @abc.abstractmethod
    async def send_output(self, content: str, destination: dict) -> bool: ...

    def get_sync_cursor(self) -> str | None:
        return self._connector.sync_config.get("sync_cursor")

    def set_sync_cursor(self, cursor: str) -> dict:
        return {"sync_cursor": cursor}
