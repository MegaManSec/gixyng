import gixy
from gixy.plugins.plugin import Plugin


class if_is_evil(Plugin):
    """
    Insecure example:
        location /files {
            alias /home/;
        }
    """
    summary = 'If is Evil... when used in location context.'
    severity = gixy.severity.HIGH
    description = 'Directive "if" has problems when used in location context, in some cases it does not do what you ' \
                  'expect but something completely different instead. In some cases it even segfaults. It is ' \
                  'generally a good idea to avoid it if possible.'
    help_url = 'https://github.com/dvershinin/gixy/blob/master/docs/en/plugins/if_is_evil.md'
    directives = []

    def audit(self, directive):
        parent = directive.parent
        # if immediate parent is not "if" break out
        if not parent or parent.name != 'if':
            return

        # "rewrite ... last", "rewrite ... redirect", and "rewrite ... permanent" are safe
        if directive.name == 'rewrite' and len(directive.args) >= 3 and directive.args[-1] in ('last', 'redirect', 'permanent'):
            return

        # "return" is safe too
        if directive.name == 'return':
            return

        grandparent = parent.parent

        if grandparent and grandparent.name == 'location':
            reason = 'Directive "{directive}" is not safe to use in "if in location" context'.format(directive=directive.name)
            if directive.name == 'rewrite':
                reason = 'Directive "rewrite" is only safe to use in "if in location" context when "last", ' \
                         '"redirect", or "permanent" argument is used'
            self.add_issue(
                severity=gixy.severity.HIGH,
                directive=[directive, parent],
                reason=reason
            )


