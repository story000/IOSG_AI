#!/usr/bin/env python3
"""Fetch project RSS feeds and maintain a 7-day rolling dataset."""

import argparse
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

FEEDS: Dict[str, str] = {
    "PANews": "https://rss.panewslab.com/zh/gtimg/rss",
    "TechFlow": "https://www.techflowpost.com/rss.aspx",
    "Wu Blockchain": "https://wublockchain123.substack.com/feed",
    "Cointelegraph中文": "https://cn.cointelegraph.com/rss",
    "ChainFeeds": "https://substack.chainfeeds.xyz/feed",
    "The BlockBeats": "https://api.theblockbeats.news/v1/open-api/home-xml",
    "Odaily": "https://www.odaily.news/v1/openapi/odailyrss",
    "Coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml",
}

HEADERS = {"User-Agent": "IOSG-RSS-Fetcher/3.0 (+https://iosg.vc)"}
REQUEST_TIMEOUT = 15
FILTER_DAYS = 7
DEFAULT_OUTPUT = Path("tools/rss_fetcher/latest_feeds.json")

ATOM_NS = "{http://www.w3.org/2005/Atom}"
DC_NS = "{http://purl.org/dc/elements/1.1/}"
CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}"


@dataclass
class RawEntry:
    title: str
    link: str
    guid: str
    summary: str
    content: str
    author: Optional[str]
    published: Optional[datetime]


@dataclass
class FeedFetchResult:
    name: str
    url: str
    entries: List[RawEntry]
    error: Optional[str] = None


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch the project's RSS feeds and update a rolling 7-day dataset."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum new items to keep per feed each round (0 means all).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Aggregated JSON output path (default: {DEFAULT_OUTPUT}).",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not write the output file (useful for dry runs).",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=0,
        help="Polling interval in seconds; when >0 the script loops until stopped.",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Prefer full HTML content when available (default falls back to summaries).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console summary output.",
    )
    return parser.parse_args(argv)


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None

    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            dt = parsedate_to_datetime(text)
        except (TypeError, ValueError):
            return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def extract_link(node) -> str:
    for tag in ("link", f"{ATOM_NS}link"):
        for elem in node.findall(tag):
            href = elem.get("href")
            if href and href.strip():
                return href.strip()
            if elem.text and elem.text.strip():
                return elem.text.strip()

    for tag in ("guid", f"{ATOM_NS}id"):
        guid = node.findtext(tag)
        if guid and guid.strip():
            return guid.strip()

    return ""


def extract_author(node) -> Optional[str]:
    for tag in ("author", f"{DC_NS}creator"):
        text = node.findtext(tag)
        if text and text.strip():
            return text.strip()

    atom_author = node.find(f"{ATOM_NS}author")
    if atom_author is not None:
        name = atom_author.findtext("name") or atom_author.findtext(f"{ATOM_NS}name")
        email = atom_author.findtext("email") or atom_author.findtext(f"{ATOM_NS}email")
        parts = [part.strip() for part in (name, email) if part]
        if parts:
            return " ".join(parts)

    return None


def extract_content(node, include_raw: bool) -> Tuple[str, str]:
    summary = node.findtext("description") or node.findtext(f"{ATOM_NS}summary") or ""
    summary = summary.strip()

    content_html = ""
    if include_raw:
        for tag in (f"{CONTENT_NS}encoded", f"{ATOM_NS}content"):
            elem = node.find(tag)
            if elem is not None and elem.text and elem.text.strip():
                content_html = elem.text.strip()
                break

    if not content_html:
        content_html = summary

    return summary, content_html


def parse_feed_xml(xml_bytes: bytes, include_raw: bool) -> List[RawEntry]:
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []

    def strip(tag: str) -> str:
        return tag.split("}", 1)[-1] if "}" in tag else tag

    if strip(root.tag) == "feed":
        nodes = root.findall(f".//{ATOM_NS}entry") or root.findall(".//entry")
    else:
        nodes = root.findall(".//item") or root.findall(f".//{ATOM_NS}entry")

    entries: List[RawEntry] = []

    for node in nodes:
        title = node.findtext("title") or node.findtext(f"{ATOM_NS}title") or ""
        title = title.strip()
        link = extract_link(node)
        guid = node.findtext("guid") or node.findtext(f"{ATOM_NS}id") or link
        guid = guid.strip() if guid else link
        summary, content_html = extract_content(node, include_raw)

        published_raw = (
            node.findtext("pubDate")
            or node.findtext(f"{ATOM_NS}published")
            or node.findtext(f"{ATOM_NS}updated")
            or node.findtext(f"{DC_NS}date")
        )
        published_dt = parse_datetime(published_raw)

        author = extract_author(node)

        entries.append(
            RawEntry(
                title=title,
                link=link,
                guid=guid,
                summary=summary,
                content=content_html,
                author=author,
                published=published_dt,
            )
        )

    return entries


def fetch_feed(name: str, url: str, include_raw: bool) -> FeedFetchResult:
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:  # noqa: BLE001
        return FeedFetchResult(name=name, url=url, entries=[], error=str(exc))

    entries = parse_feed_xml(response.content, include_raw)
    return FeedFetchResult(name=name, url=url, entries=entries)


HTML_TAG_RE = re.compile(r"<[^>]+>")


def clean_html(value: str) -> str:
    if not value:
        return ""
    no_tags = HTML_TAG_RE.sub(" ", value)
    text = unescape(no_tags)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def to_timestamp(dt: Optional[datetime]) -> int:
    if not dt:
        return 0
    return int(dt.timestamp())


def format_datetime(dt: Optional[datetime]) -> str:
    if not dt:
        return ""
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")


def to_article(feed_name: str, feed_url: str, entry: RawEntry) -> Dict[str, Any]:
    source_feed_id = f"feed/{feed_url}"
    published_ts = to_timestamp(entry.published)
    content_html = entry.content or entry.summary or ""

    article_id = entry.guid or entry.link
    if not article_id:
        fingerprint = entry.link or entry.title or source_feed_id
        article_id = hashlib.sha1(
            fingerprint.encode("utf-8", errors="ignore")
        ).hexdigest()

    return {
        "id": article_id,
        "title": entry.title,
        "author": entry.author or "",
        "published": published_ts,
        "published_formatted": format_datetime(entry.published),
        "updated": 0,
        "url": entry.link or "",
        "feed_title": feed_name,
        "feed_url": source_feed_id,
        "content": content_html,
        "content_text": clean_html(content_html),
        "categories": [],
        "source_feed": feed_name,
        "source_feed_id": source_feed_id,
    }


def deduplicate_articles(articles: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    unique: Dict[str, Dict[str, Any]] = {}
    for article in articles:
        unique[article["id"]] = article
    return list(unique.values())


def load_existing_articles(path: Optional[Path]) -> List[Dict[str, Any]]:
    if path is None or not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []

    if isinstance(data, dict) and isinstance(data.get("articles"), list):
        return data["articles"]
    return []


def merge_articles(existing: Iterable[Dict[str, Any]], new_articles: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    combined = list(existing) + list(new_articles)
    deduped = deduplicate_articles(combined)
    deduped.sort(key=lambda item: item.get("published", 0), reverse=True)
    return deduped


def build_payload(
    limit: int,
    include_raw: bool,
    existing_articles: List[Dict[str, Any]],
) -> Dict[str, Any]:
    existing_ids = {article.get("id") for article in existing_articles if article.get("id")}

    new_articles: List[Dict[str, Any]] = []
    fetch_counts: Dict[str, int] = {name: 0 for name in FEEDS}
    errors: List[FeedFetchResult] = []

    for name, url in FEEDS.items():
        result = fetch_feed(name, url, include_raw)
        if result.error:
            errors.append(result)
            continue

        entries = result.entries
        if limit > 0:
            entries = entries[:limit]

        fetch_counts[name] = len(entries)
        new_articles.extend(to_article(name, url, entry) for entry in entries)

    merged = merge_articles(existing_articles, new_articles)

    cutoff_dt = datetime.now(timezone.utc) - timedelta(days=FILTER_DAYS)
    cutoff_ts = int(cutoff_dt.timestamp())

    pre_filter_total = len(merged)
    filtered = [article for article in merged if article.get("published", 0) >= cutoff_ts]
    filtered.sort(key=lambda item: item.get("published", 0), reverse=True)

    total_articles = len(filtered)

    feed_stats: Dict[str, int] = {name: 0 for name in FEEDS}
    for article in filtered:
        feed_name = article.get("feed_title", "")
        if feed_name in feed_stats:
            feed_stats[feed_name] += 1

    new_unique_ids = {
        article.get("id")
        for article in new_articles
        if article.get("id") and article.get("id") not in existing_ids
    }
    new_unique_count = len(new_unique_ids)

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_articles": total_articles,
        "original_total": pre_filter_total,
        "filtered_out": pre_filter_total - total_articles,
        "filter_days": FILTER_DAYS,
        "filter_cutoff": cutoff_dt.isoformat(),
        "feeds_stats": feed_stats,
        "target_feeds": list(FEEDS.keys()),
    }

    return {
        "payload": {
            "metadata": metadata,
            "articles": filtered,
        },
        "errors": errors,
        "fetch_counts": fetch_counts,
        "new_articles": new_unique_count,
    }


def print_summary(result: Dict[str, Any], quiet: bool) -> None:
    if quiet:
        return

    payload = result["payload"]
    metadata = payload["metadata"]
    errors: List[FeedFetchResult] = result["errors"]
    fetch_counts: Dict[str, int] = result.get("fetch_counts", {})
    new_articles = result.get("new_articles", 0)

    print(
        "Generated at {generated_at}: {total} articles kept (added {new_articles}, filtered {filtered_out} of {original}).".format(
            generated_at=metadata["generated_at"],
            total=metadata["total_articles"],
            new_articles=new_articles,
            filtered_out=metadata["filtered_out"],
            original=metadata["original_total"],
        )
    )
    print(f"Per-feed totals within {metadata['filter_days']} days:")
    for feed in FEEDS:
        total_count = metadata["feeds_stats"].get(feed, 0)
        fetched = fetch_counts.get(feed, 0)
        print(f"  - {feed}: {total_count} kept / {fetched} fetched this round")

    if errors:
        print("Errors:")
        for error in errors:
            print(f"  ✗ {error.name}: {error.error}")


def save_output(path: Path, payload: Dict[str, Any], quiet: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    if not quiet:
        print(f"Saved aggregated data to {path}")


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    interval = max(args.interval, 0)
    include_raw = bool(args.raw)
    output_path: Optional[Path] = None if args.no_save else args.output

    existing_articles = load_existing_articles(args.output)

    while True:
        result = build_payload(
            limit=args.limit,
            include_raw=include_raw,
            existing_articles=existing_articles,
        )
        payload = result["payload"]

        if output_path is not None:
            save_output(output_path, payload, quiet=args.quiet)

        print_summary(result, quiet=args.quiet)

        existing_articles = payload["articles"]

        if interval <= 0:
            break

        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            if not args.quiet:
                print("\nStopping RSS fetch loop.")
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
