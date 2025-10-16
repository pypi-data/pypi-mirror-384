# ReCodEx Client Library

A client API library for the [ReCodEx](https://github.com/ReCodEx) system.
This library can be used in custom scripts and command-line interfaces for fine-grained interactions with the system.

## Installation

The recommended way to install the library is via `pip`. Python 3.11 is recommended, but other versions may also work:

```bash
pip install recodex-pylib
```

### Installation from Source

For developers or those who prefer to install directly from the source code, follow these steps. First, you need to generate the API code from the OpenAPI Specification (OAS) file. This is done by a script that requires `wget` and Java to be installed on your system (automatically downloads the Swagger Codegen CLI as jar from Maven.org). Assuming all commands are executed from the repository root.

```bash
./bin/init.sh
```

Then, you can either use your system's Python installation:
```bash
python3 install -r requirements.txt
python3 install -e .
```

Or, you can set up a local `venv` environment (recommended):

```bash
python3 -m venv ./venv
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install -e .
```

Which can be activated in your shell with:
```bash
source ./venv/bin/activate
```

This will install the library in interactive mode, meaning that changes made to the source afterwards will be automatically reflected in the installation.


## Usage

### Creating Client Instance

The Client class is the primary interface with the library and can be created using an existing API token or ReCodEx credentials.

By using the `get_client_from_token` and `get_client_from_credentials` functions shown below, a local session file will be created that holds the host URL and API token.
In case a session already exists, the functions will remove it and create a new one.
Note that the `get_client_from_credentials` function will always communicate with the server to create a new API token, please use the function below if there is a session available.

The `get_client_from_session` function can be used to create a Client instance directly from the session file without communicating with the server.

It is not recommended to instantiate the Client directly (without the `client_factory`), because doing so will not create a session.

```python
from recodex import client_factory
from recodex.client import Client

# URL of the API server
api_url = "http://localhost:4000"

# JWT token used for authentication
api_token = "eyJhbGciOi..."

username = "user"
password = "pwd"

# creating a client with an API token (also creates a session file that stores the API token)
client = client_factory.get_client_from_token(api_url, api_token, verbose=True)

# creating a client with ReCodEx credentials (also creates a session file that stores a newly created API token)
client = client_factory.get_client_from_credentials(api_url, username, password, verbose=True)

# creating a client from the session
client = client_factory.get_client_from_session()

# removing the session file
client_factory.remove_session()
```

### Calling Endpoints

There are two methods for calling an endpoint that differ on how the it is specified.
- `send_request` accepts string names of the presenter and action.
- `send_request_by_callback` accepts a generated callback.

Request parameters are passed with the `path_params`, `query_params`, `body`, and `files` function parameters as name-value pairs.
Generated model instances can also be passed to the `body` parameter. 

```python
# DefaultApi can be used as an enumeration of all endpoint callbacks
from recodex.generated.swagger_client import DefaultApi
# generated models are imported one by one
from recodex.generated.swagger_client.models.id_organizational_body import IdOrganizationalBody

# specify endpoint with string identifiers
response = client.send_request("groups", "set_organizational", path_params={"id": "154b..."}, body={"value": True})

# specify endpoint with a callback
response = client.send_request_by_callback(
  DefaultApi.groups_presenter_action_set_organizational, 
  path_params={"id": "154b..."},
  # body can also be specified with a generated model class
  body=IdOrganizationalBody(value=True)
)
```

The methods return a `ClientResponse` object that contains the status, headers, and the actual data.
The data can be retrieved in multiple ways.

```python
# binary response data
binary_data = response.get_data_binary()

# stringified response data
utf8_string = response.get_data_str()

# raw data parsed into a dictionary
dictionary_data = response.get_parsed_data()
if dictionary_data is None:
  raise Exception("Data is not in JSON format.")

# payload extracted from the parsed data (typical case)
payload = response.get_payload()

# if the payload is irrelevant, we can only check for success
# (an exception is raised if the call failed)
response.check_success()

# formatted data (useful for printing in the CLI)
formatted_json_string = response.get_json_string()
formatted_yaml_string = response.get_yaml_string()
```

### Utility Functions

In case you want to manually create api tokens, the Client contains methods for this purpose. 

```python
new_token = client.get_login_token(username, password)
refresh_token = client.get_refresh_token()
```

To upload a file, you can use the `upload` utility function that automatically sends the file in chunks.

```python
from recodex.helpers.file_upload_helper import upload
file_id = upload(client, "file.txt", verbose=True)
```

# Development

## Commands

The `commands` folder contains four utility commands:
- `init.sh` is used for initial setup of the repository after download; it is described in the installation section.
- `update-generated-api.sh` generates code from a new OAS and replaces the old one. It also generates a diff summary in [api-changes.md](api-changes.md)
- `run-tests-locally.sh` installs the library in interactive mode and runs all tests in the `tests` folder.


## Repository Structure

### Library Code

The `./src/recodex` contains all code of the library.

The `client.py` contains the main `Client` class that links all parts together.
It uses the `SwaggerValidator` (`client_components/swagger_validator.py`) class to validate requests against their schema and the `EndpointResolver` (`client_components/endpoint_resolver.py`) to translate endpoint identifiers to the generated API functions.

It uses the generated `ApiClient` and `DefaultApi` classes to interface the generated part of the library, which is contained in the `generated` folder.
The folder is not part of the repository and needs to be manually generated.

The `aliases.yaml` file contains all aliases for endpoints. These aliases can be used instead of the default presenter and action identifiers.
The aliases are parsed and managed by the `AliasContainer` (`client_components/alias_container.py`) class.


### Repository Utilities

During code regeneration, the `./src/swagger-diffchecker.py` script is used to find differences between the old and new OAS and writes a summary to this README file.

### Testing

Testing relies on a mock ReCodEx API server implemented in flask that exposes a few endpoints, which are implemented in the `./tests/mockEndpoints` folder.
The files are then linked to the server in the `./tests/mock_server.py` script.

The actual tests are implemented in dedicated classes in the `./tests/testClasses` folder.
They derive from the `test_class_base.py` which uses the full login process to connect to the mock server.

The tests are automatically run in GitHub CI/CD, where code is generated from the `./tests/swagger.yaml` file.
This file should be updated regularly to make sure the tests reflect the latest state.


## Latest API Endpoint Changes

You can find a summary of the latest API changes [here](api-changes.md).
