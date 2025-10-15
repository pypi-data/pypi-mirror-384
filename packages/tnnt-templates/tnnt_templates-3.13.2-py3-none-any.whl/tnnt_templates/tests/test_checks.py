"""
Test cases for the functions in tnnt_templates.checks
"""

# Django
from django.conf import settings
from django.test import TestCase, override_settings

# AA Templates: Terra Nanotech
from tnnt_templates.checks import check_mandatory_settings


class TestCheckMandatorySettings(TestCase):
    """
    Test the check_mandatory_settings function
    """

    @override_settings(
        TNNT_TEMPLATE_ENTITY_ID=123456789,
        TNNT_TEMPLATE_ENTITY_NAME="Starfleet Alliance",
    )
    def test_returns_no_errors_when_all_mandatory_settings_are_present(self):
        """
        Test that the check_mandatory_settings function returns no errors when all mandatory settings are present.

        :return:
        :rtype:
        """

        errors = check_mandatory_settings(None)

        self.assertEqual(errors, [])

    @override_settings()
    def test_returns_errors_when_mandatory_settings_are_missing(self):
        """
        Test that the check_mandatory_settings function returns errors when mandatory settings are missing.

        :return:
        :rtype:
        """

        del settings.TNNT_TEMPLATE_ENTITY_ID
        del settings.TNNT_TEMPLATE_ENTITY_NAME

        errors = check_mandatory_settings(None)

        self.assertEqual(len(errors), 2)
        self.assertEqual(errors[0].msg, "Setting 'TNNT_TEMPLATE_ENTITY_ID' is missing")
        self.assertEqual(
            errors[1].msg, "Setting 'TNNT_TEMPLATE_ENTITY_NAME' is missing"
        )

    @override_settings(TNNT_TEMPLATE_ENTITY_NAME="Starfleet Alliance")
    def test_returns_error_when_one_mandatory_setting_is_missing(self):
        """
        Test that the check_mandatory_settings function returns an error when one mandatory setting is missing.

        :return:
        :rtype:
        """

        del settings.TNNT_TEMPLATE_ENTITY_ID

        errors = check_mandatory_settings(None)

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].msg, "Setting 'TNNT_TEMPLATE_ENTITY_ID' is missing")
