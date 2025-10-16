import json
import yaml

from ..generated.swagger_client.rest import RESTResponse


class ClientResponse():
    """Wrapper object containing the request response.
    """

    def __init__(self, response: RESTResponse):
        self.urllib3_response = response.urllib3_response
        self.status = response.status
        self.reason = response.reason
        self._data = response.data
        self.headers = response.getheaders()

    def _get_parsed_data_or_throw(self) -> dict:
        return json.loads(self.get_data_str())

    def get_data_binary(self) -> bytes:
        """Returns the response data in binary format.

        Returns:
            bytes: The response data in binary format.
        """
        return self._data

    def get_data_str(self) -> str:
        """Returns the response data as a string.

        Returns:
            str: The response data as a string.
        """
        return self._data.decode("utf-8")

    def get_parsed_data(self) -> dict | None:
        """Parses response and returns a dictionary or None if the parsing failed.

        Returns:
            dict|None: A dictionary constructed from the payload, or None if the data is not in JSON format.
        """
        try:
            return self._get_parsed_data_or_throw()
        except:
            return None

    def get_payload(self) -> dict | None:
        """Parses response and returns the payload dictionary or None if the parsing failed
            or the response is not a success.

        Returns:
            dict|None: A dictionary constructed from the payload, or None if the data is not in JSON format.
        """
        response = self.get_parsed_data()
        if response is None or not isinstance(response, dict) or "payload" not in response:
            return None

        if "success" not in response or not response["success"]:
            return None

        return response["payload"]

    def check_success(self) -> None:
        """Checks whether the response indicates a successful request.
        Raises an exception if the request was not successful.

        Raises:
            Exception: Thrown when the request was not successful.
        """
        response = self.get_parsed_data()
        if response is None or not isinstance(response, dict):
            raise Exception("The response data is not in the expected format.")

        if response.get("success", False):
            return

        if "error" in response:
            raise Exception(f"The request was not successful: {response['error']}")

        raise Exception("The request was not successful.")

    def get_json_string(self, minimized: bool = False) -> str:
        """Returns the response data as a JSON string.

        Args:
            minimized (bool, optional): Whether the returned string should be a single-line JSON. Defaults to False.

        Raises:
            Exception: Thrown when the response data could not be parsed.

        Returns:
            str: Returns the response data as a JSON string.
        """

        if minimized:
            return self.get_data_str()
        try:
            return json.dumps(self._get_parsed_data_or_throw(), indent=2, ensure_ascii=False)
        except:
            raise Exception("The response data is not in JSON format.")

    def get_yaml_string(self, minimized: bool = False) -> str:
        """Returns the response data as a YAML string.

        Args:
            minimized (bool, optional): Whether the returned string should be a minimized YAML. Defaults to False.

        Raises:
            Exception: Thrown when the response data could not be parsed.

        Returns:
            str: Returns the response data as a YAML string.
        """
        try:
            if minimized:
                return yaml.dump(
                    self._get_parsed_data_or_throw(),
                    default_flow_style=True,
                    indent=None,
                    allow_unicode=True
                )
            return yaml.dump(self._get_parsed_data_or_throw(), allow_unicode=True, indent=2)
        except:
            raise Exception("The response data could not be converted to YAML.")

    def save_to_file(self, file_path: str) -> None:
        """Saves the response data to a file as is (in binary).
        Args:
            file_path (str): Path to the output file.
        """
        with open(file_path, "wb") as f:
            f.write(self.data_binary)
