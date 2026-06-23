#!/usr/bin/env python3
"""
Scrape Reddit posts/comments for AgentTraceTakeMeter data collection.

Two modes:
  json  - No API credentials. Fetches public .json endpoints for seed URLs only.
  praw  - Uses Reddit API (read-only). Supports seed URLs + subreddit search.

Outputs:
  data/raw_discourse_items.csv  - flat items for labeling
  data/raw_reddit_tree.csv      - tree fields (comment_id, post_id, parent_id, ...)

If scraping quality is poor (rate limits, thin threads, too much noise), fall back
to the manual labeling web app described in docs/.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEED_FILE = ROOT / "sources" / "seed_urls.txt"
DEFAULT_SEARCH_FILE = ROOT / "sources" / "search_queries.txt"
DEFAULT_OUT_DIR = ROOT / "data"

DEFAULT_USER_AGENT = "web:takemeter:v0.1 (by /u/YOUR_USERNAME)"
MIN_TEXT_LEN = 20
REMOVED_MARKERS = {"[removed]", "[deleted]"}


def resolve_user_agent() -> str:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    return os.getenv("REDDIT_USER_AGENT", DEFAULT_USER_AGENT)


@dataclass
class RedditItem:
    item_id: str
    platform: str
    community: str
    parent_id: str
    created_utc: str
    score: int
    text: str
    permalink: str
    source_url: str
    is_submission: bool
    post_id: str
    comment_id: str

    def tree_row(self) -> dict[str, str | int]:
        return {
            "comment_id": self.comment_id,
            "post_id": self.post_id,
            "parent_id": self.parent_id,
            "created_utc": self.created_utc,
            "subreddit": self.community.removeprefix("r/"),
            "score": self.score,
            "text": self.text,
            "permalink": self.permalink,
        }

    def discourse_row(self) -> dict[str, str | int | bool]:
        return asdict(self)


def load_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def normalize_reddit_url(url: str) -> str:
    url = url.strip()
    if url.startswith("https:www.reddit.com"):
        url = "https://" + url.removeprefix("https:")
    if not url.startswith("http"):
        url = "https://" + url.lstrip("/")
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    # Drop query params; json endpoint is appended later.
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_usable_text(text: str) -> bool:
    if not text or text in REMOVED_MARKERS:
        return False
    if len(text) < MIN_TEXT_LEN:
        return False
    return True


def submission_text(data: dict) -> str:
    title = clean_text(data.get("title"))
    body = clean_text(data.get("selftext"))
    if title and body:
        return f"{title}\n\n{body}"
    return title or body


def walk_json_comment_tree(
    comment_data: dict,
    post_id: str,
    subreddit: str,
    source_url: str,
) -> Iterator[RedditItem]:
    kind = comment_data.get("kind")
    data = comment_data.get("data", {})
    if kind != "t1":
        return

    comment_id = data.get("id", "")
    parent_id = data.get("parent_id", "")
    text = clean_text(data.get("body"))
    permalink = f"https://www.reddit.com{data.get('permalink', '')}"

    if is_usable_text(text):
        yield RedditItem(
            item_id=f"t1_{comment_id}",
            platform="reddit",
            community=f"r/{subreddit}",
            parent_id=parent_id,
            created_utc=str(data.get("created_utc", "")),
            score=int(data.get("score") or 0),
            text=text,
            permalink=permalink,
            source_url=source_url,
            is_submission=False,
            post_id=post_id,
            comment_id=comment_id,
        )

    replies = data.get("replies")
    if isinstance(replies, dict):
        for child in replies.get("data", {}).get("children", []):
            yield from walk_json_comment_tree(child, post_id, subreddit, source_url)


def parse_submission_listing(
    listing: dict,
    source_url: str,
) -> list[RedditItem]:
    items: list[RedditItem] = []
    children = listing.get("data", {}).get("children", [])
    if not children:
        return items

    submission = children[0]
    if submission.get("kind") != "t3":
        return items

    sub_data = submission.get("data", {})
    post_id = sub_data.get("id", "")
    subreddit = sub_data.get("subreddit", "")
    permalink = f"https://www.reddit.com{sub_data.get('permalink', '')}"
    text = submission_text(sub_data)

    if is_usable_text(text):
        items.append(
            RedditItem(
                item_id=f"t3_{post_id}",
                platform="reddit",
                community=f"r/{subreddit}",
                parent_id="",
                created_utc=str(sub_data.get("created_utc", "")),
                score=int(sub_data.get("score") or 0),
                text=text,
                permalink=permalink,
                source_url=source_url,
                is_submission=True,
                post_id=post_id,
                comment_id="",
            )
        )

    return items


def fetch_thread_json(
    url: str,
    session: requests.Session,
    sleep_s: float,
    user_agent: str,
) -> list[RedditItem]:
    normalized = normalize_reddit_url(url)
    json_url = normalized.rstrip("/") + ".json?limit=500&depth=10"
    headers = {"User-Agent": user_agent}

    time.sleep(sleep_s)
    response = session.get(json_url, headers=headers, timeout=30)
    if response.status_code == 429:
        raise RuntimeError(
            "Reddit rate-limited this request (HTTP 429). "
            "Wait a few minutes, increase --sleep, or switch to --mode praw."
        )
    if response.status_code == 403:
        raise RuntimeError(
            "Reddit blocked this request (HTTP 403). "
            "Public JSON scraping is unreliable — use --mode praw with .env credentials."
        )
    response.raise_for_status()

    payload = response.json()
    if not isinstance(payload, list) or len(payload) < 1:
        return []

    source_url = normalized
    items = parse_submission_listing(payload[0], source_url)

    if len(payload) > 1:
        post_id = ""
        subreddit = ""
        if items:
            post_id = items[0].post_id
            subreddit = items[0].community.removeprefix("r/")
        else:
            # Submission may be link-only; still harvest comments.
            sub_data = payload[0]["data"]["children"][0]["data"]
            post_id = sub_data.get("id", "")
            subreddit = sub_data.get("subreddit", "")

        for child in payload[1].get("data", {}).get("children", []):
            items.extend(walk_json_comment_tree(child, post_id, subreddit, source_url))

    return items


def scrape_json_mode(
    urls: Iterable[str],
    sleep_s: float,
    user_agent: str,
) -> list[RedditItem]:
    session = requests.Session()
    all_items: list[RedditItem] = []
    for i, url in enumerate(urls, start=1):
        print(f"[json {i}/{len(urls)}] {url}")
        try:
            items = fetch_thread_json(url, session, sleep_s, user_agent)
            print(f"  -> {len(items)} items")
            all_items.extend(items)
        except Exception as exc:  # noqa: BLE001 - surface per-URL failures for trial runs
            print(f"  !! failed: {exc}", file=sys.stderr)
    return all_items


def scrape_praw_urls(reddit, urls: Iterable[str], sleep_s: float) -> list[RedditItem]:
    items: list[RedditItem] = []
    for i, url in enumerate(urls, start=1):
        print(f"[praw url {i}] {url}")
        time.sleep(sleep_s)
        submission = reddit.submission(url=normalize_reddit_url(url))
        submission.comments.replace_more(limit=0)
        source_url = normalize_reddit_url(url)
        subreddit = submission.subreddit.display_name
        post_id = submission.id
        text = submission_text(
            {
                "title": submission.title,
                "selftext": submission.selftext,
            }
        )
        if is_usable_text(text):
            items.append(
                RedditItem(
                    item_id=f"t3_{post_id}",
                    platform="reddit",
                    community=f"r/{subreddit}",
                    parent_id="",
                    created_utc=str(int(submission.created_utc)),
                    score=int(submission.score or 0),
                    text=text,
                    permalink=f"https://www.reddit.com{submission.permalink}",
                    source_url=source_url,
                    is_submission=True,
                    post_id=post_id,
                    comment_id="",
                )
            )

        def walk_comment(comment) -> None:
            body = clean_text(comment.body)
            if is_usable_text(body):
                items.append(
                    RedditItem(
                        item_id=f"t1_{comment.id}",
                        platform="reddit",
                        community=f"r/{subreddit}",
                        parent_id=comment.parent_id,
                        created_utc=str(int(comment.created_utc)),
                        score=int(comment.score or 0),
                        text=body,
                        permalink=f"https://www.reddit.com{comment.permalink}",
                        source_url=source_url,
                        is_submission=False,
                        post_id=post_id,
                        comment_id=comment.id,
                    )
                )
            for reply in comment.replies:
                walk_comment(reply)

        for top_level in submission.comments:
            walk_comment(top_level)

        print(f"  -> {len(items)} cumulative items")
    return items


def parse_search_line(line: str) -> tuple[str, str, int]:
    parts = [p.strip() for p in line.split("|")]
    if len(parts) != 3:
        raise ValueError(f"Bad search line (expected subreddit|query|limit): {line}")
    subreddit, query, limit_s = parts
    return subreddit, query, int(limit_s)


def scrape_praw_search(reddit, search_file: Path, sleep_s: float) -> list[RedditItem]:
    items: list[RedditItem] = []
    lines = load_lines(search_file)
    for i, line in enumerate(lines, start=1):
        subreddit, query, limit = parse_search_line(line)
        print(f"[praw search {i}] r/{subreddit} q={query!r} limit={limit}")
        time.sleep(sleep_s)
        urls: list[str] = []
        for submission in reddit.subreddit(subreddit).search(query, limit=limit):
            urls.append(f"https://www.reddit.com{submission.permalink}")
        print(f"  -> {len(urls)} submission URLs")
        items.extend(scrape_praw_urls(reddit, urls, sleep_s))
    return items


def get_praw_client():
    try:
        import praw
    except ImportError as exc:
        raise SystemExit(
            "PRAW is not installed. Run: pip install -r requirements.txt"
        ) from exc

    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    client_id = os.getenv("REDDIT_CLIENT_ID", "")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
    user_agent = resolve_user_agent()

    missing = [
        name
        for name, value in [
            ("REDDIT_CLIENT_ID", client_id),
            ("REDDIT_CLIENT_SECRET", client_secret),
        ]
        if not value or "your_" in value
    ]
    if missing:
        raise SystemExit(
            "Missing Reddit API credentials for --mode praw.\n"
            "Copy .env.example to .env and fill in values from "
            "https://www.reddit.com/prefs/apps\n"
            "Or try --mode json first (no credentials)."
        )

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )


def dedupe_items(items: list[RedditItem]) -> list[RedditItem]:
    seen: set[str] = set()
    unique: list[RedditItem] = []
    for item in items:
        if item.item_id in seen:
            continue
        seen.add(item.item_id)
        unique.append(item)
    return unique


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def summarize(items: list[RedditItem]) -> None:
    submissions = sum(1 for i in items if i.is_submission)
    comments = len(items) - submissions
    by_sub = {}
    for item in items:
        by_sub[item.community] = by_sub.get(item.community, 0) + 1

    print("\n--- scrape summary ---")
    print(f"total items: {len(items)}")
    print(f"submissions: {submissions}")
    print(f"comments:    {comments}")
    print("by subreddit:")
    for community, count in sorted(by_sub.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {community}: {count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Reddit threads for TakeMeter.")
    parser.add_argument(
        "--mode",
        choices=["json", "praw"],
        default="json",
        help="json = no credentials (seed URLs only); praw = Reddit API",
    )
    parser.add_argument(
        "--seed-file",
        type=Path,
        default=DEFAULT_SEED_FILE,
        help="File with one Reddit thread URL per line",
    )
    parser.add_argument(
        "--search-file",
        type=Path,
        default=DEFAULT_SEARCH_FILE,
        help="subreddit|query|limit lines (praw mode only)",
    )
    parser.add_argument(
        "--search",
        action="store_true",
        help="Also run subreddit searches from --search-file (praw mode only)",
    )
    parser.add_argument(
        "--url",
        action="append",
        default=[],
        help="Extra thread URL (repeatable)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Output directory for CSV files",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.5,
        help="Seconds to sleep between Reddit requests",
    )
    parser.add_argument(
        "--max-urls",
        type=int,
        default=0,
        help="Limit number of seed URLs (0 = all). Useful for a quick trial.",
    )
    args = parser.parse_args()

    seed_urls = [normalize_reddit_url(u) for u in load_lines(args.seed_file)]
    seed_urls.extend(normalize_reddit_url(u) for u in args.url)
    if args.max_urls > 0:
        seed_urls = seed_urls[: args.max_urls]

    if not seed_urls and not args.search:
        raise SystemExit("No seed URLs found. Add URLs to sources/seed_urls.txt or pass --url.")

    items: list[RedditItem] = []

    user_agent = resolve_user_agent()

    if args.mode == "json":
        if args.search:
            print("Note: --search is ignored in json mode. Use --mode praw for searches.")
        print(
            "json mode uses public endpoints (no OAuth). "
            "If you get HTTP 403, switch to --mode praw.\n"
        )
        items = scrape_json_mode(seed_urls, args.sleep, user_agent)
    else:
        reddit = get_praw_client()
        if seed_urls:
            items.extend(scrape_praw_urls(reddit, seed_urls, args.sleep))
        if args.search:
            items.extend(scrape_praw_search(reddit, args.search_file, args.sleep))

    items = dedupe_items(items)
    if not items:
        print(
            "\nNo items collected. Try a different mode, fewer rate limits, or manual collection.",
            file=sys.stderr,
        )
        sys.exit(1)

    discourse_path = args.out_dir / "raw_discourse_items.csv"
    tree_path = args.out_dir / "raw_reddit_tree.csv"

    discourse_fields = list(RedditItem.__dataclass_fields__.keys())
    tree_fields = [
        "comment_id",
        "post_id",
        "parent_id",
        "created_utc",
        "subreddit",
        "score",
        "text",
        "permalink",
    ]

    write_csv(discourse_path, discourse_fields, (i.discourse_row() for i in items))
    write_csv(tree_path, tree_fields, (i.tree_row() for i in items))

    summarize(items)
    print(f"\nWrote {discourse_path}")
    print(f"Wrote {tree_path}")
    print(
        "\nNext: review raw_discourse_items.csv, label rows into labeled_dataset.csv, "
        "or import into the labeling web app if scraping is too noisy."
    )


if __name__ == "__main__":
    main()
