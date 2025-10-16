import requests
from bs4 import BeautifulSoup
from typing import List, Dict

FIVETHIRTYEIGHT_RSS = "https://fivethirtyeight.com/all/feed"

def fetch_fivethirtyeight_articles(limit: int = 30) -> List[Dict]:
    """Fetch latest articles from FiveThirtyEight RSS feed."""
    articles = []
    try:
        resp = requests.get(FIVETHIRTYEIGHT_RSS, timeout=10)
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
                "category": "Politics"
            })
    except Exception as e:
        print(f"Error fetching FiveThirtyEight articles: {e}")
    return articles

if __name__ == "__main__":
    for art in fetch_fivethirtyeight_articles():
        print(f"{art['title']}\n{art['link']}\n")
