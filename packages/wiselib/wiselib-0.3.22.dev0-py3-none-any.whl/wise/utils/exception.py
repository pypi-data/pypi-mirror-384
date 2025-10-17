import logging
from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.response import Response
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

RETURN_TO_USER = "__return_to_user"


class NotLockedError(Exception):
    pass


class UserError(Exception):
    def __init__(self, msg, status_code: int = status.HTTP_400_BAD_REQUEST, **kwargs):
        self.msg = msg
        self.status_code = status_code
        self.kwargs = kwargs


class UserErrorResponse(Response):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user_error_response(self)


class BaseControllerException(Exception):
    status = status.HTTP_400_BAD_REQUEST
    message = "<Base Controller Exception message>"
    data: dict = {}
    return_to_user = False

    def __init__(self, **kwargs):
        self.data = kwargs


def wise_exception_handler(exc, context):
    if isinstance(exc, UserError):
        return user_error_response(
            Response({"message": exc.msg, **exc.kwargs}, status=exc.status_code)
        )

    if isinstance(exc, BaseControllerException):
        resp = Response({"message": exc.message, "data": exc.data}, status=exc.status)
        if exc.return_to_user:
            resp = user_error_response(resp)
        return resp

    if isinstance(exc, RequestException):
        try:
            data = exc.response.json()
            if data.get(RETURN_TO_USER):
                return Response(data, status=exc.response.status_code)
        except Exception as e:
            logger.error(f"Request exception parsing error: {e=}, {exc.response=}.")

        logger.exception(
            f"Request exception: {exc=}, url={exc.response.url}, "
            f"status={exc.response.status_code}, response={exc.response.text}"
        )
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Default behaviour
    return exception_handler(exc, context)


def user_error_response(response: Response) -> Response:
    data = response.data or {}
    if isinstance(data, str):
        data = {"message": data}

    data[RETURN_TO_USER] = True
    response.data = data

    if response.status_code // 100 not in (4, 5):
        response.status_code = status.HTTP_400_BAD_REQUEST
    return response


def optional_exception_handling():
    """
    Adds a boolean parameter to decorated function determined whether to return None on exception or raise it.
    """

    def decorator(func: callable):
        def wrapper(*args, none_on_exception=False, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if not none_on_exception:
                    raise
                logger.exception(f"Exception in {func.__name__}: {e}")
                return None

        return wrapper

    return decorator
