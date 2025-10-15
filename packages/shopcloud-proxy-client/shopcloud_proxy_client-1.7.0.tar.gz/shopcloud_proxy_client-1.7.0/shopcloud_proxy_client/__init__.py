"""
ShopCloud Proxy Client
======================

A simple wrapper around requests that transparently routes all HTTP requests
through the ShopCloud Proxy API.

Usage:
    from shopcloud_proxy_client import ProxySession

    # Create session with your proxy credentials
    session = ProxySession(
        proxy_url="https://test-proxy.example.dev",
        username="your-username",
        password="your-password"
    )

    # Use it like normal requests!
    response = session.get("https://api.github.com/users/octocat")
    print(response.json())

    # Or use the convenience functions
    import shopcloud_proxy_client as proxy

    proxy.configure(
        proxy_url="https://test-proxy.example.dev",
        username="your-username",
        password="your-password"
    )

    response = proxy.get("https://api.github.com/users/octocat")
    print(response.json())
"""

from .client import (
    ProxyAuthenticationError,
    ProxyError,
    ProxyRateLimitError,
    ProxySession,
    ProxyTargetError,
    ProxyTimeoutError,
    configure,
    delete,
    get,
    head,
    options,
    patch,
    post,
    put,
)

__version__ = "1.7.0"
__all__ = [
    "ProxySession",
    "ProxyError",
    "ProxyAuthenticationError",
    "ProxyRateLimitError",
    "ProxyTargetError",
    "ProxyTimeoutError",
    "configure",
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "options",
    "head",
]
