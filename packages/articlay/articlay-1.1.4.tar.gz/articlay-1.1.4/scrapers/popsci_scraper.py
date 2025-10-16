import requests
from bs4 import BeautifulSoup
from typing import List, Dict

POPSCI_RSS = "https://www.popsci.com/rss.xml"

def fetch_popsci_articles(limit: int = 5) -> List[Dict]:
    articles = []
    try:
        resp = requests.get(POPSCI_RSS, timeout=10)
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
        print(f"Error fetching Popular Science articles: {e}")
    return articles

if __name__ == "__main__":
    for art in fetch_popsci_articles():
        print(f"{art['title']}\n{art['link']}\n")
