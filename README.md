GIXY
====


[![Mozilla Public License 2.0](https://img.shields.io/badge/license-MPLv2.0-brightgreen?style=flat-square)](https://github.com/dvershinin/gixy/blob/master/LICENSE)
[![Python tests](https://github.com/dvershinin/gixy/actions/workflows/pythonpackage.yml/badge.svg)](https://github.com/dvershinin/gixy/actions/workflows/pythonpackage.yml)
[![Your feedback is greatly appreciated](https://img.shields.io/maintenance/yes/2025.svg?style=flat-square)](https://github.com/dvershinin/gixy/issues/new)
[![GitHub issues](https://img.shields.io/github/issues/dvershinin/gixy.svg?style=flat-square)](https://github.com/dvershinin/gixy/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/dvershinin/gixy.svg?style=flat-square)](https://github.com/dvershinin/gixy/pulls)

> [!TIP]
> This is an **actively maintained fork** of the original [Gixy](https://github.com/yandex/gixy) project by **Yandex LLC**.  

# Overview
<img align="right" width="192" height="192" src="docs/gixy.png">

Gixy is a tool to analyze NGINX configuration.
The main goal of Gixy is to prevent security misconfiguration and automate flaw detection.

Currently supported Python versions are 3.6 through 3.13.

Disclaimer: Gixy is well tested only on GNU/Linux, other OSs may have some issues.

# What it can do

Right now Gixy can find:

*   [[ssrf] Server Side Request Forgery](https://github.com/dvershinin/gixy/blob/master/docs/en/plugins/ssrf.md)
*   [[http_splitting] HTTP Splitting](https://github.com/dvershinin/gixy/blob/master/docs/en/plugins/httpsplitting.md)
*   [[origins] Problems with referrer/origin validation](https://github.com/dvershinin/gixy/blob/master/docs/en/plugins/origins.md)
*   [[add_header_redefinition] Redefining of response headers by  "add_header" directive](https://github.com/dvershinin/gixy/blob/master/docs/en/plugins/addheaderredefinition.md)
*   [[host_spoofing] Request's Host header forgery](https://github.com/dvershinin/gixy/blob/master/docs/en/plugins/hostspoofing.md)
*   [[valid_referers] none in valid_referers](https://github.com/dvershinin/gixy/blob/master/docs/en/plugins/validreferers.md)
*   [[add_header_multiline] Multiline response headers](https://github.com/dvershinin/gixy/blob/master/docs/en/plugins/addheadermultiline.md)
*   [[alias_traversal] Path traversal via misconfigured alias](https://github.com/dvershinin/gixy/blob/master/docs/en/plugins/aliastraversal.md)
*   [[if_is_evil] If is evil when used in location context](https://github.com/dvershinin/gixy/blob/master/docs/en/plugins/if_is_evil.md)
*   [[allow_without_deny] Allow specified without deny](https://github.com/dvershinin/gixy/blob/master/docs/en/plugins/allow_without_deny.md)
*   [[add_header_content_type] Setting Content-Type via add_header](https://github.com/dvershinin/gixy/blob/master/docs/en/plugins/add_header_content_type.md)
*   [[resolver_external] Using external DNS nameservers](https://blog.zorinaq.com/nginx-resolver-vulns/)
*   [[version_disclosure] Using insecure values for server_tokens](https://github.com/dvershinin/gixy/blob/master/docs/en/plugins/version_disclosure.md)
*   [[try_files_is_evil_too] The try_files directive is evil without open_file_cache](https://www.getpagespeed.com/server-setup/nginx-try_files-is-evil-too)
*   [[proxy_pass_normalized] proxy_pass will decode and normalize paths when specified with a path](https://joshua.hu/proxy-pass-nginx-decoding-normalizing-url-path-dangerous#nginx-proxy_pass)

You can find things that Gixy is learning to detect at [Issues labeled with "new plugin"](https://github.com/dvershinin/gixy/issues?q=is%3Aissue+is%3Aopen+label%3A%22new+plugin%22)

# Installation

## CentOS/RHEL and other RPM-based systems

```bash
yum -y install https://extras.getpagespeed.com/release-latest.rpm
yum -y install gixy
```
### Other systems

Gixy is distributed on [PyPI](https://pypi.python.org/pypi/gixy-ng). The best way to install it is with pip:

```bash
pip install gixy-ng
```

Run Gixy and check results:
```bash
gixy
```

# Usage

By default, Gixy will try to analyze NGINX configuration placed in `/etc/nginx/nginx.conf`.

But you can always specify the needed path:
```
$ gixy /etc/nginx/nginx.conf

==================== Results ===================

Problem: [http_splitting] Possible HTTP-Splitting vulnerability.
Description: Using variables that can contain "\n" may lead to http injection.
Additional info: https://github.com/dvershinin/gixy/blob/master/docs/en/plugins/httpsplitting.md
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

You can also make `gixy` use pipes (stdin), like so:

```bash
echo "resolver 1.1.1.1;" | gixy -
```

## Docker usage

Gixy is available as a Docker image [from the Docker hub](https://hub.docker.com/r/getpagespeed/gixy/). To
use it, mount the configuration that you want to analyse as a volume and provide the path to the
configuration file when running the Gixy image.
```
$ docker run --rm -v `pwd`/nginx.conf:/etc/nginx/conf/nginx.conf getpagespeed/gixy /etc/nginx/conf/nginx.conf
```

If you have an image that already contains your nginx configuration, you can share the configuration
with the Gixy container as a volume.
```
$  docker run --rm --name nginx -d -v /etc/nginx
nginx:alpinef68f2833e986ae69c0a5375f9980dc7a70684a6c233a9535c2a837189f14e905

$  docker run --rm --volumes-from nginx dvershinin/gixy /etc/nginx/nginx.conf

==================== Results ===================
No issues found.

==================== Summary ===================
Total issues:
    Unspecified: 0
    Low: 0
    Medium: 0
    High: 0

```

# Contributing
Contributions to Gixy are always welcome! You can help us in different ways:
  * Open an issue with suggestions for improvements and errors you're facing;
  * Fork this repository and submit a pull request;
  * Improve the documentation.

Code guidelines:
  * Python code style should follow [pep8](https://www.python.org/dev/peps/pep-0008/) standards whenever possible;
  * Pull requests with new plugins must have unit tests for it.
