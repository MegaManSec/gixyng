# [invalid_regex] Using a nonexistent regex capture group

When using regular expressions with capturing groups in NGINX directives like `rewrite` or within `if` conditions, you can reference these captured groups using `$1`, `$2`, etc. in replacement strings or subsequent directives. However, if you reference a capture group that doesn't exist in the regex pattern, NGINX will treat it as an empty string, which can lead to unexpected behavior.

## How can I find it?

You should check:
- `rewrite` directives where the replacement string references capture groups (e.g., `$1`, `$2`) that don't exist in the regex pattern
- `set` directives inside `if` blocks that reference capture groups from the `if` condition's regex pattern
- Non-capturing groups like `(?:...)` or inline modifiers like `(?i)` which don't create numbered capture groups

## Examples

### Example 1: Non-capturing inline modifier

**Problematic configuration:**
```nginx
server {
    location / {
        # (?i) is a case-insensitive flag, NOT a capturing group
        rewrite "(?i)/" $1 break;
    }
}
```

**Issue:** The pattern `(?i)/` uses `(?i)` to enable case-insensitive matching, but it doesn't create a capturing group. The `$1` reference will be empty.

**Fix:**
```nginx
server {
    location / {
        # Add parentheses to create a capturing group
        rewrite "(?i)/(.*)" /$1 break;
    }
}
```

### Example 2: Missing capture groups

**Problematic configuration:**
```nginx
server {
    location / {
        rewrite "^/path" $1 redirect;
    }
}
```

**Issue:** The pattern `^/path` has no capturing groups, so `$1` will be empty.

**Fix:**
```nginx
server {
    location / {
        # Either remove the unnecessary $1 reference
        rewrite "^/path" /newpath redirect;
        # Or add a capturing group if needed
        rewrite "^/path/(.*)$" /newpath/$1 redirect;
    }
}
```

### Example 3: Referencing wrong group number

**Problematic configuration:**
```nginx
server {
    location / {
        # Pattern has only 1 capturing group, but references $2
        rewrite "^/(.*)$" /$1/$2 break;
    }
}
```

**Issue:** The pattern only has one capturing group `(.*)`, but the replacement references both `$1` and `$2`. The `$2` will be empty.

**Fix:**
```nginx
server {
    location / {
        # Add a second capturing group if needed
        rewrite "^/([^/]+)/(.*)$" /$2/$1 break;
        # Or remove the invalid reference
        rewrite "^/(.*)$" /prefix/$1 break;
    }
}
```

### Example 4: Set in if block

**Problematic configuration:**
```nginx
server {
    location / {
        if ($uri ~ "^/path") {
            set $x $1;  # $1 doesn't exist
        }
    }
}
```

**Issue:** The regex pattern in the `if` condition has no capturing groups, so `$1` is undefined.

**Fix:**
```nginx
server {
    location / {
        if ($uri ~ "^/path/(.*)$") {
            set $x $1;  # Now $1 contains the captured value
        }
    }
}
```

## What can I do?

1. **Add capturing groups to your regex pattern** if you need to reference parts of the matched string
2. **Remove unnecessary capture group references** if you don't actually need them
3. **Use the correct group numbers** - remember that group numbering starts at 1, and `$0` is not available in NGINX
4. **Remember that non-capturing groups don't create references** - patterns like `(?:...)`, `(?i)`, `(?=...)` don't create numbered groups
5. **Test your regex patterns** to ensure they capture what you expect

--8<-- "en/snippets/nginx-extras-cta.md"
