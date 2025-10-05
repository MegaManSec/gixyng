## return_bypasses_allow_deny

Warns when `return` is used in the same scope as `allow`/`deny`, because `return` takes precedence and can bypass access controls.

- Severity: Medium
- Directives: `allow`, `deny`

### Why it matters

In nginx, `return` short-circuits request processing and is evaluated before `allow`/`deny` in the same context, potentially exposing content unintentionally.

### Insecure

```nginx
location / {
  allow 127.0.0.1;
  deny all;
  return 200 "hi";
}
```

### Safer alternatives

- Use a named location and `try_files` to direct traffic conditionally.
- Move access control to a higher or matching context where it applies before `return`.

--8<-- "en/snippets/nginx-extras-cta.md"
