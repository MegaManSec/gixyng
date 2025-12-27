# \[origins\]: Weak Referer/Origin validation

This check looks for common mistakes when using `$http_origin` or `$http_referer` to gate security behavior (CORS, clickjacking headers, etc.). It focuses on regex-based validation in `if` conditions and in `map`-based CORS allowlists that reflect an origin into a response header.

## What it detects

### Regex that can be bypassed to match an untrusted domain

Examples of bypasses this plugin tries to find:

- Suffix injection: `https://good.example.com.evil.com`
- Prefix injection: `http://evil.com/?https://good.example.com`
- Scheme confusion (when you meant to require https): `http://good.example.com`

### Invalid values that should never be treated as a valid Origin/Referer

The plugin reports patterns that accept values that are syntactically invalid for the header being validated:

- Origin must be: `<scheme>://<hostname>[:port]` (no path, query, or fragment).
- Referer should be an absolute URL including scheme and hostname.

It can also flag values that contain uppercase letters or unusual characters in the scheme/host.

### Common header typo

`$http_referrer` is not a valid NGINX variable for the HTTP Referer header. The correct variable is `$http_referer`.

## Why this matters

Origin and Referer are attacker-controlled request headers. If your config uses them to decide whether to:

- set `Access-Control-Allow-Origin`,
- set `X-Frame-Options` / `Content-Security-Policy: frame-ancestors`,
- enable credentials (`Access-Control-Allow-Credentials: true`),

then a slightly-wrong regex can silently turn a strict policy into "trust anything that looks kind of right".

Regex allowlists are especially easy to get wrong when you combine:

- alternation (`|`),
- partial anchoring (`^` without `$`, or vice versa),
- match-any-character dots (`.`),
- optional groups,
- subdomain handling,
- ports,
- scheme handling.

## What triggers a finding

You will typically see findings in these patterns:

### `if`-based validation

```
# Intended: allow only yandex.ru
# Risk: also matches https://metrika-hacked-yandex.ru/
if ($http_referer !~ "^https://([^/])+metrika.*yandex\.ru/") {
    add_header X-Frame-Options SAMEORIGIN;
}
```

```
# Invalid for Origin: origin cannot contain a path
if ($http_origin !~ "^https://yandex\.ru/$") {
    add_header X-Frame-Options SAMEORIGIN;
}
```

```
# Wrong variable name (typo)
if ($http_referrer !~ "^https://yandex\.ru/") {
    add_header X-Frame-Options SAMEORIGIN;
}
```

### `map`-based CORS allowlists that reflect an origin

The plugin also inspects this common pattern:

```
# Invalid origin reflected: matches subdomain5example.com
map $http_origin $allow_origin {
    default "";
    ~^https://subdomain.example.com$ $http_origin;
}

add_header Access-Control-Allow-Origin $allow_origin always;
```

If the `map` regex can be bypassed (or matches invalid Origin forms), you can end up reflecting a hostile origin.

## Bad configuration example

```
# Intended to allow only yandex domains, but can also match:
# https://www.yandex.ru.evil.com
if ($http_origin ~* ((^https://www\.yandex\.ru)|(^https://ya\.ru)$)) {
    add_header Access-Control-Allow-Origin "$http_origin";
    add_header Access-Control-Allow-Credentials "true";
}
```

Common issues here:

- alternation with uneven anchoring,
- missing `$` anchors,
- reflecting `$http_origin` directly when the allowlist is not strict.

## Safer configuration patterns

### Prefer `map` with a strict allowlist and controlled reflection

```
map $http_origin $allow_origin {
    default "";

    # Allow example.com and any subdomain, optional port, https only.
    ~^https://([A-Za-z0-9-]+\.)?example\.com(?::[0-9]{1,5})?$ $http_origin;
}

add_header Access-Control-Allow-Origin $allow_origin always;
add_header Access-Control-Allow-Credentials "true" always;
```

Why this is better:

- only allowlisted origins are reflected,
- everything else becomes an empty value,
- the pattern is fully anchored and describes the full Origin syntax.

### Keep Origin rules strict (Origin has no path)

If you need to validate `Origin`, always anchor the entire value, including any optional port.

Good structure to aim for:

- `^https://`
- optional subdomain
- exact registrable domain
- optional `:port`
- `$`

## Notes for Referer validation

If your goal is anti-hotlinking or basic referer checks, consider using `valid_referers` (from `ngx_http_referer_module`, [here](https://nginx.org/en/docs/http/ngx_http_referer_module.html)) instead of hand-rolled regex in `if`. It is not perfect, but it is easier to audit than ad-hoc patterns.
