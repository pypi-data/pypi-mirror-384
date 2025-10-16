import requests
from bs4 import BeautifulSoup
from typing import List, Dict

MASHABLE_RSS = "https://mashable.com/feeds/rss/all"

def fetch_mashable_articles(limit: int = 5) -> List[Dict]:
    """Fetch latest tech and culture articles from Mashable RSS feed."""
    articles = []
    try:
        resp = requests.get(MASHABLE_RSS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, features="xml")
        items = soup.find_all('item')[:limit]
        for item in items:
            title = item.title.text.strip() if item.title else ""
            link = item.link.text.strip() if item.link else ""
            description = item.description.text.strip() if item.description else ""
            pubdate = item.pubDate.text.strip() if item.pubDate else ""
            articles.append({
                "title": title,
                "link": link,
                "description": description,
                "pubDate": pubdate,
                "category": "Technology"
            })
    except Exception as e:
        print(f"Error fetching Mashable articles: {e}")
    return articles

if __name__ == "__main__":
    for art in fetch_mashable_articles():
        print(f"{art['title']}\n{art['link']}\n")
