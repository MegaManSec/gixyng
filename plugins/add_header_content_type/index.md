# [add_header_content_type] Using add_header to set Content-Type

## What this check looks for

This plugin looks for configurations that try to set the `Content-Type` response header using `add_header`.

## Why this is a problem

NGINX can end up sending two `Content-Type` headers: one from the upstream, and one you added. Different clients handle duplicates differently, and caches may store an unexpected value. If you are trying to set a fallback MIME type for static content, `default_type` is the right tool.

## Bad configuration

```
# Adds a second Content-Type if the upstream already sets one
add_header Content-Type text/plain;
```

If your backend returns `Content-Type: application/json`, the response may contain both headers.

## Better configuration

```
# Sets the default MIME type for responses that do not already have one
default_type text/plain;
```

`default_type` applies when there is no explicit content type, so you avoid duplicates.

## Safe exception

If you are intentionally replacing the upstream header, hide it first and then add your own:

```
proxy_hide_header Content-Type;
add_header Content-Type "application/octet-stream";
```

This pattern removes the upstream `Content-Type` before adding a new one, so the client sees only a single value.
