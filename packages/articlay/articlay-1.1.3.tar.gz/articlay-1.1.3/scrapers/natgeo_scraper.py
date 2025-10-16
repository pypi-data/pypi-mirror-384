import requests
from bs4 import BeautifulSoup
from typing import List, Dict

NATGEO_RSS = "https://www.nationalgeographic.com/content/natgeo/en_us/index.rss"

def fetch_natgeo_articles(limit: int = 5) -> List[Dict]:
    """Fetch latest articles from National Geographic RSS feed."""
    articles = []
    try:
        resp = requests.get(NATGEO_RSS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, features="xml")
        items = soup.find_all('item')[:limit]
        for item in items:
            title = item.title.text.strip()
            link = item.link.text.strip()
            description = item.description.text.strip() if item.description else ""
            pubdate = item.pubDate.text.strip() if item.pubDate else ""
            articles.append({
                "title": title,
                "link": link,
                "description": description,
                "pubDate": pubdate,
                "category": "Science"
            })
    except Exception as e:
        print(f"Error fetching National Geographic articles: {e}")
    return articles

if __name__ == "__main__":
    for art in fetch_natgeo_articles():
        print(f"{art['title']}\n{art['link']}\n")
