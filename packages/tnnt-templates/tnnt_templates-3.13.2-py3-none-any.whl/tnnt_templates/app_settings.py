"""
App settings
"""

# Django
from django.apps import apps

# Alliance Auth (External Libs)
from app_utils.app_settings import clean_setting


class AppSettings:  # pylint: disable=too-few-public-methods
    """
    App settings from local.py
    """

    TNNT_TEMPLATE_ENTITY_TYPE = clean_setting(
        name="TNNT_TEMPLATE_ENTITY_TYPE", default_value="alliance", required_type=str
    )

    TNNT_TEMPLATE_ENTITY_ID = clean_setting(
        name="TNNT_TEMPLATE_ENTITY_ID", default_value=1, required_type=int
    )

    TNNT_TEMPLATE_ENTITY_NAME = clean_setting(
        name="TNNT_TEMPLATE_ENTITY_NAME", default_value="", required_type=str
    )

    @staticmethod
    def aagdpr_installed() -> bool:
        """
        Check if aagdpr is installed
        """

        return apps.is_installed("aagdpr")
