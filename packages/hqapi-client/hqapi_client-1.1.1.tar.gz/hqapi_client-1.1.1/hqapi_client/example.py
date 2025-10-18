import requests
from typing import Dict, Any

class ExampleClientError(Exception):
    """Custom exception for ExampleClient API errors."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")

class ExampleClient:
    """
    Client for interacting with the Example  API.

    Method:
        - nop: performs no action and returns an empty response.
        - ping: echoes back the provided value in the response.
        - add: accepts two integers and returns their sum.
    """

    BASE_URL = "https://api.eu-west.hqapi.com/api/v1"

    def __init__(self, token: str):
        """
        Initialize the ExampleClient with your API token.

        Args:
            token (str): Your API token.
        """
        self.token = token

    def add(
        self,
        a: int,
        b: int,
    ) -> int:
        """
        The Add method accepts two integers, a and b, and returns their sum.
        This endpoint demonstrates a simple arithmetic operation via a POST request.

        Args:
            s (int): The first number.
            b (int): The second number.

        Returns:
            int: the sum of a and b.
        """
        url_endpoint = f"{self.BASE_URL}/{self.token}/example/add"

        payload: Dict[str, Any] = {
            "a": a,
            "b": b,
        }

        try:
            response = requests.post(url_endpoint, json=payload)
            response.raise_for_status()
            response_json = response.json()
            return int(response_json['value'])
        except requests.exceptions.HTTPError as e:
            try:
                error_json = response.json()
                message = error_json.get("message", str(error_json))
            except ValueError:
                message = response.text
            raise ExampleClientError(response.status_code, message) from e

    def ping(
        self,
        value: str,
    ) -> str:
        """
        The Ping method echoes back the input you send. It is primarily used
        by our development team to verify the round-trip communication of the
        integration. You can also use this method for simple connectivity
        tests to ensure your requests and responses are working correctly.

        Args:
            value (str): The string value to be echoed back by the endpoint.

        Returns:
            str: the value returned by the endpoint.
        """
        url_endpoint = f"{self.BASE_URL}/{self.token}/example/ping"

        payload: Dict[str, Any] = {
            "value": value,
        }

        try:
            response = requests.post(url_endpoint, json=payload)
            response.raise_for_status()
            response_json = response.json()
            return response_json['value']
        except requests.exceptions.HTTPError as e:
            try:
                error_json = response.json()
                message = error_json.get("message", str(error_json))
            except ValueError:
                message = response.text
            raise ExampleClientError(response.status_code, message) from e

    def nop(
        self,
    ) -> None:
        """
        This method performs no operations and returns an empty response. 
        It is intended primarily for testing connectivity and basic request
        handling.
         
        Args:
            None

        Returns:
            None
        """
        url_endpoint = f"{self.BASE_URL}/{self.token}/example/nop"

        payload: Dict[str, Any] = {
        }

        try:
            response = requests.post(url_endpoint, json=payload)
            response.raise_for_status()
            return
        except requests.exceptions.HTTPError as e:
            try:
                error_json = response.json()
                message = error_json.get("message", str(error_json))
            except ValueError:
                message = response.text
            raise ExampleClientError(response.status_code, message) from e
