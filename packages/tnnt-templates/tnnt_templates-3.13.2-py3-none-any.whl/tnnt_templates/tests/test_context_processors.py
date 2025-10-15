"""
Test the context processor for TNNT template settings.
"""

# Standard Library
import unittest
from unittest.mock import patch

# Django
from django.conf import settings

# AA Templates: Terra Nanotech
from tnnt_templates.context_processors import tnnt_settings


class TestContextProcessorTnntSettings(unittest.TestCase):
    """
    Test the tnnt_settings context processor.
    """

    @patch("tnnt_templates.context_processors.AppSettings")
    def test_tnnt_settings_returns_correct_values(self, MockAppSettings):
        """
        Test the tnnt_settings context processor with custom settings

        :param MockAppSettings:
        :type MockAppSettings:
        :return:
        :rtype:
        """

        MockAppSettings.TNNT_TEMPLATE_ENTITY_ID = 98000030
        MockAppSettings.TNNT_TEMPLATE_ENTITY_TYPE = "corporation"
        MockAppSettings.TNNT_TEMPLATE_ENTITY_NAME = "Terra Nanotech"

        settings.REGISTRATION_VERIFY_EMAIL = True

        request = None  # WSGIRequest is not used in the function
        result = tnnt_settings(request)

        self.assertEqual(
            result["TNNT_TEMPLATE_AA_LOGO"], "/static/allianceauth/images/auth-logo.svg"
        )
        self.assertTrue(result["REGISTRATION_VERIFY_EMAIL"])
        self.assertEqual(result["TNNT_TEMPLATE_ENTITY_ID"], 98000030)
        self.assertEqual(result["TNNT_TEMPLATE_ENTITY_TYPE"], "corporation")
        self.assertEqual(result["TNNT_TEMPLATE_ENTITY_NAME"], "Terra Nanotech")

    @patch("tnnt_templates.context_processors.AppSettings")
    def test_tnnt_settings_handles_missing_settings(self, MockAppSettings):
        """
        Test the tnnt_settings context processor with missing settings to return default values

        :param MockAppSettings:
        :type MockAppSettings:
        :return:
        :rtype:
        """

        del settings.REGISTRATION_VERIFY_EMAIL
        del MockAppSettings.TNNT_TEMPLATE_ENTITY_ID
        del MockAppSettings.TNNT_TEMPLATE_ENTITY_TYPE
        del MockAppSettings.TNNT_TEMPLATE_ENTITY_NAME

        request = None  # WSGIRequest is not used in the function
        result = tnnt_settings(request)

        self.assertEqual(
            result["TNNT_TEMPLATE_AA_LOGO"], "/static/allianceauth/images/auth-logo.svg"
        )
        self.assertTrue(result["REGISTRATION_VERIFY_EMAIL"])
        self.assertEqual(result["TNNT_TEMPLATE_ENTITY_ID"], 1)
        self.assertEqual(result["TNNT_TEMPLATE_ENTITY_TYPE"], "alliance")
        self.assertEqual(result["TNNT_TEMPLATE_ENTITY_NAME"], "")
