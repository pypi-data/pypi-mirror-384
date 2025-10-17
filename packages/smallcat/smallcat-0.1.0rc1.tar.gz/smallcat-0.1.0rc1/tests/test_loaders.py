from pathlib import Path

import pandas as pd
import pytest

from smallcat.datasets.csv_dataset import CSVDataset, CSVLoadOptions, CSVSaveOptions
from smallcat.datasets.delta_table_dataset import (
    DeltaTableDataset,
    DeltaTableLoadOptions,
    DeltaTableSaveOptions,
    SchemaMode,
)
from smallcat.datasets.excel_dataset import (
    ExcelDataset,
    ExcelLoadOptions,
    ExcelSaveOptions,
)
from smallcat.datasets.parquet_dataset import (
    ParquetDataset,
    ParquetLoadOptions,
)


@pytest.mark.parametrize(
    "save_options,load_options",
    [
        (None, None),
        (CSVSaveOptions(), CSVLoadOptions()),
        (None, CSVLoadOptions(sep=",", header=True)),
        (CSVSaveOptions(header=True, sep=";"), None),
        (CSVSaveOptions(header=True, sep=";"), CSVLoadOptions(sep=";", header=True)),
    ],
)
def test_csv_dataset(example_df, local_conn, save_options, load_options):
    file_name = "foo.csv"
    saver = CSVDataset(local_conn, save_options=save_options)
    saver.save_pandas(file_name, example_df)

    dataset = CSVDataset(local_conn, load_options=load_options)
    loaded_df = dataset.load_pandas(file_name)

    pd.testing.assert_frame_equal(example_df, loaded_df)


@pytest.mark.parametrize(
    ("save_options", "load_options"),
    [
        (ExcelSaveOptions(header=True), None),
        (ExcelSaveOptions(header=True), ExcelLoadOptions(header=True)),
        (
            ExcelSaveOptions(header=True, sheet="sheet2"),
            ExcelLoadOptions(
                header=True,
                sheet="sheet2",
                all_varchar=False,
                empty_as_varchar=True,
            ),
        ),
    ],
)
def test_excel_dataset(example_df, local_conn, save_options, load_options):
    file_name = "foo.xlsx"
    saver = ExcelDataset(local_conn, save_options=save_options)
    saver.save_pandas(file_name, example_df)

    dataset = ExcelDataset(local_conn, load_options=load_options)
    loaded_df = dataset.load_pandas(file_name)

    pd.testing.assert_frame_equal(example_df, loaded_df)


@pytest.mark.parametrize(
    "save_options,load_options",
    [
        (None, None),
        (None, ParquetLoadOptions(hive_partitioning=True)),
    ],
)
def test_parquet_dataset(
    example_df,
    another_example_df,
    local_conn,
    save_options,
    load_options,
):
    file_name = "foo/year=2024/part001.parquet"
    another_file_name = "foo/year=2025/part002.parquet"

    (Path(local_conn["extra"]["base_path"]) / file_name).parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    (Path(local_conn["extra"]["base_path"]) / another_file_name).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    saver = ParquetDataset(local_conn, save_options=save_options)
    saver.save_pandas(file_name, example_df)
    saver.save_pandas(another_file_name, another_example_df)

    dataset = ParquetDataset(local_conn, load_options=load_options)
    loaded_df = dataset.load_pandas("foo/**/*.parquet")

    hive_partitioning = load_options and load_options.hive_partitioning
    validation_df = pd.concat(
        [
            example_df.assign(year=2024) if hive_partitioning else example_df,
            another_example_df.assign(year=2025)
            if hive_partitioning
            else another_example_df,
        ],
    ).reset_index(drop=True)

    pd.testing.assert_frame_equal(
        validation_df,
        loaded_df.reset_index(drop=True),
    )


@pytest.mark.parametrize(
    "save_options,load_options",
    [
        (None, None),
        (DeltaTableSaveOptions(), DeltaTableLoadOptions()),
        (
            DeltaTableSaveOptions(schema_mode=SchemaMode.MERGE),
            DeltaTableLoadOptions(version=0),
        ),
    ],
)
def test_delta_table_dataset(example_df, local_conn, save_options, load_options):
    table_path = "foo/"
    saver = DeltaTableDataset(local_conn, save_options=save_options)
    saver.save_pandas(table_path, example_df)

    dataset = DeltaTableDataset(local_conn, load_options=load_options)
    loaded_df = dataset.load_pandas(table_path)

    pd.testing.assert_frame_equal(example_df, loaded_df)
