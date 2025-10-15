"""
Template filter for Terra Nanotech templates
"""

# Django
from django.apps import apps
from django.template.defaulttags import register


@register.filter
def startswith(haystack, needle):
    """
    Custom Django template filter to check if a string starts with a specified substring.

    This filter can be used in Django templates to evaluate whether the given string
    starts with the provided substring. If the condition is met,
    it returns `True`; otherwise, `False`.

    Usage:
        {% load tnnt_templates %}

        {% if string|starts_with:"substring" %}
            <!-- Render content if the string starts with the substring -->
        {% endif %}

    :param haystack: The string to be checked.
    :type haystack: str
    :param needle: The substring to check for at the start of `haystack`.
    :type needle: str
    :return: `True` if `haystack` starts with `needle`, otherwise `False`.
    :rtype: bool
    """

    return haystack.startswith(needle)


@register.simple_tag
def is_app_installed(app_name):
    """
    Custom Django template tag to check if a specific app is installed.

    This tag can be used in Django templates to determine whether a given app,
    identified by its name, is included in the `INSTALLED_APPS` setting. It returns
    `True` if the app is installed, otherwise `False`.

    Usage:
        {% load tnnt_templates %}

        {% is_app_installed "myapp" as is_myapp_installed %}
        {% if is_myapp_installed %}
            <!-- Render content if the app is installed -->
        {% endif %}

    :param app_name: The name of the app to check.
    :type app_name: str
    :return: `True` if the app is installed, otherwise `False`.
    :rtype: bool
    """

    return apps.is_installed(app_name)
