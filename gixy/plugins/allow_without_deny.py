import gixy
from gixy.plugins.plugin import Plugin


class allow_without_deny(Plugin):
    """
    Bad example: add_header Content-Type text/plain;
    Good example: default_type text/plain;
    """
    summary = 'Found allow directive(s) without deny in the same context.'
    severity = gixy.severity.HIGH
    description = 'The "allow" directives should be typically accompanied by "deny all;" directive.'
    help_url = 'https://github.com/dvershinin/gixy/blob/master/docs/en/plugins/allow_without_deny.md'
    directives = ['allow']

    def audit(self, directive):
        parent = directive.parent
        if not parent:
            return
        if directive.args == ['all']:
            # for example, "allow all" in a nested location which allows access to otherwise forbidden parent location
            return
        deny_found = False
        for child in parent.children:
            if child.name == 'deny':
                deny_found = True
        if not deny_found:
            reason = 'You probably want "deny all;" after all the "allow" directives'
            self.add_issue(
                directive=directive,
                reason=reason
            )


