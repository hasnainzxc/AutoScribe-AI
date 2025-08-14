"""Ingestion pipeline for fetching stories from Reddit.

This module defines functions to pull posts from a subreddit using the
PRAW (Python Reddit API Wrapper) library.  It abstracts the details
of authentication and retrieval so that other parts of the pipeline can
focus on processing the content.  You should set the environment
variables `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` and
`REDDIT_USER_AGENT` before running this module.  See the PRAW
documentation for details on how to obtain these credentials.

Typical usage::

    from content_pipeline.ingestion.reddit_ingest import fetch_subreddit_posts

    posts = fetch_subreddit_posts('aws', limit=10)
    for post in posts:
        print(post['title'])

"""

from __future__ import annotations

import os
from typing import List, Dict
from pathlib import Path
from dotenv import load_dotenv

try:
    import praw  # type: ignore
except ImportError as e:
    raise ImportError(
        "praw must be installed to use this module. Install it via `pip install praw`."
    ) from e

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def _create_reddit_instance() -> praw.Reddit:
    """Create a PRAW Reddit instance using environment variables.

    Returns:
        praw.Reddit: An authenticated Reddit instance.

    Raises:
        RuntimeError: If required environment variables are missing.
    """
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "content-pipeline-script")

    if not client_id or not client_secret:
        raise RuntimeError(
            "Missing Reddit credentials. Please set REDDIT_CLIENT_ID and "
            "REDDIT_CLIENT_SECRET environment variables."
        )

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )


def fetch_subreddit_posts(
    subreddit_name: str,
    limit: int = 10,
    sort: str = "top",
    time_filter: str = "day",
) -> List[Dict[str, str]]:
    """Fetch posts from a given subreddit.

    Args:
        subreddit_name (str): Name of the subreddit (without the leading 'r/').
        limit (int, optional): Maximum number of posts to fetch. Defaults to 10.
        sort (str, optional): One of 'hot', 'new', 'top' or 'rising'. Defaults to 'top'.
        time_filter (str, optional): If sort is 'top', one of 'all', 'year', 'month', 'week',
            'day', or 'hour'. Defaults to 'day'. Ignored for other sorts.

    Returns:
        List[Dict[str, str]]: A list of dictionaries with keys 'title', 'selftext', and 'url'.

    Note:
        This function intentionally strips away fields like the author's username or
        subreddit metadata to minimise collection of personal data.  You can extend
        the returned dictionary if additional metadata is needed.
    """
    reddit = _create_reddit_instance()
    subreddit = reddit.subreddit(subreddit_name)

    if sort == "hot":
        submissions = subreddit.hot(limit=limit)
    elif sort == "new":
        submissions = subreddit.new(limit=limit)
    elif sort == "rising":
        submissions = subreddit.rising(limit=limit)
    else:
        submissions = subreddit.top(limit=limit, time_filter=time_filter)

    posts: List[Dict[str, str]] = []
    for submission in submissions:
        # Skip stickied posts to avoid pinned announcements
        if submission.stickied:
            continue
        post = {
            "title": submission.title,
            "selftext": submission.selftext or "",
            "url": submission.url,
        }
        posts.append(post)
    return posts


if __name__ == "__main__":  # pragma: no cover - manual invocation
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Fetch posts from a subreddit and output them as JSON."
    )
    parser.add_argument("subreddit", help="The name of the subreddit to fetch from.")
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=10,
        help="Number of posts to fetch (default: 10)",
    )
    parser.add_argument(
        "-s",
        "--sort",
        choices=["hot", "new", "rising", "top"],
        default="top",
        help="Sort order to use (default: top)",
    )
    parser.add_argument(
        "-t",
        "--time-filter",
        choices=["all", "year", "month", "week", "day", "hour"],
        default="day",
        help=(
            "Time filter if sorting by top (default: day). "
            "Ignored for other sort methods."
        ),
    )

    args = parser.parse_args()
    posts = fetch_subreddit_posts(
        args.subreddit, limit=args.limit, sort=args.sort, time_filter=args.time_filter
    )
    print(json.dumps(posts, indent=2))