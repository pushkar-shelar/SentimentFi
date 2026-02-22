"""
SentimentFi — Live Data Fetcher
================================
Fetches real-time crypto news and social posts from two sources:
  A. Reddit  — public subreddit posts (no API key needed)
  B. News RSS — CoinDesk, Decrypt, CoinGape (no API key needed)

Both return a list of plain text strings ready for sentiment analysis.
"""

import re
import json
import email.utils
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# ── Reddit Config ──────────────────────────────────────────────────────
# Maps token → subreddit name
REDDIT_SUBREDDITS: dict[str, str] = {
    "MONAD": "monad",
    "BTC":   "Bitcoin",
    "ETH":   "ethereum",
}

# Reddit requires a User-Agent header or returns 429
REDDIT_USER_AGENT = "SentimentFi/1.0 (hackathon project)"

# Maximum age for token live feeds (1 week)
MAX_AGE_SECONDS = 7 * 24 * 3600
# Maximum age for custom query search (30 days — niche topics have older content)
MAX_QUERY_AGE_SECONDS = 30 * 24 * 3600


def _is_fresh(unix_ts: float, max_age: int = MAX_AGE_SECONDS) -> bool:
    """Return True if the Unix timestamp is within max_age seconds of now."""
    if not unix_ts:
        return False
    try:
        return (datetime.now(timezone.utc).timestamp() - float(unix_ts)) <= max_age
    except Exception:
        return False


def _time_ago(unix_ts: float) -> str:
    """Convert a Unix timestamp to a human-readable 'X ago' string."""
    if not unix_ts:
        return ""
    try:
        diff = int(datetime.now(timezone.utc).timestamp() - unix_ts)
        if diff < 60:        return f"{diff}s ago"
        if diff < 3600:      return f"{diff // 60}m ago"
        if diff < 86400:     return f"{diff // 3600}h ago"
        return f"{diff // 86400}d ago"
    except Exception:
        return ""


def _parse_pub_date(pub: str) -> str:
    """Parse an RSS pubDate string to a relative age like '2h ago'."""
    if not pub:
        return ""
    try:
        ts = email.utils.parsedate_to_datetime(pub).timestamp()
        return _time_ago(ts)
    except Exception:
        return pub[:16]

# ── News Config ──────────────────────────────────────────────────────────
# Keywords to filter headlines by token
TOKEN_KEYWORDS: dict[str, list[str]] = {
    "MONAD": ["monad"],
    "BTC":   ["bitcoin", "btc"],
    "ETH":   ["ethereum", "eth", "vitalik"],
}

NEWS_FEEDS = [
    {"name": "CoinDesk",  "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
    {"name": "Decrypt",   "url": "https://decrypt.co/feed"},
    {"name": "CoinGape",  "url": "https://coingape.com/feed/"},
]


# ── Reddit Fetcher ─────────────────────────────────────────────────────

def fetch_reddit(token: str, limit: int = 10, timeout: int = 8) -> list[dict]:
    """
    Fetch hot posts from the token's subreddit using Reddit's public JSON API.

    Args:
        token:   Token symbol (e.g., "MONAD", "BTC", "ETH").
        limit:   Max number of posts to fetch.
        timeout: HTTP timeout in seconds.

    Returns:
        List of dicts with keys: title, text, url, score, subreddit.
        Returns empty list on any error.
    """
    subreddit = REDDIT_SUBREDDITS.get(token)
    if not subreddit:
        return []

    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": REDDIT_USER_AGENT},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())

        posts = []
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            title = post.get("title", "").strip()
            selftext = post.get("selftext", "").strip()

            # Skip removed/deleted posts and stickied mod posts
            if post.get("stickied") or selftext in ("[removed]", "[deleted]"):
                selftext = ""

            # Skip posts older than 1 week
            if not _is_fresh(post.get("created_utc", 0)):
                continue

            # Use title + first 200 chars of body if available
            combined = title
            if selftext:
                combined += " — " + selftext[:200]

            if combined:
                posts.append({
                    "title":     title,
                    "text":      combined,
                    "url":       f"https://reddit.com{post.get('permalink', '')}",
                    "upvotes":   post.get("ups", 0),
                    "subreddit": subreddit,
                    "source":    "Reddit",
                    "age":       _time_ago(post.get("created_utc", 0)),
                })

        return posts

    except Exception as e:
        print(f"[DataFetcher] Reddit fetch failed for {token}: {e}")
        return []


# ── Crypto News RSS Fetcher ───────────────────────────────────────────

def fetch_news(token: str, limit: int = 10, timeout: int = 8) -> list[dict]:
    """
    Fetch crypto news from CoinDesk, Decrypt, and CoinGape RSS feeds,
    filtered by token keywords. No API key required.

    Args:
        token:   Token symbol (e.g., "MONAD", "BTC", "ETH").
        limit:   Max total headlines to return.
        timeout: HTTP timeout per feed in seconds.

    Returns:
        List of dicts with keys: title, text, url, source, age.
        Returns empty list on total failure.
    """
    keywords = TOKEN_KEYWORDS.get(token, [token.lower()])
    all_posts: list[dict] = []

    for feed in NEWS_FEEDS:
        if len(all_posts) >= limit:
            break
        try:
            req = urllib.request.Request(
                feed["url"],
                headers={"User-Agent": "Mozilla/5.0 (SentimentFi/1.0)"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw_xml = resp.read()

            root = ET.fromstring(raw_xml)
            channel = root.find("channel")
            items = (channel if channel is not None else root).findall("item")

            for item in items:
                if len(all_posts) >= limit:
                    break

                title = (item.findtext("title") or "").strip()
                link  = (item.findtext("link")  or "").strip()
                desc  = (item.findtext("description") or "").strip()
                pub   = (item.findtext("pubDate") or "").strip()

                # Filter by token keywords (case-insensitive)
                combined_raw = (title + " " + desc).lower()
                if not any(kw in combined_raw for kw in keywords):
                    continue

                # Strip HTML tags from description
                desc_clean = re.sub(r"<[^>]+>", "", desc)[:200].strip()
                text = title
                if desc_clean and desc_clean.lower() != title.lower():
                    text += " — " + desc_clean

                # Parse pubDate to relative age
                age = _parse_pub_date(pub)

                # Skip articles older than 1 week
                ts = 0
                try:
                    ts = email.utils.parsedate_to_datetime(pub).timestamp() if pub else 0
                except Exception:
                    pass
                if ts and not _is_fresh(ts):
                    continue

                all_posts.append({
                    "title":   title,
                    "text":    text,
                    "url":     link,
                    "source":  feed["name"],
                    "age":     age,
                    "upvotes": None,
                })

        except Exception as e:
            print(f"[DataFetcher] {feed['name']} fetch failed: {e}")
            continue

    return all_posts


# Keep old name as alias so nothing else breaks
fetch_cryptopanic = fetch_news


# ── Query-Based Fetcher ────────────────────────────────────────────

def fetch_by_query(query: str, reddit_limit: int = 8, news_limit: int = 8, timeout: int = 8) -> dict:
    """
    Search Reddit and crypto news RSS feeds using a free-text query.
    Used when the user types a custom search topic (e.g. 'monad testnet speed',
    'bitcoin ETF approval', 'ethereum merge upgrade').

    Reddit search API:  reddit.com/search.json?q=...
    News feeds:         keyword-filtered by words extracted from the query

    Returns same shape as fetch_all().
    """
    query = query.strip()
    if not query:
        return {"reddit": [], "cryptopanic": [], "combined_texts": [],
                "reddit_ok": False, "cryptopanic_ok": False, "total": 0}

    # ── Reddit search ────────────────────────────────────────────
    encoded = urllib.parse.quote_plus(query)
    reddit_url = f"https://www.reddit.com/search.json?q={encoded}&limit={reddit_limit}&sort=relevance&type=link"
    req = urllib.request.Request(reddit_url, headers={"User-Agent": REDDIT_USER_AGENT})
    reddit_posts: list[dict] = []
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            title    = post.get("title", "").strip()
            selftext = post.get("selftext", "").strip()
            if post.get("stickied") or selftext in ("[removed]", "[deleted]"):
                selftext = ""
            combined = title
            if selftext:
                combined += " — " + selftext[:200]
            if combined:
                # Skip posts older than 30 days for query-based search
                if not _is_fresh(post.get("created_utc", 0), MAX_QUERY_AGE_SECONDS):
                    continue
                reddit_posts.append({
                    "title":     title,
                    "text":      combined,
                    "url":       f"https://reddit.com{post.get('permalink', '')}",
                    "upvotes":   post.get("ups", 0),
                    "subreddit": post.get("subreddit", "r/search"),
                    "source":    "Reddit",
                    "age":       _time_ago(post.get("created_utc", 0)),
                })
    except Exception as e:
        print(f"[DataFetcher] Reddit query search failed: {e}")

    # ── News RSS filtered by query keywords ───────────────────────────
    # Extract meaningful words (3+ chars) from the query as filter keywords
    keywords = [w.lower() for w in re.findall(r"[a-zA-Z0-9]{3,}", query)]
    news_posts: list[dict] = []
    for feed in NEWS_FEEDS:
        if len(news_posts) >= news_limit:
            break
        try:
            req2 = urllib.request.Request(
                feed["url"],
                headers={"User-Agent": "Mozilla/5.0 (SentimentFi/1.0)"},
            )
            with urllib.request.urlopen(req2, timeout=timeout) as resp:
                raw_xml = resp.read()
            root    = ET.fromstring(raw_xml)
            channel = root.find("channel")
            items   = (channel if channel is not None else root).findall("item")
            for item in items:
                if len(news_posts) >= news_limit:
                    break
                title = (item.findtext("title") or "").strip()
                link  = (item.findtext("link")  or "").strip()
                desc  = (item.findtext("description") or "").strip()
                pub   = (item.findtext("pubDate") or "").strip()
                combined_raw = (title + " " + desc).lower()
                if keywords and not any(kw in combined_raw for kw in keywords):
                    continue
                desc_clean = re.sub(r"<[^>]+>", "", desc)[:200].strip()
                text = title
                if desc_clean and desc_clean.lower() != title.lower():
                    text += " — " + desc_clean
                # Skip articles older than 30 days for query search
                _ts = 0
                try:
                    _ts = email.utils.parsedate_to_datetime(pub).timestamp() if pub else 0
                except Exception:
                    pass
                if _ts and not _is_fresh(_ts, MAX_QUERY_AGE_SECONDS):
                    continue
                news_posts.append({
                    "title":   title,
                    "text":    text,
                    "url":     link,
                    "source":  feed["name"],
                    "age":     _parse_pub_date(pub),
                    "upvotes": None,
                })
        except Exception as e:
            print(f"[DataFetcher] {feed['name']} query fetch failed: {e}")

    # ── Subreddit fallback if Reddit search returned fewer than 4 posts ──
    # Detect token context from query and pull directly from its subreddit
    if len(reddit_posts) < 4:
        q_lower = query.lower()
        fallback_sub = None
        if any(w in q_lower for w in ["monad"]):
            fallback_sub = "monad"
        elif any(w in q_lower for w in ["bitcoin", "btc"]):
            fallback_sub = "Bitcoin"
        elif any(w in q_lower for w in ["ethereum", "eth", "vitalik"]):
            fallback_sub = "ethereum"
        if fallback_sub:
            try:
                fb_url = f"https://www.reddit.com/r/{fallback_sub}/hot.json?limit={reddit_limit}"
                fb_req = urllib.request.Request(fb_url, headers={"User-Agent": REDDIT_USER_AGENT})
                with urllib.request.urlopen(fb_req, timeout=timeout) as resp:
                    fb_data = json.loads(resp.read().decode())
                for child in fb_data.get("data", {}).get("children", []):
                    post = child.get("data", {})
                    title    = post.get("title", "").strip()
                    selftext = post.get("selftext", "").strip()
                    if post.get("stickied") or selftext in ("[removed]", "[deleted]"):
                        selftext = ""
                    combined = title + (" — " + selftext[:200] if selftext else "")
                    if combined and _is_fresh(post.get("created_utc", 0), MAX_QUERY_AGE_SECONDS):
                        reddit_posts.append({
                            "title":     title,
                            "text":      combined,
                            "url":       f"https://reddit.com{post.get('permalink', '')}",
                            "upvotes":   post.get("ups", 0),
                            "subreddit": fallback_sub,
                            "source":    "Reddit",
                            "age":       _time_ago(post.get("created_utc", 0)),
                        })
            except Exception as e:
                print(f"[DataFetcher] Subreddit fallback failed for {fallback_sub}: {e}")

    # Deduplicate by title (cross-posts appear multiple times in search)
    seen: set[str] = set()
    deduped_reddit: list[dict] = []
    for p in reddit_posts:
        key = p["title"].lower().strip()
        if key not in seen:
            seen.add(key)
            deduped_reddit.append(p)
    reddit_posts = deduped_reddit

    all_texts = [p["text"] for p in reddit_posts] + [p["text"] for p in news_posts]
    return {
        "reddit":         reddit_posts,
        "cryptopanic":    news_posts,
        "combined_texts": all_texts,
        "reddit_ok":      len(reddit_posts) > 0,
        "cryptopanic_ok": len(news_posts) > 0,
        "total":          len(all_texts),
    }


# ── Combined Fetcher ───────────────────────────────────────────────────

def fetch_all(token: str, reddit_limit: int = 8, news_limit: int = 10) -> dict:
    """
    Fetch from Reddit and crypto news RSS feeds (CoinDesk, Decrypt, CoinGape).

    Returns:
        dict with:
            reddit:         list of post dicts from Reddit
            cryptopanic:    list of news dicts (CoinDesk/Decrypt/CoinGape)
            combined_texts: flat list of text strings (for sentiment analysis)
            reddit_ok:      bool — whether Reddit fetch succeeded
            cryptopanic_ok: bool — whether news fetch succeeded
            total:          total signal count
    """
    reddit_posts = fetch_reddit(token, limit=reddit_limit)
    news_posts   = fetch_news(token, limit=news_limit)

    all_texts = (
        [p["text"] for p in reddit_posts] +
        [p["text"] for p in news_posts]
    )

    return {
        "reddit":           reddit_posts,
        "cryptopanic":      news_posts,   # keep key name for app.py compatibility
        "combined_texts":   all_texts,
        "reddit_ok":        len(reddit_posts) > 0,
        "cryptopanic_ok":   len(news_posts) > 0,
        "total":            len(all_texts),
    }
