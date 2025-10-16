"""
ShopCloud Proxy Client Implementation
======================================

Core client that wraps requests to transparently use the ShopCloud Proxy API.
"""

import base64
import binascii
import json
import time
from typing import Any

import requests


class ProxyError(Exception):
    """Base exception for proxy client errors."""

    pass


class ProxyAuthenticationError(ProxyError):
    """Authentication failed or token expired."""

    pass


class ProxyRateLimitError(ProxyError):
    """Rate limit exceeded."""

    pass


class ProxyTargetError(ProxyError):
    """Target API returned an error or is unreachable."""

    pass


class ProxyTimeoutError(ProxyError):
    """Request timed out."""

    pass


class ProxyResponse:
    """
    Wrapper around the proxy API response that mimics requests.Response.

    Allows seamless transition from requests without changing your code.
    """

    def __init__(self, proxy_response: dict, original_url: str):
        """
        Initialize from proxy API response.

        Args:
            proxy_response: Response from /proxy/ endpoint
            original_url: The original target URL requested
        """
        self._proxy_response = proxy_response
        self._original_url = original_url

        # Extract data from proxy response
        self.status_code = proxy_response["status_code"]
        self.headers = proxy_response.get("headers", {})
        self._body = proxy_response.get("body")
        self.duration_ms = proxy_response.get("duration_ms", 0)

        # For compatibility with requests.Response
        self.url = original_url
        self.ok = 200 <= self.status_code < 300
        self.reason = self._get_reason_phrase()

    def _get_reason_phrase(self) -> str:
        """Get HTTP reason phrase from status code."""
        reasons = {
            # 1xx Informational
            100: "Continue",
            101: "Switching Protocols",
            102: "Processing",
            103: "Early Hints",
            # 2xx Success
            200: "OK",
            201: "Created",
            202: "Accepted",
            203: "Non-Authoritative Information",
            204: "No Content",
            205: "Reset Content",
            206: "Partial Content",
            207: "Multi-Status",
            208: "Already Reported",
            226: "IM Used",
            # 3xx Redirection
            300: "Multiple Choices",
            301: "Moved Permanently",
            302: "Found",
            303: "See Other",
            304: "Not Modified",
            305: "Use Proxy",
            307: "Temporary Redirect",
            308: "Permanent Redirect",
            # 4xx Client Errors
            400: "Bad Request",
            401: "Unauthorized",
            402: "Payment Required",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            406: "Not Acceptable",
            407: "Proxy Authentication Required",
            408: "Request Timeout",
            409: "Conflict",
            410: "Gone",
            411: "Length Required",
            412: "Precondition Failed",
            413: "Payload Too Large",
            414: "URI Too Long",
            415: "Unsupported Media Type",
            416: "Range Not Satisfiable",
            417: "Expectation Failed",
            418: "I'm a teapot",
            421: "Misdirected Request",
            422: "Unprocessable Entity",
            423: "Locked",
            424: "Failed Dependency",
            425: "Too Early",
            426: "Upgrade Required",
            428: "Precondition Required",
            429: "Too Many Requests",
            431: "Request Header Fields Too Large",
            451: "Unavailable For Legal Reasons",
            # 5xx Server Errors
            500: "Internal Server Error",
            501: "Not Implemented",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout",
            505: "HTTP Version Not Supported",
            506: "Variant Also Negotiates",
            507: "Insufficient Storage",
            508: "Loop Detected",
            510: "Not Extended",
            511: "Network Authentication Required",
        }
        return reasons.get(self.status_code, "Unknown")

    @property
    def text(self) -> str:
        """Get response body as text."""
        if isinstance(self._body, str):
            return self._body
        elif isinstance(self._body, dict):
            return json.dumps(self._body)
        elif self._body is None:
            return ""
        else:
            return str(self._body)

    @property
    def content(self) -> bytes:
        """Get response body as bytes."""
        return self.text.encode("utf-8")

    def json(self, **kwargs) -> Any:
        """
        Parse response body as JSON.

        Returns:
            Parsed JSON object

        Raises:
            ValueError: If response is not valid JSON
        """
        if isinstance(self._body, dict) or isinstance(self._body, list):
            return self._body
        elif isinstance(self._body, str):
            return json.loads(self._body, **kwargs)
        else:
            raise ValueError(f"Response body is not JSON: {type(self._body)}")

    def raise_for_status(self):
        """
        Raise HTTPError if status code indicates an error.

        Compatible with requests.Response.raise_for_status()
        """
        if not self.ok:
            raise requests.HTTPError(
                f"{self.status_code} {self.reason} for url: {self.url}", response=self
            )


class ProxySession:
    """
    Session object that routes all HTTP requests through ShopCloud Proxy API.

    Usage similar to requests.Session:
        session = ProxySession(
            proxy_url="https://test-proxy.example.dev",
            username="your-username",
            password="your-password",
            default_headers={"User-Agent": "My-Custom-App"}
        )

        response = session.get("https://api.github.com/users/octocat")
        print(response.json())
    """

    def __init__(
        self,
        proxy_url: str,
        username: str,
        password: str,
        auto_login: bool = True,
        default_timeout: int = 30,
        default_headers: dict[str, str] | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize proxy session.

        Args:
            proxy_url: Base URL of the ShopCloud Proxy API
            username: Proxy API username
            password: Proxy API password
            auto_login: Automatically login on first request (default: True)
            default_timeout: Default timeout for requests in seconds (default: 30)
            default_headers: Headers to send with every proxy request (default: None)
            max_retries: Maximum number of retries for transient errors (default: 3)
            retry_delay: Delay in seconds between retries (default: 1.0)
        """
        self.proxy_url = proxy_url.rstrip("/")
        self.username = username
        self.password = password
        self.default_timeout = default_timeout
        self.headers = default_headers if default_headers is not None else {}
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self._session = requests.Session()
        self._token: str | None = None
        self._token_expires_at: float | None = None

        if auto_login:
            self.login()

    def _decode_jwt_exp(self, token: str) -> float | None:
        """
        Extract expiration time from JWT token.

        Args:
            token: JWT token string

        Returns:
            Expiration timestamp (Unix time) or None if cannot parse
        """
        try:
            # JWT format: header.payload.signature
            parts = token.split(".")
            if len(parts) != 3:
                return None

            # Decode payload (add padding if needed)
            payload = parts[1]
            padding = len(payload) % 4
            if padding:
                payload += "=" * (4 - padding)

            decoded = base64.urlsafe_b64decode(payload)
            payload_data = json.loads(decoded)

            # Return exp claim if present
            return payload_data.get("exp")
        except (json.JSONDecodeError, binascii.Error, AttributeError, TypeError):
            # If we can't decode, just return None
            return None

    def login(self) -> str:
        """
        Login to proxy API and get authentication token.

        Returns:
            Access token

        Raises:
            ProxyAuthenticationError: If login fails
        """
        try:
            response = self._session.post(
                f"{self.proxy_url}/auth/token",
                json={"username": self.username, "password": self.password},
            )
            response.raise_for_status()

            self._token = response.json()["access_token"]

            # Try to extract token expiration
            self._token_expires_at = self._decode_jwt_exp(self._token)

            return self._token
        except requests.HTTPError as e:
            raise ProxyAuthenticationError(f"Authentication failed: {e}") from e
        except requests.RequestException as e:
            raise ProxyAuthenticationError(f"Login error: {e}") from e

    def _ensure_authenticated(self):
        """
        Ensure we have a valid authentication token.

        Proactively refreshes token if it expires within 30 seconds.
        """
        if not self._token:
            self.login()
            return

        # Proactive token refresh: renew if expires in < 30 seconds
        if self._token_expires_at:
            time_until_expiry = self._token_expires_at - time.time()
            if time_until_expiry < 30:
                self.login()

    def _proxy_request(
        self,
        method: str,
        url: str,
        headers: dict | None = None,
        data: Any = None,
        json: Any = None,
        timeout: int | None = None,
        **kwargs,
    ) -> ProxyResponse:
        """
        Internal method to make a request through the proxy.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Target URL to request
            headers: Optional headers to forward
            data: Optional request body data
            json: Optional JSON body
            timeout: Optional timeout in seconds
            **kwargs: Additional arguments (for compatibility, mostly ignored)

        Returns:
            ProxyResponse object

        Raises:
            ProxyAuthenticationError: If authentication fails
            ProxyRateLimitError: If rate limit is exceeded
            ProxyTimeoutError: If request times out
            ProxyTargetError: If target API returns error
            ProxyError: For other proxy-related errors
        """
        self._ensure_authenticated()

        # Merge default headers with request-specific headers
        final_headers = self.headers.copy()
        if headers:
            final_headers.update(headers)

        # Prepare proxy request body
        proxy_request = {
            "url": url,
            "method": method.upper(),
            "timeout": timeout or self.default_timeout,
        }

        # Add headers if provided (now contains default and specific headers)
        if final_headers:
            proxy_request["headers"] = final_headers

        # Add body if provided
        if json is not None:
            # Convert JSON to string for proxy API
            proxy_request["body"] = json if isinstance(json, str) else json
        elif data is not None:
            if isinstance(data, str):
                proxy_request["body"] = data
            else:
                raise TypeError(f"data parameter must be str, not {type(data).__name__}")

        # Retry loop for transient errors
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                # Make request to proxy API
                response = self._session.post(
                    f"{self.proxy_url}/proxy/",
                    headers={"Authorization": f"Bearer {self._token}"},
                    json=proxy_request,
                )

                # Handle authentication errors (token expired)
                if response.status_code == 401:
                    self.login()  # Re-login
                    # Retry request with new token
                    response = self._session.post(
                        f"{self.proxy_url}/proxy/",
                        headers={"Authorization": f"Bearer {self._token}"},
                        json=proxy_request,
                    )

                # Check for specific error types with better messages
                if response.status_code == 429:
                    raise ProxyRateLimitError(
                        "Rate limit exceeded for proxy API. Please slow down requests."
                    )

                # Check for transient errors that should be retried
                if response.status_code in (502, 503, 504):
                    if attempt < self.max_retries - 1:
                        # Wait before retry
                        time.sleep(self.retry_delay * (attempt + 1))  # Linear backoff
                        continue
                    else:
                        retries = self.max_retries
                        status = response.status_code
                        raise ProxyTargetError(
                            f"Target API unavailable after {retries} retries (HTTP {status})"
                        )

                # Raise for other HTTP errors
                response.raise_for_status()

                # Return wrapped response
                return ProxyResponse(response.json(), url)

            except requests.Timeout as e:
                raise ProxyTimeoutError(
                    f"Request to {url} timed out after {timeout or self.default_timeout}s"
                ) from e
            except requests.ConnectionError as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    last_exception = e
                    continue
                raise ProxyError(f"Connection error after {self.max_retries} retries: {e}") from e
            except ProxyError:
                # Re-raise our custom exceptions
                raise
            except requests.HTTPError as e:
                # Convert to our custom exception with better message
                raise ProxyTargetError(f"Target API error: {e}") from e
            except Exception as e:
                raise ProxyError(f"Unexpected error during proxy request: {e}") from e

        # Should not reach here, but just in case
        if last_exception:
            raise ProxyError(f"Failed after {self.max_retries} retries") from last_exception
        raise ProxyError("Request failed for unknown reason")

    def get(self, url: str, **kwargs) -> ProxyResponse:
        """Make a GET request through the proxy."""
        return self._proxy_request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> ProxyResponse:
        """Make a POST request through the proxy."""
        return self._proxy_request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> ProxyResponse:
        """Make a PUT request through the proxy."""
        return self._proxy_request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs) -> ProxyResponse:
        """Make a PATCH request through the proxy."""
        return self._proxy_request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs) -> ProxyResponse:
        """Make a DELETE request through the proxy."""
        return self._proxy_request("DELETE", url, **kwargs)

    def options(self, url: str, **kwargs) -> ProxyResponse:
        """Make an OPTIONS request through the proxy."""
        return self._proxy_request("OPTIONS", url, **kwargs)

    def head(self, url: str, **kwargs) -> ProxyResponse:
        """Make a HEAD request through the proxy."""
        return self._proxy_request("HEAD", url, **kwargs)

    def close(self):
        """Close the underlying session."""
        self._session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit."""
        self.close()


# Global session for convenience functions
_global_session: ProxySession | None = None


def configure(proxy_url: str, username: str, password: str, **kwargs):
    """
    Configure global proxy session for convenience functions.

    After calling this, you can use module-level functions like:
        proxy.get("https://api.github.com/users/octocat")

    Args:
        proxy_url: Base URL of the ShopCloud Proxy API
        username: Proxy API username
        password: Proxy API password
        **kwargs: Additional arguments passed to ProxySession
    """
    global _global_session
    _global_session = ProxySession(proxy_url, username, password, **kwargs)


def _ensure_configured():
    """Ensure global session is configured."""
    if _global_session is None:
        raise RuntimeError(
            "Proxy client not configured. Call configure() first or use ProxySession directly."
        )


def get(url: str, **kwargs) -> ProxyResponse:
    """Make a GET request using the global session."""
    _ensure_configured()
    return _global_session.get(url, **kwargs)


def post(url: str, **kwargs) -> ProxyResponse:
    """Make a POST request using the global session."""
    _ensure_configured()
    return _global_session.post(url, **kwargs)


def put(url: str, **kwargs) -> ProxyResponse:
    """Make a PUT request using the global session."""
    _ensure_configured()
    return _global_session.put(url, **kwargs)


def patch(url: str, **kwargs) -> ProxyResponse:
    """Make a PATCH request using the global session."""
    _ensure_configured()
    return _global_session.patch(url, **kwargs)


def delete(url: str, **kwargs) -> ProxyResponse:
    """Make a DELETE request using the global session."""
    _ensure_configured()
    return _global_session.delete(url, **kwargs)


def options(url: str, **kwargs) -> ProxyResponse:
    """Make an OPTIONS request using the global session."""
    _ensure_configured()
    return _global_session.options(url, **kwargs)


def head(url: str, **kwargs) -> ProxyResponse:
    """Make a HEAD request using the global session."""
    _ensure_configured()
    return _global_session.head(url, **kwargs)
