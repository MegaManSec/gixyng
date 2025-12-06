# Low `keepalive_requests` value

The `keepalive_requests` directive sets the maximum number of requests that can be served through one keep-alive connection. After the maximum number of requests are made, the connection is closed.

## Why this matters

Prior to nginx 1.19.10, the default value was 100. This was raised to 1000 because low values can cause problems:

- **HTTP/2 multiplexing**: Modern browsers open fewer connections but send many requests over each one. A low `keepalive_requests` value forces frequent connection resets.
- **Client disconnections**: Some clients may experience failed requests when connections are closed prematurely.
- **Performance overhead**: Establishing new connections has overhead (TCP handshake, TLS negotiation). Keeping connections alive longer improves performance.

## Bad example

```nginx
keepalive_requests 100;
```

This forces connection closure after only 100 requests, which can cause issues with HTTP/2 clients.

## Good example

```nginx
keepalive_requests 1000;
```

Or simply omit the directive to use nginx's default (1000 since nginx 1.19.10).

## References

- [nginx documentation: keepalive_requests](https://nginx.org/en/docs/http/ngx_http_core_module.html#keepalive_requests)
- [nginx ticket #2155: Increase default keepalive_requests](https://trac.nginx.org/nginx/ticket/2155)
- [Debugging failures of HTTP/2 in Burp, mitmproxy, and browsers](https://joshua.hu/http2-burp-proxy-mitmproxy-nginx-failing-load-resources-chromium#nginx-keepalive_requests)
--8<-- "en/snippets/nginx-extras-cta.md"

