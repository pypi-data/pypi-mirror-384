"""
Management command to anonymize all email addresses in the database.
"""

# Standard Library
from urllib.parse import urlparse

# Django
from django.conf import settings
from django.core.management.base import BaseCommand

# Alliance Auth
from allianceauth.authentication.models import User


def get_input(text) -> str:
    """
    Wrapped input to enable import

    :param text:
    :type text:
    :return:
    :rtype:
    """

    return input(text)


class Command(BaseCommand):
    """
    Anonymize all email addresses in the database.
    """

    help = "This command will anonymize each user's email address in the database."

    def add_arguments(self, parser):
        """
        Add argument to parser
        :param parser:
        :type parser:
        :return:
        :rtype:
        """

        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_true",
            help="Do NOT prompt the user for input of any kind.",
        )

    def _anonymize_user_emails(self) -> None:
        """
        Start the anonymization

        :return:
        :rtype:
        """

        self.stdout.write(msg="Anonymizing email addresses …")

        site_fqdn = urlparse(settings.SITE_URL).netloc

        # Get all users and filter those who need anonymization
        users = User.objects.exclude(email="").exclude(email__endswith=f"@{site_fqdn}")

        # Loop through filtered users and anonymize email address
        for user in users:
            self.stdout.write(f"Anonymizing email address for {user.username} …")

            user.email = f"{user.pk}@{site_fqdn}"
            user.save()

        self.stdout.write(msg=self.style.SUCCESS("Anonymization complete!"))

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        """
        Ask before running …

        :param args:
        :type args:
        :param options:
        :type options:
        :return:
        :rtype:
        """

        self.stdout.write(
            msg=self.style.SUCCESS(
                "This will anonymize each user's email address in the database."
            )
        )

        if not options["noinput"]:
            user_input = get_input(text="Are you sure you want to proceed? (yes/no) ")
        else:
            user_input = "yes"

        if user_input.lower() == "yes":
            self.stdout.write(msg="Starting, Please stand by …")
            self._anonymize_user_emails()
        else:
            self.stdout.write(msg=self.style.WARNING("Aborted."))
