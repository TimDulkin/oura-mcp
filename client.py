"""
Oura API client — pure stdlib, hardcoded base URL.

This module is the *only* place we make HTTP calls. The base URL is a constant.
By construction this code cannot reach any host other than api.ouraring.com.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

BASE_URL = "https://api.ouraring.com/v2/usercollection"
TIMEOUT_SECONDS = 30


def _load_token() -> str:
    token = os.environ.get("OURA_TOKEN")
    if token:
        return token.strip()

    token_path = Path.home() / ".config" / "oura-mcp" / "token"
    if token_path.exists():
        token = token_path.read_text().strip()
        if token and token != "PASTE_TOKEN_HERE":
            return token

    raise RuntimeError(
        "Oura token not found. Set OURA_TOKEN env var or create "
        f"{token_path} with your PAT from https://cloud.ouraring.com/personal-access-tokens"
    )


class OuraClient:
    """Thin wrapper. One method (request) + date helpers."""

    def __init__(self) -> None:
        self._token = _load_token()

    def request(self, endpoint: str, params: dict[str, str] | None = None) -> dict:
        """GET BASE_URL/<endpoint>?<params>. Returns parsed JSON."""
        url = f"{BASE_URL}/{endpoint}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(
            url, headers={"Authorization": f"Bearer {self._token}"}
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as r:
            return json.loads(r.read().decode())

    @staticmethod
    def yesterday() -> str:
        return (date.today() - timedelta(days=1)).isoformat()

    @staticmethod
    def days_ago(n: int) -> str:
        return (date.today() - timedelta(days=n)).isoformat()
