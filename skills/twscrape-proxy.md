---
name: twscrape-proxy
description: Proxy configuration for twscrape — per-account proxies, global proxies, priority order, and environment variables. Use when setting up proxies with twscrape.
user-invocable: false
---

# twscrape Proxy Configuration

## Priority Order (highest to lowest)

1. **`api.proxy`** property — overrides everything
2. **`TWS_PROXY`** environment variable — used if `api.proxy` is None
3. **Per-account proxy** — lowest priority, set during `add_account`

If you want per-account proxies to work, do NOT set a global proxy.

## Global Proxy

```python
# At initialization
api = API(proxy="http://user:pass@proxy.example.com:8080")

# Change at runtime
api.proxy = "socks5://user:pass@host:1080"

# Clear (falls back to env var or per-account)
api.proxy = None
```

## Environment Variable

```bash
TWS_PROXY=socks5://user:pass@127.0.0.1:1080 python script.py
```

## Per-Account Proxy

```python
await api.pool.add_account("user", "pass", "e@m.com", "ep",
    proxy="http://user:pass@proxy1.example.com:8080")

await api.pool.add_account("user2", "pass2", "e2@m.com", "ep2",
    proxy="socks5://user:pass@proxy2.example.com:1080")
```

## Supported Protocols

- `http://` and `https://`
- `socks5://`

## Common Pattern: Rotating Proxies per Account

```python
proxies = [
    "socks5://u:p@proxy1:1080",
    "socks5://u:p@proxy2:1080",
    "socks5://u:p@proxy3:1080",
]

for i, (user, pw, email, epw, cookies) in enumerate(account_list):
    await api.pool.add_account(user, pw, email, epw,
        cookies=cookies,
        proxy=proxies[i % len(proxies)])
```
