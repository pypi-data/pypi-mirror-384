#!/usr/bin/env python3
"""
Articlay - Magzter Article Aggregator
Gathers popular magazine articles and archives them to GitHub Gist
"""

import os
import sys
import json
import random
import argparse
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import requests
from bs4 import BeautifulSoup


class MagzterScraper:
    """Scraper for Magzter magazines and articles"""
    
    BASE_URL = "https://www.magzter.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_popular_magazines(self, limit: int = 10) -> List[Dict]:
        """
        Fetch popular magazines from Magzter
        
        Args:
            limit: Number of top magazines to fetch (10, 20, or 30)
        
        Returns:
            List of magazine dictionaries with name, url, and latest edition
        """
        magazines = []
        
        # For demonstration, since we can't actually access Magzter without proper auth
        # This would be the actual implementation structure
        try:
            # Placeholder: In real implementation, scrape from Magzter's popular section
            # url = f"{self.BASE_URL}/popular"
            # response = self.session.get(url)
            # soup = BeautifulSoup(response.content, 'html.parser')
            
            # For now, return sample data structure
            sample_magazines = [
                {
                    'name': f'Magazine {i}',
                    'url': f'{self.BASE_URL}/magazine-{i}',
                    'latest_edition': f'Edition {datetime.now().strftime("%Y-%m")}'
                }
                for i in range(1, limit + 1)
            ]
            magazines = sample_magazines[:limit]
            
        except Exception as e:
            print(f"Error fetching magazines: {e}")
        
        return magazines
    
    def get_articles_from_magazine(self, magazine: Dict) -> List[Dict]:
        """
        Extract articles from a magazine's latest edition
        
        Args:
            magazine: Magazine dictionary with url
        
        Returns:
            List of article dictionaries with title and link
        """
        articles = []
        
        try:
            # Placeholder: In real implementation, scrape articles from magazine page
            # response = self.session.get(magazine['url'])
            # soup = BeautifulSoup(response.content, 'html.parser')
            
            # For now, return sample articles
            for i in range(1, 6):
                articles.append({
                    'title': f"{magazine['name']} - Article {i}",
                    'link': f"{magazine['url']}/article-{i}",
                    'magazine': magazine['name']
                })
                
        except Exception as e:
            print(f"Error fetching articles from {magazine['name']}: {e}")
        
        return articles


class GistArchiver:
    """Handler for archiving articles to GitHub Gist"""
    
    GIST_API_URL = "https://api.github.com/gists"
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            print("Warning: No GitHub token provided. Gist archiving disabled.")
    
    def archive_articles(self, articles: List[Dict]) -> Optional[str]:
        """
        Archive articles to a GitHub Gist
        
        Args:
            articles: List of article dictionaries
        
        Returns:
            URL of the created gist, or None if failed
        """
        if not self.token:
            print("Cannot archive: No GitHub token available")
            return None
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"articlay-{date_str}.md"
        
        # Format articles as markdown
        content = f"# Articlay - Popular Magazine Articles\n"
        content += f"Date: {date_str}\n\n"
        
        for i, article in enumerate(articles, 1):
            content += f"## {i}. {article['title']}\n"
            content += f"**Magazine:** {article['magazine']}\n"
            content += f"**Link:** {article['link']}\n\n"
        
        gist_data = {
            "description": f"Articlay articles for {date_str}",
            "public": True,
            "files": {
                filename: {
                    "content": content
                }
            }
        }
        
        try:
            headers = {
                'Authorization': f'token {self.token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.post(self.GIST_API_URL, 
                                   headers=headers, 
                                   json=gist_data)
            
            if response.status_code == 201:
                gist_url = response.json()['html_url']
                print(f"\n✓ Archived to Gist: {gist_url}")
                return gist_url
            else:
                print(f"Failed to create gist: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"Error creating gist: {e}")
            return None


class Articlay:
    """Main application class"""
    
    def __init__(self, github_token: Optional[str] = None, gist_id: Optional[str] = None):
        self.scraper = MagzterScraper()
        self.archiver = GistArchiver(github_token)
        
        # Default Gist ID - can be overridden by user
        DEFAULT_GIST_ID = "17c58ca69bfa6f204a353a76f21b7774"
        
        # Priority order for Gist ID:
        # 1. Provided as argument
        # 2. Environment variable
        # 3. gist_config.py file
        # 4. Default hardcoded ID
        
        self.gist_id = gist_id
        
        if not self.gist_id:
            # Check environment variable
            self.gist_id = os.getenv('ARTICLAY_GIST_ID') or os.getenv('GIST_ID')
        
        if not self.gist_id:
            # Try to load from gist_config.py
            try:
                from gist_config import GIST_ID
                self.gist_id = GIST_ID
            except ImportError:
                pass
        
        if not self.gist_id:
            # Use default Gist ID
            self.gist_id = DEFAULT_GIST_ID
    
    def fetch_gist_articles(self) -> Dict[str, List[Dict]]:
        """
        Fetch articles from the configured GitHub Gist.
        
        Returns:
            Dictionary with date as key and list of articles as value
        """
        if not self.gist_id:
            print("No Gist ID configured. Cannot fetch articles.")
            return {}
        
        try:
            url = f"https://api.github.com/gists/{self.gist_id}"
            headers = {}
            
            # Add authentication if token is available
            if self.archiver.token:
                headers['Authorization'] = f'token {self.archiver.token}'
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            gist_data = response.json()
            files = gist_data.get('files', {})
            
            # Look for the main data file
            data_file = None
            for filename, file_info in files.items():
                if filename.endswith('.json'):
                    data_file = file_info
                    break
            
            if data_file:
                content = data_file.get('content', '{}')
                articles_data = json.loads(content)
                return articles_data
            else:
                print("No JSON file found in Gist.")
                return {}
                
        except Exception as e:
            print(f"Error fetching articles from Gist: {e}")
            print("Note: If the Gist is private, you need to provide a GitHub token using --token or GITHUB_TOKEN env var.")
            return {}
    
    def get_articles_by_category(self, category: Optional[str] = None, limit: int = 5) -> List[Dict]:
        """
        Get articles filtered by category.
        
        Args:
            category: Category to filter by (None for all)
            limit: Maximum number of articles to return
            
        Returns:
            List of articles
        """
        articles_data = self.fetch_gist_articles()
        
        if not articles_data:
            return []
        
        # Check if data structure is date-based or source-based
        all_articles = []
        
        # Check if there's a nested date structure like {"2025-10-15": {...}}
        today = datetime.now().strftime("%Y-%m-%d")
        
        # If the top level has a date key
        if today in articles_data and isinstance(articles_data[today], dict):
            # Date-based with nested sources: {"2025-10-15": {"Healthline": [...], ...}}
            for source_name, source_articles in articles_data[today].items():
                if isinstance(source_articles, list):
                    all_articles.extend(source_articles)
        else:
            # Try to find date-like keys
            date_keys = [k for k in articles_data.keys() if '-' in k and len(k) == 10]
            if date_keys:
                # Use the most recent date
                dates = sorted(date_keys, reverse=True)
                recent_date = dates[0]
                print(f"Using articles from {recent_date} (today's articles not available)")
                
                if isinstance(articles_data[recent_date], dict):
                    # Nested structure
                    for source_name, source_articles in articles_data[recent_date].items():
                        if isinstance(source_articles, list):
                            all_articles.extend(source_articles)
                elif isinstance(articles_data[recent_date], list):
                    # Flat list
                    all_articles = articles_data[recent_date]
            else:
                # Assume source-based structure at top level (e.g., {"Healthline": [...], "Vogue": [...]})
                for source_name, source_articles in articles_data.items():
                    if isinstance(source_articles, list):
                        all_articles.extend(source_articles)
        
        # Filter by category if specified
        if category:
            filtered = [a for a in all_articles if isinstance(a, dict) and a.get('category', '').lower() == category.lower()]
        else:
            filtered = [a for a in all_articles if isinstance(a, dict)]
        
        # Return limited results
        return filtered[:limit] if limit > 0 else filtered
    
    def display_articles_table(self, articles: List[Dict], category: Optional[str] = None):
        """Display articles in a formatted table."""
        if not articles:
            print(f"\nNo articles found" + (f" in category '{category}'" if category else "") + ".")
            return
        
        print(f"\n📚 Articles" + (f" in '{category}'" if category else "") + f" ({len(articles)} total):")
        print(f"{'=' * 80}\n")
        
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'No title')
            cat = article.get('category', 'Uncategorized')
            link = article.get('link', '')
            
            # Truncate title if too long
            if len(title) > 60:
                title = title[:57] + '...'
            
            print(f"{i:2d}. {title}")
            print(f"    Category: {cat}")
            if link:
                print(f"    Link: {link}")
            print()
    
    def select_random_articles(self, magazines: List[Dict], 
                              count: int = 5) -> List[Dict]:
        """
        Select random articles from different magazines
        
        Args:
            magazines: List of magazine dictionaries
            count: Number of articles to select
        
        Returns:
            List of selected article dictionaries
        """
        selected_articles = []
        used_magazines = set()
        
        # Shuffle magazines to randomize selection
        shuffled_magazines = magazines.copy()
        random.shuffle(shuffled_magazines)
        
        for magazine in shuffled_magazines:
            if len(selected_articles) >= count:
                break
            
            if magazine['name'] not in used_magazines:
                articles = self.scraper.get_articles_from_magazine(magazine)
                if articles:
                    # Pick a random article from this magazine
                    article = random.choice(articles)
                    selected_articles.append(article)
                    used_magazines.add(magazine['name'])
        
        return selected_articles
    
    def run(self, magazine_count: int = 10, article_count: int = 5, 
           archive: bool = True) -> List[Dict]:
        """
        Main execution flow
        
        Args:
            magazine_count: Number of top magazines to consider (10, 20, or 30)
            article_count: Number of articles to select
            archive: Whether to archive to Gist
        
        Returns:
            List of selected articles
        """
        print(f"\n📰 Articlay - Magzter Article Aggregator")
        print(f"{'=' * 50}\n")
        
        print(f"Fetching top {magazine_count} popular magazines...")
        magazines = self.scraper.get_popular_magazines(magazine_count)
        
        if not magazines:
            print("No magazines found!")
            return []
        
        print(f"Found {len(magazines)} magazines")
        print(f"\nSelecting {article_count} random articles from different magazines...")
        
        articles = self.select_random_articles(magazines, article_count)
        
        if not articles:
            print("No articles found!")
            return []
        
        # Display articles
        print(f"\n📚 Selected Articles:")
        print(f"{'-' * 50}\n")
        
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article['title']}")
            print(f"   Magazine: {article['magazine']}")
            print(f"   Link: {article['link']}\n")
        
        # Archive to Gist if requested
        if archive:
            self.archiver.archive_articles(articles)
        
        return articles


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Articlay - News & Magazine Article Aggregator',
        epilog='Examples:\n'
               '  articlay                  # Show For You tab articles (default 5)\n'
               '  articlay --foryou         # Show For You tab articles\n'
               '  articlay --india          # Show India news articles\n'
               '  articlay --tamilnadu      # Show Tamil Nadu news articles\n'
               '  articlay random           # Show one random article\n'
               '  articlay --all            # Show all articles from today\n',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Random command
    random_parser = subparsers.add_parser('random', help='Display one random article')
    
    # Category filter arguments
    parser.add_argument(
        '--foryou',
        action='store_true',
        help='Show articles from "For You" tab'
    )
    
    parser.add_argument(
        '--india', '--indi',
        action='store_true',
        dest='india',
        help='Show articles from India news'
    )
    
    parser.add_argument(
        '--tamilnadu', '--tn',
        action='store_true',
        dest='tamilnadu',
        help='Show articles from Tamil Nadu news'
    )
    
    parser.add_argument(
        '--movie',
        action='store_true',
        help='Show articles from Movie category'
    )
    
    parser.add_argument(
        '--literature', '--lit',
        action='store_true',
        dest='literature',
        help='Show articles from Literature category'
    )
    
    parser.add_argument(
        '--writing',
        action='store_true',
        help='Show articles from Writing category'
    )
    
    parser.add_argument(
        '--reddit',
        action='store_true',
        help='Show articles from Reddit category'
    )
    
    parser.add_argument(
        '--codetech', '--tech',
        action='store_true',
        dest='codetech',
        help='Show articles from Code & Tech category'
    )
    
    parser.add_argument(
        '--artculture', '--art',
        action='store_true',
        dest='artculture',
        help='Show articles from Art & Culture category'
    )
    
    parser.add_argument(
        '--others',
        action='store_true',
        help='Show articles from Others category'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Show all articles from today'
    )
    
    # Number of articles to display
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=5,
        help='Number of articles to display (default: 5, use 0 for all)'
    )
    
    # Legacy Magzter scraper arguments
    parser.add_argument(
        '--magazines', '-m',
        type=int,
        choices=[10, 20, 30],
        help='[Legacy] Number of top magazines to consider'
    )
    
    parser.add_argument(
        '--articles', '-a',
        type=int,
        help='[Legacy] Number of articles to select'
    )
    
    parser.add_argument(
        '--no-archive',
        action='store_true',
        help='[Legacy] Skip archiving to GitHub Gist'
    )
    
    parser.add_argument(
        '--token', '-t',
        type=str,
        help='GitHub personal access token (or set GITHUB_TOKEN env var)'
    )
    
    parser.add_argument(
        '--gist-id', '-g',
        type=str,
        help='GitHub Gist ID containing articles (or set ARTICLAY_GIST_ID env var)'
    )
    
    args = parser.parse_args()
    
    # Get GitHub token from args or environment
    github_token = args.token or os.getenv('GITHUB_TOKEN')
    
    # Get Gist ID from args or environment
    gist_id = args.gist_id or os.getenv('ARTICLAY_GIST_ID') or os.getenv('GIST_ID')
    
    # Create application instance
    app = Articlay(github_token, gist_id=gist_id)
    
    # Handle random command
    if args.command == 'random':
        print("\n🎲 Fetching a random article...\n")
        articles = app.get_articles_by_category(limit=0)  # Get all articles
        if articles:
            random_article = random.choice(articles)
            app.display_articles_table([random_article])
        else:
            print("No articles available.")
        return 0
    
    # Check if using new tab-based interface
    category_flags = [
        ('foryou', 'For You'),
        ('india', 'India'),
        ('tamilnadu', 'Tamil Nadu'),
        ('movie', 'Movie'),
        ('literature', 'Literature'),
        ('writing', 'Writing'),
        ('reddit', 'Reddit'),
        ('codetech', 'Code & Tech'),
        ('artculture', 'Art & Culture'),
        ('others', 'Others'),
    ]
    
    selected_category = None
    for flag, category in category_flags:
        if getattr(args, flag, False):
            selected_category = category
            break
    
    # If --all flag is set or no specific category selected, show For You by default
    if args.all:
        articles = app.get_articles_by_category(limit=args.limit)
        app.display_articles_table(articles)
        return 0
    elif selected_category:
        articles = app.get_articles_by_category(category=selected_category, limit=args.limit)
        app.display_articles_table(articles, category=selected_category)
        return 0
    elif not args.magazines and not args.articles:
        # Default behavior: show one random article
        print("\n🎲 Fetching a random article...\n")
        articles = app.get_articles_by_category(limit=0)  # Get all articles
        if articles:
            random_article = random.choice(articles)
            app.display_articles_table([random_article])
        else:
            print("No articles available.")
        return 0
    
    # Legacy Magzter mode
    if args.magazines or args.articles:
        magazine_count = args.magazines or 10
        article_count = args.articles or 5
        
        articles = app.run(
            magazine_count=magazine_count,
            article_count=article_count,
            archive=not args.no_archive
        )
        
        # Save to local file as backup
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_file = f"articlay-{date_str}.json"
        
        with open(output_file, 'w') as f:
            json.dump(articles, f, indent=2)
        
        print(f"\n✓ Articles saved to: {output_file}")
        
        return 0 if articles else 1
    
    # Should not reach here
    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())
