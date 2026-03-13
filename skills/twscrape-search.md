---
name: twscrape-search
description: Twitter/X advanced search query syntax and operators for use with twscrape's search method. Use when building search queries, filtering tweets, or using X search operators.
user-invocable: false
---

# twscrape Search Query Syntax

twscrape passes search queries directly to X's search API. All of X's advanced search operators work.

## Basic Operators

```python
# Keywords (AND is implicit)
api.search("python asyncio")

# Exact phrase
api.search('"machine learning"')

# OR
api.search("python OR rust")

# Exclude
api.search("python -tutorial")

# Hashtag
api.search("#python")

# Cashtag
api.search("$AAPL")
```

## User Filters

```python
# From a specific user
api.search("from:elonmusk")

# Replies to a user
api.search("to:elonmusk")

# Mentioning a user
api.search("@elonmusk")
```

## Date Range

```python
# After a date
api.search("query since:2024-01-01")

# Before a date
api.search("query until:2024-06-01")

# Date range
api.search("query since:2024-01-01 until:2024-06-01")
```

## Engagement Filters

```python
# Minimum likes
api.search("query min_faves:1000")

# Minimum retweets
api.search("query min_retweets:100")

# Minimum replies
api.search("query min_replies:50")
```

## Content Filters

```python
# Only tweets with media (images/video)
api.search("query filter:media")

# Only tweets with images
api.search("query filter:images")

# Only tweets with video
api.search("query filter:videos")

# Only tweets with links
api.search("query filter:links")

# Exclude retweets
api.search("query -filter:retweets")

# Only retweets
api.search("query filter:retweets")

# Only replies
api.search("query filter:replies")
```

## Language Filter

```python
api.search("query lang:en")
api.search("query lang:es")
api.search("query lang:ja")
```

## Search Tabs

Control which tab results come from via the `kv` parameter:

```python
# Latest (default) — reverse chronological
await gather(api.search("query", limit=20))

# Top — algorithmically ranked
await gather(api.search("query", limit=20, kv={"product": "Top"}))

# Media — tweets with media
await gather(api.search("query", limit=20, kv={"product": "Media"}))
```

## Complex Query Examples

```python
# Tech news from specific accounts, with engagement, in English
api.search("from:user1 OR from:user2 min_retweets:10 lang:en since:2024-01-01")

# Viral AI content excluding retweets
api.search("artificial intelligence min_faves:5000 -filter:retweets lang:en")

# Recent media posts about a topic
api.search('"breaking news" filter:media since:2024-06-01")
```
