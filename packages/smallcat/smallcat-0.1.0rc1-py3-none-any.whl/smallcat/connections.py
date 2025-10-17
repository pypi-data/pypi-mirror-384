"""Connection interface abstractions with optional Airflow compatibility.

This module defines a lightweight protocol for connection objects and a small
adapter (:class:`ConnectionLike`) that lets you supply a plain `dict` with
Airflow-compatible fields while still satisfying the protocol expected by the
rest of the library.

Smallcat can operate with or without Airflow installed. When Airflow is
available, objects implementing the same attributes (e.g., `BaseConnection`)
are compatible with :class:`ConnectionProtocol`.
"""

import json
from typing import Protocol


class ConnectionProtocol(Protocol):
    """Protocol describing the minimal connection interface.

    Attributes:
        conn_type: Provider/type identifier (e.g., `"fs"`, `"google"`).
        host: Optional hostname/base URL used by some providers.
        schema: Optional logical schema/namespace (provider-specific).
        login: Optional username or key identifier.
        password: Optional password, token, or secret value.
        extra: JSON string with provider-specific extras.

    Properties:
        extra_dejson: Parsed `extra` as a dictionary. Returns `{}` if
            `extra` is falsy.
    """

    conn_type: str
    host: str | None
    schema: str | None
    login: str | None
    password: str | None
    extra: str | None

    @property
    def extra_dejson(self) -> dict:
        """JSON parsed view of `extra`; returns {} when missing."""
        ...


class ConnectionLike(ConnectionProtocol):
    """Dictionary-backed connection compatible with :class:`ConnectionProtocol`.

    This adapter allows passing a plain dict (e.g., from YAML or environment)
    instead of an Airflow connection instance. The expected keys mirror the
    Airflow connection structure.

    Expected dictionary keys:
        - `conn_type` (required)
        - `host` (optional)
        - `schema` (optional)
        - `login` (optional)
        - `password` (optional)
        - `extra` (optional; `str` JSON or `dict`)

    Notes:
        If `extra` is provided as a `dict`, it is serialized to JSON. If it
        is a string, it must be valid JSON when accessed via `extra_dejson`.
    """

    def __init__(self, connection: dict) -> None:
        """Initialize the adapter from a mapping.

        Args:
            connection: Mapping with Airflow-like connection fields. See class
                docstring for expected keys.
        """
        self.conn_type = connection["conn_type"]
        self.host = connection.get("host")
        self.schema = connection.get("schema")
        self.login = connection.get("login")
        self.password = connection.get("password")
        extra = connection.get("extra")
        if isinstance(extra, dict):
            self.extra = json.dumps(extra)
        else:
            assert isinstance(extra, str)
            self.extra = extra

    @property
    def extra_dejson(self) -> dict:
        """Return `extra` parsed as JSON, or an empty dict if missing/empty.

        Returns:
            Dictionary representation of `extra`. If `extra` is falsy,
            returns `{}`. If `extra` is a non-JSON string, this will raise
            `json.JSONDecodeError`.
        """
        return json.loads(self.extra) if self.extra else {}
