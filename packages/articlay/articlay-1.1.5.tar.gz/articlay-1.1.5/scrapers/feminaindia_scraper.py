import requests
from bs4 import BeautifulSoup
from typing import List, Dict

FEMINAINDIA_RSS = "https://www.femina.in/feed"

def fetch_feminaindia_articles(limit: int = 5) -> List[Dict]:
    """Fetch latest articles from Femina India RSS feed."""
    articles = []
    try:
        resp = requests.get(FEMINAINDIA_RSS, timeout=10)
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
                "category": "Fashion"
            })
    except Exception as e:
        print(f"Error fetching Femina India articles: {e}")
    return articles

if __name__ == "__main__":
    for art in fetch_feminaindia_articles():
        print(f"{art['title']}\n{art['link']}\n")
