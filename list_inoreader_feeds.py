#!/usr/bin/env python3
"""List all Inoreader RSS subscriptions using stored OAuth tokens."""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv, find_dotenv

from inoreader_client import InoreaderClient


def load_environment() -> None:
    """Load environment variables from the nearest .env file if present."""
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv()


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch the authenticated Inoreader account's subscriptions and "
            "print their RSS stream IDs. Requires prior OAuth token setup."
        )
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Optional path to save the feed list as JSON."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the feed list as JSON on stdout."
    )
    return parser


def ensure_credentials() -> tuple[str, str]:
    client_id = os.getenv("INOREADER_CLIENT_ID")
    client_secret = os.getenv("INOREADER_CLIENT_SECRET")
    missing = [name for name, value in (
        ("INOREADER_CLIENT_ID", client_id),
        ("INOREADER_CLIENT_SECRET", client_secret),
    ) if not value]

    if missing:
        message = (
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Please set them or update your .env file."
        )
        raise RuntimeError(message)

    return client_id, client_secret


def fetch_subscriptions(client: InoreaderClient) -> list[dict]:
    response = client.get_subscription_list()
    subscriptions = response.get("subscriptions", [])
    feeds: list[dict] = []

    for subscription in subscriptions:
        stream_id = subscription.get("id", "").strip()
        if not stream_id:
            continue

        feed_url = stream_id[len("feed/"):] if stream_id.startswith("feed/") else None
        title = subscription.get("title") or feed_url or stream_id
        categories = [
            category.get("label")
            for category in subscription.get("categories", [])
            if isinstance(category, dict) and category.get("label")
        ]

        feeds.append({
            "title": title,
            "stream_id": stream_id,
            "feed_url": feed_url,
            "site_url": subscription.get("htmlUrl"),
            "categories": categories,
        })

    feeds.sort(key=lambda item: item["title"].lower())
    return feeds


def print_human_readable(feeds: list[dict]) -> None:
    if not feeds:
        print("No subscriptions found.")
        return

    for feed in feeds:
        print(f"- {feed['title']}")
        print(f"  stream: {feed['stream_id']}")
        if feed["feed_url"]:
            print(f"  rss: {feed['feed_url']}")
        if feed["site_url"]:
            print(f"  site: {feed['site_url']}")
        if feed["categories"]:
            joined = ", ".join(feed["categories"])
            print(f"  tags: {joined}")



def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    load_environment()

    try:
        client_id, client_secret = ensure_credentials()
    except RuntimeError as exc:
        parser.error(str(exc))

    client = InoreaderClient(client_id, client_secret)

    if not client.is_authenticated():
        parser.error(
            "Inoreader client is not authenticated. Run refresh_inoreader_token.py "
            "to complete OAuth before listing subscriptions."
        )

    try:
        feeds = fetch_subscriptions(client)
    except Exception as exc:  # noqa: BLE001 - surface API errors to the user
        parser.error(f"Failed to fetch subscriptions: {exc}")

    if args.output:
        args.output.write_text(json.dumps(feeds, indent=2, ensure_ascii=False))

    if args.json or args.output:
        print(json.dumps(feeds, indent=2, ensure_ascii=False))
    else:
        print_human_readable(feeds)

    return 0


if __name__ == "__main__":
    sys.exit(main())
