"""Module for try_files_is_evil_too plugin."""

import gixy
from gixy.plugins.plugin import Plugin


class try_files_is_evil_too(Plugin):
    """
    Insecure example:
        location / {
            try_files $uri $uri/ /index.php$is_args$args;
        }
    """

    summary = "The try_files directive is evil without open_file_cache"
    severity = gixy.severity.MEDIUM
    description = "The try_files directive introduces performance overhead."
    help_url = "https://www.getpagespeed.com/server-setup/nginx-try_files-is-evil-too"
    directives = ["try_files"]

    def audit(self, directive):
        # search for open_file_cache ...; on the same or higher level
        open_file_cache = directive.find_single_directive_in_scope("open_file_cache")
        if not open_file_cache or open_file_cache.args[0] == "off":
            self.add_issue(
                severity=gixy.severity.MEDIUM,
                directive=[directive],
                reason="The try_files directive introduces performance overhead without open_file_cache",
            )
