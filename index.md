# GixyNG: NGINX Security Scanner & Configuration Checker for Security Audits

## Overview

GixyNG is an open source NGINX configuration security scanner and hardening tool that performs static analysis of your nginx.conf to detect security misconfigurations, hardening gaps, and common performance pitfalls before they reach production. Run it locally or in CI/CD to automate NGINX security audits and configuration compliance checks, producing actionable findings that help prevent unstable/slow NGINX servers, and reduce risk from unsafe directives and insecure defaults.

### Quick start

GixyNG (the `gixy` CLI) is distributed on [PyPI](https://pypi.python.org/pypi/GixyNG). You can install it with pip or uv:

```
# pip
pip install GixyNG

# uv
uv tool install GixyNG
```

You can also export your NGINX configuration to a single dump file:

```
# Dumps the full NGINX configuration into a single file (including all includes)
nginx -T > ./nginx-dump.conf
```

And then scan the dump file elsewhere (or via stdin):

```
# Equivalent to scanning the full rendered configuration output.
gixy ./nginx-dump.conf

# Equivalent to above
cat ./nginx-dump.conf | gixy -
```

## What it can do

GixyNG can detect a wide range of NGINX security and performance misconfigurations across `nginx.conf` and included configuration files. The following plugins are supported:

- [[add_header_content_type] Setting Content-Type via add_header](https://gixy.io/plugins/add_header_content_type/)
- [[add_header_multiline] Multiline response headers](https://gixy.io/plugins/add_header_multiline/)
- [[add_header_redefinition] Redefining of response headers by "add_header" directive](https://gixy.io/plugins/add_header_redefinition/)
- [[alias_traversal] Path traversal via misconfigured alias](https://gixy.io/plugins/alias_traversal/)
- [[allow_without_deny] Allow specified without deny](https://gixy.io/plugins/allow_without_deny/)
- [[default_server_flag] Missing default_server flag](https://gixy.io/plugins/default_server_flag/)
- [[error_log_off] `error_log` set to `off`](https://gixy.io/plugins/error_log_off/)
- [[hash_without_default] Missing default in hash blocks](https://gixy.io/plugins/hash_without_default/)
- [[host_spoofing] Request's Host header forgery](https://gixy.io/plugins/host_spoofing/)
- [[http_splitting] HTTP Response Splitting](https://gixy.io/plugins/http_splitting/)
- [[if_is_evil] If is evil when used in location context](https://gixy.io/plugins/if_is_evil/)
- [[invalid_regex] Invalid regex capture groups](https://gixy.io/plugins/invalid_regex/)
- [[low_keepalive_requests] Low `keepalive_requests`](https://gixy.io/plugins/low_keepalive_requests/)
- [[origins] Problems with referer/origin header validation](https://gixy.io/plugins/origins/)
- [[proxy_pass_normalized] `proxy_pass` path normalization issues](https://gixy.io/plugins/proxy_pass_normalized/)
- [[regex_redos] Regular expression denial of service (ReDoS)](https://gixy.io/plugins/regex_redos/)
- [[resolver_external] Using external DNS nameservers](https://gixy.io/plugins/resolver_external/)
- [[return_bypasses_allow_deny] Return directive bypasses allow/deny restrictions](https://gixy.io/plugins/return_bypasses_allow_deny/)
- [[ssrf] Server Side Request Forgery](https://gixy.io/plugins/ssrf/)
- [[try_files_is_evil_too] `try_files` directive is evil without open_file_cache](https://gixy.io/plugins/try_files_is_evil_too/)
- [[unanchored_regex] Unanchored regular expressions](https://gixy.io/plugins/unanchored_regex/)
- [[valid_referers] none in valid_referers](https://gixy.io/plugins/valid_referers/)
- [[version_disclosure] Using insecure values for server_tokens](https://gixy.io/plugins/version_disclosure/)
- [[worker_rlimit_nofile_vs_connections] `worker_rlimit_nofile` must be at least twice `worker_connections`](https://gixy.io/plugins/worker_rlimit_nofile_vs_connections/)

Something not detected? Please open an [issue](https://github.com/MegaManSec/GixyNG/issues) on GitHub with what's missing!

## Usage (flags)

`gixy` defaults to reading a system's NGINX configuration from `/etc/nginx/nginx.conf`. You can also specify the location by passing it to `gixy`:

```
# Analyze the configuration in /opt/nginx.conf
gixy /opt/nginx.conf
```

You can run a focused subset of checks with `--tests`:

```
# Only run these checks
gixy --tests http_splitting,ssrf,version_disclosure
```

Or skip a few noisy checks with `--skips`:

```
# Run everything except these checks
gixy --skips low_keepalive_requests,worker_rlimit_nofile_vs_connections
```

To only report issues of a certain severity or higher, use the compounding `-l` flag:

```
# -l for LOW severity issues and high, -ll for MEDIUM and higher, and -lll for only HIGH severity issues
gixy -ll
```

By default, the output of `gixy` is ANSI-colored; best viewed in an ANSI-compatible terminal. You can use the `--format` (`-f`) flag with the `text` value to get an uncolored output:

```
$ gixy -f text

==================== Results ===================

Problem: [http_splitting] Possible HTTP-Splitting vulnerability.
Description: Using variables that can contain "\n" may lead to http injection.
Additional info: https://gixy.io/plugins/http_splitting/
Reason: At least variable "$action" can contain "\n"
Pseudo config:
include /etc/nginx/sites/default.conf;

    server {

        location ~ /v1/((?<action>[^.]*)\.json)?$ {
            add_header X-Action $action;
        }
    }


==================== Summary ===================
Total issues:
    Unspecified: 0
    Low: 0
    Medium: 0
    High: 1
```

You can also use `-f json` to get a reproducible, machine-readable JSON output:

```
$ gixy -f json
[{"config":"\nserver {\n\n\tlocation ~ /v1/((?<action>[^.]*)\\.json)?$ {\n\t\tadd_header X-Action $action;\n\t}\n}","description":"Using variables that can contain \"\\n\" or \"\\r\" may lead to http injection.","file":"/etc/nginx/nginx.conf","line":4,"path":"/etc/nginx/nginx.conf","plugin":"http_splitting","reason":"At least variable \"$action\" can contain \"\\n\"","reference":"https://gixy.io/plugins/http_splitting/","severity":"HIGH","summary":"Possible HTTP-Splitting vulnerability."}]
```

More flags for usage can be found by passing `--help` to `gixy`. You can also find more information in the [Usage Guide](https://gixy.io/usage/).

## Configuration and plugin options

Some plugins expose options which you can set via CLI flags or a configuration file. You can read more about those in the [Configuration guide](https://gixy.io/configuration/).

## GixyNG for NGINX security and compliance

Unlike running `nginx -t` which only checks syntax, GixyNG actually analyzes your configuration and detects unhardened instances and vulnerabilities.

With GixyNG, you can perform an automated NGINX configuration security review that can run locally or in CI/CD on every change, whether that be for auditing purposes, compliance, or just general testing.

## Contributing

Contributions to GixyNG are always welcome! You can help us in different ways, such as:

- Reporting bugs.
- Suggesting new plugins for detection.
- Improving documentation.
- Fixing, refactoring, improving, and writing new code.

Before submitting any changes in pull requests, please read the contribution guideline document, [Contributing to GixyNG](https://gixy.io/contributing/).

The official homepage of GixyNG is <https://gixy.io/>. Any changes to documentation in GixyNG will automatically be reflected on that website.

The source code can be found at <https://github.com/MegaManSec/GixyNG>.

## What is Gixy? (Background)

*Gixy* is an older NGINX configuration analyzer originally developed by Yandex. GixyNG is a maintained fork of Gixy that adds new checks, performance improvements, hardening suggestions, and support for modern Python and NGINX versions. If you are looking for an NGINX config scanner that is actively maintained, use GixyNG.
