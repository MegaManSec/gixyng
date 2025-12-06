# `try_files` without `open_file_cache`

The `try_files` directive is commonly used in nginx to check for file existence before falling back to other options. However, without `open_file_cache`, each request triggers multiple `stat()` system calls, which can significantly impact performance.

## Why this matters

For every request, `try_files` performs file existence checks using `stat()` system calls. Without caching:

- **High I/O overhead**: Each request causes multiple disk operations
- **Performance degradation**: Under load, this becomes a bottleneck
- **Increased latency**: Especially on network filesystems (NFS, distributed storage)

## Bad example

```nginx
location / {
    try_files $uri $uri/ /index.php$is_args$args;
}
```

Every request will perform 2-3 `stat()` calls without any caching.

## Good example

```nginx
# Enable file cache at http or server level
open_file_cache max=1000 inactive=20s;
open_file_cache_valid 30s;
open_file_cache_min_uses 2;
open_file_cache_errors on;

location / {
    try_files $uri $uri/ /index.php$is_args$args;
}
```

With `open_file_cache`, nginx caches file metadata, dramatically reducing `stat()` calls.

## Cache configuration options

| Directive | Description |
|-----------|-------------|
| `open_file_cache max=N inactive=T` | Cache up to N entries, expire after T inactive |
| `open_file_cache_valid T` | How often to validate cached entries |
| `open_file_cache_min_uses N` | Min accesses before caching |
| `open_file_cache_errors on` | Cache "file not found" errors too |

## When to disable this check

If you're serving dynamic content where files change frequently, or using a RAM disk, the performance impact may be negligible. You can disable this specific check in your gixy configuration.

## References

- [nginx documentation: open_file_cache](https://nginx.org/en/docs/http/ngx_http_core_module.html#open_file_cache)
- [try_files is evil too](https://www.getpagespeed.com/server-setup/nginx-try_files-is-evil-too)

--8<-- "en/snippets/nginx-extras-cta.md"

