import requests
from bs4 import BeautifulSoup
from typing import List, Dict

TREEHUGGER_RSS = "https://www.treehugger.com/feeds/all"

def fetch_treehugger_articles(limit: int = 5) -> List[Dict]:
    """Fetch latest environment articles from TreeHugger RSS feed."""
    articles = []
    try:
        resp = requests.get(TREEHUGGER_RSS, timeout=10)
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
                "category": "Environment"
            })
    except Exception as e:
        print(f"Error fetching TreeHugger articles: {e}")
    return articles

if __name__ == "__main__":
    for art in fetch_treehugger_articles():
        print(f"{art['title']}\n{art['link']}\n")
