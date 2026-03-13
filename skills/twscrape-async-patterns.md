---
name: twscrape-async-patterns
description: Async/await patterns for twscrape — using gather, async generators, aclosing for early breaks, and parallel scraping. Use when writing async code with twscrape or handling its async generators.
user-invocable: false
---

# twscrape Async Patterns

twscrape is async-only. All I/O uses `async/await`. Paginated methods return async generators.

## Collecting Results with `gather`

```python
from twscrape import API, gather

api = API()
tweets = await gather(api.search("query", limit=100))   # list[Tweet]
users = await gather(api.followers(user_id, limit=500))  # list[User]
```

`gather` consumes the entire async generator into a list. Good for small-to-medium result sets.

## Streaming with `async for`

```python
async for tweet in api.search("query", limit=1000):
    save_to_db(tweet)
```

Memory-efficient for large result sets — processes one item at a time.

## Early Break with `aclosing` (REQUIRED)

When breaking out of an async generator, you **must** use `aclosing` to properly release the account lock. Without it, the account stays locked until Python's garbage collector runs.

```python
from contextlib import aclosing

async with aclosing(api.search("query")) as gen:
    async for tweet in gen:
        if found_what_i_need(tweet):
            break  # account is properly released
```

This applies to ALL paginated methods (`search`, `followers`, `user_tweets`, etc.).

## Parallel Queries

twscrape safely handles concurrent access to the account pool. Multiple tasks share accounts correctly.

```python
import asyncio
from twscrape import API, gather

api = API()

# Multiple searches in parallel
results = await asyncio.gather(
    gather(api.search("python", limit=50)),
    gather(api.search("rust", limit=50)),
    gather(api.search("golang", limit=50)),
)
python_tweets, rust_tweets, go_tweets = results
```

### Parallel with per-task processing

```python
async def scrape_user_tweets(api, username):
    user = await api.user_by_login(username)
    if not user:
        return username, []
    tweets = await gather(api.user_tweets(user.id, limit=100))
    return username, tweets

results = await asyncio.gather(
    *[scrape_user_tweets(api, u) for u in usernames]
)
```

### Parallel with `aclosing` and early exit

```python
async def find_viral_tweet(api, query):
    async with aclosing(api.search(query)) as gen:
        async for tweet in gen:
            if tweet.likeCount > 10000:
                return tweet
    return None

viral = await asyncio.gather(
    find_viral_tweet(api, "AI news"),
    find_viral_tweet(api, "tech news"),
)
```

## Converting Models

All twscrape models support serialization:

```python
tweet = await api.tweet_details(123)
tweet.dict()  # Python dict
tweet.json()  # JSON string
```
