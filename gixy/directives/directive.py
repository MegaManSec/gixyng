"""This module contains all the classes for directives"""

from gixy.core.variable import Variable
from gixy.core.regexp import Regexp


def get_overrides():
    """Get a list of all directives that override the default behavior"""
    result = {}
    for klass in Directive.__subclasses__():
        if not klass.nginx_name:
            continue

        if not klass.__name__.endswith("Directive"):
            continue

        result[klass.nginx_name] = klass
    return result


class Directive:
    """Base class for all directives"""

    nginx_name = None
    is_block = False
    provide_variables = False

    def __init__(self, name, args, raw=None):
        self.name = name
        self.parent = None
        self.args = args
        self._raw = raw

    def set_parent(self, parent):
        """Set parent block for this directive"""
        self.parent = parent

    @property
    def parents(self):
        parent = self.parent
        while parent:
            yield parent
            parent = parent.parent

    @property
    def variables(self):
        raise NotImplementedError()

    def find_directives_in_scope(self, name):
        """Find directives in the current scope"""
        for parent in self.parents:
            directive = parent.some(name, flat=False)
            if directive:
                yield directive
        return None

    def __str__(self):
        return "{name} {args};".format(name=self.name, args=" ".join(self.args))


class AddHeaderDirective(Directive):
    nginx_name = "add_header"

    def __init__(self, name, args):
        super(AddHeaderDirective, self).__init__(name, args)
        self.header = args[0].lower()
        self.value = args[1]
        self.always = False
        if len(args) > 2 and args[2] == "always":
            self.always = True


class SetDirective(Directive):
    nginx_name = "set"
    provide_variables = True

    def __init__(self, name, args):
        super(SetDirective, self).__init__(name, args)
        self.variable = args[0].strip("$")
        self.value = args[1]

    @property
    def variables(self):
        return [Variable(name=self.variable, value=self.value, provider=self)]


class AuthRequestSetDirective(Directive):
    nginx_name = "auth_request_set"
    provide_variables = True

    def __init__(self, name, args):
        super().__init__(name, args)
        self.variable = args[0].strip("$")
        self.value = args[1]

    @property
    def variables(self):
        return [Variable(name=self.variable, value=self.value, provider=self)]


class PerlSetDirective(Directive):
    """The perl_set directive is used to set a value of a variable to a value"""

    nginx_name = "perl_set"
    provide_variables = True

    def __init__(self, name, args):
        super().__init__(name, args)
        self.variable = args[0].strip("$")
        self.value = args[1]

    @property
    def variables(self):
        return [Variable(name=self.variable, provider=self, have_script=False)]


class SetByLuaDirective(Directive):
    nginx_name = "set_by_lua"
    provide_variables = True

    def __init__(self, name, args):
        super().__init__(name, args)
        self.variable = args[0].strip("$")
        self.value = args[1]

    @property
    def variables(self):
        return [Variable(name=self.variable, provider=self, have_script=False)]


class RewriteDirective(Directive):
    nginx_name = "rewrite"
    provide_variables = True
    boundary = Regexp(r"[^\s\r\n]")

    def __init__(self, name, args):
        super().__init__(name, args)
        self.pattern = args[0]
        self.replace = args[1]
        self.flag = None
        if len(args) > 2:
            self.flag = args[2]

    @property
    def variables(self):
        regexp = Regexp(self.pattern, case_sensitive=True)
        result = []
        for name, group in regexp.groups.items():
            result.append(
                Variable(name=name, value=group, boundary=self.boundary, provider=self)
            )
        return result


class RootDirective(Directive):
    """The root directive is used to define a directory that will hold the files."""

    nginx_name = "root"
    provide_variables = True

    def __init__(self, name, args):
        super().__init__(name, args)
        self.path = args[0]

    @property
    def variables(self):
        return [Variable(name="document_root", value=self.path, provider=self)]


class AliasDirective(Directive):
    nginx_name = "alias"

    def __init__(self, name, args):
        super().__init__(name, args)
        self.path = args[0]


def is_local_ipv6(ip):
    """
    Check if an IPv6 address is a local address
    IP may include a port number, e.g. `[::1]:80`
    If port is not specified, IP can be specified without brackets, e.g. ::1
    """
    # Remove brackets if present
    if ip.startswith("[") and "]" in ip:
        ip = ip.split("]")[0][1:]

    # Exclude loopback address ([::1])
    if ip == "::1":
        return True
    # Exclude link-local addresses (fe80::/10)
    if ip.startswith("fe80:"):
        return True
    # Exclude unique local addresses (fc00::/7)
    if ip.startswith("fc") or ip.startswith("fd"):
        return True
    return False


def is_local_ipv4(addr):
    """Check if an IPv4 address is a local address"""
    ip = addr.rsplit(":", 1)[0]
    # Exclude loopback addresses (127.0.0.0/8)
    if ip.startswith("127."):
        return True
    # Exclude private addresses (10.x.x.x, 172.16.x.x - 172.31.x.x, 192.168.x.x)
    if ip.startswith("10.") or ip.startswith("192.168."):
        return True
    if ip.startswith("172."):
        second_octet = int(ip.split(".")[1])
        if 16 <= second_octet <= 31:
            return True
    return False


class ResolverDirective(Directive):
    """
    Syntax:	resolver address ... [valid=time] [ipv4=on|off] [ipv6=on|off] [status_zone=zone];
    """

    nginx_name = "resolver"

    def __init__(self, name, args):
        super().__init__(name, args)
        addresses = []
        for arg in args:
            if "=" in arg:
                continue
            addresses.append(arg)
        self.addresses = addresses

    def get_external_nameservers(self):
        """Get a list of external nameservers used by the resolver directive"""
        external_nameservers = []
        for addr in self.addresses:
            # Check for IPv4 addresses
            if "." in addr and is_local_ipv4(addr):
                continue
            # Check for IPv6 addresses
            if ":" in addr and is_local_ipv6(addr):
                continue

            external_nameservers.append(addr)
        return external_nameservers
