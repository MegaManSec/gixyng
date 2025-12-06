"""Module for low_keepalive_requests plugin."""

import gixy
from gixy.plugins.plugin import Plugin


class low_keepalive_requests(Plugin):
    """
    Insecure example:
        keepalive_requests 100;
    """

    summary = "The keepalive_requests directive should be at least 1000."
    severity = gixy.severity.LOW
    description = "The keepalive_requests directive should be at least 1000. Any value lower than this may result in client disconnections."
    help_url = "https://gixy.getpagespeed.com/en/plugins/low_keepalive_requests/"
    directives = ["keepalive_requests"]

    def audit(self, directive):
        if not directive.args:
            return
        try:
            value = int(directive.args[0])
        except (ValueError, TypeError, IndexError):
            return
        if value < 1000:
            self.add_issue(
                severity=self.severity,
                directive=[directive],
                reason="The keepalive_requests directive should be at least 1000.",
            )

