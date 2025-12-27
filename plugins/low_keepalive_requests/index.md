# [low_keepalive_requests] Low keepalive_requests value

## What this check looks for

This plugin warns when `keepalive_requests` is set to an unusually low number.

## Why this is a problem

`keepalive_requests` controls how many requests a client can send over a single keep-alive connection before NGINX closes it.

Low values create avoidable connection churn:

- With HTTP/2, browsers tend to use fewer connections and multiplex many requests. Closing a connection early forces unnecessary reconnects.
- Some clients will see failed or retried requests when the server closes a busy connection at the wrong time.
- Extra TLS handshakes and TCP setup cost CPU and latency.

In newer NGINX versions, the default is 1000. Older versions historically used 100.

## Bad configuration

```
keepalive_requests 100;
```

This is often too low for modern browsers and HTTP/2 workloads.

## Better configuration

```
keepalive_requests 1000;
```

If your NGINX already defaults to 1000, you can also omit the directive and keep the defaults.

## Additional notes

The "right" number depends on your traffic and timeouts, but the takeaway is simple: avoid values that force constant reconnecting. If you are tuning performance, look at `keepalive_timeout` and (for upstream keepalive) the `keepalive` directive in `upstream` blocks as well. For more information about when this error can show up, read [this post](https://joshua.hu/http2-burp-proxy-mitmproxy-nginx-failing-load-resources-chromium).
