# Virement Maitrise Python Library

**Powered by Fintecture**


The Virement Maitrise Python library provides convenient access to the Virement Maitrise API from
applications written in the Python language. It includes a pre-defined set of
classes for API resources that initialize themselves dynamically from API
responses which makes it compatible with a wide range of versions of the Virement Maitrise
API.

## Documentation

See the [Python API docs](https://doc.virementmaitrise.societegenerale.eu).

## Installation (from PyPI)

```sh
pip install --upgrade virementmaitrise
```

### Build Distribution Packages

```sh
pip install build

python -m build
```

### Requirements

-   Python 3.10+ (Python 3.11, 3.12, 3.13 supported)

## Usage

The library needs to be configured with your application identifier, the secret and private keys which is
available in your [Virement Maitrise Developer Console](https://console.virementmaitrise.societegenerale.eu/developers).
For instance, set `virementmaitrise.app_id` to its value:

```python
import virementmaitrise

virementmaitrise.app_id = "39b1597f-b7dd..."

# list application information
resp = virementmaitrise.Application.retrieve()

attributes = resp.data.attributes

# print the description of the application
print(attributes.description)

# print if application supports AIS and PIS scope
print("Supports AIS scope: %r" % attributes.scope.ais)
print("Supports PIS scope: %r" % attributes.scope.pis)
```
