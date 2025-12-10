# [regex_redos] Regular expressions may cause ReDoS

Some regular expressions can exhibit catastrophic backtracking. Attackers can send carefully crafted inputs that make the regex engine consume excessive CPU, resulting in a denial of service.

## Insecure example

```nginx
# Catastrophic backtracking for long "a" runs
location ~ ^/(a|aa|aaa|aaaa)+$ {
    return 200 "ok";
}
```

A path like `/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaab` can tie up CPU for a long time.

## Safer alternatives

- Anchor and simplify patterns; avoid nested alternations and ambiguous repetitions
- Prefer explicit, linear-time constructs where possible
- Constrain input length before applying expensive regexes

```nginx
# Safer: anchored and simplified
location ~ ^/a+$ {
    return 200 "ok";
}
```

## Why it matters

Ambiguous regexes in locations and other directives can be exploited remotely. Keep patterns simple and well-anchored, and avoid constructs known to trigger backtracking explosions.

--8<-- "en/snippets/nginx-extras-cta.md"
