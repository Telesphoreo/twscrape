---
name: twscrape-accounts
description: twscrape account pool management — monitoring health, re-login, recovery, stats, and handling account exhaustion. Use when managing twscrape accounts, checking status, or troubleshooting account issues.
user-invocable: false
---

# twscrape Account Management

The `AccountsPool` manages authentication, rotation, locking, and health for all accounts. Access it via `api.pool`.

## Monitoring

### Account status overview
```python
for info in await api.pool.accounts_info():
    print(info)
# Output per account:
#   username, logged_in (bool), active (bool), last_used (datetime),
#   total_req (int), error_msg (str | None)
```

### Pool statistics
```python
stats = await api.pool.stats()
# {"total": 10, "active": 8, "inactive": 2}
```

### Get specific account
```python
account = await api.pool.get("username")
```

## Account States

- **Active**: Logged in, has valid session, available for requests
- **Inactive**: Login failed, banned, or session expired. Has `error_msg` explaining why.
- **Locked** (per-queue): Temporarily rate-limited for a specific endpoint. Auto-unlocks when the rate limit window resets.

## Recovery

### Re-login specific accounts
```python
await api.pool.relogin("user1", "user2")
```

### Re-login all failed accounts
```python
await api.pool.relogin_failed()
```

### Manual login with email code prompt
```python
await api.pool.login_all(manual=True)  # prompts for email verification codes
```

### Reset all rate limit locks
```python
await api.pool.reset_locks()  # use sparingly — for troubleshooting only
```

### Activate/deactivate accounts
```python
await api.pool.set_active("username", True)
await api.pool.set_active("username", False)
```

## Cleanup

```python
# Delete specific accounts
await api.pool.delete_accounts("user1", "user2")

# Delete accounts that never logged in successfully
await api.pool.delete_inactive()
```

## Handling Account Exhaustion

By default, twscrape waits indefinitely when all accounts are rate-limited. To fail fast:

```python
from twscrape import API, NoAccountError

# Option 1: constructor
api = API(raise_when_no_account=True)

# Option 2: environment variable
# TWS_RAISE_WHEN_NO_ACCOUNT=true

try:
    tweets = await gather(api.search("query", limit=100))
except NoAccountError:
    print("All accounts exhausted — wait or add more accounts")
```

## How Rotation Works (for understanding, not reimplementation)

1. Picks the least-recently-used active account without a lock on the requested endpoint
2. Enforces a 5-second minimum cooldown between uses of the same account
3. During pagination, randomly rotates to a different account every 1-3 pages
4. When an account hits 80% of its rate limit budget, proactively rotates before hitting the wall
5. Banned/expired accounts are automatically marked inactive

**You do not need to manage any of this.** Just add accounts and call API methods.
