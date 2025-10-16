# Articlay Setup Guide

This guide will help you set up Articlay to run on your own GitHub repository.

## Prerequisites

- A GitHub account
- Basic knowledge of GitHub Actions and GitHub Pages

## Step-by-Step Setup

### 1. Fork the Repository

1. Go to https://github.com/pappater/articlay
2. Click the "Fork" button in the top right
3. Wait for the fork to complete

### 2. Create a GitHub Gist

1. Go to https://gist.github.com/
2. Click "Create new gist"
3. Set filename to `magazine-articles.json`
4. Add initial content: `{}`
5. Click "Create public gist"
6. Copy the Gist ID from the URL (e.g., if URL is `https://gist.github.com/username/abc123`, the ID is `abc123`)

### 3. Update Configuration Files

#### Update `gist_config.py`

```python
GIST_ID = "abc123def456"  # Replace with your actual Gist ID
GIST_FILENAME = "magazine-articles.json"
```

#### Update `docs/index.html`

Find these lines and update the GIST_ID:

```javascript
const GIST_ID = "abc123def456";  // Replace with your actual Gist ID
const GIST_FILENAME = "magazine-articles.json";
```

### 4. Create GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a descriptive name like "Articlay Gist Access"
4. Select the `gist` scope
5. Click "Generate token"
6. **Important**: Copy the token immediately (you won't see it again!)

### 5. Add Token as Repository Secret

1. Go to your forked repository
2. Click Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `GIST_TOKEN`
5. Value: Paste the token you copied
6. Click "Add secret"

### 6. Enable GitHub Pages

1. Go to repository Settings → Pages
2. Under "Build and deployment":
   - Source: "Deploy from a branch"
   - Branch: `main`
   - Folder: `/docs`
3. Click "Save"
4. Wait a few minutes for the site to deploy
5. Your site will be available at: `https://yourusername.github.io/articlay/`

### 7. Enable GitHub Actions

1. Go to the Actions tab in your repository
2. If prompted, click "I understand my workflows, go ahead and enable them"
3. The workflows are now enabled and will run automatically

### 8. Test the Setup

#### Manual Test

1. Go to Actions tab
2. Click "Daily Magazine Scraper to Gist" workflow
3. Click "Run workflow" → "Run workflow"
4. Wait for it to complete
5. Check your Gist - it should have today's articles
6. Visit your GitHub Pages site - you should see the articles

#### Verify Automatic Schedule

The workflow is scheduled to run daily at 6:00 AM IST (00:30 UTC). After the first automatic run:

1. Check the Actions tab for the scheduled run
2. Verify articles are added to the Gist
3. Confirm the UI displays the new articles

## Customization

### Change Schedule Time

Edit `.github/workflows/daily-gist.yml`:

```yaml
on:
  schedule:
    - cron: '30 0 * * *'  # 6:00 AM IST (00:30 UTC)
```

To change the time, modify the cron expression. Use https://crontab.guru/ for help.

### Add/Remove News Sources

Edit `daily_gist_job.py` and modify the `SCRAPERS` list:

```python
SCRAPERS = [
    ("source_scraper", "fetch_source_articles"),
    # Add your scrapers here
]
```

To add a new scraper:

1. **Create the scraper file**: `scrapers/newsource_scraper.py`

2. **Implement the fetch function**:
   ```python
   import requests
   from bs4 import BeautifulSoup
   from typing import List, Dict

   RSS_URL = "https://example.com/rss"

   def fetch_newsource_articles(limit: int = 5) -> List[Dict]:
       """Fetch latest articles from News Source RSS feed."""
       articles = []
       try:
           resp = requests.get(RSS_URL, timeout=10)
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
                   "category": "World"  # Choose appropriate category
               })
       except Exception as e:
           print(f"Error fetching News Source articles: {e}")
       return articles
   ```

3. **Add to SCRAPERS list** in `daily_gist_job.py`:
   ```python
   SCRAPERS = [
       # ... existing scrapers ...
       ("newsource_scraper", "fetch_newsource_articles"),
   ]
   ```

The scraper will be automatically imported and called during the daily run.

### Customize UI

Edit `docs/index.html` to:
- Change colors in the `<style>` section
- Modify category icons in `categoryIcons` object
- Adjust layout and design

## Troubleshooting

### No Articles Appearing

1. Check Actions tab for failed workflows
2. Verify GIST_TOKEN secret is set correctly
3. Check that Gist ID is correct in both config files
4. Look at workflow logs for specific errors

### UI Not Loading

1. Verify GitHub Pages is enabled and deployed from `/docs` folder
2. Check that GIST_ID in `docs/index.html` matches your Gist
3. Make sure the Gist is public
4. Clear browser cache and reload

### Scrapers Failing

Some scrapers may fail due to:
- RSS feed changes by the source
- Network restrictions
- Rate limiting

This is normal - the system is designed to skip failed scrapers gracefully. Check the workflow logs to see which scrapers succeeded.

## Maintenance

### Monitoring

- Check Actions tab weekly for workflow status
- Review Gist size (GitHub limits Gists to 100MB)
- Monitor scraper success rate in workflow logs

### Updates

- Pull latest changes from upstream repository periodically
- Test new scrapers before deploying
- Back up your Gist data regularly

## Support

For issues or questions:
1. Check existing GitHub Issues
2. Open a new issue with:
   - Description of the problem
   - Relevant logs from Actions
   - Configuration details (without exposing tokens!)

## Security Notes

- **Never commit your GitHub token** to the repository
- Keep tokens in GitHub Secrets only
- Regularly rotate your access tokens
- Use tokens with minimal required permissions (gist scope only)

## License

This project is licensed under the MIT License. See LICENSE file for details.
