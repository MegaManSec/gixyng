# [invalid_regex] Using a nonexistent regex capture group

## What this check looks for

This plugin looks for places where a configuration references `$1`, `$2`, and so on, but the regex being used does not actually define that capture group.

Common places this shows up:

- `rewrite` replacement strings
- `set` inside an `if ($var ~ regex)` block
- patterns that use non-capturing groups like `(?:...)` or inline modifiers like `(?i)` and then expect numbered captures

## Why this is a problem

NGINX does not throw an error when you reference a missing group. It just substitutes an empty string. That turns into subtle bugs: broken redirects, unexpected paths, or conditions that never match the way you think they do.

## Bad configuration

### Case 1: modifier without a capture

```
rewrite "(?i)/path" /$1 break;
```

`(?i)` changes matching behavior, but it does not create a capture. There is no `$1`, so the replacement becomes `/`.

### Case 2: no captures at all

```
rewrite "^/path" /$1 redirect;
```

The pattern has zero capture groups, so `$1` is always empty.

## Better configuration

Either remove the unnecessary capture reference:

```
rewrite "^/path" /newpath redirect;
```

Or add a capture group if you actually need part of the input:

```
rewrite "^/path/(.*)$" /newpath/$1 redirect;
```

Same idea inside an `if`:

```
if ($uri ~ "^/path/(.*)$") {
    set $x $1;
}
```
