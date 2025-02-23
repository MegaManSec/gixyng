## [worker_rlimit_nofile_vs_connections] worker_rlimit_nofile must be at least twice `worker_connections`

A frequent configuration error is not raising the file descriptor (FD) limit to at least double the `worker_connections` value. To resolve this, configure the `worker_rlimit_nofile directive` in the main configuration context,
and ensure it is at least twice the value of `worker_connections`.

Why are additional FDs necessary?

* **Web Server Mode**:
    * FD is used for the client connection.
    * An additional FD is required for each file served, meaning at least two FDs per client—even more if the web page consists of multiple files.
* **Proxy Server Mode**:
    * One FD for the connection to the client.
    * One FD for the connection to the upstream server.
    * Potentially a third FD for temporarily storing the upstream server’s response.
* **Caching Server Mode**:
    * NGINX behaves like a web server when serving cached responses (using FDs similarly as above).
    * It acts like a proxy server when the cache is empty or the cached content has expired.

By ensuring the FD limit is at least twice the number of `worker_connections`, you accommodate the minimum FD requirements across these different modes of operation.
