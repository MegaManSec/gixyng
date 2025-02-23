"""Module for try_files_is_evil_too plugin."""

import gixy
from gixy.plugins.plugin import Plugin


class error_log_off(Plugin):
    """
    Insecure example:
        location / {
            try_files $uri $uri/ /index.php$is_args$args;
        }
    """

    summary = "The error_log directive does not take the off parameter."
    severity = gixy.severity.MEDIUM
    description = "The error_log directive should not be set to off. It should be set to a valid file path."
    help_url = "https://gixy.getpagespeed.com/en/plugins/error_log_off/"
    directives = ["error_log"]

    def audit(self, directive):
        if directive.args[0] == "off":
            self.add_issue(
                severity=self.severity,
                directive=[directive],
                reason="The error_log directive should not be set to off.",
            )
