"""Test script for Reddit post fetching."""

from ingestion.reddit_ingest import fetch_subreddit_posts

def test_reddit_fetching():
    """Test the Reddit post fetching functionality."""
    print("\nTesting Reddit post fetching...")
    print("-" * 50)
    
    subreddit = "beermoney"
    limit = 2
    sort = "top"
    time_filter = "week"
    
    print(f"Fetching {limit} posts from r/{subreddit}")
    print(f"Sort: {sort}, Time filter: {time_filter}")
    print("-" * 50)
    
    try:
        posts = fetch_subreddit_posts(
            subreddit_name=subreddit,
            limit=limit,
            sort=sort,
            time_filter=time_filter
        )
        
        print(f"\nFetched {len(posts)} posts:")
        print("-" * 50)
        
        for i, post in enumerate(posts, 1):
            print(f"\nPost {i}:")
            print(f"Title: {post['title']}")
            print(f"Score: {post.get('score', 'N/A')}")
            print(f"URL: {post['url']}")
            print("-" * 25)
            print("Content preview:")
            print(post['selftext'][:200] + "..." if len(post['selftext']) > 200 else post['selftext'])
            print("-" * 50)
            
    except Exception as e:
        print(f"Error fetching posts: {str(e)}")
        raise

if __name__ == "__main__":
    test_reddit_fetching()
