import gixy
from gixy.plugins.plugin import Plugin


class return_with_allow_deny(Plugin):
    """
    Insecure example:
        location / {
            allow 127.0.0.1;
            deny all;
            return 200 "hi";
        }
    """
    summary = "The return directive does not obey allow or deny directives, and always takes precedence."
    severity = gixy.severity.MEDIUM
    description = "The return directive is executed before the allow or deny directivres take any affect. You may want to use a named location with the try_files directive instead."
    help_url = "https://joshua.hu/nginx-return-allow-deny"
    directives = ["allow", "deny"]

    def audit(self, directive):
        parent = directive.parent
        return_directive = []
        for ctx in parent.find_recursive('return'):
            return_directive.append(ctx)

        if return_directive:
            self.add_issue(
                directive=[directive] + return_directive,
                reason="The allow and deny directives do not restrict access to pages returned with 'return'.",
            )
