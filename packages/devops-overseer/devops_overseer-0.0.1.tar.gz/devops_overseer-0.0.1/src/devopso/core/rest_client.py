from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, cast

import requests
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from devopso.core.configuration import Configuration
from devopso.core.configuration import Error as ConfigurationError
from devopso.core.logging import ConfiguredLogger


@dataclass(frozen=True)
class Auth:
    """Authentication data for the devopso Cloud REST API."""

    email: str
    api_token: str  # unencoded


class Error(Exception):
    """Raised for non-2xx responses with useful context."""

    def __init__(self, status: int, url: str, body: str):
        """
        Initialize an Error.

        Args:
            status: HTTP status code returned by the server.
            url: The request URL that triggered the error.
            body: Response body content (trimmed for readability).
        """
        super().__init__(f"devopso API error {status} for {url}: {body[:500]}")
        self.status = status
        self.url = url
        self.body = body


class RestClient(ConfiguredLogger):
    """
    devopso-style HTTP client for devopso Cloud REST API (v3).

    Features:
        - Single shared Session with retries + backoff.
        - Base64 Basic auth derived from email:api_token.
        - Default timeouts (configurable per call).
        - Small helpers for pagination and common services.
    """

    def __init__(self, config_path: str) -> None:
        """
        Initialize the HTTP client with configuration and credentials.

        Args:
            config_path: Path to a YAML configuration file. The file must
                contain keys like `base-url`, `user-agent`, `timeout`,
                `max-retries`, `backoff-factor`, `extra-headers`, and a
                `credentials` path for authentication.
        """
        super().__init__(config_path)

        base_url = self._conf["base-url"]
        user_agent = self._conf["user-agent"]
        timeout_s = self._conf["timeout"]
        max_retries = self._conf["max-retries"]
        backoff_factor = self._conf["backoff-factor"]
        extra_headers = self._conf["extra-headers"]

        if base_url.endswith("/"):
            base_url = base_url[:-1]
        self.base_url = base_url
        self.timeout_s = timeout_s

        self._read_credentials()

        # Session with retries
        self.session = requests.Session()
        retry = Retry(
            total=max_retries,
            read=max_retries,
            connect=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "POST", "PUT", "DELETE"),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self._base_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": user_agent,
        }
        if extra_headers:
            self._base_headers.update(extra_headers)

    def _read_credentials(self) -> None:
        # Load credentials
        if "credentials" in self._conf:
            creds_conf = self._conf["credentials"]
            app_credentials = {}
            credentials = {}

            if "path" in creds_conf:
                app_credentials = Configuration.read_configuration(Path(creds_conf["path"]).expanduser().resolve(strict=False))

            if not app_credentials:
                raise ConfigurationError(self._conf_path, "missing app credentials configuration")

            if "app" in creds_conf and creds_conf["app"] in app_credentials["apps"]:
                credentials = app_credentials["apps"][creds_conf["app"]]

            if not credentials:
                raise ConfigurationError(self._conf_path, "missing credentials configuration")

            if "auth-type" not in credentials:
                raise ConfigurationError(self._conf_path, "missing authentication type")

            if credentials["auth-type"] == "basic":
                raw = f"{credentials['login']}:{credentials['api-token']}".encode("utf-8")
                b64 = base64.b64encode(raw).decode("utf-8")
                self._auth_header = {"Authorization": f"Basic {b64}"}

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        timeout_s: Optional[float] = None,
    ) -> Response:
        """
        Perform an HTTP request with retries, backoff, and error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            endpoint: Logical endpoint key defined in the configuration file.
            params: Optional query string parameters.
            json_body: Optional JSON payload to send in the body.
            timeout_s: Optional request timeout in seconds. Defaults to
                the configured client timeout.

        Returns:
            Response: A `requests.Response` object for successful requests.

        Raises:
            Error: If the request fails or the endpoint is not defined
                in the configuration.
        """
        if endpoint not in self._conf["endpoints"]:
            raise Error(1, endpoint, "endpoint doesn't exist in configuration")

        path = self._conf["endpoints"][endpoint]["path"]

        url = f"{self.base_url}{path}"
        self.debug(f"calling on {url}")

        if not self._auth_header:
            raise ConfigurationError(self._conf_path, "missing authentication")

        headers = {**self._base_headers, **self._auth_header}

        resp = self.session.request(
            method=method.upper(),
            url=url,
            headers=headers,
            params=params,
            json=json_body,
            timeout=timeout_s or self.timeout_s,
        )

        # Handle explicit rate limits
        if resp.status_code == 429:
            retry_after = float(resp.headers.get("Retry-After", "1"))
            time.sleep(min(retry_after, 10))  # cap at 10s
            resp = self.session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=json_body,
                timeout=timeout_s or self.timeout_s,
            )

        if 200 <= resp.status_code < 300:
            return resp

        # Raise with trimmed body
        try:
            snippet = json.dumps(resp.json())
        except Exception:
            snippet = resp.text
        raise Error(resp.status_code, url, snippet)

    def get(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform a GET request to the given endpoint.

        Args:
            path: Endpoint key defined in configuration.
            params: Optional query string parameters.

        Returns:
            dict: JSON response body parsed as a dictionary.

        Raises:
            Error: If the request fails or response is not JSON object.
        """
        return RestClient._json_dict(self._request("GET", path, params=params))

    def post(self, path: str, *, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform a POST request to the given endpoint.

        Args:
            path: Endpoint key defined in configuration.
            body: Optional JSON body to send with the request.

        Returns:
            dict: JSON response body parsed as a dictionary.

        Raises:
            Error: If the request fails or response is not JSON object.
        """
        return RestClient._json_dict(self._request("POST", path, json_body=body))

    def put(self, path: str, *, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform a PUT request to the given endpoint.

        Args:
            path: Endpoint key defined in configuration.
            body: Optional JSON body to send with the request.

        Returns:
            dict: JSON response body parsed as a dictionary.

        Raises:
            Error: If the request fails or response is not JSON object.
        """
        return RestClient._json_dict(self._request("PUT", path, json_body=body))

    def delete(self, path: str) -> None:
        """
        Perform a DELETE request to the given endpoint.

        Args:
            path: Endpoint key defined in configuration.

        Raises:
            Error: If the request fails.
        """
        self._request("DELETE", path)

    @staticmethod
    def _json_dict(resp: Response) -> Dict[str, Any]:
        """
        Parse a Response object as a JSON dictionary.

        Args:
            resp: Response object to parse.

        Returns:
            dict: Parsed JSON body.

        Raises:
            TypeError: If the JSON body is not a dictionary.
        """
        data = resp.json()
        if not isinstance(data, dict):
            raise TypeError(f"Expected JSON object (dict), got {type(data).__name__}")
        return cast(Dict[str, Any], data)
