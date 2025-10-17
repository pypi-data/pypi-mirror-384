from __future__ import annotations

from typing import Any, Dict, Mapping, Optional
import os
import time
import random
import httpx

from .exceptions import ClientError, HTTPError, NotFoundError, RateLimitError, ServerError, UnauthorizedError

"""HTTP transport abstraction for the Poelis SDK.

Provides a thin wrapper around httpx with sensible defaults for timeouts,
retries, and headers including authentication and optional org scoping.
"""


class Transport:
    """Synchronous HTTP transport using httpx.Client.

    This wrapper centralizes auth headers, tenant scoping, timeouts, and
    retry behavior. Retries are implemented here in a simple, explicit way to
    avoid external dependencies, following the professional defaults defined
    in the SDK planning document.
    """

    def __init__(self, base_url: str, api_key: str, org_id: str, timeout_seconds: float) -> None:
        """Initialize the transport.

        Args:
            base_url: Base API URL.
            api_key: API key provided by backend to authenticate requests.
            org_id: Organization id for tenant scoping.
            timeout_seconds: Request timeout in seconds.
        """

        self._client = httpx.Client(base_url=base_url, timeout=timeout_seconds)
        self._api_key = api_key
        self._org_id = org_id
        self._timeout = timeout_seconds
        # Auth mode is intentionally read from environment to keep the public
        # constructor signature stable for tests and backwards-compatibility.
        # Supported values:
        # - "bearer" (default): Authorization: Bearer <api_key>
        # - "api_key": X-API-Key/X-Poelis-Api-Key headers with no Authorization
        self._auth_mode = os.environ.get("POELIS_AUTH_MODE", "api_key").strip().lower()
        

    def _headers(self, extra: Optional[Mapping[str, str]] = None) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        # Resolve auth mode with a safe fallback in case tests monkeypatch __init__
        auth_mode = getattr(self, "_auth_mode", None) or os.environ.get("POELIS_AUTH_MODE", "api_key").strip().lower()
        if auth_mode == "api_key":
            # Some staging environments expect an API key header and reject Bearer
            # Include common header variants for compatibility; backend may accept either.
            headers["X-API-Key"] = self._api_key
            headers["X-Poelis-Api-Key"] = self._api_key
            # Additionally include Authorization with Api-Key scheme for services
            # that only read credentials from Authorization.
            headers["Authorization"] = f"Api-Key {self._api_key}"
        else:
            # Default: send API key as Bearer token
            headers["Authorization"] = f"Bearer {self._api_key}"
        headers["X-Poelis-Org"] = self._org_id
        if extra:
            headers.update(dict(extra))
        return headers

    def get(self, path: str, params: Optional[Mapping[str, Any]] = None) -> httpx.Response:
        return self._request("GET", path, params=params)

    def post(self, path: str, json: Any = None) -> httpx.Response:  # noqa: A003
        return self._request("POST", path, json=json)

    def patch(self, path: str, json: Any = None) -> httpx.Response:
        return self._request("PATCH", path, json=json)

    def delete(self, path: str) -> httpx.Response:
        return self._request("DELETE", path)

    def graphql(self, query: str, variables: Optional[Mapping[str, Any]] = None) -> httpx.Response:
        """Post a GraphQL operation to /v1/graphql.

        Args:
            query: GraphQL document string.
            variables: Optional mapping of variables.
        """

        payload: Dict[str, Any] = {"query": query, "variables": dict(variables or {})}
        return self._request("POST", "/v1/graphql", json=payload)

    def _request(self, method: str, path: str, *, params: Optional[Mapping[str, Any]] = None, json: Any = None) -> httpx.Response:
        # Retries: up to 3 attempts on idempotent GET/HEAD and 429s respecting Retry-After.
        max_attempts = 3
        last_exc: Optional[Exception] = None
        for attempt in range(1, max_attempts + 1):
            try:
                response = self._client.request(method, path, headers=self._headers(), params=params, json=json)
                # Map common error codes
                if 200 <= response.status_code < 300:
                    return response
                if response.status_code == 401:
                    raise UnauthorizedError(401, message=_safe_message(response))
                if response.status_code == 404:
                    raise NotFoundError(404, message=_safe_message(response))
                if response.status_code == 429:
                    retry_after_header = response.headers.get("Retry-After")
                    retry_after: Optional[float] = None
                    if retry_after_header:
                        try:
                            retry_after = float(retry_after_header)
                        except Exception:
                            retry_after = None
                    if attempt < max_attempts:
                        if retry_after is not None:
                            time.sleep(retry_after)
                        else:
                            # fallback exponential backoff with jitter
                            time.sleep(_backoff_sleep(attempt))
                        continue
                    raise RateLimitError(429, message=_safe_message(response), retry_after_seconds=retry_after)
                if 400 <= response.status_code < 500:
                    raise ClientError(response.status_code, message=_safe_message(response))
                if 500 <= response.status_code < 600:
                    # Retry on idempotent
                    if method in {"GET", "HEAD"} and attempt < max_attempts:
                        time.sleep(_backoff_sleep(attempt))
                        continue
                    raise ServerError(response.status_code, message=_safe_message(response))
                # Fallback
                raise HTTPError(response.status_code, message=_safe_message(response))
            except httpx.HTTPError as exc:
                last_exc = exc
                if method not in {"GET", "HEAD"} or attempt == max_attempts:
                    raise
        assert last_exc is not None
        raise last_exc


def _safe_message(response: httpx.Response) -> str:
    try:
        data = response.json()
        if isinstance(data, dict):
            msg = data.get("message") or data.get("detail") or data.get("error")
            if isinstance(msg, str):
                return msg
        return response.text
    except Exception:
        return response.text


def _backoff_sleep(attempt: int) -> float:
    # Exponential backoff with jitter: base 0.5s, cap ~4s
    base = 0.5 * (2 ** (attempt - 1))
    return min(4.0, base + random.uniform(0, 0.25))


