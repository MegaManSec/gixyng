# Version Disclosure Plugin

## Overview

The version_disclosure plugin detects nginx configurations that may expose version information to attackers. This information can be used to identify known vulnerabilities specific to the running nginx version.

## What it detects

### 1. Explicit Dangerous Values (Original functionality)
The plugin detects when `server_tokens` is explicitly set to dangerous values:
- `server_tokens on;` - Exposes full nginx version and OS
- `server_tokens build;` - Exposes nginx version with build information

### 2. Missing server_tokens Directive (New in Full Config Mode)
When gixy detects a full nginx configuration (contains `http` block), the plugin also checks for **missing** `server_tokens` directives, since nginx defaults to `server_tokens on;` when not specified.

## Full Config Mode

The plugin automatically enters "full config mode" when:
- The configuration contains an `http` block
- This indicates gixy is analyzing a complete nginx configuration, not just a snippet

In full config mode, the plugin performs comprehensive analysis:

### Analysis Hierarchy
1. **HTTP Level**: Checks if `server_tokens off;` is set at the http block level
2. **Server Level**: For each server block, checks for missing or misconfigured `server_tokens`
3. **Location Level**: Only checked if server level is properly configured

### Inheritance Logic
The plugin understands nginx's directive inheritance:
- If `server_tokens off;` is set at http level → no issues reported
- If `server_tokens off;` is set at server level → no issues for that server
- Missing directives inherit the parent's value (or nginx's default of `on`)

## Examples

### ❌ Bad: Missing server_tokens (Full Config Mode)
```nginx
http {
    server {
        listen 80;
        server_name example.com;
        # Missing server_tokens - defaults to 'on'
        location / {
            return 200 "Hello";
        }
    }
}
```
**Issue**: `Missing server_tokens directive - defaults to 'on' which promotes information disclosure`

### ❌ Bad: Explicit dangerous value
```nginx
http {
    server {
        listen 80;
        server_name example.com;
        server_tokens on;  # Explicit dangerous value
    }
}
```
**Issue**: `Using server_tokens value which promotes information disclosure`

### ✅ Good: Set at HTTP level
```nginx
http {
    server_tokens off;  # Applies to all servers
    server {
        listen 80;
        server_name example.com;
    }
}
```

### ✅ Good: Set at Server level
```nginx
http {
    server {
        listen 80;
        server_name example.com;
        server_tokens off;  # Safe value
    }
}
```

### ✅ Good: Partial config (no full analysis)
```nginx
# This is a partial config - no http block
server {
    listen 80;
    # Missing server_tokens won't trigger in partial config mode
}
```

## Configuration Contexts

The `server_tokens` directive can be used in:
- `http` - Applies to all servers
- `server` - Applies to specific server and its locations  
- `location` - Applies to specific location

## Plugin Configuration

The plugin supports both modes automatically:
- **Partial Config Mode**: Only reports explicit dangerous values
- **Full Config Mode**: Reports both explicit dangerous values AND missing directives

No additional configuration is required - the mode is detected automatically.

## Why This Matters

By default, nginx includes version information in:
- HTTP response headers (`Server: nginx/1.18.0`)
- Error pages
- Other diagnostic output

This information helps attackers:
1. Identify the exact nginx version
2. Look up known vulnerabilities for that version
3. Craft targeted attacks

## Best Practices

1. **Always set `server_tokens off;`** at the http level for global protection
2. **Or set it individually** in each server block if you need granular control
3. **Never use `server_tokens build;`** as it exposes even more information
4. **Test your configuration** to ensure version information is not leaked
