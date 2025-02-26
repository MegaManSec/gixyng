import gixy
from gixy.directives.directive import AddHeaderDirective
from gixy.plugins.plugin import Plugin


class add_header_content_type(Plugin):
    """
    Bad example: add_header Content-Type text/plain;
    Good example: default_type text/plain;
    """

    summary = "Found add_header usage for setting Content-Type."
    severity = gixy.severity.LOW
    description = 'Target Content-Type in NGINX should not be set via "add_header"'
    help_url = "https://github.com/dvershinin/gixy/blob/master/docs/en/plugins/add_header_content_type.md"
    directives = ["add_header"]

    def audit(self, directive: AddHeaderDirective):
        if directive.header == "content-type":
            reason = 'You probably want "default_type {default_type};" instead of "add_header" or "more_set_headers"'.format(
                default_type=directive.value
            )
            self.add_issue(directive=directive, reason=reason)
