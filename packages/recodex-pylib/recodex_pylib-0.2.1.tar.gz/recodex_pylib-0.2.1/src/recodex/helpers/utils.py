from collections.abc import Callable


def camel_case_to_snake_case(camel_case_string):
    return ''.join(['_' + char.lower() if char.isupper() else char for char in camel_case_string])


def parse_endpoint_function(endpoint: Callable) -> tuple[str, str]:
    """Extracts the presenter and action names from a generated endpoint function.

    Args:
        endpoint (Callable): A generated endpoint function.

    Returns:
        tuple[str]: Returns a (presenter, action) tuple.
    """

    name = endpoint.__name__
    presenter_pos = name.find("_presenter")
    action_pos = name.find("action_")
    presenter = name[:presenter_pos]
    action = name[action_pos:]

    return (presenter, action)


def preprocess_raw_input_data(
        path_params: dict,
        query_params: dict,
        presenter: str,
        action: str,
        endpoint_resolver
) -> tuple[dict, dict]:
    """Refines raw string values of path and query parameters based on a schema.

    Args:
        path_params (dict): Path parameters.
        query_params (dict): Query parameters.
        presenter (str): Endpoint presenter.
        action (str): Endpoint action.
        endpoint_resolver (_type_): Endpoint resolver used by the client.

    Returns:
        tuple[dict, dict]: Returns preprocessed path and query parameters.
    """

    processed_path_params = _parse_input_values(path_params, presenter, action, endpoint_resolver.get_path_param)
    processed_query_params = _parse_input_values(query_params, presenter, action, endpoint_resolver.get_query_param)
    return (processed_path_params, processed_query_params)


def _parse_input_values(params: dict, presenter: str, action: str, param_definition_callback: Callable) -> dict:
    processed_params = {}
    for key, value in params.items():
        # get parameter schema
        param_definition = param_definition_callback(presenter, action, key)
        # by default, the new value will be the same
        processed_params[key] = value

        # skip undefined parameters or parameters that are not stringified
        if param_definition is None or (not isinstance(value, str)):
            continue

        # parse value based on type
        type = param_definition['schema']['type']
        if type == "boolean":
            if value.lower() == 'true':
                processed_params[key] = True
            elif value.lower() == 'false':
                processed_params[key] = False
            # keep invalid values for jsonschema errors
        elif type == "number" or type == "integer":
            try:
                if type == "integer":
                    processed_params[key] = int(value)
                else:
                    processed_params[key] = float(value)
            except:
                # keep invalid values for jsonschema errors
                pass
    return processed_params
