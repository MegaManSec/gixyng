import gixy
from gixy.directives.directive import AddHeaderDirective
from gixy.plugins.plugin import Plugin


class add_header_multiline(Plugin):
    """
        Insecure example:
    add_header Content-Security-Policy "
        default-src: 'none';
        img-src data: https://mc.yandex.ru https://yastatic.net *.yandex.net https://mc.yandex.${tld} https://mc.yandex.ru;
        font-src data: https://yastatic.net;";
    """

    summary = "Found a multi-line header."
    severity = gixy.severity.LOW
    description = (
        "Multi-line headers are deprecated (see RFC 7230). "
        "Some clients never supports them (e.g. IE/Edge)."
    )
    help_url = "https://github.com/dvershinin/gixy/blob/master/docs/en/plugins/addheadermultiline.md"
    directives = ["add_header", "more_set_headers"]

    def audit(self, directive: AddHeaderDirective):
        for header, value in directive.headers.items():
            if "\n\x20" in value or "\n\t" in value:
                self.add_issue(directive=directive)
                break
            if "\n" in value:
                reason = (
                    'A newline character is found in the directive "{directive}". The resulting header {header} will be '
                    "incomplete. Ensure the value is fit on a single line".format(
                        directive=directive.name, header=header
                    )
                )
                self.add_issue(
                    severity=gixy.severity.HIGH, directive=directive, reason=reason
                )
                break
