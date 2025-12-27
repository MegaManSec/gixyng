# [return_bypasses_allow_deny] return bypasses allow and deny

## What this check looks for

This plugin warns when `return` appears in the same context as `allow`/`deny`.

## Why this is a problem

`return` runs in the rewrite phase and ends request processing immediately. Access controls (`allow`/`deny`) are evaluated later. That means a `return` placed next to access rules can effectively ignore them, even if the config looks like it should be restricted.

In other words: the block reads like "allow X, deny everyone else", but the request never actually reaches the access phase: it simply returns unconditionally.

## Bad configuration

```
location /admin/ {
    allow 127.0.0.1;
    deny all;

    # This is evaluated before the access rules above
    return 200 "hi";
}
```

The response is served to everyone, including clients you intended to deny.

## Better configuration

If you need to return a response and still enforce allow/deny, move the return into a separate internal handler and put the access rules there:

```
location /admin/ {
    # Always internally redirect to a named location
    error_page 418 = @admin_handler;
    return 418;
}

location @admin_handler {
    allow 127.0.0.1;
    deny all;

    return 200 "hi";
}
```

Named locations cannot be requested directly by clients, so you can safely concentrate the access rules and the response logic there.

## Additional notes

If your goal is simply "block everyone but X", prefer expressing it as access control only (for example return 403/444 for everyone else) rather than combining allow/deny with unconditional returns in the same block.

For more information about this issue, see [this post](https://joshua.hu/nginx-return-allow-deny).
