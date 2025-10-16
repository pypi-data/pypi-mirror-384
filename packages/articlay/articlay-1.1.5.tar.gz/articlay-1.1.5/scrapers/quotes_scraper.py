import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import random

def fetch_quote_of_day() -> List[Dict]:
    """Fetch quote of the day from various sources."""
    articles = []
    
    # Try multiple quote sources
    sources = [
        ("https://www.brainyquote.com/quote_of_the_day", "BrainyQuote"),
        ("https://www.goodreads.com/quotes", "Goodreads"),
    ]
    
    for url, source_name in sources:
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            soup = BeautifulSoup(response.content, 'html.parser')
            
            if source_name == "BrainyQuote":
                quote_elem = soup.find('img', {'class': 'p-qotd'})
                if quote_elem:
                    quote_text = quote_elem.get('alt', '')
                    if quote_text:
                        articles.append({
                            "title": "Quote of the Day",
                            "link": url,
                            "description": quote_text,
                            "content": quote_text,
                            "pubDate": "",
                            "category": "Inspiration"
                        })
                        break
            elif source_name == "Goodreads":
                quote_elem = soup.find('div', {'class': 'quoteText'})
                if quote_elem:
                    quote_text = quote_elem.get_text().strip()
                    articles.append({
                        "title": "Quote of the Day",
                        "link": url,
                        "description": quote_text[:300],
                        "content": quote_text,
                        "pubDate": "",
                        "category": "Inspiration"
                    })
                    break
        except Exception as e:
            print(f"Error fetching quote from {source_name}: {e}")
            continue
    
    # Fallback: Use a curated list of quotes
    if not articles:
        fallback_quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "Innovation distinguishes between a leader and a follower. - Steve Jobs",
            "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
            "It is during our darkest moments that we must focus to see the light. - Aristotle",
            "The only impossible journey is the one you never begin. - Tony Robbins",
        ]
        quote = random.choice(fallback_quotes)
        articles.append({
            "title": "Quote of the Day",
            "link": "https://en.wikipedia.org/wiki/List_of_quotes",
            "description": quote,
            "content": quote,
            "pubDate": "",
            "category": "Inspiration"
        })
    
    return articles

def fetch_zen_quote() -> List[Dict]:
    """Fetch a zen/philosophy quote."""
    articles = []
    try:
        # Use ZenQuotes API
        response = requests.get("https://zenquotes.io/api/today", timeout=10)
        data = response.json()
        
        if data and len(data) > 0:
            quote = data[0]
            quote_text = f"{quote.get('q', '')} - {quote.get('a', 'Unknown')}"
            
            articles.append({
                "title": "Zen Quote of the Day",
                "link": "https://zenquotes.io",
                "description": quote_text,
                "content": quote_text,
                "pubDate": "",
                "category": "Inspiration"
            })
    except Exception as e:
        print(f"Error fetching Zen quote: {e}")
    
    return articles

if __name__ == "__main__":
    print("Quote of the Day:")
    for art in fetch_quote_of_day():
        print(f"{art['title']}\n{art['description']}\n")
    
    print("\nZen Quote:")
    for art in fetch_zen_quote():
        print(f"{art['title']}\n{art['description']}\n")
