"""
AppConfig for Terra Nanotech theme.
"""

# Django
from django.apps import AppConfig

# AA Templates: Terra Nanotech
from tnnt_templates import __version__


class TerraNanotechThemeConfig(AppConfig):
    """
    AppConfig for Terra Nanotech theme.
    """

    name = "tnnt_templates.theme.terra_nanotech"
    label = "terra_nanotech"
    verbose_name = f"Terra Nanotech Corp Auth Theme v{__version__}"

    def ready(self):
        """
        Ready

        :return:
        :rtype:
        """

        pass  # pylint: disable=unnecessary-pass
