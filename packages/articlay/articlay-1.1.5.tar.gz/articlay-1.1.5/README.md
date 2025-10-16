# Articlay 📰

[![PyPI version](https://badge.fury.io/py/articlay.svg)](https://badge.fury.io/py/articlay)
[![Python](https://img.shields.io/pypi/pyversions/articlay.svg)](https://pypi.org/project/articlay/)
[![Downloads](https://pepy.tech/badge/articlay)](https://pepy.tech/project/articlay)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive news aggregator that fetches articles from popular magazines and news sources worldwide, including India and Tamil Nadu, and presents them in a beautiful, minimalistic UI.

**✨ Zero Configuration CLI** - Install and use immediately with `pip install articlay`!

## Features

### News Aggregation
- 🌍 **Global Coverage**: Fetches from 35+ news sources including Reuters, Forbes, The Economist, Wired, Nature, BBC, CNN, Al Jazeera, and more
- 🇮🇳 **Indian News**: Includes The Hindu, Times of India, Indian Express, NDTV, Hindustan Times, Zee News, India Today, DD News
- 🏛️ **Tamil Nadu News**: Features Dinamalar, Dinamani, Daily Thanthi
- 🎬 **Movie & Film**: Mubi, Letterboxd, RogerEbert.com, IndieWire, Criterion Collection, Film Companion, Filmfare, Variety
- 📚 **Literature**: Literary Hub, Project Gutenberg, The Paris Review, Granta, New Yorker Books, Hindu Literary Review
- ✍️ **Writing**: Medium, Substack, Wattpad, Electric Literature, Poets.org, Reddit r/writing
- 📂 **Categorized Articles**: Organized by World, India, Tamil Nadu, Movie, Literature, Writing, Reddit, Business, Technology, Science, Culture, and more
- ⚡ **Frequent Updates**: Runs automatically every 15 minutes
- 🔄 **Deduplication**: Intelligent article deduplication to prevent duplicates across sources
- 🎯 **One Article Per Source**: Displays one unique article from each news source per update

### Wikipedia & Special Content
- 📚 **Wikipedia Article of the Day**: Featured article with full content
- 🖼️ **Wikipedia Picture of the Day**: Beautiful daily images from Wikimedia Commons
- 📜 **Wikipedia Quote of the Day**: Inspiring quotes from Wikiquote
- 🎲 **Random Wikipedia Article**: Discover something new every day
- 📅 **On This Day in History**: Historical events that happened on the current date
- 💡 **Daily Quotes**: Inspirational quotes from multiple sources

### User Interface
- 🌐 **GitHub Pages UI**: Beautiful, minimalistic interface to browse today's articles
- 🎨 **1970s Retro Design**: Bold red Courier New header with vintage text shadow effects
- 🌈 **Retro Article Highlights**: Colorful gradient left border appears on hover for a vintage magazine feel
- 🎭 **Easter Egg**: Jean-Michel Basquiat-style art revealed when scrolling to bottom (footer fades away)
- 👆 **Touch Gestures**: Swipe left/right to switch between tabs (no refresh), pull down to refresh
- 🌓 **Dark Mode**: Toggle between light and dark themes with localStorage persistence
- 🔍 **Powerful Search**: Real-time search by keywords or source names (e.g., "forbes", "technology", "climate")
  - Search across all fields or filter by source name, title, description, or category
  - Case-insensitive with instant results as you type
  - Clear search to return to all articles
- 📊 **Statistics Dashboard**: View article counts, sources, and categories at a glance
- 📱 **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- 🕐 **IST Timezone**: All times and dates use Indian Standard Time

### Data Management
- 💾 **Gist Storage**: Stores current date's article data (title, description, link, publish date, category) to GitHub Gist
- 🎯 **Current Date Focus**: Only keeps today's articles to maintain optimal performance (keeps JSON ~386KB instead of accumulating to 11+MB over time)

## Installation

### Prerequisites

- Python 3.7 or higher
- GitHub Personal Access Token (for Gist archiving)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/pappater/articlay.git
cd articlay
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your GitHub token (for Gist archiving):
```bash
export GITHUB_TOKEN="your_github_personal_access_token"
```

Or create a `.env` file:
```
GITHUB_TOKEN=your_github_personal_access_token
```

## Usage

### Daily Automation (Recommended)

The repository is configured to automatically fetch articles every day at **6:00 AM IST** via GitHub Actions. The scraped articles are:
1. Stored in a GitHub Gist
2. Displayed on the [live UI](https://pappater.github.io/articlay/)

No manual intervention is required!

### Command-Line Interface (CLI)

Articlay provides a powerful CLI for viewing articles right in your terminal.

✨ **Zero Configuration Required!** The CLI works immediately after installation with no setup needed.

#### Installation

Install from PyPI (recommended):
```bash
pip install articlay
```

That's it! No configuration, no Gist ID, no setup. Just install and use.

Or install from source:
```bash
git clone https://github.com/pappater/articlay.git
cd articlay
pip install -e .
```

#### Quick Start (No Setup Needed!)

```bash
# Install and use immediately
pip install articlay

# Show all articles
articlay --all

# Show India news
articlay --india --limit 10

# Get one random article
articlay random

# Show Tamil Nadu news
articlay --tamilnadu --limit 5

# Show tech articles
articlay --codetech -l 15
```

✅ **Works out of the box** - No Gist ID or environment variables needed!  
✅ **Same content as web UI** - Access all articles from the terminal  
✅ **Perfect for developers** - Fast, lightweight, and scriptable

#### Available Category Flags

- `--foryou` - Curated selection from all sources
- `--india` or `--indi` - India news
- `--tamilnadu` or `--tn` - Tamil Nadu news
- `--movie` - Movie reviews and film news
- `--literature` or `--lit` - Literature and books
- `--writing` - Writing tips and author resources
- `--reddit` - Popular Reddit posts
- `--codetech` or `--tech` - Technology and programming
- `--artculture` or `--art` - Art exhibitions and culture
- `--others` - All other categories
- `--all` - Show all articles from today

#### Examples

```bash
# View help
articlay --help

# Show specific category with limit
articlay --india --limit 10
articlay --movie -l 5

# Random article discovery
articlay random

# Show all available articles
articlay --all --limit 0
```

#### Advanced Configuration (Optional)

**Note:** Configuration is NOT required for normal use! Only needed for advanced scenarios.

```bash
# Use your own Gist ID (optional)
export ARTICLAY_GIST_ID="your_gist_id"
articlay --all

# Use a private Gist (optional)
export GITHUB_TOKEN="your_token"
articlay --india

# Or pass Gist ID as argument (optional)
articlay --gist-id your_gist_id --all
```

For complete CLI documentation, see [CLI_GUIDE.md](CLI_GUIDE.md).

### Manual Scraper Execution

To manually run the article scraper:

```bash
# Set your GitHub token (required for Gist storage)
export GITHUB_TOKEN="your_github_token_here"

# Run the daily scraper
python daily_gist_job.py
```

This will:
- Fetch articles from all configured news sources
- Store them in the configured GitHub Gist
- Organize them by date and category

### Legacy Magzter Tool

The original `articlay.py` tool for Magzter is still available:

```bash
# Basic usage (uses placeholder data)
python articlay.py --magazines 20 --articles 10
```

## Output

The tool generates two types of output:

1. **Console Output**: Displays selected articles with titles, magazine names, and links
2. **JSON File**: Saves articles locally as `articlay-YYYY-MM-DD.json`
3. **GitHub Gist**: Archives articles as markdown to a public Gist (if enabled)

### Example Output

```
📰 Articlay - Magzter Article Aggregator
==================================================

Fetching top 10 popular magazines...
Found 10 magazines

Selecting 5 random articles from different magazines...

📚 Selected Articles:
--------------------------------------------------

1. Magazine 1 - Article 3
   Magazine: Magazine 1
   Link: https://www.magzter.com/magazine-1/article-3

2. Magazine 5 - Article 2
   Magazine: Magazine 5
   Link: https://www.magzter.com/magazine-5/article-2

...

✓ Archived to Gist: https://gist.github.com/...
✓ Articles saved to: articlay-2024-01-15.json
```

## Setup for Your Own Instance

If you want to run Articlay on your own repository:

1. **Fork the repository**

2. **Create a GitHub Gist**
   - Go to https://gist.github.com/
   - Create a new gist with filename `magazine-articles.json`
   - Initialize it with `{}`
   - Copy the Gist ID from the URL

3. **Update Configuration**
   - Edit `gist_config.py` with your Gist ID
   - Edit `docs/index.html` to update the `GIST_ID` constant

4. **Set up GitHub Token**
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate a new token with `gist` scope
   - Add it as a repository secret named `GIST_TOKEN`

5. **Enable GitHub Pages**
   - Go to repository Settings → Pages
   - Source: Deploy from a branch
   - Branch: main, folder: /docs
   - Save

6. **Enable GitHub Actions**
   - The workflows will run automatically
   - Articles will be fetched daily at 6 AM IST

## Requirements

See `requirements.txt`:
- requests>=2.31.0
- beautifulsoup4>=4.12.0
- lxml>=4.9.0

## Live Demo

Visit the live UI: [https://pappater.github.io/articlay/](https://pappater.github.io/articlay/)

Browse daily articles in a clean, minimalistic interface organized by category.

## News Sources

### World News (7 sources)
- Reuters, Time, The Atlantic, NPR, BBC, CNN, Al Jazeera

### Business & Economics (3 sources)
- Forbes, The Economist, Bloomberg

### Technology (1 source)
- Wired

### Science & Nature (5 sources)
- National Geographic, Scientific American, Popular Science, New Scientist, Nature

### Culture (2 sources)
- The New Yorker, Smithsonian Magazine

### India (8 sources)
- The Hindu, Times of India, Indian Express, NDTV, Hindustan Times, Zee News, India Today, DD News

### Tamil Nadu (3 sources)
- Dinamalar, Dinamani, Daily Thanthi

### Wikipedia & Special Content (6 sources)
- Wikipedia Article of the Day
- Wikipedia Picture of the Day
- Random Wikipedia Article
- Wikiquote Quote of the Day
- On This Day in History
- Daily Inspirational Quotes

**Total: 35+ sources across 9 categories**

## Automation

Articles are automatically scraped and stored **every 15 minutes** via GitHub Actions. Non-working scrapers are gracefully skipped.

**Note**: The 15-minute schedule is aggressive and may cause rate limiting with some sources. Monitor the GitHub Actions logs and adjust the schedule in `.github/workflows/daily-gist.yml` if needed (e.g., change to `0 */1 * * *` for hourly updates).

## Scraper Status

For tracking which scrapers are working and which need attention, see [SCRAPER_STATUS.md](SCRAPER_STATUS.md). This document helps identify:
- Newly added scrapers pending production testing
- Known issues with specific scrapers
- Alternative sources when scrapers fail
- Testing instructions for individual scrapers

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.