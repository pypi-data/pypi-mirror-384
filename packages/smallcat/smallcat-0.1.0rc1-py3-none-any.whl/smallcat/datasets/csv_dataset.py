"""CSV dataset using DuckDB's CSV reader/writer.

This module defines :class:`CSVDataset`, a concrete dataset for CSV/TSV/DSV
files using DuckDB (`read_csv_auto` / `COPY ... WITH (FORMAT CSV)`).
All paths are treated as **relative** to the dataset's base URI.

Features:
  * Auto-schema inference (delimiter, header, types) with overrides.
  * Large-file handling via DuckDB streaming.
  * Optional Hive-style partitioning on write.

Example:
  >>> ds = CSVDataset.from_conn_id("local_fs")
  >>> tbl = ds.load_arrow_table("bronze/raw/users.csv")
  >>> ds.save_arrow_table("silver/users/", tbl)

Typical options (suggested):
  * Load: `header`, `delimiter`, `columns`, `nullstr`, `types`.
  * Save: `header`, `delimiter`, `partition_by`, `overwrite`.

Note:
  An implementation typically builds SQL like:
  `SELECT * FROM read_csv_auto(? , ...options...)` for reading and
  `COPY (SELECT * FROM tmp_input) TO ? WITH (FORMAT CSV, ...)` for writing.
"""

from __future__ import annotations

import typing
from collections.abc import Mapping  # noqa: TC003

from pydantic import BaseModel, Field

from smallcat.datasets.base_dataset import BaseDataset

if typing.TYPE_CHECKING:
    import pyarrow as pa


class CSVLoadOptions(BaseModel):
    r"""Options that control how CSV files are *read*.

    These mirror DuckDB's `read_csv_auto` parameters we expose.
    All fields are optional; unset values defer to DuckDB defaults.

    Attributes:
    ----------
    columns
        Optional mapping of column names to logical types
        (e.g. {"id": "INTEGER", "amount": "DOUBLE"}) used to override
        DuckDB's type inference when auto-detect is not good enough.
    sep
        Field separator (e.g. ",", "|", "\t"). If None, DuckDB will try to detect it.
    header
        Whether the first row contains column names. If None, DuckDB will detect.
    sample_size
        Number of rows to sample for schema detection. If None, DuckDB default applies.
    all_varchar
        If True, read all columns as VARCHAR (string). Useful when types are messy.
    """

    columns: Mapping[str, str] | None = Field(
        None,
        description="Override inferred types per column, e.g. {'id': 'INTEGER'}.",
    )
    sep: str | None = Field(
        None,
        description="Field separator (e.g. ',', '|', '\\t'); auto-detected if None.",
    )
    header: bool | None = Field(
        None,
        description="Whether the first row is a header; auto-detected if None.",
    )
    sample_size: int | None = Field(
        None,
        description="Rows to sample for inference; DuckDB default if None.",
    )
    all_varchar: bool | None = Field(
        None,
        description="If True, read all columns as VARCHAR.",
    )


class CSVSaveOptions(BaseModel):
    r"""Options that control how CSV files are *written*.

    Attributes:
    ----------
    header
        Whether to write a header row with column names.
    sep
        Field separator to use when writing (e.g. ',', '|', '\t').
    overwrite
        If True, allow overwriting existing files at the destination.
        Compression is *inferred from the file extension* ('.gz', '.zst', …).
    """

    header: bool | None = Field(
        None,
        description="Write a header row with column names.",
    )
    sep: str | None = Field(
        None,
        description="Field separator to use (e.g. ',', '|', r'\t').",
    )
    # compression is inferred from extension (.gz, .zst, …) don't expose unless you must
    overwrite: bool | None = Field(
        None,
        description="If True, overwrite existing files at the destination.",
    )


class CSVDataset(BaseDataset[CSVLoadOptions, CSVSaveOptions]):
    """Dataset that reads/writes CSV using DuckDB.

    - **Paths** are resolved relative to the dataset's connection base
      (local filesystem, `gs://`, etc.).
    - **Reading** uses `DuckDBPyConnection.read_csv` under the hood and returns a
      `pyarrow.Table`.
    - **Writing** uses `Relation.write_csv` to materialize a table to CSV.

    Notes:
    -----
    - Use :class:`CSVLoadOptions` to override auto-detection (separator, header,
      per-column types).
    - Use :class:`CSVSaveOptions` to control delimiter, header, and overwrite behavior.
    """

    def load_arrow_table(self, path: str) -> pa.Table:
        """Load a CSV file (or files) into a PyArrow Table.

        Parameters
        ----------
        path
            Path to a single CSV file or a glob, relative to the connection base.

        Returns:
        -------
        pyarrow.Table
            The loaded data as an Arrow table.

        Raises:
        ------
        duckdb.CatalogException
            If the path cannot be resolved.
        duckdb.IOException
            If the file cannot be read.
        """
        full_uri = self._full_uri(path)
        with self._duckdb_conn() as con:
            rel = con.read_csv(full_uri, **self.load_options_dict())
            return rel.fetch_arrow_table()

    def save_arrow_table(self, path: str, table: pa.Table) -> None:
        """Write a PyArrow Table to CSV.

        Parameters
        ----------
        path
            Destination path (file or pattern) relative to the connection base.
            Compression is inferred from the extension (e.g. '.gz', '.zst').
        table
            The Arrow table to write.

        Raises:
        ------
        duckdb.IOException
            If the destination is not writable.
        """
        full_uri = self._full_uri(path)
        with self._duckdb_conn() as con:
            con.register("tmp_input", table)
            con.sql("SELECT * FROM tmp_input").write_csv(
                full_uri,
                **self.save_options_dict(),
            )
