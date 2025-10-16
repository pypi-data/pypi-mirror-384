import requests
from bs4 import BeautifulSoup
from typing import List, Dict

def fetch_reddit_subreddit(subreddit: str, limit: int = 5) -> List[Dict]:
    """Fetch top posts from a subreddit RSS feed."""
    articles = []
    try:
        rss_url = f"https://www.reddit.com/r/{subreddit}/top/.rss?t=day"
        resp = requests.get(rss_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, features="xml")
        entries = soup.find_all('entry')[:limit]
        for entry in entries:
            title = entry.title.text.strip() if entry.title else ""
            link_elem = entry.find('link')
            link = link_elem.get('href', '') if link_elem else ""
            content = entry.content.text.strip() if entry.content else ""
            # Remove any HTML tags from content
            description = BeautifulSoup(content, 'html.parser').get_text()
            updated = entry.updated.text.strip() if entry.updated else ""
            articles.append({
                "title": title,
                "link": link,
                "description": description[:300] + "..." if len(description) > 300 else description,
                "pubDate": updated,
                "category": "Reddit"
            })
    except Exception as e:
        print(f"Error fetching Reddit r/{subreddit}: {e}")
    return articles

def fetch_reddit_worldnews(limit: int = 5) -> List[Dict]:
    """Fetch top posts from r/worldnews."""
    return fetch_reddit_subreddit("worldnews", limit)

def fetch_reddit_india(limit: int = 5) -> List[Dict]:
    """Fetch top posts from r/india."""
    return fetch_reddit_subreddit("india", limit)

def fetch_reddit_chennai(limit: int = 5) -> List[Dict]:
    """Fetch top posts from r/chennai."""
    return fetch_reddit_subreddit("chennai", limit)

def fetch_reddit_programming(limit: int = 5) -> List[Dict]:
    """Fetch top posts from r/programming."""
    return fetch_reddit_subreddit("programming", limit)

def fetch_reddit_technology(limit: int = 5) -> List[Dict]:
    """Fetch top posts from r/technology."""
    return fetch_reddit_subreddit("technology", limit)

def fetch_reddit_science(limit: int = 5) -> List[Dict]:
    """Fetch top posts from r/science."""
    return fetch_reddit_subreddit("science", limit)

def fetch_reddit_books(limit: int = 5) -> List[Dict]:
    """Fetch top posts from r/books."""
    return fetch_reddit_subreddit("books", limit)

def fetch_reddit_movies(limit: int = 5) -> List[Dict]:
    """Fetch top posts from r/movies."""
    return fetch_reddit_subreddit("movies", limit)

def fetch_reddit_writing(limit: int = 5) -> List[Dict]:
    """Fetch top posts from r/writing."""
    return fetch_reddit_subreddit("writing", limit)

if __name__ == "__main__":
    print("=== r/worldnews ===")
    for art in fetch_reddit_worldnews():
        print(f"{art['title']}\n{art['link']}\n")
    
    print("\n=== r/india ===")
    for art in fetch_reddit_india():
        print(f"{art['title']}\n{art['link']}\n")
    
    print("\n=== r/chennai ===")
    for art in fetch_reddit_chennai():
        print(f"{art['title']}\n{art['link']}\n")
