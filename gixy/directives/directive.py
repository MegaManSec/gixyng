"""This module contains all the classes for directives"""

from gixy.core.variable import Variable
from gixy.core.regexp import Regexp

import ipaddress
import tldextract

_TLD = tldextract.TLDExtract(include_psl_private_domains=False, suffix_list_urls=())

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
        self.line = None  # Line number in source file
        self.file = None  # Source file path

    def set_parent(self, parent):
        """Set parent block for this directive"""
        self.parent = parent

    @property
    def parents(self):
        """Get all parent blocks"""
        parent = self.parent
        while parent:
            yield parent
            parent = parent.parent

    @property
    def variables(self):
        """Get all variables provided by this directive"""
        raise NotImplementedError()

    def find_directives_in_scope(self, name):
        """Find directives in the current scope"""
        for parent in self.parents:
            directive = parent.some(name, flat=False)
            if directive:
                yield directive
        return None

    def find_single_directive_in_scope(self, name):
        """Find a single directive in the current scope"""
        for parent in self.parents:
            directive = parent.some(name, flat=False)
            if directive:
                return directive
        return None



    def __str__(self):
        return f"{self.name} {' '.join(self.args)};"


class AddHeaderDirective(Directive):
    """The add_header directive is used to add a header to the response"""

    nginx_name = "add_header"

    def __init__(self, name, args):
        super(AddHeaderDirective, self).__init__(name, args)
        self.header = args[0].lower()
        self.value = args[1]
        self.headers = {self.header: self.value}
        self.always = False
        if len(args) > 2 and args[2] == "always":
            self.always = True


class MoreSetHeadersDirective(Directive):
    """
    Syntax:	more_set_headers 'Foo: bar' 'Baz: bah';
    """

    nginx_name = "more_set_headers"

    def get_headers(self):
        result = {}
        skip_next = False
        for arg in self.args:
            if arg in ["-s", "-t"]:
                # Mark to skip the next value because it's not a header
                skip_next = True
            elif arg.startswith("-"):
                # Skip any options
                continue
            elif skip_next:
                skip_next = False
            elif not skip_next:
                # Now it's a header in format "Header: value" or "Header:" or just "Header" (for clearing)
                parts = arg.split(":", 1)
                header = parts[0]
                value = ""
                if len(parts) > 1 and parts[1].strip():
                    # strip only whitespace character from left side, preserving newlines
                    # this is needed to support multiline headers
                    value = parts[1].lstrip(" ")
                result[header] = value
        return result

    def __init__(self, name, args):
        super().__init__(name, args)
        self.headers = self.get_headers()
        # first header is the main header name
        self.header = list(self.headers.keys())[0]
        # value is
        self.value = self.headers[self.header]


class SetDirective(Directive):
    nginx_name = "set"
    provide_variables = True

    def __init__(self, name, args):
        super(SetDirective, self).__init__(name, args)
        self.variable = args[0].lstrip("$")
        self.value = args[1]

    @property
    def variables(self):
        return [Variable(name=self.variable, value=self.value, provider=self)]


class AuthRequestSetDirective(Directive):
    nginx_name = "auth_request_set"
    provide_variables = True

    def __init__(self, name, args):
        super().__init__(name, args)
        self.variable = args[0].lstrip("$")
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
        self.variable = args[0].lstrip("$")
        self.value = args[1]

    @property
    def variables(self):
        return [Variable(name=self.variable, provider=self, have_script=False)]


class SetByLuaDirective(Directive):
    nginx_name = "set_by_lua"
    provide_variables = True

    def __init__(self, name, args):
        super().__init__(name, args)
        self.variable = args[0].lstrip("$")
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
    if ip.startswith("[") and "]" in ip:
        ip = ip.split("]")[0][1:]
    try:
        ip_obj = ipaddress.IPv6Address(ip)
        return ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_private
    except ValueError:
        return False


def is_local_ipv4(addr):
    """Check if an IPv4 address is a local address (loopback/private/link-local)."""
    ip = addr.rsplit(":", 1)[0]
    try:
        ip_obj = ipaddress.IPv4Address(ip)
        return ip_obj.is_loopback or ip_obj.is_private or ip_obj.is_link_local
    except ValueError:
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
            ip_candidate = addr
            if addr.startswith("[") and "]" in addr:
                ip_candidate = addr.split("]")[0][1:] # [::1]:53 -> ::1
            elif addr.count(":") == 1:
                ip_candidate = addr.rsplit(":", 1)[0] # 1.2.3.4:53 -> 1.2.3.4 (or name:53 -> name)

            if is_local_ipv4(addr) or is_local_ipv6(addr):
                continue

            try:
                ipaddress.ip_address(ip_candidate) # is it even an ip address?
            except ValueError:
                host = ip_candidate.rstrip(".") # example.com. -> example.com
                if not _TLD(host).suffix:
                    continue # Non-registerable hostname
                external_nameservers.append(addr)
                continue

            external_nameservers.append(addr)
        return external_nameservers

class MapDirective(Directive):
    """
    map $source $destination {
        default value; <- this part
        key     value; <- this part
    }

    geo [$remote_addr] $destination {
      default        ZZ; <-- this part.
      include        conf/geo.conf; <-- this part.
      delete         127.0.0.0/16; <-- this part.
      proxy          192.168.100.0/24; <-- this part.
      proxy          2001:0db8::/32; <-- this part.
      key            value; <-- this part.
    }
    """

    nginx_name = "map" # XXX: Also used for "geo". Could also work for "charset_map"
    provide_variables = True

    def __init__(self, source, destination):
        super().__init__(source, destination)
        self.src_val = source
        self.dest_val = destination[0] if destination and len(destination) == 1 else None
        self.regex = None

        if self.is_regex:
            if self.src_val.startswith('~*'):
                pattern = self.src_val[2:]
                cs = False
            else:
                pattern = self.src_val[1:]
                cs = True
            self.regex = Regexp(pattern, case_sensitive=cs)

    def __str__(self):
        map_str = self.src_val
        if self.dest_val:
            map_str += f" {self.dest_val}"
        map_str += ";"
        return map_str

    @property
    def is_regex(self):
        return self.src_val.startswith("~")

    @property
    def variables(self):
        if not self.regex:
            return []

        ancestor = self.parent
        while ancestor is not None and ancestor.nginx_name != 'map': # XXX: Better to check isinstance(ancestor, MapBlock) but circular import..
            ancestor = getattr(ancestor, 'parent', None)

        if ancestor is None: # This happens for "geo" directives, which is ok because geo directive does not provide variables.
            return []

        result = []
        for name, group in self.regex.groups.items():
            result.append(
                Variable(name=name, value=group, provider=self, boundary=None, ctx=self.src_val)
            )
        return result
