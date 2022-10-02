from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidToken(APIException):
    status_code = status.HTTP_406_NOT_ACCEPTABLE
    default_detail = "Token contained no recognizable user identification."
    default_code = "error"


class AuthTokenError(APIException):
    status_code = status.HTTP_406_NOT_ACCEPTABLE
    default_detail = "Recognizable user identification not found."
    default_code = "error"
