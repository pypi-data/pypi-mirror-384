import requests
from bs4 import BeautifulSoup
from typing import List, Dict

DEV_TO_RSS = "https://dev.to/feed"

def fetch_dev_to_articles(limit: int = 1) -> List[Dict]:
    """Fetch latest tech articles from Dev.to RSS feed."""
    articles = []
    try:
        resp = requests.get(DEV_TO_RSS, timeout=10)
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
                "category": "Code & Tech"
            })
    except Exception as e:
        print(f"Error fetching Dev.to articles: {e}")
    return articles

if __name__ == "__main__":
    for art in fetch_dev_to_articles():
        print(f"{art['title']}\n{art['link']}\n")
