"""Module for unanchored_regex plugin."""

import gixy
from gixy.directives.block import LocationBlock
from gixy.plugins.plugin import Plugin


class unanchored_regex(Plugin):
    r"""
    Insecure example:
        location ~ \.php {

        }
    """

    summary = "Regular expressions without anchors can be slow"
    severity = gixy.severity.LOW
    description = "Regular expressions without anchors can be slow"
    help_url = "https://gixy.getpagespeed.com/en/plugins/unanchored_regex/"
    directives = ["location"]

    def audit(self, directive: LocationBlock):
        # check for `location ~ \.php` instead of `location ~ \.php$`
        if not directive.is_regex:
            return
        if directive.needs_anchor():
            self.add_issue(
                severity=gixy.severity.LOW,
                directive=[directive],
                reason="Regular expressions without anchors can be slow",
            )
