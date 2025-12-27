# [valid_referers] none in valid_referers

## What this check looks for

This plugin warns when `valid_referers` includes the `none` keyword.

## Why this is a problem

`none` means: treat requests with no `Referer` header as valid.

The trouble is that the `Referer` header is optional. Users and browsers can drop it for perfectly normal reasons (HTTPS to HTTP redirects, referrer policy, opaque origins, `data:` URLs), and attackers can omit it deliberately. If you accept `none`, a client can bypass your referer-based control simply by not sending the header.

## Bad configuration

```
valid_referers none server_names *.example.com;

if ($invalid_referer) {
    return 403;
}
```

With `none` allowed, a request without `Referer` will not be considered invalid.

## Better configuration

If you rely on referer checking, be strict:

```
valid_referers server_names *.example.com;

if ($invalid_referer) {
    return 403;
}
```

Then decide what you want to do for missing referers. If missing referers must be allowed for user experience, referer validation is not a reliable security boundary for that endpoint.

## Additional notes

Referer checks are best treated as a friction mechanism (hotlink protection, lightweight clickjacking mitigation), not as any actual security measure.
