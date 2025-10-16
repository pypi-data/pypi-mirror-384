import http


class Error(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def get_error_message(key):
    messages = {
        "ErrorApi4xxBadRequest": "Bad request",
        "ErrorApi401Unauthorized": "Unauthorized",
        "ErrorApi403Forbidden": "Forbidden",
        "ErrorApi404NotFound": "Not found",
        "ErrorApi408Timeout": "Request timed out",
        "ErrorApi409Conflict": "Conflict",
        "ErrorApi410Gone": "Gone",
        "ErrorApi5xxInternalServerError": "Internal server error",
        "ErrorApi504GatewayTimedOut": "Gateway timed out"
    }
    return messages.get(key, "Unknown error")


class BadRequestError(Exception):
    def __init__(self):
        super().__init__(get_error_message("ErrorApi4xxBadRequest"))


class UnauthorizedError(Exception):
    def __init__(self):
        super().__init__(get_error_message("ErrorApi401Unauthorized"))


class ForbiddenError(Exception):
    def __init__(self):
        super().__init__(get_error_message("ErrorApi403Forbidden"))


class NotFoundError(Exception):
    def __init__(self):
        super().__init__(get_error_message("ErrorApi404NotFound"))


class RequestTimedOutError(Exception):
    def __init__(self):
        super().__init__(get_error_message("ErrorApi408Timeout"))


class ConflictError(Exception):
    def __init__(self):
        super().__init__(get_error_message("ErrorApi409Conflict"))


class GoneError(Exception):
    def __init__(self):
        super().__init__(get_error_message("ErrorApi410Gone"))


class InternalServerError(Exception):
    def __init__(self):
        super().__init__(get_error_message("ErrorApi5xxInternalServerError"))


class GatewayTimedOutError(Exception):
    def __init__(self):
        super().__init__(get_error_message("ErrorApi504GatewayTimedOut"))


def credential_notfound_error(name: str) -> Exception:
    return Exception(f"配置名 '{name}' 不存在, 使用 bayes switch '{name}' -e {{endpoint}} 设置")


def request_failed(status_code: int):
    if status_code == http.HTTPStatus.GATEWAY_TIMEOUT:
        return GatewayTimedOutError()
    elif status_code >= 500:
        return InternalServerError()
    elif status_code == http.HTTPStatus.UNAUTHORIZED:
        return UnauthorizedError()
    elif status_code == http.HTTPStatus.FORBIDDEN:
        return ForbiddenError()
    elif status_code == http.HTTPStatus.NOT_FOUND:
        return NotFoundError()
    elif status_code == http.HTTPStatus.REQUEST_TIMEOUT:
        return RequestTimedOutError()
    elif status_code == http.HTTPStatus.CONFLICT:
        return ConflictError()
    elif status_code == http.HTTPStatus.GONE:
        return GoneError()
    elif status_code >= 400:
        return Exception(f"Request failed with status code {status_code}")
    return None
