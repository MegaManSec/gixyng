# [unanchored_regex]: Regular expression without anchors

In NGINX, when definining location with regular expression, it's recommended to anchor the regex at least to the beginning or end of the string. 
Otherwise, the regex will match any part of the string, which may lead to unexpected behavior or decreased performance.

For example, the following location block will match any URL that contains `/v1/`:

```nginx
location ~ /v1/ {
    # ...
}
```

This will match:

- `/v1/`
- `/v1/foo`
- `/foo/v1/bar`
- `/foo/v1/`

To match only URLs that start with `/v1/`, the regex should be anchored:

```nginx
location ~ ^/v1/ {
    # ...
}
```

This way, the regex will match only URLs that start with `/v1/`.

For matching file extensions, e.g., PHP files, the regex should be anchored at the end of the string.

Incorrect:

```nginx
location ~ \.php {
    # ...
}
```

It will match any URL that contains `.php`: `/foo.php`, `/foo.phpanything`, which is incorrect.

Correct:

```nginx
location ~ \.php$ {
    # ...
}
```

This way, the regex will match only URLs that end with `.php`.
