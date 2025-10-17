# SPEC Utils
SPEC-Utils is a set of connectors to consume [Grupo SPEC](https://grupospec.com) and third-party applications from Python.

SPEC-Utils is used by Grupo SPEC within [netSync](https://gitlab.com/spec-sa-ar/net_sync), but it can be used by anyone in their integration projects -or any other purpose that they want :sunglasses: -. 


Why use SPEC-Utils?
- :zap: __Fast to code__: Increase the speed to develop integrations features by about 200% to 300%. \*
- :x: __Fewer bugs__: Reduce about 40% of human (developer) induced errors. \*
- :bulb: __Intuitive__: Great editor support. Completion everywhere. Less time debugging.
- :nerd_face: __Easy__: Designed to be easy to use and learn. Less time reading docs.
- :part_alternation_mark: __Short__: Minimize code duplication. Multiple features from each parameter declaration. Fewer bugs.

\* Estimation based on tests on an internal development team, building production applications.

For more info and help, visit the [SPEC-Utils Repository](https://gitlab.com/spec-sa-ar/spec-utils) and [SPEC-Utils Documentation](https://spec-utils.readthedocs.io/en/latest/)


## Requirements
Python 3.8+

SPEC-Utils stands on shoulders of:

- [requests](https://pypi.org/project/requests/): For the synchronous HTTP requests.
- [aiohttp](https://pypi.org/project/aiohttp/): For the asynchronous HTTP requests.
- [pandas](https://pypi.org/project/pandas/): For the database features.
- [SQLAlchemy](https://pypi.org/project/SQLAlchemy/): For the database connections.
- [pydantic](https://pypi.org/project/pydantic/): For the data parts.

## Install

Can use: 
```shell
pip install spec-utils
```
Or:

```shell
python -m pip install spec-utils
```

## Example
### Net-Time
#### Import module

```python
from spec_utils import nettime6 as nt6
```

#### Client settings


```python
URL = '<your-nettime-url>'
USERNAME = '<your-username>'
PWD = '<your-password>'
```

#### Using client

```python
with nt6.Client(url=URL, username=USERNAME, pwd=PWD) as client:
    print(client.get_employees())

```

<details>

<summary>See out...</summary>

```python

{
  'total': 2,
  'items': [{'id': 1, 'nif': '123789456'}, {'id': 2, 'nif': '987321654'}
]}
```

</details>


#### Using async client
```python
async with nt6.AsyncClient(url=URL, username=USERNAME, pwd=PWD) as client:
    print(await client.get_employees())

```

<details>

<summary>See out...</summary>

```python

{
  'total': 2,
  'items': [{'id': 1, 'nif': '123789456'}, {'id': 2, 'nif': '987321654'}
]}
```

</details>


## Async coverage

|     Module     |    Async support   |       Index name       |
|:--------------:|:------------------:|:----------------------:|
| nettime6       | :heavy_check_mark: | `NT6AsyncClient`       |
| specmanagerapi | :heavy_check_mark: | `SMAPIAsyncClient`     |
| visma          | :heavy_check_mark: | `VismaAsyncClient`     |
| certronic      | :heavy_check_mark: | `CertronicAsyncClient` |
| wdms           | :x:                | `WDMSClient`           |
| exactian       | :x:                | :x:                    |
| specmanagerdb  | :x:                | :x:                    |


## License
This project is licensed under the terms of the GNU GPLv3 license.