from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from devopso.core.configuration import Configuration
from devopso.core.configuration import Error as ConfigurationError
from devopso.core.logging import ConfiguredLogger


@dataclass(frozen=True)
class Auth:
    email: str
    api_token: str  # unencoded


class Error(Exception):
    def __init__(self, status: int, url: str, body: str):
        super().__init__(f"devopso API error {status} for {url}: {body[:500]}")
        self.status = status
        self.url = url
        self.body = body


class RestAdapter(ConfiguredLogger):
    def __init__(self, config_path: str) -> None:
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

            if credentials["auth-type"] == "Basic":
                raw = f"{credentials['login']}:{credentials['api-token']}".encode("utf-8")
                b64 = base64.b64encode(raw).decode("utf-8")
                self._auth_header = {"Authorization": f"Basic {b64}"}
