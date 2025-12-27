# [add_header_redefinition] Redefining response headers with add_header

## What this check looks for

This plugin looks for nested contexts where `add_header` is used in both places.

## Why this is a problem

`add_header` follows an all-or-nothing inheritance rule: headers from the previous level are inherited only if there are no `add_header` directives at the current level. As soon as you add any header in a nested block, you stop inheriting every header defined above it.

That is how teams end up with security headers on most pages, but missing on "just one location".

## Bad configuration

```
server {
    add_header X-Frame-Options "DENY";
    add_header X-Content-Type-Options "nosniff";

    location /static/ {
        # Looks harmless, but it drops the two headers above for /static/
        add_header Cache-Control "public, max-age=86400";
    }
}
```

Requests under `/static/` will only get `Cache-Control`, and the security headers vanish.

## Better configuration

Option 1: keep all headers at one level (often `server`), and avoid redefining them in child blocks.

```
server {
    add_header X-Frame-Options "DENY";
    add_header X-Content-Type-Options "nosniff";
    add_header Cache-Control "public, max-age=86400";
}
```

Option 2: if you really need headers that vary by location, repeat the important ones in the nested block:

```
server {
    add_header X-Frame-Options "DENY";
    add_header X-Content-Type-Options "nosniff";

    location /static/ {
        add_header X-Frame-Options "DENY";
        add_header X-Content-Type-Options "nosniff";
        add_header Cache-Control "public, max-age=86400";
    }
}
```

## Additional information

Recent NGINX versions added `add_header_inherit` to adjust how `add_header` inherits across levels. If you have it available, `add_header_inherit merge;` can help keep a base set of headers while appending per-location headers. The [documentation](https://nginx.org/en/docs/http/ngx_http_headers_module.html#add_header_inherit) states that for `add_header_inherit`:

> The inheritance rules themselves are inherited in a standard way. For example, add_header_inherit merge; specified at the top level will be inherited in all nested levels recursively unless redefined later.
