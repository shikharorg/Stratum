from __future__ import annotations

import hashlib
import hmac

import httpx
import structlog

from app.connectors.base import BaseConnector
from app.models.connector import Connector

logger = structlog.get_logger()

_SLACK_API = "https://slack.com/api"


class SlackConnector(BaseConnector):
    def __init__(self, connector: Connector, credentials: dict) -> None:
        super().__init__(connector, credentials)
        self._bot_token: str | None = credentials.get("bot_token")

    def _is_stub(self) -> bool:
        return not self._bot_token or not self._bot_token.startswith("xoxb-")

    async def fetch_items(self) -> list[dict]:
        if self._is_stub():
            logger.warning("slack.fetch_items.stub", connector_id=str(self._connector.id))
            return []

        cursor = self.get_sync_cursor()
        params: dict = {"limit": 200}
        if cursor:
            params["cursor"] = cursor

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_SLACK_API}/conversations.history",
                headers={"Authorization": f"Bearer {self._bot_token}"},
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        messages: list[dict] = data.get("messages", [])
        logger.info("slack.fetch_items.completed", count=len(messages), connector_id=str(self._connector.id))
        return messages

    async def format_item(self, item: dict) -> dict:
        return {
            "text": item.get("text", ""),
            "source_type": "slack",
            "source_url": item.get("permalink"),
            "name": f"slack_message_{item.get('ts', '')}",
            "extra_metadata": {
                "channel": item.get("channel"),
                "user": item.get("user"),
                "timestamp": item.get("ts"),
            },
        }

    async def handle_webhook(self, payload: dict) -> list[dict]:
        if payload.get("type") != "event_callback":
            return []

        if self._connector.webhook_secret:
            raw_body = payload.get("_raw_body", b"")
            timestamp = payload.get("_timestamp", "")
            sig_base = f"v0:{timestamp}:{raw_body}".encode()
            expected = "v0=" + hmac.new(
                self._connector.webhook_secret.encode(),
                sig_base,
                hashlib.sha256,
            ).hexdigest()
            received = payload.get("_signature", "")
            if not hmac.compare_digest(expected, received):
                logger.warning("slack.webhook.invalid_signature", connector_id=str(self._connector.id))
                return []

        event = payload.get("event", {})
        if event.get("type") != "message" or event.get("subtype"):
            return []

        formatted = await self.format_item(event)
        logger.info("slack.webhook.handled", connector_id=str(self._connector.id))
        return [formatted]

    async def send_output(self, content: str, destination: dict) -> bool:
        if self._is_stub():
            logger.warning("slack.send_output.stub", connector_id=str(self._connector.id))
            return True

        channel_id = destination.get("channel_id", "")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_SLACK_API}/chat.postMessage",
                headers={"Authorization": f"Bearer {self._bot_token}"},
                json={"channel": channel_id, "text": content},
            )
            response.raise_for_status()
            data = response.json()

        success: bool = data.get("ok", False)
        logger.info("slack.send_output.completed", ok=success, connector_id=str(self._connector.id))
        return success
