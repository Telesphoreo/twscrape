---
name: twscrape-models
description: twscrape data models — Tweet, User, Media, Trend fields and structure. Use when accessing tweet/user data, working with twscrape response objects, or serializing results.
user-invocable: false
---

# twscrape Data Models

All models inherit from `JSONTrait` and support `.dict()` (Python dict) and `.json()` (JSON string).

## Tweet

```python
@dataclass
class Tweet:
    id: int
    url: str
    date: datetime
    user: User
    lang: str
    rawContent: str
    replyCount: int
    retweetCount: int
    likeCount: int
    quoteCount: int
    bookmarkedCount: int
    conversationId: int
    hashtags: list[str]
    cashtags: list[str]
    mentionedUsers: list[UserRef]
    links: list[TextLink]
    media: Media
    viewCount: int | None
    retweetedTweet: Tweet | None
    quotedTweet: Tweet | None
    place: Place | None
    coordinates: Coordinates | None
    inReplyToTweetId: int | None
    inReplyToUser: UserRef | None
    source: str | None
    sourceUrl: str | None
    sourceLabel: str | None
    card: SummaryCard | PollCard | BroadcastCard | AudiospaceCard | None
    possibly_sensitive: bool | None
```

## User

```python
@dataclass
class User:
    id: int
    username: str
    displayname: str
    created: datetime
    followersCount: int
    friendsCount: int
    statusesCount: int
    favouritesCount: int
    listedCount: int
    mediaCount: int
    location: str
    profileImageUrl: str
    profileBannerUrl: str | None
    verified: bool | None
    blue: bool | None          # Twitter Blue / Premium
    blueType: str | None
    descriptionLinks: list[TextLink]
    pinnedIds: list[int]
```

## Media

```python
@dataclass
class Media:
    photos: list[MediaPhoto]    # .url
    videos: list[MediaVideo]    # .thumbnailUrl, .variants (list[MediaVideoVariant])
    animated: list[MediaAnimated]

@dataclass
class MediaVideoVariant:
    contentType: str
    url: str
    bitrate: int | None
```

## Supporting Types

- `UserRef`: `id`, `username`, `displayname` — lightweight user reference
- `TextLink`: `url`, `text`, `tcourl` — link in tweet/bio text
- `Place`: geographic info
- `Coordinates`: `longitude`, `latitude`
- `Trend`: `id`, `name`, `description`, `trendUrl`, `metadata`

## Card Types

- `SummaryCard`: `title`, `description`, `thumbnailUrl`, `url`
- `PollCard`: poll data
- `BroadcastCard`: live broadcast info
- `AudiospaceCard`: Twitter Spaces info

## Serialization

```python
tweet = await api.tweet_details(123)
tweet.dict()   # -> dict
tweet.json()   # -> str (JSON)

# Access nested data
tweet.user.username
tweet.media.videos[0].variants[0].url
tweet.quotedTweet.rawContent if tweet.quotedTweet else None
```

## Imports

```python
from twscrape.models import Tweet, User, Media, Trend
# or
from twscrape import *  # exports all models
```
