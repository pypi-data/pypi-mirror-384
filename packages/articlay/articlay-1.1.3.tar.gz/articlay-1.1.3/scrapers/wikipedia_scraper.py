import requests
from bs4 import BeautifulSoup
from typing import List, Dict

def fetch_wikipedia_article_of_day() -> List[Dict]:
    """Fetch Wikipedia's Article of the Day (Featured Article) with full text and related articles."""
    articles = []
    try:
        from datetime import datetime
        
        # Use Wikipedia's REST API to get today's featured article
        today = datetime.now()
        year = today.year
        month = str(today.month).zfill(2)
        day = str(today.day).zfill(2)
        
        # Try the REST API first
        api_url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/featured/{year}/{month}/{day}"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            tfa = data.get('tfa', {})
            
            if tfa:
                title = tfa.get('displaytitle', tfa.get('title', 'Featured Article'))
                # Remove HTML tags from title
                from bs4 import BeautifulSoup as BS
                title = BS(title, 'html.parser').get_text()
                
                article_url = tfa.get('content_urls', {}).get('desktop', {}).get('page', '')
                extract = tfa.get('extract', '')
                
                # Fetch the full article text
                if article_url:
                    try:
                        article_response = requests.get(article_url, timeout=10)
                        article_soup = BeautifulSoup(article_response.content, 'html.parser')
                        
                        # Get the main content
                        content_div = article_soup.find('div', {'id': 'mw-content-text'})
                        if content_div:
                            # Get all paragraphs
                            paragraphs = content_div.find_all('p', recursive=False)
                            full_text = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                            
                            # Get related articles from "See also" section
                            related = []
                            see_also = article_soup.find('span', {'id': 'See_also'})
                            if see_also:
                                ul = see_also.find_next('ul')
                                if ul:
                                    links = ul.find_all('a', href=True)[:5]
                                    related = [f"• {link.get_text()}" for link in links]
                            
                            related_text = '\n'.join(related) if related else ''
                            
                            articles.append({
                                "title": f"Wikipedia Article of the Day: {title}",
                                "link": article_url,
                                "description": full_text[:1000] + "..." if len(full_text) > 1000 else full_text,
                                "content": full_text,
                                "related_articles": related_text,
                                "pubDate": "",
                                "category": "Wikipedia"
                            })
                        else:
                            # Fallback to extract
                            articles.append({
                                "title": f"Wikipedia Article of the Day: {title}",
                                "link": article_url,
                                "description": extract,
                                "content": extract,
                                "pubDate": "",
                                "category": "Wikipedia"
                            })
                    except Exception as e:
                        print(f"Error fetching full article: {e}")
                        # Fallback to extract
                        articles.append({
                            "title": f"Wikipedia Article of the Day: {title}",
                            "link": article_url,
                            "description": extract,
                            "content": extract,
                            "pubDate": "",
                            "category": "Wikipedia"
                        })
    except Exception as e:
        print(f"Error fetching Wikipedia Article of the Day: {e}")
    return articles

def fetch_wikipedia_image_of_day() -> List[Dict]:
    """Fetch Wikipedia's Picture of the Day."""
    articles = []
    try:
        from datetime import datetime
        
        # Use Wikipedia's REST API to get today's picture
        today = datetime.now()
        year = today.year
        month = str(today.month).zfill(2)
        day = str(today.day).zfill(2)
        
        api_url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/featured/{year}/{month}/{day}"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            image_data = data.get('image', {})
            
            if image_data:
                title = image_data.get('title', 'Wikipedia Picture of the Day')
                description = image_data.get('description', {}).get('text', 'Picture of the Day')
                # Remove HTML tags
                from bs4 import BeautifulSoup as BS
                description = BS(description, 'html.parser').get_text()
                
                img_url = image_data.get('thumbnail', {}).get('source', '')
                if not img_url:
                    img_url = image_data.get('image', {}).get('source', '')
                
                page_url = image_data.get('file_page', 'https://commons.wikimedia.org')
                
                articles.append({
                    "title": "Wikipedia Picture of the Day",
                    "link": page_url,
                    "description": description,
                    "image_url": img_url,
                    "pubDate": "",
                    "category": "Wikipedia"
                })
    except Exception as e:
        print(f"Error fetching Wikipedia Picture of the Day: {e}")
    return articles

def fetch_random_wikipedia_article() -> List[Dict]:
    """Fetch a random Wikipedia article."""
    articles = []
    try:
        response = requests.get("https://en.wikipedia.org/api/rest_v1/page/random/summary", timeout=10)
        data = response.json()
        
        articles.append({
            "title": f"Random Wikipedia Article: {data.get('title', 'Unknown')}",
            "link": data.get('content_urls', {}).get('desktop', {}).get('page', 'https://en.wikipedia.org'),
            "description": data.get('extract', ''),
            "pubDate": "",
            "category": "Wikipedia"
        })
    except Exception as e:
        print(f"Error fetching random Wikipedia article: {e}")
    return articles

def fetch_wikipedia_quote_of_day() -> List[Dict]:
    """Fetch quote of the day from Wikipedia's REST API."""
    articles = []
    try:
        from datetime import datetime
        
        # Use Wikipedia's REST API to get today's quote
        today = datetime.now()
        year = today.year
        month = str(today.month).zfill(2)
        day = str(today.day).zfill(2)
        
        api_url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/featured/{year}/{month}/{day}"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # The API doesn't have a dedicated quote field, so we'll try the "onthisday" section
            # as it contains interesting historical quotes and facts
            onthisday = data.get('onthisday', [])
            
            if onthisday and len(onthisday) > 0:
                # Get the first interesting event
                event = onthisday[0]
                text = event.get('text', '')
                year_event = event.get('year', '')
                
                quote_text = f"{text} ({year_event})" if year_event else text
                
                articles.append({
                    "title": "Wikipedia On This Day",
                    "link": f"https://en.wikipedia.org/wiki/{today.strftime('%B_%d')}",
                    "description": quote_text,
                    "content": quote_text,
                    "pubDate": "",
                    "category": "Wikipedia"
                })
    except Exception as e:
        print(f"Error fetching Wikipedia Quote/On This Day: {e}")
    return articles

def fetch_on_this_day() -> List[Dict]:
    """Fetch 'On This Day' events from Wikipedia REST API."""
    articles = []
    try:
        from datetime import datetime
        
        today = datetime.now()
        year = today.year
        month = str(today.month).zfill(2)
        day = str(today.day).zfill(2)
        month_name = today.strftime("%B")
        
        api_url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/featured/{year}/{month}/{day}"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            onthisday = data.get('onthisday', [])
            
            if onthisday:
                # Get top 5 events
                events = []
                for event in onthisday[:5]:
                    text = event.get('text', '')
                    year_event = event.get('year', '')
                    if text:
                        events.append(f"• {year_event}: {text}" if year_event else f"• {text}")
                
                if events:
                    events_text = '\n'.join(events)
                    
                    articles.append({
                        "title": f"On This Day in History - {month_name} {today.day}",
                        "link": f"https://en.wikipedia.org/wiki/{month_name}_{today.day}",
                        "description": events_text,
                        "content": events_text,
                        "pubDate": "",
                        "category": "Wikipedia"
                    })
    except Exception as e:
        print(f"Error fetching On This Day: {e}")
    return articles

if __name__ == "__main__":
    print("Wikipedia Article of the Day:")
    for art in fetch_wikipedia_article_of_day():
        print(f"{art['title']}\n{art['link']}\n")
    
    print("\nWikipedia Picture of the Day:")
    for art in fetch_wikipedia_image_of_day():
        print(f"{art['title']}\n{art['link']}\n")
    
    print("\nRandom Wikipedia Article:")
    for art in fetch_random_wikipedia_article():
        print(f"{art['title']}\n{art['link']}\n")
    
    print("\nWikiquote Quote of the Day:")
    for art in fetch_wikipedia_quote_of_day():
        print(f"{art['title']}\n{art['link']}\n")
    
    print("\nOn This Day:")
    for art in fetch_on_this_day():
        print(f"{art['title']}\n{art['link']}\n")
