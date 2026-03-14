---
name: twscrape-best-practices
description: Critical best practices and anti-patterns when writing code that uses twscrape. Use whenever generating or reviewing code that imports or uses twscrape to avoid common mistakes.
user-invocable: false
---

# twscrape Best Practices

## Core Principle: Let twscrape Handle It

twscrape has built-in systems for rate limiting, account rotation, request pacing, and deduplication. **Never reimplement these.** Adding your own logic on top will conflict with twscrape's internals and make things worse.

### What twscrape manages automatically:
- **Rate limits**: Monitors API headers, rotates accounts at 80% usage before hitting the wall
- **Account rotation**: LRU selection, rotates every 1-3 pages during pagination, 5-second cooldowns
- **Request pacing**: 1-3 second random jitter between requests (human-like timing)
- **Deduplication**: Multi-level dedup — entry_ids ordering filters out embedded/quoted tweets from primary results, plus seen-ID sets prevent duplicates
- **Stuck pagination**: Detects repeated cursors and stops automatically
- **Anti-bot headers**: Generates realistic `x-client-transaction-id`, rotates user agents
- **Ban detection**: Identifies bans, marks accounts inactive, switches to healthy ones

## Anti-Patterns

### DO NOT add sleep/delays
```python
# BAD — twscrape already paces 1-3s between requests
async for tweet in api.search("query"):
    await asyncio.sleep(2)
    process(tweet)

# GOOD
async for tweet in api.search("query"):
    process(tweet)
```

### DO NOT implement your own rotation
```python
# BAD — fighting twscrape's rotation
for acc_db in ["acc1.db", "acc2.db", "acc3.db"]:
    api = API(acc_db)
    results.extend(await gather(api.search("query", limit=10)))

# GOOD — one pool, all accounts, twscrape rotates
api = API()
for acc in accounts:
    await api.pool.add_account(acc, ...)
results = await gather(api.search("query", limit=30))
```

### DO NOT deduplicate within a single query
```python
# UNNECESSARY — twscrape already deduplicates
seen = set()
async for tweet in api.search("query"):
    if tweet.id not in seen:
        seen.add(tweet.id)
        process(tweet)

# GOOD
async for tweet in api.search("query"):
    process(tweet)

# EXCEPTION: dedup IS needed when merging DIFFERENT queries
all_tweets = {}
for q in ["python", "asyncio"]:
    async for tweet in api.search(q, limit=100):
        all_tweets[tweet.id] = tweet
```

### DO NOT create multiple API instances for parallelism
```python
# BAD — separate pools, no coordination
apis = [API(f"db{i}.db") for i in range(5)]

# GOOD — one pool, concurrent tasks share accounts
api = API()
results = await asyncio.gather(
    gather(api.search("q1", limit=50)),
    gather(api.search("q2", limit=50)),
)
```

### DO NOT use unlimited queries carelessly
```python
# DANGEROUS — limit=-1 is default, can run for hours
tweets = await gather(api.search("popular topic"))

# GOOD — set explicit limits
tweets = await gather(api.search("popular topic", limit=500))
```

### DO NOT forget `aclosing` with `break`
```python
# BAD — account lock leaks until garbage collection
async for tweet in api.search("query"):
    if done(tweet):
        break

# GOOD — proper cleanup
from contextlib import aclosing
async with aclosing(api.search("query")) as gen:
    async for tweet in gen:
        if done(tweet):
            break
```

### DO NOT catch and suppress twscrape errors silently
```python
# BAD — hides real problems
try:
    tweets = await gather(api.search("query", limit=100))
except Exception:
    tweets = []

# GOOD — handle specific exceptions
from twscrape import NoAccountError
try:
    tweets = await gather(api.search("query", limit=100))
except NoAccountError:
    logger.error("All accounts exhausted or rate-limited")
    raise
```

## Result Ordering & Quoted Tweets

Results are returned in timeline order using entry IDs from the API response. Quoted and retweeted tweets are **not** yielded as separate primary results — they're only accessible via the parent tweet's `.quotedTweet` and `.retweetedTweet` fields:

```python
async for tweet in api.search("query", limit=50):
    # This is a primary search result
    print(tweet.rawContent)

    # Access the quoted tweet if present
    if tweet.quotedTweet:
        print(f"  Quoting: {tweet.quotedTweet.rawContent}")
```

## Performance Tips

- **More accounts = higher throughput.** twscrape distributes load across all active accounts. There's no upper limit.
- **Use `gather` for small-to-medium result sets** and `async for` for large/streaming workloads.
- **Parallel queries are safe.** `asyncio.gather` with multiple API calls works correctly — twscrape coordinates account access.
- **Prefer cookies over login/password** for account setup. Cookie accounts are immediately active with no login flow.
