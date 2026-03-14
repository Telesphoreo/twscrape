---
name: twscrape-api
description: twscrape API method reference — all available methods for searching tweets, getting user info, fetching followers, timelines, trends, and bookmarks. Use when writing code that calls twscrape API methods.
user-invocable: false
---

# twscrape API Methods

All methods are on the `API` class. Paginated methods return async generators. Single-item methods return `Model | None`.

## Search

```python
api.search(q, limit=-1, kv=None)          # async gen -> Tweet
api.search_user(q, limit=-1, kv=None)     # async gen -> User
api.search_raw(q, limit=-1, kv=None)      # async gen -> httpx.Response
```

Control search tab via `kv`:
```python
await gather(api.search("query", limit=20))                          # Latest (default)
await gather(api.search("query", limit=20, kv={"product": "Top"}))   # Top
await gather(api.search("query", limit=20, kv={"product": "Media"})) # Media
```

## Users

```python
await api.user_by_login("username")          # User | None
await api.user_by_id(44196397)               # User | None
await api.user_about("username")             # AccountAbout | None (identity verification, username history, location)

api.followers(uid, limit=-1, kv=None)            # async gen -> User
api.verified_followers(uid, limit=-1, kv=None)   # async gen -> User
api.following(uid, limit=-1, kv=None)            # async gen -> User
api.subscriptions(uid, limit=-1, kv=None)        # async gen -> User
```

## Tweets

```python
await api.tweet_details(tweet_id)                # Tweet | None

api.tweet_replies(twid, limit=-1, kv=None)       # async gen -> Tweet (small pages ~5/req)
api.retweeters(twid, limit=-1, kv=None)          # async gen -> User
```

## User Timelines

```python
api.user_tweets(uid, limit=-1, kv=None)              # async gen -> Tweet (max ~3200)
api.user_tweets_and_replies(uid, limit=-1, kv=None)   # async gen -> Tweet (max ~3200)
api.user_media(uid, limit=-1, kv=None)                # async gen -> Tweet
```

## Lists

```python
api.list_timeline(list_id, limit=-1, kv=None)    # async gen -> Tweet
```

## Trends

```python
api.trends(trend_id, limit=-1, kv=None)          # async gen -> Trend
# trend_id options: "trending", "news", "sport", "entertainment"
```

## Bookmarks

```python
api.bookmarks(limit=-1, kv=None)                 # async gen -> Tweet (own bookmarks)
```

## Raw Variants

Every method has a `_raw` variant returning `httpx.Response`:
```python
api.search_raw(q, limit, kv)
api.user_by_id_raw(uid, kv)
api.user_by_login_raw(login, kv)
api.user_about_raw(username, kv)
api.tweet_details_raw(twid, kv)
api.followers_raw(uid, limit, kv)
# ... etc for all methods
```

## The `limit` Parameter

`limit` is a **desired minimum**, not exact. twscrape paginates until it has at least that many results. The actual count may differ because X's page sizes vary per endpoint. Set `limit=-1` for unlimited.

## The `kv` Parameter

`kv` overrides GraphQL variables sent to the API. Most users only need it for search tab control (`{"product": "Top"}`). The default variables are sensible for general use.
