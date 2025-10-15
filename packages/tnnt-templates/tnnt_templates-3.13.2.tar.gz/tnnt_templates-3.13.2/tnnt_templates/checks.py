"""
Settings checks
"""

# Standard Library
from enum import Enum

# Django
from django.conf import settings
from django.core.checks import CheckMessage, register


class CheckLevel(Enum):
    """
    Check levels
    """

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


@register()
def check_mandatory_settings(
    app_configs, **kwargs  # pylint: disable=unused-argument
) -> list[CheckMessage]:
    """
    Checks if the mandatory settings are set
    """

    errors: list[CheckMessage] = []

    mandatory_settings = ["TNNT_TEMPLATE_ENTITY_ID", "TNNT_TEMPLATE_ENTITY_NAME"]

    for setting in mandatory_settings:
        if not hasattr(settings, setting):
            errors.append(
                CheckMessage(
                    msg=f"Setting '{setting}' is missing",
                    hint="Please add this setting to your settings file",
                    id="tnnt_templates.E001",
                    level=CheckLevel.ERROR.value,
                ),
            )

    return errors
