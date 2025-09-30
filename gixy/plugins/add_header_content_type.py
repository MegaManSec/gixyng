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
            # Check if *_hide_header Content-Type is present in the same scope
            # This is a valid pattern to override backend Content-Type
            if self._has_hide_header_content_type(directive):
                return
            
            reason = 'You probably want "default_type {default_type};" instead of "add_header" or "more_set_headers"'.format(
                default_type=directive.value
            )
            self.add_issue(directive=directive, reason=reason)
    
    def _has_hide_header_content_type(self, directive: AddHeaderDirective):
        """Check if *_hide_header Content-Type exists in the same scope or parent scopes"""
        # List of nginx directives that can hide headers from backend
        hide_header_directives = [
            'proxy_hide_header',
            'fastcgi_hide_header',
            'uwsgi_hide_header',
            'scgi_hide_header',
            'grpc_hide_header'
        ]
        
        # Check in the same block (parent)
        if directive.parent:
            for hide_directive in hide_header_directives:
                hide_headers = directive.parent.find(hide_directive)
                for hh in hide_headers:
                    # hide_header has one argument: the header name
                    if hh.args and hh.args[0].lower() == 'content-type':
                        return True
        
        # Also check in parent scopes (server, http, etc.) because *_hide_header is inherited
        for parent in directive.parents:
            for hide_directive in hide_header_directives:
                hide_headers = parent.find(hide_directive)
                for hh in hide_headers:
                    if hh.args and hh.args[0].lower() == 'content-type':
                        return True
        
        return False
