"""Core dataset base class for Smallcat.

This module defines :class:`BaseDataset`, the abstract foundation for concrete
datasets (CSV, Parquet, Excel, Delta, etc.). It standardizes how a dataset:

* Receives an Airflow-like connection (or dict) and exposes its extras.
* Resolves relative paths to fully-qualified URIs (e.g., `file://`, `gs://`).
* Creates isolated DuckDB connections, loading extensions and provider secrets.
* Loads and saves data via a simple Arrow/pandas-friendly API.

Typical usage:
  >>> ds = MyDataset.from_conn_id("my_fs")
  >>> table = ds.load_arrow_table("bronze/my_table.parquet")
  >>> ds.save_pandas("silver/my_table.parquet", table.to_pandas())

Key concepts:
  * `_full_uri(rel_path)` joins relative paths to the connection's base URI.
  * `_duckdb_conn()` returns a fresh, configured DuckDB connection per call.
  * Subclasses must implement `load_arrow_table` and `save_arrow_table`.

Dependencies:
  duckdb, pyarrow, pandas, pydantic, and Smallcat connection utilities.
"""

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar

import duckdb
import pandas as pd
import pyarrow as pa
from pydantic import BaseModel

from smallcat.connections import ConnectionLike, ConnectionProtocol
from smallcat.path_utils import norm_join_uri, to_relative_posix_path

try:
    from airflow.sdk.bases.hook import BaseHook  # type: ignore[attr-defined]
except ImportError:
    try:
        from airflow.hooks.base import BaseHook  # type: ignore[attr-defined,no-redef]
    except ImportError:
        BaseHook = None  # type: ignore[assignment,misc]

L = TypeVar("L", bound=BaseModel)  # Load options model
S = TypeVar("S", bound=BaseModel)  # Save options model


class BaseDataset[L, S](ABC):
    """Base class for dataset loaders/savers backed by DuckDB and a connection.

    This class:
      * Wraps an Airflow-like connection (or connection dict).
      * Expands relative dataset paths into fully-qualified URIs using the
        connection's base settings.
      * Creates a fresh DuckDB connection per operation, configuring extensions
        and any provider-specific secrets (e.g., GCS).
      * Defines an abstract API to load and save Arrow tables, plus
        convenience pandas helpers.

    Type Parameters:
      L: Pydantic model describing load options.
      S: Pydantic model describing save options.

    Attributes:
      conn: The resolved connection implementing `ConnectionProtocol`.
      extras: Parsed `extra_dejson` from the connection.
      base_uri: Base URI inferred from the connection extras (e.g., `file://...`,
        `gs://bucket/prefix`). May be `None` for unknown types.
      load_options: Instance of `L` with load-time options, if any.
      save_options: Instance of `S` with save-time options, if any.
    """

    conn: ConnectionProtocol

    def __init__(
        self,
        conn: ConnectionProtocol | dict,
        load_options: L | None = None,
        save_options: S | None = None,
    ) -> None:
        """Initialize the dataset with a connection and optional options.

        Args:
          conn: An Airflow-like connection object implementing
            `ConnectionProtocol` or a plain dict compatible with
            `ConnectionLike`.
          load_options: Optional Pydantic model with load configuration.
          save_options: Optional Pydantic model with save configuration.

        Side Effects:
          May create a local directory if the inferred base URI is a
          `file://` path that does not exist.

        """
        if isinstance(conn, dict):
            self.conn = ConnectionLike(conn)
        else:
            self.conn = conn
        self.extras = self.conn.extra_dejson
        # For 'fs', prefer extras["base_uri"];
        #  fallback to extras["base_path"] for local paths.
        # For GCP, prefer extras["base_uri"]; else build from bucket: gs://{bucket}
        self.base_uri = self._infer_base_uri()
        if self.base_uri and self.base_uri.startswith("file://"):
            Path(self.base_uri[len("file://") :]).mkdir(exist_ok=True)

        self.load_options = load_options
        self.save_options = save_options

    @classmethod
    def from_conn_id(
        cls: type["BaseDataset[L, S]"],
        conn_id: str,
        *,
        load_options: L | None = None,
        save_options: S | None = None,
    ) -> "BaseDataset[L, S]":
        """Construct an instance by looking up an Airflow connection ID.

        Uses `airflow.hooks.base.BaseHook` (or the SDK alternative) to fetch
        the connection and then calls the class constructor.

        Args:
          conn_id: Airflow connection ID to resolve.
          load_options: Optional load options model.
          save_options: Optional save options model.

        Returns:
          A fully constructed `BaseDataset` subclass instance.
        """
        if BaseHook is None:
            raise RuntimeError("Airflow not available. Install smallcat[airflow]")  # noqa: TRY003, EM101

        conn = BaseHook.get_connection(conn_id)
        return cls(conn=conn, load_options=load_options, save_options=save_options)

    # ---------- Public API ----------

    @abstractmethod
    def load_arrow_table(self, path: str) -> pa.Table:
        """Load data as a PyArrow table.

        Subclasses must implement this to execute a query or read from storage.

        Args:
          path: Relative dataset path (joined under the connection's base).
            Use `self._full_uri(path)` for the fully-qualified location and
            `self._duckdb_conn()` for an isolated DuckDB connection.

        Returns:
          A `pyarrow.Table` with the loaded data.
        """
        ...

    @abstractmethod
    def save_arrow_table(self, path: str, table: pa.Table) -> None:
        """Persist a PyArrow table to the target destination.

        Args:
          path: Relative dataset path under the connection base.
          table: Table to write.

        Returns:
          None
        """
        ...

    def load_pandas(self, path: str) -> pd.DataFrame:
        """Load data as a pandas DataFrame.

        This is a convenience wrapper over `load_arrow_table`.

        Args:
          path: Relative dataset path.

        Returns:
          A pandas `DataFrame`.
        """
        arrow_table = self.load_arrow_table(path)
        return arrow_table.to_pandas()

    def save_pandas(self, path: str, df: pd.DataFrame) -> None:
        """Persist a pandas DataFrame.

        Converts the DataFrame to a `pyarrow.Table` and delegates to
        `save_arrow_table`.

        Args:
            path: Relative dataset path.
            df: DataFrame to persist.

        Returns:
            None
        """
        arrow_table = pa.Table.from_pandas(df)
        self.save_arrow_table(path, table=arrow_table)

    def save_options_dict(self) -> dict:
        """Serialize save options to a plain dict.

        Uses `Pydantic.model_dump(exclude_unset=True)` when available.

        Returns:
          A dict of save options, or an empty dict if unset.
        """
        if self.save_options:
            return self.save_options.model_dump(exclude_unset=True)  # type: ignore[attr-defined]
        return {}

    def load_options_dict(self) -> dict:
        """Serialize load options to a plain dict.

        Uses `Pydantic.model_dump(exclude_unset=True)` when available.

        Returns:
          A dict of load options, or an empty dict if unset.
        """
        if self.load_options:
            return self.load_options.model_dump(exclude_unset=True)  # type: ignore[attr-defined]
        return {}

    # ---------- Helpers available to subclasses ----------

    def _full_uri(self, rel_path: str) -> str:
        """Build a fully-qualified URI for a relative path.

        Args:
          rel_path: Path relative to the connection's base.

        Returns:
          A fully-qualified URI (e.g., `file://...`, `gs://bucket/...`),
          or a normalized relative POSIX path if no base is known.
        """
        if not self.base_uri:
            return to_relative_posix_path(rel_path)
        return norm_join_uri(self.base_uri, rel_path)

    def _infer_base_uri(self) -> str | None:  # noqa: PLR0911
        """Infer a base URI from the connection configuration.

        Rules:
          * `fs`: use `extras.base_uri`; otherwise derive from
            `extras.base_path` (normalized to `file://`). Defaults to
            `file://` (current working directory) if neither is provided.
          * `google_cloud_platform` / `google`: use `extras.base_uri`; otherwise
            derive from `gs://{bucket}` and optional `prefix`.
          * Other/unknown types: fall back to `extras.base_uri` if present.

        Returns:
          The inferred base URI string, or `None` if it cannot be determined.
        """
        ctype = (self.conn.conn_type or "").lower()
        x = self.extras

        if ctype == "fs":
            if x.get("base_uri"):
                return x["base_uri"]
            # allow local base path
            base_path = x.get("base_path")
            if base_path:
                # Normalize to file:// for consistency
                if re.match(r"^[a-zA-Z0-9+.-]+://", base_path):
                    return base_path
                return f"file://{base_path}"
            return "file://"  # local current-dir root by default

        if ctype in {"google_cloud_platform", "google"}:
            if x.get("base_uri"):
                return x["base_uri"]
            bucket = x.get("bucket")
            prefix = x.get("prefix", "")
            if bucket:
                return norm_join_uri(f"gs://{bucket}", prefix)
            # Last resort: no bucket provided
            return None

        # Unknown type: try an explicit base_uri if provided
        return x.get("base_uri")

    def _duckdb_conn(self) -> duckdb.DuckDBPyConnection:
        """Create and configure a fresh DuckDB connection.

        The connection installs and loads common extensions (`httpfs`, `json`,
        `parquet`). For GCP-like connections, it also configures a GCS secret.

        Returns:
          A new, isolated `duckdb.DuckDBPyConnection` instance.

        Notes:
          Each call returns a brand-new connection to avoid cross-task
          interference.
        """
        con = duckdb.connect()
        # Common extensions
        con.install_extension("httpfs")
        con.load_extension("json")
        con.load_extension("parquet")
        con.load_extension("httpfs")

        ctype = (self.conn.conn_type or "").lower()
        if ctype in {"google_cloud_platform", "google"}:
            self._configure_gcp_secret(con)

        return con

    # ---------- Backend configuration ----------

    def _configure_gcp_secret(self, con: duckdb.DuckDBPyConnection) -> None:
        """Create a DuckDB GCS secret from the Airflow GCP connection.

        Supports any of the following credential sources in `extras`:
          * `keyfile_dict` (JSON dict)
          * `keyfile` (raw JSON string)
          * `key_path` (filesystem path on the worker)

        The method currently uses `login` as the key ID and `password` as
        the secret value, matching Airflow GCP connection conventions.

        Args:
          con: An open DuckDB connection to configure.

        Returns:
          None
        """
        con.execute(
            f"""
            CREATE OR REPLACE SECRET (
                TYPE gcs,
                KEY_ID '{self.conn.login}',
                SECRET '{self.conn.password}'
            );
            """,
        )
