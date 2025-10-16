
import requests


class DdcException(Exception):
    """Base exception for DDC"""

    def __init__(self, message: str):
        super().__init__(message)


class DdcConfigurationError(DdcException):
    """
    Exception raised for invalid configuration
    """
    pass


class DdcRequestError(DdcException):
    """
    Exception raised for unsuccessful request to remote
    """
    pass


class DdcClientError(DdcException):
    """
    Exception raised for client related errors
    """
    pass



class HTTPException(Exception):
    """
    Exception raised when an HTTP request fails
    """

    def __init__(self, response: requests.Response, response_json=None):
        self.response = response

        self.api_errors = []
        self.api_codes = []
        self.api_messages = []

        status_code = response.status_code

        if response_json is None:
            try:
                response_json = response.json()
            except requests.JSONDecodeError:
                super().__init__(f"{status_code} {response.reason}")
                return

        errors = [response_json.get("Error", [])]
        if response_json.get("error", None):
            errors.append(response_json["error"])
    
        error_text = ""

        for error in errors:
            self.api_errors.append(error)

            if isinstance(error, str):
                self.api_messages.append(error)
                error_text += error + "\n"
                continue

            if "code" in error:
                self.api_codes.append(error["code"])
            if "message" in error:
                self.api_messages.append(error["message"])

            if "code" in error and "message" in error:
                error_text += f"\n{error['code']} - {error['message']}"
            elif "message" in error:
                error_text += '\n' + error["message"]

        # Use := when support for Python 3.7 is dropped
        if not error_text and "detail" in response_json:
            self.api_messages.append(response_json["detail"])
            error_text = '\n' + str(response_json["detail"])

        super().__init__(
            f"{status_code} {response.reason} {error_text}"
        )


class BadRequest(HTTPException):
    """
    Exception raised for a 400 HTTP status code
    """
    pass


class Unauthorized(HTTPException):
    """
    Exception raised for a 401 HTTP status code
    """
    pass


class Forbidden(HTTPException):
    """
    Exception raised for a 403 HTTP status code
    """
    pass


class NotFound(HTTPException):
    """
    Exception raised for a 404 HTTP status code
    """
    pass


class TooManyRequests(HTTPException):
    """
    Exception raised for a 429 HTTP status code
    """
    pass


class ServerError(HTTPException):
    """
    Exception raised for a 5xx HTTP status code
    """
    pass
