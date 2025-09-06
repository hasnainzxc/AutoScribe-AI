
from __future__ import annotations

from typing import List, Dict, Tuple, Any

from ingestion.reddit_ingest import fetch_subreddit_posts
from story_generation.dialogue_template import generate_dialogue_from_post
from story_generation.character_registry import get_character


def create_stories(
    subreddit: str = "beermoney",
    number_of_posts: int = 5,
    sort: str = "top",
    time_filter: str = "day",
    character: str = "rickmorty",
) -> List[Dict[str, Any]]:
    """Generate dialogues for a set of posts from a subreddit.

    Args:
        subreddit (str): Name of the subreddit to pull posts from.
        number_of_posts (int): How many posts to process. Defaults to 5.
        sort (str): Sorting method for subreddit posts ('hot', 'new', 'rising', 'top'). Defaults to 'top'.
        time_filter (str): Time filter if sorting by 'top'. Defaults to 'day'.

    Returns:
        List[Dict]: For each post, returns a dict with:
            - 'character': str
            - 'lines': List[str] (for multi‑speaker characters) OR
            - 'text': str (for single‑speaker characters)
            - 'metadata': Dict
            - 'post': original post dict
    """
    print(f"\n[Story Generator] Starting to fetch {number_of_posts} posts from r/{subreddit}...")
    posts = fetch_subreddit_posts(
        subreddit_name=subreddit,
        limit=number_of_posts,
        sort=sort,
        time_filter=time_filter,
    )
    outputs: List[Dict[str, Any]] = []
    spec = get_character(character)
    for post in posts:
        if spec and spec.single_speaker:
            # Single‑speaker monologue generation (e.g., DJ Cara)
            text, meta = spec.generator(post)
            outputs.append({
                "character": spec.key,
                "text": text,
                "metadata": meta,
                "post": post,
            })
        else:
            # Multi‑speaker (e.g., Rick & Morty) returns lines
            result = generate_dialogue_from_post(post, character=character)
            if isinstance(result, tuple) and len(result) == 2:
                lines, meta = result
            else:
                lines, meta = result, {}
            outputs.append({
                "character": character,
                "lines": lines,
                "metadata": meta,
                "post": post,
            })
    return outputs


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
    parser.add_argument(
        "-c",
        "--character",
        choices=["rickmorty", "djcara"],
        default="rickmorty",
        help="Choose character style for generation",
    )

    args = parser.parse_args()
    dialogues = create_stories(
        subreddit=args.subreddit,
        number_of_posts=args.number_of_posts,
        sort=args.sort,
        time_filter=args.time_filter,
        character=args.character,
    )
    print(json.dumps(dialogues, indent=2))
