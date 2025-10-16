import requests
from bs4 import BeautifulSoup
from typing import List, Dict

MUBI_RSS = "https://mubi.com/notebook/posts.atom"

def fetch_mubi_articles(limit: int = 1) -> List[Dict]:
    """Fetch latest film essays from MUBI Notebook RSS feed."""
    articles = []
    try:
        resp = requests.get(MUBI_RSS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, features="xml")
        entries = soup.find_all('entry')[:limit]
        for entry in entries:
            title = entry.title.text.strip() if entry.title else ""
            link_elem = entry.find('link')
            link = link_elem.get('href', '') if link_elem else ""
            summary = entry.summary.text.strip() if entry.summary else ""
            # Remove any HTML tags from description
            description = BeautifulSoup(summary, 'html.parser').get_text()
            updated = entry.updated.text.strip() if entry.updated else ""
            articles.append({
                "title": title,
                "link": link,
                "description": description,
                "pubDate": updated,
                "category": "Movie"
            })
    except Exception as e:
        print(f"Error fetching MUBI articles: {e}")
    return articles

if __name__ == "__main__":
    for art in fetch_mubi_articles():
        print(f"{art['title']}\n{art['link']}\n")
