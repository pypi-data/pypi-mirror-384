# Mindsight Full API
[![PyPI Latest Release](https://img.shields.io/pypi/v/mindsight-full-api.svg)](https://pypi.org/project/mindsight-full-api/)

Use mindsight full functionalities in your python application.
## Instalation
```sh
pip install mindsight-full-api
```

# Configuration
## Environment variables
To use mindsight-full-api, you need to set two environment variables:
```dotenv
# ---DOTENV EXAMPLE---
MINDSIGHT_FULL_API_TOKEN= #Token to authenticate
MINDSIGHT_FULL_API_URL= #Base path of your api instance
```
# Usage Example
You can use mindsight-full-api in order to create, update and delete registers on all system tables.

## List registers
You can use get methods to list registers of system table. See the following example:
```python
from mindsight_full_api import Absence

# Instantiate Absence client object
absence_client = Absence()

# get_list_absences will return a ApiPaginationResponse object.
# This object represents a pagination response from rest api from people control
# and with get_all method from ApiPaginationResponse object, you can get all
# data of all pages. The data will stored in results attribute of ApiPaginationResponse

absence_data = absence_client.get_list_absences().get_all().results
```
