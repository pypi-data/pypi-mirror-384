"""
Test cases for the management command to anonymizes user emails.
"""

# Standard Library
from io import StringIO
from unittest.mock import patch

# Django
from django.test import TestCase, override_settings

# Alliance Auth (External Libs)
from app_utils.testing import create_fake_user

# AA Templates: Terra Nanotech
from tnnt_templates.management.commands.tnnt_anonymize_emails import Command, get_input


class TestManagementCommandAnonymizeEmails(TestCase):
    """
    Test cases for the management command to anonymizes user emails.
    """

    def call_command(self, *args, **kwargs):
        """
        Call the management command to anonymize emails.

        :param args:
        :type args:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """

        # Django
        from django.core.management import call_command

        call_command(
            "tnnt_anonymize_emails",
            *args,
            stdout=StringIO(),
            stderr=StringIO(),
            **kwargs,
        )

    def setUp(self):
        """
        Set up the test case by creating a fake user with a specific email address.

        :return:
        :rtype:
        """

        self.user = create_fake_user(character_id=2001, character_name="Wesley Crusher")

        self.user.email = "wesley.crusher@enterprise.space"
        self.user.save()

    @override_settings(SITE_URL="https://auth.testserver.net")
    def test_command_anonymize_emails_with_noinput(self):
        """
        Test that the command anonymizes emails when noinput is set

        :return:
        :rtype:
        """

        self.call_command("--no-input")

        self.user.refresh_from_db()

        self.assertEqual(
            first=self.user.email, second=f"{self.user.pk}@auth.testserver.net"
        )

    def test_starts_anonymization_when_user_confirms(self):
        """
        Test that the command starts anonymization when the user confirms

        :return:
        :rtype:
        """

        with (
            patch(
                "tnnt_templates.management.commands.tnnt_anonymize_emails.get_input"
            ) as mock_input,
            patch.object(Command, "_anonymize_user_emails") as mock_anonymize,
        ):
            mock_input.return_value = "yes"
            command = Command()
            command.handle(noinput=False)

        mock_input.assert_called_once_with(
            text="Are you sure you want to proceed? (yes/no) "
        )
        mock_anonymize.assert_called_once()

    def test_aborts_anonymization_when_user_declines(self):
        """
        Test that the command does not start anonymization when the user declines

        :return:
        :rtype:
        """

        with (
            patch(
                "tnnt_templates.management.commands.tnnt_anonymize_emails.get_input"
            ) as mock_input,
            patch.object(Command, "_anonymize_user_emails") as mock_anonymize,
        ):
            mock_input.return_value = "no"
            command = Command()
            command.handle(noinput=False)

        mock_input.assert_called_once_with(
            text="Are you sure you want to proceed? (yes/no) "
        )
        mock_anonymize.assert_not_called()

    def test_returns_user_input_when_valid_string_is_provided(self):
        """
        Test that the get_input function returns the user input when a valid string is provided.

        :return:
        :rtype:
        """

        with patch("builtins.input", return_value="yes"):
            result = get_input("Are you sure?")

            self.assertEqual(result, "yes")

    def test_handles_empty_input_gracefully(self):
        """
        Test that the get_input function handles empty input gracefully.

        :return:
        :rtype:
        """

        with patch("builtins.input", return_value=""):
            result = get_input("Enter something:")

            self.assertEqual(result, "")

    def test_handles_whitespace_only_input(self):
        """
        Test that the get_input function handles whitespace-only input correctly.

        :return:
        :rtype:
        """

        with patch("builtins.input", return_value="   "):
            result = get_input("Enter something:")

            self.assertEqual(result, "   ")

    def test_handles_special_characters_in_input(self):
        """
        Test that the get_input function handles special characters in input correctly.

        :return:
        :rtype:
        """

        with patch("builtins.input", return_value="!@#$%^&*()"):
            result = get_input("Enter special characters:")

            self.assertEqual(result, "!@#$%^&*()")
