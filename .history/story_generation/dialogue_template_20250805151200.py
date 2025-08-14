"""Dialogue templates and helper functions for generating conversation-style stories.

This module provides simple utilities to transform raw post content into a
two-person dialogue.  The functions here are designed to be lightweight and
easily replaceable with more sophisticated LLM-driven generators in the
future.  For example, you can plug in a call to an LLM to summarise the
post and then construct a Q&A conversation around that summary.

The current implementation uses naive heuristics: it selects the most
important sentences from the body and constructs a question/answer pair.
"""

from __future__ import annotations

import re
from typing import List, Dict


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences using a simple period-based heuristic.

    This function is intentionally naive and does not handle abbreviations or
    languages other than English well.  It should be replaced with a more
    robust sentence splitter (e.g. nltk.sent_tokenize) when available.

    Args:
        text (str): The text to split into sentences.

    Returns:
        List[str]: A list of sentence strings.
    """
    # Replace newline characters with spaces to avoid false boundaries
    cleaned = re.sub(r"\s+", " ", text.strip())
    # Split on period, question mark, exclamation mark
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    # Filter out empty strings
    return [s for s in sentences if s]


def summarise_text(body: str, max_sentences: int = 2) -> str:
    """Summarise the body text by extracting the first few sentences.

    This simplistic summarisation picks the first `max_sentences` sentences.  In
    practice you should replace this with a call to an LLM or a proper
    summarisation algorithm.

    Args:
        body (str): The body of the post to summarise.
        max_sentences (int): The maximum number of sentences to include in the summary.

    Returns:
        str: A short summary of the body.
    """
    sentences = _split_sentences(body)
    if not sentences:
        return ""
    return " ".join(sentences[:max_sentences])


def generate_dialogue_from_post(post: Dict[str, str]) -> List[str]:
    """Generate a simple question/answer dialogue for a Reddit post.

    The dialogue consists of two lines:

    - A question asked by a curious host about the post's topic.
    - An answer provided by an expert summarising the key information.

    Args:
        post (Dict[str, str]): A dictionary containing 'title' and 'selftext'.

    Returns:
        List[str]: A list of dialogue lines alternating speaker prefixes.
    """
    title = post.get("title", "").strip()
    body = post.get("selftext", "").strip()

    summary = summarise_text(body) if body else ""

    question = (
        f"Morty: Ah geez Rick, I was reading about '{title}' on Reddit. W-what's that all about?"
        if title
        else "Morty: Ah geez Rick, I found this thing on Reddit. What's the deal with that?"
    )

    if summary:
        # Add Rick's characteristic speech patterns
        answer_content = summary.replace(". ", ". *burp* ")
        answer_content = f"Listen Morty, {answer_content} And that's *burp* the way the news goes!"
    else:
        answer_content = (
            f"Oh man Morty, it's about {title}. *burp* That's all there is to it Morty!"
            if title
            else "The post is empty Morty! Empty like your *burp* understanding of quantum mechanics!"
        )

    answer = f"Rick: {answer_content}"
    return [question, answer]
