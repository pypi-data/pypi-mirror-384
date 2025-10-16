from collections.abc import Callable

from .generated.swagger_client import ApiClient
from .generated.swagger_client import DefaultApi
from .generated.swagger_client.configuration import Configuration
from .generated.swagger_client.rest import RESTResponse
from .generated.swagger_client.models.v1_login_body import V1LoginBody
from .client_components.swagger_validator import SwaggerValidator
from .client_components.endpoint_resolver import EndpointResolver
from .client_components.client_response import ClientResponse
from .helpers.utils import parse_endpoint_function
from .helpers.utils import preprocess_raw_input_data


def _fix_boolean_url_params(params: dict):
    '''
    Converts boolean values of the dict to 'true' or 'false'
    The urllib.urlencode function used converts bools to 'True' or 'False',
    which causes an error on the endpoint
    '''
    for key, value in params.items():
        if value is True or value is False:
            params[key] = str(value).lower()


def _convert_names_to_snake_case(data: dict) -> dict:
    '''
    Converts all keys in the dict from camelCase to snake_case
    '''
    new_data = {}
    for key, value in data.items():
        new_key = ''.join(['_' + c.lower() if c.isupper() else c for c in key]).lstrip('_')
        new_data[new_key] = value
    return new_data


def _preprocess_query_params(query_params: dict):
    '''
    Removes nested objects by moving nested keys up.
    Converts query object keys ({filters: {search: value}} => {filters_search: value})
    '''
    removed_keys = []
    new_values = {}
    # find nested objects
    for key, value in query_params.items():
        if isinstance(value, dict):
            removed_keys.append(key)
            for nested_key, nested_value in _convert_names_to_snake_case(value).items():
                new_values[f"{key}_{nested_key}"] = nested_value

    # remove nested objects
    for key in removed_keys:
        query_params.pop(key)
    # put nested object data to the top-level object
    for key, value in new_values.items():
        query_params[key] = value


class Client:
    """A client that can send requests to ReCodEx.
    Automatically handles request validation based on the current swagger specification file.
    """

    def __init__(self, token: str, api_url: str):
        """
        Args:
            token (str): The JWT token used for authentication.
            host (str): The URL of the ReCodEx server.
        """

        # initialize generated classes
        config = Configuration()
        config.host = api_url
        self._generated_client = ApiClient(config, "Authorization", f"Bearer {token}")
        self._generated_api = DefaultApi(self._generated_client)

        # initialize endpoint resolution and validation
        self.endpoint_resolver = EndpointResolver()
        self._validator = SwaggerValidator()

    def get_login_token(self, username: str, password: str) -> str:
        """Fetches the JWT token from ReCodEx.

        Args:
            username (str): The ReCodEx username.
            password (str): The ReCodEx password.

        Returns:
            str: Returns the JWT token.
        """

        response = self.send_request_by_callback(
            DefaultApi.login_presenter_action_default,
            V1LoginBody(username, password),
        )

        response_dict = response.get_parsed_data()
        if response_dict is None:
            raise Exception("Unable to fetch JWT token with the provided credentials")

        return response_dict["payload"]["accessToken"]

    def get_refresh_token(self) -> str:
        """Fetches a new JWT token if the previous did not expire yet.

        Returns:
            str: Returns the new token.
        """

        response = self.send_request_by_callback(DefaultApi.login_presenter_action_refresh)
        response_dict = response.get_parsed_data()
        if response_dict is None:
            raise Exception("Unable to refresh JWT token")

        return response_dict["payload"]["accessToken"]

    def send_request(
        self,
        presenter: str,
        action: str,
        body={},
        path_params={},
        query_params={},
        files={},
        raw_body=False
    ) -> ClientResponse:
        """Sends a request to a single ReCodEx endpoint.
        Automatically validates the request parameters.

        Args:
            presenter (str): The name of the endpoint presenter.
            action (str): The name of the endpoint action.
            body (dict, optional): The body of the request. Can either be a dictionary of a generated model object.
                Defaults to {}.
            path_params (dict, optional): A dictionary of path parameter name-value pairs. Defaults to {}.
            query_params (dict, optional): A dictionary of query parameter name-value pairs. Defaults to {}.
            files (dict, optional): A dictionary of name-path pairs of sent files. Defaults to {}.
            raw_body (bool, optional): Whether the body is sent raw (octet-stream). Defaults to False.

        Returns:
            ClientResponse: Returns an object detailing the response.
        """

        # get the request schema
        endpoint_definition = self.endpoint_resolver.get_endpoint_definition(presenter, action)

        # in case the values are in string format, convert them to the correct types
        path_params, query_params = preprocess_raw_input_data(
            path_params,
            query_params,
            presenter,
            action,
            self.endpoint_resolver
        )

        # validate the request (throws jsonschema.exceptions.ValidationError when invalid)
        if raw_body:
            self._validator.validate(endpoint_definition, path_params=path_params, query_params=query_params)
        else:
            self._validator.validate(endpoint_definition, body, path_params, query_params)

        # convert boolean values to strings to avoid urllib errors
        _fix_boolean_url_params(path_params)
        _fix_boolean_url_params(query_params)

        path_params = _convert_names_to_snake_case(path_params)
        query_params = _convert_names_to_snake_case(query_params)
        files = _convert_names_to_snake_case(files)

        # convert query object keys ({filters: {search: value}} => {filters_search: value})
        _preprocess_query_params(query_params)

        endpoint_callback = self.endpoint_resolver.get_endpoint_callback(presenter, action, self._generated_api)

        # the endpoints must not have the body param passed if empty
        if bool(body):
            endpoint_callback(body=body, **path_params, **query_params, **files)
        else:
            endpoint_callback(**path_params, **query_params, **files)

        raw_response: RESTResponse = self._generated_client.last_response
        response = ClientResponse(raw_response)

        return response

    def send_request_by_callback(
        self,
        endpoint: Callable,
        body={},
        path_params={},
        query_params={},
        files={},
        raw_body=False
    ) -> ClientResponse:
        """Sends a request to a single ReCodEx endpoint.
        Automatically validates the request parameters.

        Args:
            endpoint (Callable): The generated endpoint function to be called.
            body (dict, optional): The body of the request. Can either be a dictionary of a generated model object.
                Defaults to {}.
            path_params (dict, optional): A dictionary of path parameter name-value pairs. Defaults to {}.
            query_params (dict, optional): A dictionary of query parameter name-value pairs. Defaults to {}.
            files (dict, optional): A dictionary of name-path pairs of sent files. Defaults to {}.
            raw_body (bool, optional): Whether the body is sent raw (octet-stream). Defaults to False.

        Returns:
            ClientResponse: Returns an object detailing the response.
        """

        presenter, action = parse_endpoint_function(endpoint)
        return self.send_request(presenter, action, body, path_params, query_params, files, raw_body)
