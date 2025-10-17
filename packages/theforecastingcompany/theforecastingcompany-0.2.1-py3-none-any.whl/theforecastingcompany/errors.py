from typing import Optional

import httpx


class TFCAPIError(RuntimeError):
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)

    def __str__(self):
        error_msg = f"{self.message}"
        if self.status_code:
            error_msg += f" (Status code: {self.status_code})"
        if self.response_body:
            error_msg += f"\nResponse body: {self.response_body}"
        return error_msg


class TFCBadRequestError(TFCAPIError):
    """Exception for 400 Bad Request errors."""

    pass


class TFCUnauthorizedError(TFCAPIError):
    """Exception for 401 Unauthorized errors."""

    pass


class TFCForbiddenError(TFCAPIError):
    """Exception for 403 Forbidden errors."""

    pass


class TFCNotFoundError(TFCAPIError):
    """Exception for 404 Not Found errors."""

    pass


class TFCUnprocessableEntityError(TFCAPIError):
    """Exception for 422 Unprocessable Entity errors."""

    pass


class TFCServerError(TFCAPIError):
    """Exception for 5xx Server errors."""

    pass


def _handle_response(response: httpx.Response) -> None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        error_body = exc.response.text
        if exc.response.status_code == 400:
            raise TFCBadRequestError(
                "Bad request. Check your input parameters.",
                status_code=400,
                response_body=error_body,
            ) from exc
        elif exc.response.status_code == 401:
            raise TFCUnauthorizedError(
                "Unauthorized. Check your API key.",
                status_code=401,
                response_body=error_body,
            ) from exc
        elif exc.response.status_code == 403:
            raise TFCForbiddenError(
                "Forbidden. You don't have permission to access this resource.",
                status_code=403,
                response_body=error_body,
            ) from exc
        elif exc.response.status_code == 404:
            raise TFCNotFoundError("Resource not found.", status_code=404, response_body=error_body) from exc
        elif exc.response.status_code == 422:
            raise TFCUnprocessableEntityError(
                "Unprocessable entity. Check your request data.",
                status_code=422,
                response_body=error_body,
            ) from exc
        elif 500 <= exc.response.status_code < 600:
            raise TFCServerError(
                f"Server error: {exc.response.status_code}",
                status_code=exc.response.status_code,
                response_body=error_body,
            ) from exc
        else:
            raise TFCAPIError(
                f"Unexpected error: {exc.response.status_code}",
                status_code=exc.response.status_code,
                response_body=error_body,
            ) from exc

    try:
        response.json()
    except ValueError as exc:
        raise TFCAPIError("Invalid JSON in response body", response_body=response.text) from exc
