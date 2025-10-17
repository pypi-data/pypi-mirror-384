"""
Models for the custom_css app
"""

import os
import re

# Django Solo
from solo.models import SingletonModel

# Django
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomCSS(SingletonModel):
    """
    Model for storing custom CSS for the site
    """

    css = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Your custom CSS"),
        help_text=_("This CSS will be added to the site after the default CSS."),
    )
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Meta for CustomCSS
        """

        default_permissions = ()
        verbose_name = _("Custom CSS")
        verbose_name_plural = _("Custom CSS")

    def __str__(self) -> str:
        """
        String representation of CustomCSS

        :return:
        :rtype:
        """

        return str(_("Custom CSS"))

    def save(self, *args, **kwargs):
        """
        Save method for CustomCSS

        :param args:
        :type args:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """

        self.pk = 1

        if self.css and len(self.css.replace(" ", "")) > 0:
            # Write the custom CSS to a file
            custom_css_file = open(
                f"{settings.STATIC_ROOT}allianceauth/custom-styles.css", "w+"
            )
            custom_css_file.write(self.compress_css())
            custom_css_file.close()
        else:
            # Remove the custom CSS file
            try:
                os.remove(f"{settings.STATIC_ROOT}allianceauth/custom-styles.css")
            except FileNotFoundError:
                pass

        super().save(*args, **kwargs)

    def compress_css(self) -> str:
        """
        Compress CSS

        :return:
        :rtype:
        """

        css = self.css
        new_css = ""

        # Remove comments
        css = re.sub(pattern=r"\s*/\*\s*\*/", repl="$$HACK1$$", string=css)
        css = re.sub(pattern=r"/\*[\s\S]*?\*/", repl="", string=css)
        css = css.replace("$$HACK1$$", "/**/")

        # url() doesn't need quotes
        css = re.sub(pattern=r'url\((["\'])([^)]*)\1\)', repl=r"url(\2)", string=css)

        # Spaces may be safely collapsed as generated content will collapse them anyway.
        css = re.sub(pattern=r"\s+", repl=" ", string=css)

        # Shorten collapsable colors: #aabbcc to #abc
        css = re.sub(
            pattern=r"#([0-9a-f])\1([0-9a-f])\2([0-9a-f])\3(\s|;)",
            repl=r"#\1\2\3\4",
            string=css,
        )

        # Fragment values can loose zeros
        css = re.sub(
            pattern=r":\s*0(\.\d+([cm]m|e[mx]|in|p[ctx]))\s*;", repl=r":\1;", string=css
        )

        for rule in re.findall(pattern=r"([^{]+){([^}]*)}", string=css):
            # We don't need spaces around operators
            selectors = [
                re.sub(
                    pattern=r"(?<=[\[\(>+=])\s+|\s+(?=[=~^$*|>+\]\)])",
                    repl=r"",
                    string=selector.strip(),
                )
                for selector in rule[0].split(",")
            ]

            # Order is important, but we still want to discard repetitions
            properties = {}
            porder = []

            for prop in re.findall(pattern="(.*?):(.*?)(;|$)", string=rule[1]):
                key = prop[0].strip().lower()

                if key not in porder:
                    porder.append(key)

                properties[key] = prop[1].strip()

            # output rule if it contains any declarations
            if properties:
                new_css += "{}{{{}}}".format(
                    ",".join(selectors),
                    "".join([f"{key}:{properties[key]};" for key in porder])[:-1],
                )

        return new_css
