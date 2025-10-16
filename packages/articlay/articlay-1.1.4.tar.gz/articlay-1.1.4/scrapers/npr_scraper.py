import requests
from bs4 import BeautifulSoup
from typing import List, Dict

NPR_RSS = "https://www.npr.org/rss/rss.php?id=1001"

def fetch_npr_articles(limit: int = 5) -> List[Dict]:
    articles = []
    try:
        resp = requests.get(NPR_RSS, timeout=10)
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
                "category": "World"
            })
    except Exception as e:
        print(f"Error fetching NPR articles: {e}")
    return articles

if __name__ == "__main__":
    for art in fetch_npr_articles():
        print(f"{art['title']}\n{art['link']}\n")
