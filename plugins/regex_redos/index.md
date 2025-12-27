# [regex_redos] Regular Expression Denial of Service (ReDoS)

## What this check looks for

This plugin scans regex usage in directives like:

- `location ~ ...`
- `if ($var ~ ...)`
- `rewrite ...`

and warns about patterns that are likely to cause catastrophic backtracking. This issue is also known as [ReDoS](https://en.wikipedia.org/wiki/ReDoS).

## Why this is a problem

PCRE-style regex engines can take exponential time on certain inputs when the pattern is ambiguous (nested groups, overlapping alternations, repeated wildcards). With user-controlled input (URI, headers), a single request can burn a lot of CPU in one worker, allowing it to effectively be killed.

## Bad configuration

```
# Classic catastrophic backtracking style pattern
location ~ (a+)+$ {
    return 200 "ok";
}
```

A long string of `a` characters followed by a mismatch can keep the engine backtracking for an extremely long time (many seconds per request).

## Better configuration

Anchor the pattern, simplify it, and avoid nested quantifiers:

```
# Anchored, linear-time for simple inputs
location ~ ^a+$ {
    return 200 "ok";
}
```

General approaches:

- use `^` and `$` anchors whenever possible,
- avoid nested `(...)+` or `(.*)+` constructs,
- keep alternations unambiguous,
- constrain input length before matching expensive patterns.
- use [recheck](https://makenowjust-labs.github.io/recheck/playground/) against any regex patterns used to check for vulnerable expressions.

## Additional notes

For more information about issue in nginx, see [this post](https://joshua.hu/nginx-directives-regex-redos-denial-of-service-vulnerable).
