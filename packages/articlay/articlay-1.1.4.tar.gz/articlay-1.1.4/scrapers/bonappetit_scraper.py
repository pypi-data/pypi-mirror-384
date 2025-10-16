import requests
from bs4 import BeautifulSoup
from typing import List, Dict

# Note: RSS feed URLs vary by publisher (e.g., /feed/rss, /feeds/all, /rss.xml)
# Each URL is based on the actual feed endpoint provided by the respective publication
BONAPPETIT_RSS = "https://www.bonappetit.com/feed/rss"

def fetch_bonappetit_articles(limit: int = 5) -> List[Dict]:
    """Fetch latest food articles from Bon Appetit RSS feed."""
    articles = []
    try:
        resp = requests.get(BONAPPETIT_RSS, timeout=10)
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
                "category": "Food"
            })
    except Exception as e:
        print(f"Error fetching Bon Appetit articles: {e}")
    return articles

if __name__ == "__main__":
    for art in fetch_bonappetit_articles():
        print(f"{art['title']}\n{art['link']}\n")
