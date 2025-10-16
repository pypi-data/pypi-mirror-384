import requests
from bs4 import BeautifulSoup
from typing import List, Dict

BLOOMBERG_RSS = "https://www.bloomberg.com/feed/podcast/etf-report.xml"

def fetch_bloomberg_articles(limit: int = 5) -> List[Dict]:
    articles = []
    try:
        resp = requests.get(BLOOMBERG_RSS, timeout=10)
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
                "category": "Business"
            })
    except Exception as e:
        print(f"Error fetching Bloomberg articles: {e}")
    return articles

if __name__ == "__main__":
    for art in fetch_bloomberg_articles():
        print(f"{art['title']}\n{art['link']}\n")
