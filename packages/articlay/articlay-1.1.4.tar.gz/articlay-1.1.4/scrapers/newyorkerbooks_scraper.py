import requests
from bs4 import BeautifulSoup
from typing import List, Dict

NEWYORKERBOOKS_RSS = "https://www.newyorker.com/feed/books"

def fetch_newyorkerbooks_articles(limit: int = 10) -> List[Dict]:
    """Fetch latest book articles from The New Yorker Books section RSS feed."""
    articles = []
    try:
        resp = requests.get(NEWYORKERBOOKS_RSS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, features="xml")
        items = soup.find_all('item')[:limit]
        for item in items:
            title = item.title.text.strip() if item.title else ""
            link = item.link.text.strip() if item.link else ""
            description = item.description.text.strip() if item.description else ""
            # Remove any HTML tags from description
            description = BeautifulSoup(description, 'html.parser').get_text()
            pubdate = item.pubDate.text.strip() if item.pubDate else ""
            articles.append({
                "title": title,
                "link": link,
                "description": description,
                "pubDate": pubdate,
                "category": "Literature"
            })
    except Exception as e:
        print(f"Error fetching New Yorker Books articles: {e}")
    return articles

if __name__ == "__main__":
    for art in fetch_newyorkerbooks_articles():
        print(f"{art['title']}\n{art['link']}\n")
