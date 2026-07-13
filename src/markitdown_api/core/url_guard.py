"""SSRF guardrail for user-supplied URLs passed to markitdown's convert()."""

import ipaddress
import socket

_ALLOWED_SCHEMES = {"http", "https"}


class UnsafeUrlError(ValueError):
    """Raised when a user-supplied URL fails scheme or destination checks."""


def _is_blocked_address(host: str) -> bool:
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        return False
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local  # covers cloud metadata endpoints (169.254.169.254)
        or addr.is_reserved
        or addr.is_multicast
    )


def ensure_public_http_url(url: str) -> None:
    """Raise UnsafeUrlError if the URL is not a safe public http(s) destination."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise UnsafeUrlError(f"URL scheme '{parsed.scheme}' is not allowed")
    if not parsed.hostname:
        raise UnsafeUrlError("URL is missing a hostname")

    if _is_blocked_address(parsed.hostname):
        raise UnsafeUrlError("URL resolves to a blocked network destination")

    try:
        resolved = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror as err:
        raise UnsafeUrlError(f"Could not resolve host '{parsed.hostname}'") from err

    for _family, _, _, _, sockaddr in resolved:
        ip = sockaddr[0]
        if _is_blocked_address(ip):
            raise UnsafeUrlError("URL resolves to a blocked network destination")
