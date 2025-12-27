# [unanchored_regex] Regular expression without anchors

## What this check looks for

This plugin flags regular expressions (commonly in `location ~` blocks) that are not anchored to the start and/or end of the string.

## Why this is a problem

Without anchors, the regex engine can match anywhere inside the input. That has two downsides:

- you may match URLs you did not intend to match,
- the engine has to work harder because it can try many starting positions.

## Bad configuration

```
# Matches any URL that contains /v1/ anywhere
location ~ /v1/ {
    # ...
}
```

Another common example:

```
# Matches /foo.php and also /foo.phpanything
location ~ \.php {
    # ...
}
```

## Better configuration

Anchor patterns to reflect what you really mean:

```
location ~ ^/v1/ {
    # ...
}

location ~ \.php$ {
    # ...
}
```
