from __future__ import annotations

import hashlib
import hmac

import httpx
import structlog

from app.connectors.base import BaseConnector
from app.models.connector import Connector

logger = structlog.get_logger()

_GITHUB_API = "https://api.github.com"


class GitHubConnector(BaseConnector):
    def __init__(self, connector: Connector, credentials: dict) -> None:
        super().__init__(connector, credentials)
        self._token: str | None = credentials.get("personal_access_token")
        self._owner: str = connector.sync_config.get("owner", "")
        self._repo: str = connector.sync_config.get("repo", "")

    def _is_stub(self) -> bool:
        return not self._token or not self._token.startswith("ghp_")

    def _auth_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def fetch_items(self) -> list[dict]:
        if self._is_stub():
            logger.warning("github.fetch_items.stub", connector_id=str(self._connector.id))
            return []

        cursor = self.get_sync_cursor()
        page = int(cursor) if cursor else 1
        items: list[dict] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for endpoint in ("issues", "pulls"):
                response = await client.get(
                    f"{_GITHUB_API}/repos/{self._owner}/{self._repo}/{endpoint}",
                    headers=self._auth_headers(),
                    params={"state": "all", "per_page": 50, "page": page},
                )
                response.raise_for_status()
                batch = response.json()
                for item in batch:
                    item["_is_pull_request"] = endpoint == "pulls"
                items.extend(batch)

        logger.info("github.fetch_items.completed", count=len(items), connector_id=str(self._connector.id))
        return items

    async def format_item(self, item: dict) -> dict:
        is_pr = item.get("_is_pull_request", "pull_request" in item)
        return {
            "text": f"{item.get('title', '')}\n{item.get('body') or ''}".strip(),
            "source_type": "github",
            "source_url": item.get("html_url", ""),
            "name": f"github_{item.get('number', '')}",
            "extra_metadata": {
                "repo": f"{self._owner}/{self._repo}",
                "number": item.get("number"),
                "state": item.get("state"),
                "labels": [lb.get("name") for lb in item.get("labels", [])],
                "is_pull_request": is_pr,
            },
        }

    async def handle_webhook(self, payload: dict) -> list[dict]:
        event_type = payload.get("_event_type", "")
        if event_type not in ("issues", "pull_request"):
            return []

        if self._connector.webhook_secret:
            raw_body = payload.get("_raw_body", b"")
            if isinstance(raw_body, str):
                raw_body = raw_body.encode()
            expected = "sha256=" + hmac.new(
                self._connector.webhook_secret.encode(),
                raw_body,
                hashlib.sha256,
            ).hexdigest()
            received = payload.get("_signature", "")
            if not hmac.compare_digest(expected, received):
                logger.warning("github.webhook.invalid_signature", connector_id=str(self._connector.id))
                return []

        issue = payload.get("issue") or payload.get("pull_request")
        if not issue:
            return []

        if payload.get("pull_request"):
            issue["_is_pull_request"] = True

        formatted = await self.format_item(issue)
        logger.info("github.webhook.handled", event_type=event_type, connector_id=str(self._connector.id))
        return [formatted]

    async def send_output(self, content: str, destination: dict) -> bool:
        if self._is_stub():
            logger.warning("github.send_output.stub", connector_id=str(self._connector.id))
            return True

        owner = destination.get("owner", self._owner)
        repo = destination.get("repo", self._repo)
        issue_number = destination.get("issue_number")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}/comments",
                headers=self._auth_headers(),
                json={"body": content},
            )
            response.raise_for_status()

        logger.info("github.send_output.completed", issue_number=issue_number, connector_id=str(self._connector.id))
        return True
