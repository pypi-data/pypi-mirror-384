import jsonschema.exceptions
import jsonschema
from jsonschema import validate


class SwaggerValidator:
    """Class used to validate requests against a swagger schema.
    """

    def __validate_params(self, endpoint_definition, method, params):
        # skip validation if the endpoint does not expect any
        if "parameters" not in endpoint_definition:
            return

        param_defs = endpoint_definition["parameters"]
        for param_def in param_defs:
            # check if correct method
            if method != param_def["in"]:
                continue

            param_name = param_def["name"]
            # check if param is absent
            if param_name not in params:
                # fail validation if it is required
                if param_def["required"]:
                    raise jsonschema.exceptions.ValidationError(f"Param '{param_name}' is required.")
                # skip if it is not required
                continue

            validate(params[param_name], param_def["schema"])

    # converts a generated body instance to a dictionary
    def __convert_generated_to_dict(self, generated_body):
        # this dict contains the body parameters with a '_' prefix
        raw_dict = generated_body.__dict__
        refined_dict = {}
        # keep keys with the prefix
        for key, value in raw_dict.items():
            if key[0] == '_':
                # remove the prefix
                refined_dict[key[1:]] = value
        return refined_dict

    def __validate_body(self, endpoint_definition: dict, body):
        # skip if there is no body definition
        if "requestBody" not in endpoint_definition:
            return

        content = endpoint_definition["requestBody"]["content"]
        # validate json bodies, do not validate uploaded files
        if "application/json" in content:
            schema = content["application/json"]["schema"]
            validate(body, schema)

    def validate(self, endpoint_definition: dict, body={}, path_params={}, query_params={}):
        """Validates request parameters.

        Args:
            endpoint_definition (dict): The parsed swagger schema of the request.
            body (dict, optional): The body of the request. Can either be a dictionary of a generated model object.
                Defaults to {}.
            path_params (dict, optional): A dictionary of path parameter name-value pairs. Defaults to {}.
            query_params (dict, optional): A dictionary of query parameter name-value pairs. Defaults to {}.
        """

        self.__validate_params(endpoint_definition, "path", path_params)
        self.__validate_params(endpoint_definition, "query", query_params)

        # convert generated body objects to a dict
        if type(body) is dict:
            body_dict = body
        else:
            body_dict = self.__convert_generated_to_dict(body)
        self.__validate_body(endpoint_definition, body_dict)
