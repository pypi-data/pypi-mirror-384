from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken
from django.utils.translation import gettext_lazy as _


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, ValidationError):
            response.data = {
                "error": _("please provide correct data."),
                "fields": response.data,
            }
        elif isinstance(exc, InvalidToken):
            response.data = {
                "error": _("please login again"),
            }
        else:
            response.data = {"error": str(exc)}
        response.data["status_code"] = response.status_code

    return response