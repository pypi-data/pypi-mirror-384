import os
from collections.abc import Callable
import yaml
from prance import ResolvingParser
from ..helpers.utils import camel_case_to_snake_case
from ..generated.swagger_client import DefaultApi
from ..generated.swagger_client.rest import ApiException
from ..client_components.alias_container import AliasContainer


class EndpointResolver:
    """Class that converts endpoint presenter and action names or their aliases to a callback.
    """

    def __init__(self):
        # load aliases.yaml
        self.__load_user_aliases()

        # load the swagger spec
        self.__load_spec()

        # extract endpoint definitions
        self.__init_definitions()

        # init the alias container and add user aliases
        self.__init_aliases()

    def __get_spec_path(self):
        # the swagger is located in the 'generated' folder
        dirname = os.path.dirname(__file__)
        return os.path.join(dirname, '../generated/swagger.yaml')

    def __load_spec(self):
        filepath = self.__get_spec_path()
        parser = ResolvingParser(filepath, backend='openapi-spec-validator')
        self.spec = parser.specification

    def __load_user_aliases(self):
        dirname = os.path.dirname(__file__)
        filepath = os.path.join(dirname, '../aliases.yaml')
        with open(filepath) as file:
            self.user_aliases: dict[str, dict] = yaml.safe_load(file)

    # construct dict from operationId (snake case) to endpoint definitions
    # definitions are identical to swagger definitions (body of method field) with the added 'method' key
    def __init_definitions(self):
        self.definitions: dict[str, dict] = {}
        for path, path_body in self.spec["paths"].items():
            for method, method_body in path_body.items():
                method_body["method"] = method

                # add snake case names used by the endpoint functions
                if "parameters" in method_body:
                    param_defs = method_body["parameters"]
                    for param_def in param_defs:
                        param_def["python_name"] = camel_case_to_snake_case(param_def["name"])

                operation_id = method_body["operationId"]
                snake_case_operation_id = camel_case_to_snake_case(operation_id)
                self.definitions[snake_case_operation_id] = method_body

    def __init_aliases(self):
        # init the alias container
        self.alias_container = AliasContainer(self.definitions)

        for presenter, presenter_alias_obj in self.user_aliases.items():
            if 'alias' in presenter_alias_obj:
                self.alias_container.add_presenter_alias(presenter, presenter_alias_obj['alias'])

            if 'actions' not in presenter_alias_obj:
                continue

            for action, action_alias in presenter_alias_obj['actions'].items():
                self.alias_container.add_action_alias(presenter, action, action_alias)

    def get_swagger(self) -> str:
        """Reads the current swagger specification file and returns it.

        Returns:
            str: Returns the content of the swagger specification file.
        """
        filepath = self.__get_spec_path()
        with open(filepath, "r") as handle:
            return handle.read()

    def get_endpoint_callback(self, presenter: str, action: str, generated_api: DefaultApi) -> Callable:
        """Finds and returns the generated endpoint.

        Args:
            presenter (str): The name of the presenter or alias.
            action (str): The name of the action or alias.
            generated_api (DefaultApi): The generated DefaultApi instance used.

        Raises:
            ApiException: Thrown when the endpoint was not found.

        Returns:
            Callable: Returns the generated endpoint callback.
        """

        operation_id = self.alias_container.get_operation_id(presenter, action)
        endpoint_callback = getattr(generated_api, operation_id, None)
        if endpoint_callback is None:
            raise ApiException(500, f"Endpoint {operation_id} not found.")
        return endpoint_callback

    def get_endpoint_definition(self, presenter: str, action: str) -> dict:
        """Returns the schema definition of the endpoint.

        Args:
            presenter (str): The name of the presenter or alias.
            action (str): The name of the action or alias.

        Returns:
            dict: A dictionary containing the endpoint schema.
        """

        operation_id = self.alias_container.get_operation_id(presenter, action)
        return self.definitions[operation_id]

    def endpoint_has_body(self, presenter: str, action: str) -> bool:
        """Returns whether an endpoint request expects a body.

        Args:
            presenter (str): ReCodEx presenter or alias.
            action (str): ReCodEx action or alias.

        Returns:
            bool: Returns whether an endpoint request expects a body.
        """
        definition = self.get_endpoint_definition(presenter, action)
        return "requestBody" in definition

    def get_endpoint_params(self, presenter: str, action: str, method: str) -> list[dict]:
        """Returns a list of endpoint parameters matching the selected method.

        Args:
            presenter (str): ReCodEx presenter or alias.
            action (str): ReCodEx action or alias.
            method (str): Either 'path' or 'query'.

        Returns:
            list[dict]: Returns a list of endpoint parameters matching the selected method.
        """
        definition = self.get_endpoint_definition(presenter, action)

        if "parameters" not in definition:
            return []

        # filter params by method
        param_defs_filtered = []
        param_defs = definition["parameters"]
        for param_def in param_defs:
            if method.lower() == param_def["in"]:
                param_defs_filtered.append(param_def)

        return param_defs_filtered

    def get_path_params(self, presenter: str, action: str) -> list[dict]:
        """Returns a list of endpoint path parameters.

        Args:
            presenter (str): ReCodEx presenter or alias.
            action (str): ReCodEx action or alias.

        Returns:
            list[dict]: Returns a list of endpoint path parameters.
        """
        return self.get_endpoint_params(presenter, action, 'path')

    def get_path_param(self, presenter: str, action: str, param_name: str) -> dict | None:
        """Returns a specific endpoint path parameter or None if not found.

        Args:
            presenter (str): ReCodEx presenter or alias.
            action (str): ReCodEx action or alias.
            param_name (str): Name of a path parameter.

        Returns:
            Returns a specific endpoint path parameter or None if not found.
        """
        path_params = self.get_path_params(presenter, action)
        for path_param in path_params:
            if path_param["name"] == param_name or path_param["python_name"] == param_name:
                return path_param
        return None

    def get_query_params(self, presenter: str, action: str) -> list[dict]:
        """Returns a list of endpoint query parameters.

        Args:
            presenter (str): ReCodEx presenter or alias.
            action (str): ReCodEx action or alias.

        Returns:
            list[dict]: Returns a list of endpoint query parameters.
        """
        return self.get_endpoint_params(presenter, action, 'query')

    def get_query_param(self, presenter: str, action: str, param_name: str) -> dict | None:
        """Returns a specific endpoint query parameter or None if not found.

        Args:
            presenter (str): ReCodEx presenter or alias.
            action (str): ReCodEx action or alias.
            param_name (str): Name of a query parameter.

        Returns:
            Returns a specific endpoint query parameter or None if not found.
        """
        query_params = self.get_query_params(presenter, action)
        for query_param in query_params:
            if query_param["name"] == param_name or query_param["python_name"] == param_name:
                return query_param
        return None

    def get_presenters(self) -> list[str]:
        """Returns a list of presenters in snake case without the '_presenter' suffix.

        Returns:
            list[str]: Returns a list of presenters in snake case without the '_presenter' suffix.
        """
        return self.alias_container.get_presenters()

    def get_actions(self, presenter) -> list[str]:
        """Returns a list of actions in snake case without the 'action_' prefix.

        Args:
            presenter (str): The presenter containing the actions. Can be any presenter alias.

        Returns:
            list[str]: Returns a list of actions in snake case without the 'action_' prefix.
        """
        return self.alias_container.get_actions(presenter)
