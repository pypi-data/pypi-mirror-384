"""
TN-NT Templates content processor
"""

# Django
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest

# AA Templates: Terra Nanotech
from tnnt_templates.app_settings import AppSettings


def tnnt_settings(request: WSGIRequest) -> dict:  # pylint: disable=unused-argument
    """
    Returning a settings dict
    :param request:
    :return:
    """

    # AA logo
    return_value = {
        "TNNT_TEMPLATE_AA_LOGO": "/static/allianceauth/images/auth-logo.svg",
        "REGISTRATION_VERIFY_EMAIL": getattr(
            settings, "REGISTRATION_VERIFY_EMAIL", True
        ),
        "TNNT_TEMPLATE_ENTITY_TYPE": getattr(
            AppSettings, "TNNT_TEMPLATE_ENTITY_TYPE", "alliance"
        ),
        "TNNT_TEMPLATE_ENTITY_ID": getattr(AppSettings, "TNNT_TEMPLATE_ENTITY_ID", 1),
        "TNNT_TEMPLATE_ENTITY_NAME": getattr(
            AppSettings, "TNNT_TEMPLATE_ENTITY_NAME", ""
        ),
    }

    return return_value
