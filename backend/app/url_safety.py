"""Conservative URL preflight for authorized media references.

This function does not download content and is NOT a complete SSRF defense.
"""
from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit


class UnsafeMediaURL(ValueError):
    """A URL is not acceptable as an external media source."""


def validate_media_url(raw: str, *, allowed_hosts: set[str] | None = None) -> str:
    """Accept HTTPS URLs only when the exact DNS host is allowlisted.

    The eventual fetcher must also validate DNS answers and redirects, pin the
    validated IP, enforce egress rules, and limit response sizes and timeouts.
    """
    if not isinstance(raw, str) or not raw or len(raw) > 2048:
        raise UnsafeMediaURL("Invalid URL length")
    if raw != raw.strip() or any(ord(c) < 33 or ord(c) == 127 for c in raw):
        raise UnsafeMediaURL("Whitespace or control characters are forbidden")
    try:
        parsed = urlsplit(raw)
        host = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise UnsafeMediaURL("Malformed URL") from exc
    if parsed.scheme != "https" or not host:
        raise UnsafeMediaURL("Only HTTPS URLs are supported")
    if parsed.username is not None or parsed.password is not None:
        raise UnsafeMediaURL("URL credentials are forbidden")
    if parsed.fragment:
        raise UnsafeMediaURL("URL fragments are forbidden")
    if port not in (None, 443):
        raise UnsafeMediaURL("Nonstandard ports are forbidden")
    host = host.lower().rstrip(".")
    if not host or host in {"localhost", "localhost.localdomain"}:
        raise UnsafeMediaURL("Local hosts are forbidden")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise UnsafeMediaURL("IP literals are forbidden")
    if host.endswith((".localhost", ".local", ".internal", ".test", ".invalid")):
        raise UnsafeMediaURL("Internal or reserved hosts are forbidden")
    if "." not in host or any(not label or len(label) > 63 for label in host.split(".")):
        raise UnsafeMediaURL("Invalid DNS hostname")
    if allowed_hosts is None or host not in {h.lower().rstrip(".") for h in allowed_hosts}:
        raise UnsafeMediaURL("Host is not approved for direct media ingestion")
    return raw
