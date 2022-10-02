from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from rest_framework.reverse import reverse

from utils.authentication import JWT, AudienceENUM


class Email:
    @staticmethod
    def send(
        subject: str, message: str, recipients: list[str], from_email: str | None = None
    ):
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipients,
        )

    @classmethod
    def verify_user(cls, recipient: str, payload: dict):
        username = payload.get("username") or recipient.split("@")[0]
        username = username.capitalize()
        token = JWT.encode(
            payload=payload, aud=AudienceENUM.VERIFY_USER, exp=timedelta(minutes=30)
        )
        subject = "%(username)s account verification for %(base_url)s" % {
            "username": username,
            "base_url": settings.BASE_URL,
        }
        message = "Hii %(username)s, click this link to verify yourself.\n %(url)s" % {
            "username": username,
            "url": settings.BASE_URL
            + reverse("api:verify_user", kwargs={"token": token}),
        }
        print(message)
        cls.send(recipients=[recipient], subject=subject, message=message)
