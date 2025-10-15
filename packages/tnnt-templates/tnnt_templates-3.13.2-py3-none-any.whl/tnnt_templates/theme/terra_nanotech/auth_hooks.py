"""
Auth hooks for Terra Nanotech theme
"""

# Alliance Auth
from allianceauth import hooks
from allianceauth.theme.hooks import ThemeHook


class TerraNanotechThemeHook(ThemeHook):
    """
    Terra Nanotech Corp Auth Theme
    https://github.com/terra-nanotech/tn-nt-auth-templates/
    """

    def __init__(self):
        """
        Init
        """

        ThemeHook.__init__(
            self=self,
            name="Terra Nanotech",
            description="Terra Nanotech Corp Auth Theme",
            html_tags={"data-theme": "terra-nanotech"},
            css=[],
            js=[],
            css_template="tnnt_templates/includes/theme/css.html",
            js_template="tnnt_templates/includes/theme/js.html",
            header_padding="3.5em",
        )


@hooks.register("theme_hook")
def register_terra_nanotech_hook():
    """
    Registers the Terra Nanotech theme hook

    :return:
    :rtype:
    """

    return TerraNanotechThemeHook()
