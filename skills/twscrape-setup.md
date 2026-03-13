---
name: twscrape-setup
description: How to install and initialize twscrape, a Twitter/X GraphQL scraping library. Use when setting up twscrape, adding it as a dependency, or creating the initial API instance.
user-invocable: false
---

# twscrape Setup & Installation

twscrape is an async Python library for scraping Twitter/X via their internal GraphQL API. It is NOT on PyPI. Requires Python 3.13+.

## Installation

```bash
# pip
pip install git+https://github.com/Telesphoreo/twscrape.git

# uv
uv add twscrape --git https://github.com/Telesphoreo/twscrape.git
```

## Initialization

```python
from twscrape import API

# Default — uses "accounts.db" in current directory
api = API()

# Custom database path
api = API("path/to/accounts.db")

# With global proxy
api = API(proxy="http://proxy:8080")

# Fail fast when no accounts available (instead of waiting indefinitely)
api = API(raise_when_no_account=True)

# Enable debug mode (dumps raw responses)
api = API(debug=True)
```

## Adding Accounts

Accounts are required. twscrape uses them to authenticate with X's GraphQL API.

### With cookies (preferred — immediately active, no login flow)
```python
cookies = "ct0=abc123; auth_token=xyz789"  # string, JSON, or base64 all work
await api.pool.add_account("username", "password", "email@ex.com", "email_pass", cookies=cookies)
```

### With login/password (requires login step)
```python
await api.pool.add_account("user", "pass", "email@ex.com", "email_pass")
await api.pool.login_all()  # handles email verification via IMAP automatically
```

### With MFA/2FA
```python
await api.pool.add_account("user", "pass", "email@ex.com", "email_pass", mfa_code="TOTP_SECRET")
```

### Bulk loading from file
```python
# File: username:password:email:email_password:cookies (one per line)
await api.pool.load_from_file("accounts.txt", "username:password:email:email_password:cookies")

# Skip columns with underscore
await api.pool.load_from_file("accounts.txt", "username:password:email:email_password:_:cookies")
```

### Per-account proxy
```python
await api.pool.add_account("user", "pass", "e@m.com", "ep",
    proxy="socks5://user:pass@proxy:1080")
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `TWS_PROXY` | None | Global proxy URL (http or socks5) |
| `TWS_WAIT_EMAIL_CODE` | `30` | Seconds to wait for email verification during login |
| `TWS_RAISE_WHEN_NO_ACCOUNT` | `false` | Raise `NoAccountError` instead of waiting |

## Minimal Working Example

```python
import asyncio
from twscrape import API, gather

async def main():
    api = API()
    await api.pool.add_account("user", "pass", "e@m.com", "ep",
        cookies="ct0=xxx; auth_token=yyy")

    tweets = await gather(api.search("python", limit=10))
    for t in tweets:
        print(t.id, t.rawContent)

asyncio.run(main())
```
