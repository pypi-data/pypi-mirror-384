# Catalog
::: smallcat.catalog.Catalog
    options:
      show_root_heading: true
      members: true

## Entries
::: smallcat.catalog.CSVEntry
    options:
      heading_level: 3
      show_root_heading: true
      members: true
      inherited_members:
        - save_pandas
        - load_pandas

::: smallcat.catalog.ExcelEntry
    options:
      heading_level: 3
      show_root_heading: true
      members: true
      inherited_members:
        - save_pandas
        - load_pandas

::: smallcat.catalog.ParquetEntry
    options:
      heading_level: 3
      show_root_heading: true
      members: true
      inherited_members:
        - save_pandas
        - load_pandas

::: smallcat.catalog.DeltaTableEntry
    options:
      heading_level: 3
      show_root_heading: true
      members: true
      inherited_members:
        - save_pandas
        - load_pandas
