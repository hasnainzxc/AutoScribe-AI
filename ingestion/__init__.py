"""Subpackage for ingestion logic.

Currently contains modules for ingesting Reddit content.  Additional data
sources (e.g. RSS feeds, Twitter) can be added here in the future.
"""

from .reddit_ingest import fetch_subreddit_posts  # noqa: F401

__all__ = ["fetch_subreddit_posts"]