import enum
from datetime import datetime, timedelta

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from utils.exception import AuthTokenError, InvalidToken

JWT_AUTH = getattr(settings, "JWT_AUTH_CONFIG")


@enum.unique
class AudienceENUM(str, enum.Enum):
    AUTH = "auth"
    TEST = "test"
    VERIFY_USER = "verify_user"


class JWT:
    @staticmethod
    def encode(
        payload: dict,
        exp: datetime = datetime.utcnow() + JWT_AUTH["EXP"],
        aud: AudienceENUM = AudienceENUM.TEST,
    ) -> str:
        payload.update(
            aud=aud,
            iss=JWT_AUTH["ISS"],
            iat=datetime.utcnow(),
            exp=exp,
        )
        return jwt.encode(payload, key=JWT_AUTH["KEY"], algorithm=JWT_AUTH["ALGORITHM"])

    @staticmethod
    def decode(token, aud) -> dict:
        try:
            return jwt.decode(
                token,
                key=JWT_AUTH["KEY"],
                algorithms=(JWT_AUTH["ALGORITHM"],),
                audience=aud,
            )
        except jwt.exceptions.PyJWTError as e:
            raise e


class JWTAuthentication(BaseAuthentication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_model = get_user_model()

    def get_raw_token(self, header_token: str):
        parts = header_token.split()
        if len(parts) < 0:
            raise AuthenticationFailed(
                "Token not provided.", code="unauthorised_access"
            )

        if len(parts) == 2 and parts[0] != JWT_AUTH["AUTH_TYPE"]:
            raise AuthenticationFailed(
                "Invalid auth type used.", code="unauthorised_access"
            )
        if len(parts) == 2 and parts[0] == JWT_AUTH["AUTH_TYPE"]:
            return parts[1]

        return parts[0]

    def get_user(self, raw_token: str):
        payload = JWT.decode(token=raw_token, aud=AudienceENUM.AUTH)
        try:
            user_id = payload["user_id"]
        except KeyError:
            raise InvalidToken()

        try:
            user = self.user_model.objects.get(id=user_id)
        except self.user_model.DoesNotExist:
            raise AuthenticationFailed("User not found.", code="user_not_found")

        if not user.is_active and not user.is_verified:
            raise AuthenticationFailed("User not verified.", code="user_not_verified")
        return user

    def authenticate(self, request):
        header = request.headers.get(JWT_AUTH["AUTH_TYPE"])
        if not header:
            raise AuthenticationFailed(
                "Token not provided.", code="unauthorised_access"
            )
        raw_token = self.get_raw_token(header_token=header)
        user = self.get_user(raw_token=raw_token)
        return user, raw_token


class AuthToken:
    @staticmethod
    def token(**payload) -> dict:
        if "user_id" not in payload.keys():
            raise AuthTokenError()
        exp = datetime.utcnow() + JWT_AUTH["AUTH_EXP"]
        token = JWT.encode(payload=payload, exp=exp, aud=AudienceENUM.AUTH)
        return {"access_token": token}
