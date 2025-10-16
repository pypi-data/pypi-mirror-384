from NEMO_osticket.tests.test_settings import DATABASES

# NEMO-osticket

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/NEMO-osticket?label=python)](https://www.python.org/downloads/release/python-3110/)
[![PyPI](https://img.shields.io/pypi/v/nemo-osticket?label=pypi%20version)](https://pypi.org/project/NEMO-osticket/)
[![Changelog](https://img.shields.io/gitlab/v/release/nemo-community/atlantis-labs/nemo-osticket?include_prereleases&label=changelog)](https://gitlab.com/nemo-community/atlantis-labs/nemo-osticket/-/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://gitlab.com/nemo-community/atlantis-labs/nemo-osticket/blob/main/LICENSE)

osTicket plugin for NEMO linking tickets to a specific tool

## Installation

```bash
python -m install nemo-osticket
```

### In settings.py:

1. Add `NEMO_osticket` to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    '...',
    'NEMO_osticket', # This needs to be before NEMO
    '...',
    'NEMO',
]
```

2. Add `osticket` database information:
```python
DATABASES = {
    'default': {'...'},
    "osticket": {
        "ENGINE": "mysql.connector.django",
        'NAME': '<db_name>', # usually 'osticket'
        'USER': '<db_user>', # usually 'osticket'
        'PASSWORD': '<db_password>',
        'HOST':'<db_host>',
        'PORT':'<db_port>',
    }
}
```

3. Add an osticket API config dictionary:
```python
OSTICKET_SERVICE = {
    "available": True,
    "url": "https://myosticketservice.com",
    'keyword_arguments': {
        'timeout': 5, # optional
        'headers': {"X-API-Key": "<api_key>"}
    },
}
```

## Usage

Go to Administration -> Customization to configure this plugin and how to match Tool with Tickets from OsTicket

Add a Landing page choice with url `/osticket/tickets` to have a direct link to the search and generic submit a ticket pages

# Tests

To run the tests:
```bash
python runtests.py
```
