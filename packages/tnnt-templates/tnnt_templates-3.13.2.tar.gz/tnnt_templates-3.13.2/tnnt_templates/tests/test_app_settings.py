"""
Test the AppSettings class
"""

# Standard Library
import unittest
from unittest.mock import patch

# AA Templates: Terra Nanotech
from tnnt_templates.app_settings import AppSettings


class TestAppSettings(unittest.TestCase):
    """
    Test the AppSettings class
    """

    @patch("django.apps.apps.is_installed", return_value=True)
    def test_aagdpr_installed_returns_true(self, mock_is_installed):
        """
        Test the aagdpr_installed method when aagdpr is installed

        :param mock_is_installed:
        :type mock_is_installed:
        :return:
        :rtype:
        """

        self.assertTrue(AppSettings.aagdpr_installed())

    @patch("django.apps.apps.is_installed", return_value=False)
    def test_aagdpr_installed_returns_false(self, mock_is_installed):
        """
        Test the aagdpr_installed method when aagdpr is not installed

        :param mock_is_installed:
        :type mock_is_installed:
        :return:
        :rtype:
        """

        self.assertFalse(AppSettings.aagdpr_installed())
