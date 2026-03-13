"""Tests for _gql_items pagination loop: cursor handling, stuck-cursor detection, and deduplication."""

import asyncio
import json
from contextlib import aclosing
from unittest.mock import patch

import pytest
from pytest_httpx import HTTPXMock

from twscrape.accounts_pool import AccountsPool
from twscrape.api import API, GQL_URL, OP_SearchTimeline
from twscrape.utils import gather


@pytest.fixture
async def paginated_api(tmp_path, mock_xclidgenstore):
    """API fixture with multiple accounts and no cooldown, suitable for pagination tests."""
    db_path = tmp_path / "test_pagination.db"
    pool = AccountsPool(db_path)

    # Add enough accounts to survive mid-stream rotation
    for i in range(1, 6):
        await pool.add_account(f"user{i}", f"pass{i}", f"email{i}", f"email_pass{i}")
        await pool.set_active(f"user{i}", True)

    # Disable cooldown and request jitter for fast tests
    with (
        patch("twscrape.accounts_pool.ACCOUNT_COOLDOWN_SECONDS", 0),
        patch("twscrape.queue_client.REQUEST_DELAY_RANGE", (0.0, 0.0)),
    ):
        yield API(pool)


def make_search_response(tweet_ids: list[str], bottom_cursor: str | None = None):
    """Build a minimal but structurally valid SearchTimeline GQL response."""
    entries = []
    for tid in tweet_ids:
        entries.append(
            {
                "entryId": f"tweet-{tid}",
                "sortIndex": tid,
                "content": {
                    "entryType": "TimelineTimelineItem",
                    "__typename": "TimelineTimelineItem",
                    "itemContent": {
                        "itemType": "TimelineTweet",
                        "__typename": "TimelineTweet",
                        "tweet_results": {
                            "result": {
                                "__typename": "Tweet",
                                "rest_id": tid,
                                "core": {
                                    "user_results": {
                                        "result": {
                                            "__typename": "User",
                                            "id": f"VXNlcjox{tid}",
                                            "rest_id": f"900{tid}",
                                            "legacy": {
                                                "created_at": "Mon Jan 01 00:00:00 +0000 2024",
                                                "description": "test user",
                                                "entities": {"description": {"urls": []}},
                                                "favourites_count": 0,
                                                "followers_count": 10,
                                                "friends_count": 5,
                                                "listed_count": 0,
                                                "location": "",
                                                "media_count": 0,
                                                "name": f"User {tid}",
                                                "pinned_tweet_ids_str": [],
                                                "profile_image_url_https": "https://example.com/img.jpg",
                                                "screen_name": f"user{tid}",
                                                "statuses_count": 1,
                                                "verified": False,
                                            },
                                        }
                                    }
                                },
                                "legacy": {
                                    "bookmark_count": 0,
                                    "bookmarked": False,
                                    "created_at": "Mon Jan 01 00:00:00 +0000 2024",
                                    "conversation_id_str": tid,
                                    "entities": {"hashtags": [], "symbols": [], "urls": [], "user_mentions": []},
                                    "favorite_count": 0,
                                    "full_text": f"Test tweet {tid}",
                                    "id_str": tid,
                                    "lang": "en",
                                    "quote_count": 0,
                                    "reply_count": 0,
                                    "retweet_count": 0,
                                    "user_id_str": f"900{tid}",
                                    "source": '<a href="https://x.com">X</a>',
                                },
                            }
                        },
                    },
                },
            }
        )

    # Add cursor entries
    entries.append(
        {
            "entryId": "cursor-top-0",
            "sortIndex": "9999999999",
            "content": {
                "entryType": "TimelineTimelineCursor",
                "__typename": "TimelineTimelineCursor",
                "value": "top-cursor-value",
                "cursorType": "Top",
            },
        }
    )
    if bottom_cursor is not None:
        entries.append(
            {
                "entryId": "cursor-bottom-0",
                "sortIndex": "0",
                "content": {
                    "entryType": "TimelineTimelineCursor",
                    "__typename": "TimelineTimelineCursor",
                    "value": bottom_cursor,
                    "cursorType": "Bottom",
                },
            }
        )

    return {
        "data": {
            "search_by_raw_query": {
                "search_timeline": {
                    "timeline": {
                        "instructions": [
                            {
                                "type": "TimelineAddEntries",
                                "entries": entries,
                            }
                        ]
                    }
                }
            }
        }
    }


GQL_SEARCH_URL = f"{GQL_URL}/{OP_SearchTimeline}"


async def test_normal_pagination(httpx_mock: HTTPXMock, paginated_api: API):
    """Two pages of results, second page has no bottom cursor -> stops."""
    page1 = make_search_response(["100", "101", "102"], bottom_cursor="cursor-page2")
    page2 = make_search_response(["200", "201"], bottom_cursor=None)

    httpx_mock.add_response(json=page1, status_code=200)
    httpx_mock.add_response(json=page2, status_code=200)

    tweets = await gather(paginated_api.search("test", limit=-1))
    assert len(tweets) == 5
    ids = [t.id for t in tweets]
    assert ids == [100, 101, 102, 200, 201]


async def test_pagination_respects_limit(httpx_mock: HTTPXMock, paginated_api: API):
    """Limit should stop pagination even if more pages are available."""
    page1 = make_search_response(["100", "101", "102"], bottom_cursor="cursor-page2")

    httpx_mock.add_response(json=page1, status_code=200)

    tweets = await gather(paginated_api.search("test", limit=2))
    # limit=2 means we get at most the first page's worth, but parse_tweets yields all from the page
    # _is_end sets active=False when cnt >= limit, so only 1 page is fetched
    assert len(tweets) <= 3  # all from first page, but no second page fetched


async def test_empty_page_stops_pagination(httpx_mock: HTTPXMock, paginated_api: API):
    """A page with no tweet entries (only cursors) should stop pagination."""
    page1 = make_search_response(["100", "101"], bottom_cursor="cursor-page2")
    page2 = make_search_response([], bottom_cursor="cursor-page3")

    httpx_mock.add_response(json=page1, status_code=200)
    httpx_mock.add_response(json=page2, status_code=200)

    tweets = await gather(paginated_api.search("test", limit=-1))
    # Only page 1 tweets should be returned; page 2 had no results so _is_end returns rep=None
    assert len(tweets) == 2


async def test_stuck_cursor_stops_pagination(httpx_mock: HTTPXMock, paginated_api: API):
    """If the API returns the same cursor twice, we should stop instead of looping forever."""
    stuck_cursor = "same-cursor-every-time"
    # Mock exactly 2 pages — the fix should detect the stuck cursor after the 2nd page
    httpx_mock.add_response(
        json=make_search_response(["100", "101"], bottom_cursor=stuck_cursor),
        status_code=200,
    )
    httpx_mock.add_response(
        json=make_search_response(["100", "101"], bottom_cursor=stuck_cursor),
        status_code=200,
    )

    # Use asyncio.timeout to fail fast if the fix isn't working (would loop forever)
    async with asyncio.timeout(10):
        tweets = await gather(paginated_api.search("test", limit=-1))

    # Should detect the stuck cursor and stop, not loop forever
    ids = [t.id for t in tweets]
    assert 100 in ids
    assert 101 in ids
    # At most 2 pages worth of results (first page + one repeat before detection)
    assert len(tweets) <= 4


async def test_cross_page_deduplication(httpx_mock: HTTPXMock, paginated_api: API):
    """Overlapping entries across pages should be deduplicated."""
    page1 = make_search_response(["100", "101", "102"], bottom_cursor="cursor-page2")
    # Page 2 contains some IDs from page 1 (the bug from issue #295)
    page2 = make_search_response(["101", "102", "200"], bottom_cursor=None)

    httpx_mock.add_response(json=page1, status_code=200)
    httpx_mock.add_response(json=page2, status_code=200)

    tweets = await gather(paginated_api.search("test", limit=-1))
    ids = [t.id for t in tweets]
    # Should have no duplicates
    assert len(ids) == len(set(ids)), f"Duplicate tweet IDs found: {ids}"
    assert set(ids) == {100, 101, 102, 200}
