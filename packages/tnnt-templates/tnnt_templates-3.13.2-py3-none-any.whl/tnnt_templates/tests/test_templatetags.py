"""
Unit tests for TN-NT Template tags

This module contains unit tests for custom template tags used in the TN-NT Auth Theme.
The tests ensure that the template tags behave as expected under various conditions.
"""

# Django
from django.template import Context, Template
from django.test import TestCase, modify_settings

# AA Templates: Terra Nanotech
from tnnt_templates import __version__


class TestTemplateTags(TestCase):
    """
    Unit test class for verifying the functionality of TN-NT template tags.

    This class contains test cases to ensure that the custom template tags
    used in the TN-NT Auth Theme behave as expected under various conditions.
    """

    def setUp(self):
        """
        Sets up the test context for the test cases.

        This method initializes a Django template context with a predefined
        content string. The context is used in the template rendering tests
        to verify the behavior of custom template tags.

        :return:
        :rtype:
        """

        self.context = Context(
            {"content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit."}
        )

    def test_should_return_content_when_string_starts_with_substring(self):
        """
        Tests that the template renders the content when the string starts with the specified substring.

        This test verifies that the custom `startswith` filter correctly identifies
        when the `content` string begins with the substring "Lorem" and ensures
        that the content is included in the rendered template.

        :return: None
        """

        template_to_render = Template(
            "{% load tnnt_templates %}"
            '{% if content|startswith:"Lorem" %}{{ content }}{% endif %}'
        )
        rendered_template = template_to_render.render(self.context)

        self.assertInHTML(
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            rendered_template,
        )

    def test_should_not_return_content_when_string_does_not_start_with_substring(self):
        """
        Tests that the template does not render the content when the string does not start with the specified substring.

        This test verifies that the custom `startswith` filter correctly identifies
        when the `content` string does not begin with the substring "ipsum" and ensures
        that the content is excluded from the rendered template.

        :return: None
        """

        template_to_render = Template(
            "{% load tnnt_templates %}"
            '{% if content|startswith:"ipsum" %}{{ content }}{% endif %}'
        )
        rendered_template = template_to_render.render(self.context)

        self.assertNotIn(
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            rendered_template,
        )

    @modify_settings(INSTALLED_APPS={"append": "aagdpr"})
    def test_should_return_true_when_app_is_installed(self):
        """
        Tests that the template renders 'True' when the specified app is installed.

        This test verifies the behavior of the custom `is_app_installed` template tag
        by appending the app "aagdpr" to the `INSTALLED_APPS` setting. It ensures
        that the template correctly identifies the app as installed and renders 'True'.

        :return: None
        """

        template_to_render = Template(
            "{% load tnnt_templates %}"
            '{% is_app_installed "aagdpr" as is_myapp_installed %}'
            "{% if is_myapp_installed %}True{% else %}False{% endif %}"
        )
        rendered_template = template_to_render.render(Context({"version": __version__}))

        self.assertEqual(rendered_template, "True")

    @modify_settings(INSTALLED_APPS={"remove": "aagdpr"})
    def test_should_return_false_when_app_is_not_installed(self):
        """
        Tests that the template renders 'False' when the specified app is not installed.

        This test verifies the behavior of the custom `is_app_installed` template tag
        by removing the app "aagdpr" from the `INSTALLED_APPS` setting. It ensures
        that the template correctly identifies the app as not installed and renders 'False'.

        :return: None
        """

        template_to_render = Template(
            "{% load tnnt_templates %}"
            '{% is_app_installed "aagdpr" as is_myapp_installed %}'
            "{% if is_myapp_installed %}True{% else %}False{% endif %}"
        )
        rendered_template = template_to_render.render(Context({"version": __version__}))

        self.assertEqual(rendered_template, "False")
