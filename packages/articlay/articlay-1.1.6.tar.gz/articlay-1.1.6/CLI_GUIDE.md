# Articlay CLI Guide

Welcome to the Articlay command-line interface! This guide will help you get started with using Articlay to fetch and view curated news articles from various sources.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Commands](#commands)
- [Category Filters](#category-filters)
- [Options](#options)
- [Examples](#examples)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## Installation

### From PyPI (Recommended)

```bash
pip install articlay
```

### From Source

```bash
git clone https://github.com/pappater/articlay.git
cd articlay
pip install -r requirements.txt
pip install -e .
```

After installation, the `articlay` command will be available in your terminal.

## Quick Start

The simplest way to use Articlay is to just run it:

```bash
articlay
```

This will display 5 articles from the "For You" tab by default.

## Commands

### Default Command (Show Articles)

```bash
articlay [OPTIONS]
```

Displays articles from various news sources. By default, shows 5 articles from the "For You" category.

### Random Article

```bash
articlay random
```

Displays one random article from today's collection. Great for discovering new content!

## Category Filters

Articlay organizes articles into several categories. Use these flags to view articles from specific categories:

### For You
```bash
articlay --foryou
```

Curated selection of articles from various sources, tailored for a diverse reading experience.

### India News
```bash
articlay --india
# or
articlay --indi
```

Articles from major Indian news sources including The Hindu, Times of India, Indian Express, NDTV, Hindustan Times, and more.

### Tamil Nadu News
```bash
articlay --tamilnadu
# or
articlay --tn
```

Regional news from Tamil Nadu sources like Dinamalar, Dinamani, and Daily Thanthi.

### Movie
```bash
articlay --movie
```

Film reviews, interviews, and industry news from sources like Mubi, Letterboxd, RogerEbert.com, IndieWire, and more.

### Literature
```bash
articlay --literature
# or
articlay --lit
```

Book reviews, author interviews, and literary criticism from Literary Hub, Project Gutenberg, The Paris Review, and others.

### Writing
```bash
articlay --writing
```

Writing tips, author resources, and publishing advice from Writer's Digest, The Write Life, and more.

### Reddit
```bash
articlay --reddit
```

Popular posts from various subreddits including r/worldnews, r/india, r/programming, and more.

### Code & Tech
```bash
articlay --codetech
# or
articlay --tech
```

Technology news and programming articles from Dev.to, Hacker News, CSS-Tricks, and other tech sources.

### Art & Culture
```bash
articlay --artculture
# or
articlay --art
```

Art exhibitions, cultural commentary, and museum news from Colossal, Artnet, Smithsonian, and more.

### Others
```bash
articlay --others
```

Articles from miscellaneous categories including Business, Science, Sports, Health, Environment, and more.

## Options

### Limit Number of Articles

Control how many articles are displayed:

```bash
articlay --limit 10          # Show 10 articles
articlay -l 10               # Short form
articlay --india --limit 0   # Show ALL articles from India category
```

**Default:** 5 articles  
**Use 0** to display all available articles for the selected category.

### Show All Articles

Display all articles from today, regardless of category:

```bash
articlay --all
articlay --all --limit 20    # Show first 20 articles from all categories
```

### GitHub Token

If the Gist containing articles is private, provide your GitHub personal access token:

```bash
articlay --token YOUR_GITHUB_TOKEN
articlay -t YOUR_GITHUB_TOKEN

# Or set as environment variable
export GITHUB_TOKEN=YOUR_GITHUB_TOKEN
articlay
```

## Examples

### Basic Usage

```bash
# Show default For You articles
articlay

# Show 10 articles from India news
articlay --india --limit 10

# Get one random article
articlay random

# Show all Tamil Nadu articles
articlay --tamilnadu --limit 0

# Show 3 movie articles
articlay --movie -l 3
```

### Advanced Usage

```bash
# Show all available articles
articlay --all

# Show first 50 articles from all categories
articlay --all --limit 50

# Use short form flags
articlay --indi -l 10        # India news, 10 articles
articlay --tn -l 5           # Tamil Nadu news, 5 articles
articlay --lit --limit 8     # Literature, 8 articles
articlay --tech -l 15        # Tech news, 15 articles

# With authentication
export GITHUB_TOKEN=ghp_your_token_here
articlay --india
```

### Daily Workflow

```bash
# Morning routine: Check For You feed
articlay --foryou --limit 10

# Check India news during lunch
articlay --india

# Evening: Random discovery
articlay random

# Weekend: Explore literature and movies
articlay --literature --limit 10
articlay --movie --limit 10
```

## Configuration

### GitHub Gist Configuration

Articlay fetches articles from a GitHub Gist. The Gist ID is configured in `gist_config.py`:

```python
GIST_ID = "your_gist_id_here"
GIST_FILENAME = "magazine-articles.json"
```

### Environment Variables

- `GITHUB_TOKEN`: Your GitHub personal access token (needed for private Gists)

Set it in your shell:

```bash
# Bash/Zsh
export GITHUB_TOKEN=ghp_your_token_here

# Fish
set -x GITHUB_TOKEN ghp_your_token_here

# Windows Command Prompt
set GITHUB_TOKEN=ghp_your_token_here

# Windows PowerShell
$env:GITHUB_TOKEN="ghp_your_token_here"
```

Or add it to your shell configuration file (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
echo 'export GITHUB_TOKEN=ghp_your_token_here' >> ~/.bashrc
source ~/.bashrc
```

## Output Format

Articles are displayed in a clean, readable format:

```
📚 Articles in 'India' (5 total):
================================================================================

 1. Major policy changes announced by government
    Source: The Hindu | Category: India
    Link: https://www.thehindu.com/...

 2. Tech startup raises $50M in Series B funding
    Source: Economic Times | Category: India
    Link: https://economictimes.indiatimes.com/...

...
```

Each article shows:
- **Number**: Position in the list
- **Title**: Article headline (truncated if too long)
- **Source**: Publication or website name
- **Category**: Article category
- **Link**: Direct URL to the full article

## Features

### 🎲 Random Discovery
The `random` command is perfect for serendipitous content discovery. Each time you run it, you'll get a different article from the entire collection.

### 📊 Category Organization
Articles are automatically categorized, making it easy to find content that interests you.

### 🔢 Flexible Limits
Control exactly how many articles you want to see, from just 1 to all available.

### 🚀 Fast and Lightweight
Articlay is built with performance in mind. Article fetching and display is quick and efficient.

### 🌐 Multiple Sources
Content is aggregated from 100+ news sources, blogs, and content platforms worldwide.

## Troubleshooting

### "No Gist ID configured"

**Problem:** The Gist ID is not set in `gist_config.py`.

**Solution:** Check if `gist_config.py` exists and has the correct Gist ID:

```python
GIST_ID = "your_actual_gist_id"
```

### "Error fetching articles from Gist: 403 Forbidden"

**Problem:** The Gist is private and requires authentication.

**Solution:** Provide your GitHub token:

```bash
articlay --token YOUR_GITHUB_TOKEN
# or
export GITHUB_TOKEN=YOUR_GITHUB_TOKEN
articlay
```

### "No articles found"

**Problem:** No articles available for the selected category or date.

**Solutions:**
1. Try a different category: `articlay --foryou`
2. Check all categories: `articlay --all`
3. Verify the Gist has recent data
4. Try the random command: `articlay random`

### "Using articles from 2024-01-15 (today's articles not available)"

**Problem:** Today's articles haven't been scraped yet.

**Solution:** This is normal. The scraping happens automatically at 6:00 AM IST. The CLI will show the most recent date's articles instead.

## Legacy Magzter Mode

Articlay originally supported Magzter magazine scraping. This functionality is still available:

```bash
# Fetch from top 20 magazines, select 10 articles
articlay --magazines 20 --articles 10

# Skip GitHub Gist archiving
articlay --magazines 10 --articles 5 --no-archive
```

**Note:** This mode uses placeholder data as it requires Magzter authentication.

## Web Interface

Articlay also has a beautiful web interface available at:
https://pappater.github.io/articlay/

The web UI provides:
- Browse articles by date and category
- Real-time search
- Dark mode
- Statistics dashboard
- Responsive design for mobile/tablet

## Need Help?

- **Issues:** https://github.com/pappater/articlay/issues
- **Contributing:** See [CONTRIBUTING.md](CONTRIBUTING.md)
- **License:** MIT License

## Tips

1. **Alias for convenience:** Add to your shell config:
   ```bash
   alias news='articlay --india'
   alias rando='articlay random'
   ```

2. **Daily habit:** Use `articlay` in your morning routine to stay informed.

3. **Discover new sources:** The `--all` flag is great for exploring content from sources you might not usually read.

4. **Focus your reading:** Use specific category flags to avoid information overload.

5. **Save interesting articles:** Pipe output to a file:
   ```bash
   articlay --india --limit 0 > india_news.txt
   ```

## Version

Current version: 1.0.0

Check for updates regularly and visit the GitHub repository for the latest features!

---

Happy reading! 📰
