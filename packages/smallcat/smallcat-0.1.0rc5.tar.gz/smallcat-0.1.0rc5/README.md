<p align="center">
  <img src="docs/assets/images/smallcat-logo.png" width="140" alt="smallcat logo">
</p>

<h1 align="center">smallcat</h1>
<p align="center"><em>A small, modular data catalog.</em></p>

<p align="center">
  <a href="https://pypi.org/project/smallcat/"><img src="https://img.shields.io/pypi/v/smallcat.svg" alt="PyPI"></a>
  <a href="https://pypi.org/project/smallcat/"><img src="https://img.shields.io/pypi/pyversions/smallcat.svg" alt="Python versions"></a>
  <a href="https://github.com/DeepKernelLabs/smallcat/actions"><img src="https://img.shields.io/github/actions/workflow/status/DeepKernelLabs/smallcat/publish.yml?label=CI" alt="CI"></a>
  <a href="https://codecov.io/gh/DeepKernelLabs/smallcat"><img src="https://img.shields.io/codecov/c/github/DeepKernelLabs/smallcat" alt="coverage"></a>
  <a href="https://github.com/DeepKernelLabs/smallcat/blob/main/LICENSE"><img src="https://img.shields.io/github/license/DeepKernelLabs/smallcat.svg" alt="license"></a>
  <a href="https://pepy.tech/project/smallcat"><img src="https://static.pepy.tech/badge/smallcat" alt="downloads"></a>
  <a href="https://DeepKernelLabs.github.io/smallcat/"><img src="https://img.shields.io/badge/docs-mkdocs%20material-blue" alt="docs"></a>
</p>

## Install
```bash
pip install smallcat
```

## Quickstart
### Create Catalog

Local catalogs can be kept in YAML files.

```yaml
entries:
    foo:
        file_format: csv
        connection:
            conn_type: fs
            extra:
                base_path: /tmp/smallcat-example/
        load_options:
            header: true
    bar:
        file_format: parquet
        connection:
            conn_type: google_cloud_platform
            extra:
                bucket: my-bucket
        save_options:
            partition_by:
                - year
                - month
```

### Standalone

```python
from smallcat import Catalog

catalog = Catalog.from_path("catalog.yaml")
catalog.save_pandas("foo", df)
df2 = catalog.load_pandas("foo")
```

### With Airflow
```python
from smallcat import Catalog

catalog = Catalog.from_airflow_variable("example_catalog")
df = catalog.load_pandas("bar")
```

## Docs
Read more at [the official docs](https://deepkernellabs.github.io/smallcat/).
