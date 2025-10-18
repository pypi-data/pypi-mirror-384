"""Higher-level helpers for provisioning and interacting with pipelines."""

from __future__ import annotations

import time
import urllib.parse
from dataclasses import dataclass
from typing import List, Optional, Sequence

from . import models
from .exceptions import ProvisioningError, StegawaveError

if False:  # pragma: no cover - for type checking only
    from .client import StegawaveClient  # pylint: disable=cyclic-import


def _append_query_parameter(url: str, key: str, value: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    params = [(k, v) for k, v in params if k.lower() != key.lower()]
    params.append((key, value))
    new_query = urllib.parse.urlencode(params)
    rebuilt = parsed._replace(query=new_query)
    return urllib.parse.urlunsplit(rebuilt)


@dataclass
class InputDetails:
    """Normalized input description returned by `/get`."""

    protocol: Optional[str]
    uri: Optional[str]
    uris: Sequence[str]
    allowed_ips: Sequence[str]
    latency: Optional[str] = None
    raw: Optional[models.PipelineInputStatus] = None

    @classmethod
    def from_status(cls, status: Optional[models.PipelineInputStatus]) -> "InputDetails":
        if status is None:
            return cls(protocol=None, uri=None, uris=[], allowed_ips=[])
        dump = status.model_dump(exclude_none=True)  # type: ignore[call-arg]
        protocol = dump.get("protocol")
        endpoint = dump.get("endpoint")
        endpoints: List[str] = list(dump.get("endpoints", []))
        if endpoint:
            endpoints = [endpoint] + [e for e in endpoints if e != endpoint]
        allowed = dump.get("allowedIPs", [])
        latency = dump.get("latency")
        return cls(
            protocol=protocol,
            uri=endpoints[0] if endpoints else None,
            uris=endpoints,
            allowed_ips=allowed,
            latency=latency,
            raw=status,
        )


@dataclass
class Manifest:
    """Represents a CDN manifest endpoint."""

    uri: str

    def with_token(self, token: str, *, parameter: str = "token") -> str:
        return _append_query_parameter(self.uri, parameter, token)


class PipelineSession:
    """Convenience wrapper around a pipeline lifecycle."""

    def __init__(
        self,
        client: "StegawaveClient",
        event_id: str,
        *,
        status: Optional[models.PipelineStatusResponse] = None,
    ) -> None:
        self._client = client
        self.event_id = event_id
        self._status = status

    # ------------------------------------------------------------------ status
    @property
    def status(self) -> models.PipelineStatusResponse:
        if self._status is None:
            self.refresh()
        assert self._status is not None  # narrow for type-checkers
        return self._status

    def refresh(self) -> models.PipelineStatusResponse:
        self._status = self._client.get_pipeline(self.event_id)
        return self._status

    # ------------------------------------------------------------------- checks
    @property
    def is_ready(self) -> bool:
        return self.status.is_ready()

    def wait_until_ready(
        self,
        *,
        timeout: float = 600.0,
        poll_interval: float = 5.0,
    ) -> models.PipelineStatusResponse:
        deadline = time.monotonic() + timeout
        while True:
            try:
                current = self.refresh()
            except StegawaveError as exc:
                if exc.status_code == 404:
                    if time.monotonic() >= deadline:
                        raise ProvisioningError(
                            f"Timed out waiting for pipeline {self.event_id} to become visible",
                            status_code=None,
                            payload={"eventID": self.event_id},
                        ) from exc
                    time.sleep(poll_interval)
                    continue
                raise
            if current.is_terminal_failure():
                raise ProvisioningError(
                    f"Pipeline {self.event_id} entered terminal status '{current.status}'",
                    status_code=None,
                    payload={"eventID": self.event_id, "status": current.status},
                )
            if current.is_ready():
                return current
            if time.monotonic() >= deadline:
                raise ProvisioningError(
                    f"Timed out waiting for pipeline {self.event_id} to become ready",
                    status_code=None,
                    payload={"eventID": self.event_id, "status": current.status},
                )
            time.sleep(poll_interval)

    # -------------------------------------------------------------- convenience
    def get_input(self) -> InputDetails:
        return InputDetails.from_status(self.status.input)

    def get_manifests(self) -> List[Manifest]:
        cdn = self.status.cdn
        urls = list(cdn.endpoints) if cdn and cdn.endpoints else []
        return [Manifest(uri=url) for url in urls]

    @property
    def input_uri(self) -> Optional[str]:
        return self.get_input().uri

    @property
    def manifest_uris(self) -> List[str]:
        return [manifest.uri for manifest in self.get_manifests()]

    # ------------------------------------------------------------------- tokens
    def token_for(self, user_key: str, *, exp_hours: Optional[int] = None) -> str:
        response = self._client.fetch_token(user_key, exp_hours=exp_hours)
        token = response.tokens.get(user_key)
        if not token:
            raise ProvisioningError(
                f"Token response missing entry for {user_key}",
                status_code=None,
                payload={"eventID": self.event_id},
            )
        return token

    def signed_manifest_uris(
        self,
        user_key: str,
        *,
        exp_hours: Optional[int] = None,
        parameter: str = "token",
    ) -> List[str]:
        token = self.token_for(user_key, exp_hours=exp_hours)
        return [manifest.with_token(token, parameter=parameter) for manifest in self.get_manifests()]


__all__ = ["PipelineSession", "Manifest", "InputDetails"]
