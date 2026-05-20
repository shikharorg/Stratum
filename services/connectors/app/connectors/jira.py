from __future__ import annotations

import base64

import httpx
import structlog

from app.connectors.base import BaseConnector
from app.models.connector import Connector

logger = structlog.get_logger()


class JiraConnector(BaseConnector):
    def __init__(self, connector: Connector, credentials: dict) -> None:
        super().__init__(connector, credentials)
        self._api_token: str | None = credentials.get("api_token")
        self._domain: str | None = credentials.get("domain")
        self._email: str | None = credentials.get("email")

    def _is_stub(self) -> bool:
        return not self._api_token or not self._domain or not self._email

    def _auth_header(self) -> str:
        token = base64.b64encode(f"{self._email}:{self._api_token}".encode()).decode()
        return f"Basic {token}"

    async def fetch_items(self) -> list[dict]:
        if self._is_stub():
            logger.warning("jira.fetch_items.stub", connector_id=str(self._connector.id))
            return []

        cursor = self.get_sync_cursor()
        start_at = int(cursor) if cursor else 0

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://{self._domain}/rest/api/3/search",
                headers={"Authorization": self._auth_header(), "Accept": "application/json"},
                params={
                    "jql": "project is not EMPTY ORDER BY updated DESC",
                    "startAt": start_at,
                    "maxResults": 50,
                },
            )
            response.raise_for_status()
            data = response.json()

        issues: list[dict] = data.get("issues", [])
        logger.info("jira.fetch_items.completed", count=len(issues), connector_id=str(self._connector.id))
        return issues

    async def format_item(self, item: dict) -> dict:
        fields = item.get("fields", {})
        summary = fields.get("summary", "")
        description = fields.get("description") or ""
        if isinstance(description, dict):
            description = str(description)
        issue_key = item.get("key", "")
        return {
            "text": f"{summary}\n{description}".strip(),
            "source_type": "jira",
            "source_url": f"https://{self._domain}/browse/{issue_key}",
            "name": issue_key,
            "extra_metadata": {
                "project": fields.get("project", {}).get("key"),
                "status": fields.get("status", {}).get("name"),
                "assignee": (fields.get("assignee") or {}).get("displayName"),
                "priority": (fields.get("priority") or {}).get("name"),
            },
        }

    async def handle_webhook(self, payload: dict) -> list[dict]:
        event = payload.get("webhookEvent", "")
        if event not in ("jira:issue_created", "jira:issue_updated"):
            return []

        issue = payload.get("issue")
        if not issue:
            return []

        formatted = await self.format_item(issue)
        logger.info("jira.webhook.handled", event=event, connector_id=str(self._connector.id))
        return [formatted]

    async def send_output(self, content: str, destination: dict) -> bool:
        if self._is_stub():
            logger.warning("jira.send_output.stub", connector_id=str(self._connector.id))
            return True

        issue_key = destination.get("issue_key", "")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://{self._domain}/rest/api/3/issue/{issue_key}/comment",
                headers={"Authorization": self._auth_header(), "Content-Type": "application/json"},
                json={"body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": content}]}]}},
            )
            response.raise_for_status()

        logger.info("jira.send_output.completed", issue_key=issue_key, connector_id=str(self._connector.id))
        return True
