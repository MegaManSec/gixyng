# Version Disclosure Plugin
## Overview
The `version_disclosure` plugin checks Nginx configurations for settings that expose the Nginx version. This information can be used by attackers to identify specific, known vulnerabilities.

## Detection Logic
The plugin detects two types of issues:

### 1. Explicit Dangerous Values
Reports configurations where `server_tokens` is explicitly set to expose information:
* `server_tokens on;` - Exposes full version and OS.
* `server_tokens build;` - Exposes version and build info.

### 2. Missing `server_tokens` (Full Config Mode)
If the configuration contains an `http` block ("Full Config Mode"), the plugin also reports missing `server_tokens` directives. The Nginx default is `server_tokens on;` when the directive is absent.

## Full Config Mode
This mode is active when an `http` block is present. The plugin checks the configuration hierarchy:

1.  **HTTP Level**: Checks for `server_tokens off;` (global protection).
2.  **Server Level**: Checks each server block for missing or unsafe settings, respecting inheritance.

If `server_tokens off;` is not present at the `http` level, any missing directive in a `server` block is flagged as dangerous because it inherits the default `on` value.

## Why it Matters
Nginx leaks its version in HTTP headers and error pages by default. This enables attackers to quickly:
1.  Identify the exact Nginx version.
2.  Find known exploits for that version.
3.  Execute targeted attacks.

## Best Practices
1.  **Set `server_tokens off;`** in the `http` block for global security.
2.  **Never use `server_tokens on;` or `server_tokens build;`**.
3.  **Verify** the `Server` header is suppressed in live responses.
