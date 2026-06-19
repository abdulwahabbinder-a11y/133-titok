"""
Rotating residential proxy helpers for the lightweight scanner.

The sniper runs a visible local browser and typically does not need a proxy,
but you can extend this module if your institute geo-blocks non-residential IPs.
"""

from __future__ import annotations

import secrets
import string
from typing import Any
from urllib.parse import urlparse, urlunparse

from goethe_bot.config import PROXY


def _random_session_id(length: int = 12) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def build_rotating_proxy_url() -> str | None:
    """
    Return a proxy URL for the current scan request.

    Many residential providers rotate IPs when you append a unique session id to
  the username (e.g. user-session-abc123). Adjust the logic to match your vendor.
    """
    if not PROXY.enabled:
        return None

    endpoint = PROXY.rotating_endpoint.strip()
    if not endpoint or "REPLACE" in endpoint or "example" in endpoint:
        return None

    session = f"{PROXY.session_id_prefix}{_random_session_id()}"
    parsed = urlparse(endpoint)

    if parsed.username and parsed.password:
        # Provider pattern: http://user-session-ID:pass@host:port
        username = f"{parsed.username}-{session}"
        netloc = f"{username}:{parsed.password}@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"
        return urlunparse(parsed._replace(netloc=netloc))

    return endpoint


def playwright_proxy_dict() -> dict[str, Any] | None:
    """Format proxy for Playwright `browser.new_context(proxy=...)`."""
    url = build_rotating_proxy_url()
    if not url:
        return None
    parsed = urlparse(url)
    proxy: dict[str, Any] = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
    if parsed.username:
        proxy["username"] = parsed.username
    if parsed.password:
        proxy["password"] = parsed.password
    return proxy
