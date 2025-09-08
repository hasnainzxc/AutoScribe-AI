"""Ingestion pipeline for fetching stories from Reddit.

This module defines functions to pull posts from a subreddit using the
PRAW (Python Reddit API Wrapper) library.  It abstracts the details
of authentication and retrieval so that other parts of the pipeline can
focus on processing the content.  You should set the environment
variables `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` and
`REDDIT_USER_AGENT` before running this module.  See the PRAW
documentation for details on how to obtain these credentials.

Typical usage::

    from ingestion.reddit_ingest import fetch_subreddit_posts

    posts = fetch_subreddit_posts('aws', limit=10)
    for post in posts:
        print(post['title'])

"""

from __future__ import annotations

import os
from typing import List, Dict
from pathlib import Path
from config.settings import get_reddit_config

try:
    import praw  # type: ignore
except ImportError as e:
    raise ImportError(
        "praw must be installed to use this module. Install it via `pip install praw`."
    ) from e

# Environment loading is handled centrally by config.settings


def _create_reddit_instance() -> praw.Reddit:
    """Create a PRAW Reddit instance using environment variables.

    Returns:
        praw.Reddit: An authenticated Reddit instance.

    Raises:
        RuntimeError: If required environment variables are missing.
    """
    creds = get_reddit_config()
    # Determine auth flow and construct praw.Reddit accordingly
    client_id = creds["client_id"]
    client_secret = creds.get("client_secret")
    user_agent = creds["user_agent"]
    has_pw = ("username" in creds and "password" in creds)
    is_installed = creds.get("installed_app") == "true"

    if is_installed and not has_pw and client_secret is None:
        # Installed App without device/implicit flow implemented — explain clearly
        raise RuntimeError(
            "Reddit app appears to be an Installed App (no client secret provided). "
            "This pipeline does not implement the device/implicit auth flow. "
            "Either: (1) switch your Reddit app type to 'script' and set REDDIT_USERNAME/REDDIT_PASSWORD, "
            "or (2) use an app type that provides a client secret."
        )

    if has_pw:
        # Script app using password grant
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            username=creds["username"],
            password=creds["password"],
        )
        flow = "password_grant"
    else:
        # Application-only (client credentials)
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
        flow = "client_credentials"

    # Light debugging to help diagnose 401 issues (non-sensitive)
    try:
        ua = user_agent
        print(f"[Reddit Auth] flow={flow}, user_agent_present={bool(ua)}")
        if ua and " by " not in ua:
            print(
                "[Reddit Auth] Warning: 'REDDIT_USER_AGENT' should be descriptive, e.g., "
                "'AppName/Version by your_username'"
            )
    except Exception:
        pass
    # Explicitly set read-only mode for application-only access
    try:
        reddit.read_only = True
    except Exception:
        # Non-fatal; continue and let downstream error handling surface issues
        pass
    return reddit


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
    # Prefer public JSON endpoint to avoid OAuth fragility where possible
    public_posts = _fallback_fetch_public_json(subreddit_name, limit, sort, time_filter)
    if public_posts:
        return public_posts[:limit]

    # Fallback to PRAW OAuth flow if public endpoint didn't return results
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
    # Iterate and collect posts, surfacing clearer auth errors if any
    try:
        for submission in submissions:
            # Skip stickied posts to avoid pinned announcements
            if submission.stickied:
                continue
            post = {
                "title": submission.title,
                "selftext": submission.selftext or "",
                "url": submission.url,
                "subreddit": subreddit_name,
            }
            posts.append(post)
    except Exception as exc:
        # Improve error clarity around common OAuth/auth issues and fallback to public JSON
        try:
            from prawcore.exceptions import ResponseException  # type: ignore
        except Exception:
            ResponseException = tuple()  # type: ignore

        is_401 = False
        try:
            if isinstance(exc, ResponseException) and getattr(exc, "response", None):
                status = getattr(exc.response, "status_code", None)
                is_401 = (status == 401)
        except Exception:
            pass

        if is_401:
            # Attempt fallback using Reddit's public JSON endpoints (no OAuth)
            fallback = _fallback_fetch_public_json(subreddit_name, limit, sort, time_filter)
            if fallback:
                return fallback
            tips = [
                "Verify REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET (if using client credentials).",
                "Ensure REDDIT_USER_AGENT is descriptive: 'AppName/Version by your_username'.",
                "Or use a 'script' app with REDDIT_USERNAME and REDDIT_PASSWORD set.",
            ]
            raise RuntimeError(
                "Reddit API returned 401 (Unauthorized). " + " ".join(tips)
            ) from exc
        # Re-raise anything else unchanged
        raise
    return posts


def _fallback_fetch_public_json(
    subreddit_name: str, limit: int, sort: str, time_filter: str
) -> List[Dict[str, str]]:
    """Fallback fetch via Reddit's public JSON endpoint when OAuth fails.

    Returns an empty list on any error.
    """
    import requests
    headers = {"User-Agent": get_reddit_config().get("user_agent", "autoscribe/0.1 by unknown")}
    if sort not in {"hot", "new", "rising", "top"}:
        sort = "top"
    params = {"limit": max(1, min(100, int(limit)))}
    if sort == "top":
        params["t"] = time_filter or "day"
    url = f"https://www.reddit.com/r/{subreddit_name}/{sort}.json"
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code != 200:
            return []
        data = resp.json()
        children = data.get("data", {}).get("children", [])
        posts: List[Dict[str, str]] = []
        for child in children[: params["limit"]]:
            d = child.get("data", {})
            posts.append(
                {
                    "title": d.get("title", ""),
                    "selftext": d.get("selftext", ""),
                    "url": d.get("url_overridden_by_dest") or d.get("url", ""),
                    "subreddit": subreddit_name,
                }
            )
        return posts
    except Exception:
        return []


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
