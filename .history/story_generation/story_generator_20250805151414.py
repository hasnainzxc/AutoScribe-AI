"""High-level story generator for creating Rick and Morty style dialogues from Reddit posts.

This module connects the ingestion layer with the dialogue template functions to
produce ready-to-record scripts in the style of Rick and Morty conversations.
Given a subreddit name (defaults to 'beermoney'), it will pull a specified 
number of posts, summarise their content, and generate Rick and Morty styled
dialogues where:
- Morty asks questions about Reddit posts he found
- Rick provides explanations in his characteristic style with burps and snark

The dialogues are designed to be used with text-to-speech and video generation
tools to create animated content.
"""

from __future__ import annotations

from typing import List, Dict

from content_pipeline.ingestion.reddit_ingest import fetch_subreddit_posts
from content_pipeline.story_generation.dialogue_template import (
    generate_dialogue_from_post,
)


def create_stories(
    subreddit: str = "beermoney", number_of_posts: int = 5, sort: str = "top", time_filter: str = "day"
) -> List[List[str]]:
    """Generate dialogues for a set of posts from a subreddit.

    Args:
        subreddit (str): Name of the subreddit to pull posts from.
        number_of_posts (int): How many posts to process. Defaults to 5.
        sort (str): Sorting method for subreddit posts ('hot', 'new', 'rising', 'top'). Defaults to 'top'.
        time_filter (str): Time filter if sorting by 'top'. Defaults to 'day'.

    Returns:
        List[List[str]]: A list of dialogues, each a list of strings.
    """
    posts = fetch_subreddit_posts(
        subreddit_name=subreddit,
        limit=number_of_posts,
        sort=sort,
        time_filter=time_filter,
    )
    dialogues: List[List[str]] = []
    for post in posts:
        dialogue = generate_dialogue_from_post(post)
        dialogues.append(dialogue)
    return dialogues


if __name__ == "__main__":  # pragma: no cover - manual invocation
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description=(
            "Fetch posts from a subreddit and generate question/answer dialogues for them."
        )
    )
    parser.add_argument("subreddit", help="The name of the subreddit to fetch from.")
    parser.add_argument(
        "-n",
        "--number-of-posts",
        type=int,
        default=5,
        help="Number of posts to fetch and generate dialogues for (default: 5)",
    )
    parser.add_argument(
        "-s",
        "--sort",
        choices=["hot", "new", "rising", "top"],
        default="top",
        help="Sort order to use when fetching posts (default: top)",
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
    dialogues = create_stories(
        subreddit=args.subreddit,
        number_of_posts=args.number_of_posts,
        sort=args.sort,
        time_filter=args.time_filter,
    )
    print(json.dumps(dialogues, indent=2))