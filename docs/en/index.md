---
#title: "" # Deliberately left blank
description: "Open source NGINX security, hardening, and configuration compliance scanner for automating nginx.conf security audits, compliance checks, and hardening against misconfigurations."
---

# GixyNG: NGINX Security Scanner & Configuration Checker for Security Audits

## Overview

<a href="https://gixy.io/"><img width="192" height="192" alt="GixyNG Mascot Logo" style="float: right;" align="right" src="https://gixy.io/imgs/gixy.jpg" /></a>

GixyNG is an open source NGINX security scanner and configuration hardening tool. It performs static analysis of your nginx.conf to identify security vulnerabilities, misconfigurations, and performance issues before they reach production. With GixyNG, you can run automated NGINX configuration security audits, uncover missed hardening opportunities, and prevent configuration mistakes that lead to slow or unstable NGINX servers.

Currently supported Python versions are 3.6+.

Disclaimer: While GixyNG is well tested only on GNU/Linux, other OSs may have some issues. PRs and bug reports welcome.

### Quick start

GixyNG is distributed on [PyPI](https://pypi.python.org/pypi/GixyNG). You can install it with pip or uv:

```bash
# pip
pip install GixyNG

# uv (recommended for CLIs: installs `gixy` on your PATH)
uv tool install GixyNG

# uv (pip-compatible: installs into the active virtual environment)
uv pip install GixyNG
```

Alternatively, you can run it without installation:

```bash
# uvx runs the tool in an isolated temporary environment
uvx --from GixyNG gixy /etc/nginx/nginx.conf
```

You can also export your NGINX configuration to a single dump-file:

```bash
# Dumps the full nginx configuration into a single file
nginx -T | tee ./nginx-dump.conf
```

And then scan the dump-file elsewhere:

```bash
# Equivalent to scanning a full nginx configuration on a filesystem
gixy ./nginx-dump.conf
```

## What it can do

GixyNG can find various nginx configuration security issues, as well as nginx configuration performance issues, based on your `nginx.conf` and other nginx configuration files. The following plugins are supported to detect these misconfigurations:

*   [[add_header_content_type] Setting Content-Type via add_header](https://gixy.io/plugins/add_header_content_type)
*   [[add_header_multiline] Multiline response headers](https://gixy.io/plugins/add_header_multiline)
*   [[add_header_redefinition] Redefining of response headers by "add_header" directive](https://gixy.io/plugins/add_header_redefinition)
*   [[alias_traversal] Path traversal via misconfigured alias](https://gixy.io/plugins/alias_traversal)
*   [[allow_without_deny] Allow specified without deny](https://gixy.io/plugins/allow_without_deny)
*   [[default_server_flag] Missing default_server flag](https://gixy.io/plugins/default_server_flag)
*   [[error_log_off] `error_log` set to `off`](https://gixy.io/plugins/error_log_off)
*   [[hash_without_default] Missing default in hash blocks](https://gixy.io/plugins/hash_without_default)
*   [[host_spoofing] Request's Host header forgery](https://gixy.io/plugins/host_spoofing)
*   [[http_splitting] HTTP Response Splitting](https://gixy.io/plugins/http_splitting)
*   [[if_is_evil] If is evil when used in location context](https://gixy.io/plugins/if_is_evil)
*   [[invalid_regex] Invalid regex capture groups](https://gixy.io/plugins/invalid_regex)
*   [[low_keepalive_requests] Low `keepalive_requests`](https://gixy.io/plugins/low_keepalive_requests)
*   [[origins] Problems with referer/origin header validation](https://gixy.io/plugins/origins)
*   [[proxy_pass_normalized] `proxy_pass` path normalization issues](https://gixy.io/plugins/proxy_pass_normalized)
*   [[regex_redos] Regular expression denial of service (ReDoS)](https://gixy.io/plugins/regex_redos)
*   [[resolver_external] Using external DNS nameservers](https://gixy.io/plugins/resolver_external)
*   [[return_bypasses_allow_deny] Return directive bypasses allow/deny restrictions](https://gixy.io/plugins/return_bypasses_allow_deny)
*   [[ssrf] Server Side Request Forgery](https://gixy.io/plugins/ssrf)
*   [[try_files_is_evil_too] `try_files` directive is evil without open_file_cache](https://gixy.io/plugins/try_files_is_evil_too)
*   [[unanchored_regex] Unanchored regular expressions](https://gixy.io/plugins/unanchored_regex)
*   [[valid_referers] none in valid_referers](https://gixy.io/plugins/valid_referers)
*   [[version_disclosure] Using insecure values for server_tokens](https://gixy.io/plugins/version_disclosure)
*   [[worker_rlimit_nofile_vs_connections] `worker_rlimit_nofile` must be at least twice `worker_connections`](https://gixy.io/plugins/worker_rlimit_nofile_vs_connections)

Something not detected? Please open an [issue](https://github.com/MegaManSec/GixyNG/issues) on GitHub with what's missing!

## Usage

By default, GixyNG (the `gixy` CLI) will try to analyze your NGINX configuration placed in `/etc/nginx/nginx.conf`.

But you can always specify the needed path:

```
$ gixy /etc/nginx/nginx.conf

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

Or skip some tests:

```
$ gixy --skips http_splitting /etc/nginx/nginx.conf

==================== Results ===================
No issues found.

==================== Summary ===================
Total issues:
    Unspecified: 0
    Low: 0
    Medium: 0
    High: 0
```

Or something else, you can find all other `gixy` arguments with the help command: `gixy --help`

### Plugin options

Some plugins expose options which you can set via CLI flags or config file. CLI flags follow the pattern `--<PluginName>-<option>` with dashes, while config file uses `[PluginName]` sections with dashed keys.

- `origins`:
  - `--origins-domains domains`: Comma-separated list of trusted registrable domains. Use `*` to disable third‑party checks. Example: `--origins-domains example.com,foo.bar`. Default: `*`.
  - `--origins-https-only true|false`: When true, only the `https` scheme is considered valid for `Origin`/`Referer`. Default: `false`.
  - `--origins-lower-hostname true|false`: Normalize hostnames to lowercase before validation. Default: `true`.

- `add_header_redefinition`:
  - `--add-header-redefinition-headers headers`: Comma-separated allowlist of header names (case-insensitive). When set, only dropped headers from this list will be reported; when unset, all dropped headers are reported. Example: `--add-header-redefinition-headers x-frame-options,content-security-policy`. Default: unset (report all).

Examples (config file):

```
[origins]
domains = example.com, example.org
https-only = true

[add_header_redefinition]
headers = x-frame-options, content-security-policy
```

You can also make `gixy` use pipes (stdin), like so:

```bash
echo "resolver 1.1.1.1;" | gixy -
```

Here is a drop-in replacement that removes the Kubernetes section and explains the out-of-band `nginx -T` approach.

### Out-of-band config dump scanning

If you do not want to install and run GixyNG directly on the host running NGINX, you can dump the fully expanded NGINX configuration with `nginx -T` and scan that dump elsewhere.

`nginx -T` prints the complete configuration as NGINX sees it, including all `include` files, expanded in one stream. This makes it ideal for "out-of-band" scanning: export the config from production, then run GixyNG on it elsewhere.

On the system running NGINX, run:

```bash
nginx -T | tee ./nginx-dump.conf
```

Copy `nginx-dump.conf` to your scanning environment, then run:

```bash
gixy ./nginx-dump.conf
```

## What is Gixy?

_Gixy_ is an older NGINX configuration analyzer originally developed by Yandex. GixyNG is a maintained fork of Gixy that adds new checks, performance improvements, hardening suggestions, and support for modern Python and NGINX versions. If you are looking for an NGINX config scanner that is actively maintained, use GixyNG.

## GixyNG for NGINX security and compliance

Unlike running `nginx -t` which only checks syntax, GixyNG actually analyzes your configuration and detects unhardened instances and vulnerabilities.

With GixyNG, you can perform an automated NGINX configuration security review that can run locally or in CI/CD on every change, whether that be for auditing purposes, compliance, or just general testing.

## Contributing

Contributions to GixyNG are always welcome! You can help us in different ways, such as:

- Reporting bugs.
- Suggesting new plugins for detection.
- Improving documentation.
- Fixing, refactoring, improving, and writing new code.

Before submitting any changes in pull requests, please read the contribution guideline document, [Contributing to GixyNG](https://gixy.io/contributing).

The official homepage of GixyNG is [https://gixy.io/](https://gixy.io/). Any changes to documentation in GixyNG will automatically be reflected on that website.

The source code can be found at [https://github.com/MegaManSec/GixyNG](https://github.com/MegaManSec/GixyNG).

