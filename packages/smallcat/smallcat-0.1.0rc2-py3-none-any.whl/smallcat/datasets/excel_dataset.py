"""Excel (.xlsx) dataset via DuckDB's `excel` extension.

This module provides :class:`ExcelDataset` for reading/writing **.xlsx** files
(legacy **.xls** is not supported). Paths are **relative** to the configured
base URI; the DuckDB `excel` extension is installed/loaded at runtime.

Capabilities:
  * Read a whole sheet or an A1 range with optional header handling.
  * Coerce empty columns or all columns to VARCHAR for schema stability.
  * Write Arrow tables to a specific sheet (with optional header row).

Example:
  >>> ds = ExcelDataset.from_conn_id("fs_conn")
  >>> tbl = ds.load_arrow_table("inputs/budget.xlsx")  # first sheet by default
  >>> ds.save_arrow_table("outputs/budget_out.xlsx", tbl)

Options:
  * `ExcelLoadOptions`: header, sheet, range, all_varchar, empty_as_varchar.
  * `ExcelSaveOptions`: header, sheet.
"""

import pyarrow as pa
from pydantic import BaseModel, Field

from smallcat.datasets.base_dataset import BaseDataset


class ExcelLoadOptions(BaseModel):
    """Options that control how an .xlsx file is read.

    Attributes:
      header: If True, treat the first row as column headers.
      sheet: Optional worksheet name to read. If omitted, the first sheet is used.
      range: Excel A1-style range to read (e.g., "A1:D100").
             If omitted, the full sheet is read.
      all_varchar: If True, coerce all columns to VARCHAR (strings).
      empty_as_varchar: If True, treat empty columns as VARCHAR instead of NULL/typed.
    """

    header: bool | None = Field(None)
    sheet: str | None = Field(None)
    range: str | None = Field(None)
    all_varchar: bool | None = Field(None)
    empty_as_varchar: bool | None = Field(None)


class ExcelSaveOptions(BaseModel):
    """Options that control how an Arrow table is written to .xlsx.

    Attributes:
      header: If True, include column headers in the output file.
      sheet: Optional worksheet name to write into (created if missing).
    """

    header: bool | None = Field(None)
    sheet: str | None = Field(None)


class ExcelDataset(BaseDataset[ExcelLoadOptions, ExcelSaveOptions]):
    """Reads and writes **.xlsx** files via DuckDB's `excel` extension.

    Notes:
      * Legacy **.xls** format is **not** supported.
      * Paths are treated as relative to this dataset's base URI (e.g., `file://` or
        `gs://`); use the connection extras to set the base.
    """

    def load_arrow_table(self, path: str) -> pa.Table:
        """Load an .xlsx worksheet (or range) as a PyArrow table.

        Args:
          path: Relative path to the .xlsx file (joined under the dataset base).

        Returns:
          A `pyarrow.Table` with the loaded data.

        Implementation details:
          Uses DuckDB's `read_xlsx` from the `excel` extension. Load-time
          options are translated into the corresponding function arguments.
        """
        full_uri = self._full_uri(path)
        with self._duckdb_conn() as con:
            con.install_extension("excel")
            con.load_extension("excel")
            lo = self.load_options_dict()
            args_sql = ""
            if header := lo.get("header"):
                args_sql += f", header = {str(header).lower()}"
            if sheet := lo.get("sheet"):
                args_sql += f", sheet = '{sheet}'"
            if _range := lo.get("range"):
                args_sql += f", range = '{_range}'"
            if all_varchar := lo.get("all_varchar"):
                args_sql += f", all_varchar = {str(all_varchar).lower()}"
            if empty_as_varchar := lo.get("empty_as_varchar"):
                args_sql += f", empty_as_varchar = {str(empty_as_varchar).lower()}"
            query = f"select * from read_xlsx(?{args_sql})"  # noqa: S608
            return con.execute(query, [full_uri]).fetch_arrow_table()

    def save_arrow_table(self, path: str, table: pa.Table) -> None:
        """Write a PyArrow table to an .xlsx file.

        Args:
          path: Relative path of the output .xlsx file (joined under the dataset base).
          table: The `pyarrow.Table` to write.

        Notes:
          Uses DuckDB's `COPY ... TO ... WITH (FORMAT xlsx ...)` from the
          `excel` extension. Save-time options are translated into COPY options.
        """
        full_uri = self._full_uri(path)
        with self._duckdb_conn() as con:
            con.install_extension("excel")
            con.load_extension("excel")
            lo = self.save_options_dict()
            args_sql = ""
            if header := lo.get("header"):
                args_sql += f", HEADER {str(header).lower()}"
            if sheet := lo.get("sheet"):
                args_sql += f", SHEET '{sheet}'"
            con.register("tmp_input", table)
            query = f"copy (select * from tmp_input) TO ? WITH (FORMAT xlsx{args_sql})"  # noqa: S608
            con.execute(query, [full_uri]).fetch_arrow_table()
