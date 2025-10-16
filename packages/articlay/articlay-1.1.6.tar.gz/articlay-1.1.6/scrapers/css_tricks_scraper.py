import requests
from bs4 import BeautifulSoup
from typing import List, Dict

CSS_TRICKS_RSS = "https://css-tricks.com/feed/"

def fetch_css_tricks_articles(limit: int = 1) -> List[Dict]:
    """Fetch latest CSS and web dev articles from CSS-Tricks RSS feed."""
    articles = []
    try:
        resp = requests.get(CSS_TRICKS_RSS, timeout=10)
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
        print(f"Error fetching CSS-Tricks articles: {e}")
    return articles

if __name__ == "__main__":
    for art in fetch_css_tricks_articles():
        print(f"{art['title']}\n{art['link']}\n")
