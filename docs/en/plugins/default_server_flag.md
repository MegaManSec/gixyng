# [default_server_flag] Missing default_server on shared listen socket

When two or more `server` blocks share the same `listen` address and port, one
of them should be explicitly marked as `default_server` (or `default`). This
eliminates ambiguity in which server handles requests that do not match a
`server_name`.

## How can I find it?

Gixy reports an issue if it detects multiple `server` blocks listening on the
same socket without any of them being marked as `default_server`.

Misconfiguration example:

```nginx
http {
    server {
        listen 80;
        server_name a.test;
    }

    server {
        listen 80;
        server_name b.test;
    }
}
```

## What can I do?

- Add the `default_server` flag to one `server` block among those sharing the
  same socket.

Correct configuration example:

```nginx
http {
    server {
        listen 80 default_server;
        server_name a.test;
    }

    server {
        listen 80;
        server_name b.test;
    }
}
```

## References

- NGINX `listen` directive: https://nginx.org/en/docs/http/ngx_http_core_module.html#listen

--8<-- "en/snippets/nginx-extras-cta.md"
