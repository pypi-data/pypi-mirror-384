# Terra Nanotech Auth Templates<a name="terra-nanotech-auth-templates"></a>

[![Version](https://img.shields.io/pypi/v/tnnt-templates?label=release)](https://pypi.org/project/tnnt-templates/)
[![GitHub license](https://img.shields.io/github/license/terra-nanotech/tn-nt-auth-templates)](https://github.com/terra-nanotech/tn-nt-auth-templates/blob/master/LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/tnnt-templates)](https://pypi.org/project/tnnt-templates/)
[![Django](https://img.shields.io/pypi/djversions/tnnt-templates?label=django)](https://pypi.org/project/tnnt-templates/)
![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/terra-nanotech/tn-nt-auth-templates/master.svg)](https://results.pre-commit.ci/latest/github/terra-nanotech/tn-nt-auth-templates/master)
[![Code Style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](http://black.readthedocs.io/en/latest/)
[![Checks](https://github.com/terra-nanotech/tn-nt-auth-templates/actions/workflows/automated-checks.yml/badge.svg)](https://github.com/terra-nanotech/tn-nt-auth-templates/actions/workflows/automated-checks.yml)
[![codecov](https://codecov.io/gh/terra-nanotech/tn-nt-auth-templates/branch/master/graph/badge.svg?token=4JLA8CXJ64)](https://codecov.io/gh/terra-nanotech/tn-nt-auth-templates)

**Terra Nanotech Template Overrides for Alliance Auth**

![TN-NT Auth Template](https://raw.githubusercontent.com/terra-nanotech/tn-nt-auth-templates/master/tnnt_templates/images/tnnt-template.jpg "TN-NT Auth Template")

______________________________________________________________________

<!-- mdformat-toc start --slug=gitlab --maxlevel=6 --minlevel=1 -->

- [Terra Nanotech Auth Templates](#terra-nanotech-auth-templates)
  - [Important Information](#important-information)
  - [Install](#install)

<!-- mdformat-toc end -->

______________________________________________________________________

## Important Information<a name="important-information"></a>

> [!WARNING]
>
> These template overrides are specially tailored for the corporation Terra Nanotech.
> They override templates of apps we use, so it looks like we want it to. This
> might entail changes to templates that also change the behavior in a way we like it
> to be changed.
>
> If you install these template overrides, you need to be aware there will be
> no support for any kind of issues you might encounter, and you have to figure it out
> on your own.

## Install<a name="install"></a>

```shell
pip install tnnt-templates==3.13.2
```

In `local.py` right after `INSTALLED_APPS`:

```python
# TN-NT Auth Templates - https://github.com/terra-nanotech/tn-nt-auth-templates
INSTALLED_APPS.insert(
    0, "tnnt_templates"
)  # Bootstrap 3 fallback for AA community app that haven't been updated to Bootstrap 5 yet.

if "tnnt_templates" in INSTALLED_APPS:
    # Add TN-NT Auth Templates theme
    INSTALLED_APPS += [
        "tnnt_templates.theme.terra_nanotech",
    ]

    # Remove all other themes
    # If you want to use the TN-NT Auth Templates as the only theme,
    # you need to remove all other themes.
    INSTALLED_APPS.remove("allianceauth.theme.darkly")
    INSTALLED_APPS.remove("allianceauth.theme.flatly")
    INSTALLED_APPS.remove("allianceauth.theme.materia")

    # If you are using AA-GDPR, you need to remove the darkly, flatly and materia themes
    # added by AA-GDPR as well.
    if "aagdpr" in INSTALLED_APPS:
        INSTALLED_APPS.remove("aagdpr.theme.darkly")
        INSTALLED_APPS.remove("aagdpr.theme.flatly")
        INSTALLED_APPS.remove("aagdpr.theme.materia")

    # Load Terra Nanotech theme
    DEFAULT_THEME = (
        "tnnt_templates.theme.terra_nanotech.auth_hooks.TerraNanotechThemeHook"
    )
    # Legacy AAv3 user.profile.night_mode=1
    DEFAULT_THEME_DARK = (
        "tnnt_templates.theme.terra_nanotech.auth_hooks.TerraNanotechThemeHook"
    )

    # Add TN-NT Auth Templates context processor
    TEMPLATES[0]["OPTIONS"]["context_processors"].append(
        "tnnt_templates.context_processors.tnnt_settings"
    )

    # Add TN-NT Auth Templates settings
    TNNT_TEMPLATE_ENTITY_ID = 8154711  #  replace with your corp/alliance ID
    TNNT_TEMPLATE_ENTITY_TYPE = "corporation"  # default: "alliance"
    TNNT_TEMPLATE_ENTITY_NAME = "My Awesome Corp/Alliance"  # your corp/alliance name
```

**Important**

If you are using `AA-GDPR`, the template stuff needs to be **after** the `AA_GDPR`
entry, like this:

```python
# GDPR Compliance
INSTALLED_APPS.insert(0, "aagdpr")
AVOID_CDN = True

# TN-NT Auth Templates
INSTALLED_APPS.insert(0, "tnnt_templates")
```
