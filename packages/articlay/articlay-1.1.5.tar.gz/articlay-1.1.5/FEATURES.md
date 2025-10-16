# Articlay Features Guide

This document provides detailed information about all the features available in Articlay.

## Table of Contents
- [News Aggregation](#news-aggregation)
- [Wikipedia & Special Content](#wikipedia--special-content)
- [User Interface Features](#user-interface-features)
- [Weather Widget](#weather-widget)
- [Search & Filter](#search--filter)
- [Dark Mode](#dark-mode)
- [Statistics Dashboard](#statistics-dashboard)

## News Aggregation

### Multi-Source News Fetching
Articlay fetches articles from 35+ reputable news sources across the globe:

- **International News**: BBC, CNN, Reuters, Al Jazeera, NPR, Time, The Atlantic
- **Indian News**: The Hindu, Times of India, Indian Express, NDTV, Hindustan Times, Zee News, India Today, DD News
- **Regional News**: Dinamalar, Dinamani, Daily Thanthi (Tamil Nadu)
- **Business**: Forbes, The Economist, Bloomberg
- **Technology**: Wired
- **Science**: National Geographic, Scientific American, Popular Science, New Scientist, Nature
- **Culture**: The New Yorker, Smithsonian Magazine

### Intelligent Deduplication
- Automatically removes duplicate articles based on title similarity
- Ensures unique content across different sources
- Maintains article quality by selecting the best version

### Category Organization
Articles are automatically categorized into:
- 🌍 World News
- 🇮🇳 India News
- 🏛️ Tamil Nadu News
- 💼 Business
- 💻 Technology
- 🔬 Science
- 🎨 Culture
- 📚 Wikipedia
- 💡 Inspiration

### IST Timezone Support
- All dates and times are in Indian Standard Time (IST/UTC+5:30)
- Accurate "Today" marker in the date selector
- Ensures consistency for Indian users

## Wikipedia & Special Content

### Wikipedia Article of the Day
- Fetches Wikipedia's featured article
- Displays full content (400+ characters)
- Direct link to read more on Wikipedia
- Updated daily

### Wikipedia Picture of the Day
- High-quality image from Wikimedia Commons
- Includes description and context
- Changes daily with new stunning photography

### Random Wikipedia Article
- Discover something new every visit
- Random article with title and summary
- Great for learning and exploration

### Wikiquote Quote of the Day
- Inspiring quote from Wikiquote
- Changes daily
- Includes author attribution

### On This Day in History
- Historical events that occurred on the current date
- Multiple events listed chronologically
- Direct link to Wikipedia for more details

### Daily Inspirational Quotes
- Quotes from multiple sources
- Motivational and thought-provoking content
- Fallback to curated quotes if API is unavailable

## User Interface Features

### Clean & Modern Design
- Minimalistic interface focusing on content
- Card-based layout for easy scanning
- Gradient headers for category sections
- Smooth animations and transitions

### Responsive Design
Works perfectly on:
- Desktop computers (1200px+)
- Tablets (768px - 1199px)
- Mobile phones (< 768px)

### Date Selection
- Shows current date's articles
- All times in Indian Standard Time (IST)
- Optimized for current day's content

### Article Cards
Each article card displays:
- Source name (styled as a badge)
- Article title (bold, clear)
- Description/excerpt (truncated for readability)
- Images (for Wikipedia Picture of the Day)
- Click to open in new tab

### Category Sections
- Collapsible sections by category
- Icon-based identification
- Grid layout for multiple articles
- Automatic sorting by importance

## Weather Widget

### Features
- Real-time weather data using Open-Meteo API
- No API key required (free service)
- Location search by city name
- Displays:
  - Current weather condition with emoji
  - Temperature in Celsius
  - Humidity percentage
  - Wind speed in km/h
  - City name and country

### How to Use
1. Enter a city name (e.g., Mumbai, Chennai, Delhi, London, New York)
2. Click "Get Weather"
3. Weather information loads within seconds
4. Default location: Mumbai

### Supported Locations
- Works worldwide
- Supports major cities and towns
- Intelligent geocoding to find closest match

## Search & Filter

### Real-Time Search
- Instant filtering as you type
- No need to press Enter
- Case-insensitive matching
- Clears automatically when changing dates

### Search Scope
Search works across:
- Article titles
- Article descriptions
- Source names
- Category names

### How to Use
1. Type in the search box at the top
2. Results filter automatically
3. Maintains category organization
4. Clear search box to show all articles

### Examples
- Search "climate" to find all climate-related articles
- Search "India" to filter Indian news
- Search "BBC" to see only BBC articles
- Search "technology" for tech news

## Dark Mode

### Features
- Toggle between light and dark themes
- Smooth transition animations
- Persistent preference (saved in localStorage)
- Applies to all UI elements
- Easy-to-spot toggle button

### Theme Colors

**Light Mode:**
- Background: #f5f5f5
- Text: #333
- Cards: white

**Dark Mode:**
- Background: #1a1a1a
- Text: #e0e0e0
- Cards: #2a2a2a

### How to Use
1. Click the theme toggle button in the header
2. Theme changes instantly
3. Preference is saved automatically
4. Persists across page reloads and visits

## Statistics Dashboard

### Summary Banner
Displays at the top of articles showing:
- **Total Articles**: Number of articles for the day
- **Total Sources**: Number of news sources fetched
- **Categories**: Number of active categories

### Visual Design
- Gradient background (purple)
- Large numbers for easy reading
- Grid layout for organized display
- Responsive on all devices

### Updates
- Recalculates when date changes
- Updates when search filters are applied
- Always accurate and current

## Data Storage

### GitHub Gist Integration
- Current date's articles stored in a public Gist
- JSON format for easy access
- Organized by date (YYYY-MM-DD)
- Accessible via GitHub API
- Optimized for performance with minimal data size (~386KB vs potential 11+MB accumulation)

### Daily Updates
- Automated scraping at 6:00 AM IST
- GitHub Actions workflow
- Graceful handling of failed scrapers
- Comprehensive logging
- Only current date's articles stored to prevent JSON bloat and maintain fast performance

## API & Integrations

### Open-Meteo Weather API
- Free weather data service
- No authentication required
- Global coverage
- Reliable and fast

### GitHub Gist API
- Store current date's article data
- Public access for transparency
- Optimized for fast loading

### RSS Feeds
All news sources use RSS feeds for:
- Reliable content delivery
- Consistent data format
- Real-time updates
- Standard metadata (title, description, link, date)

## Performance & Optimization

### Frontend Optimization
- Minimal JavaScript dependencies
- Efficient DOM manipulation
- CSS animations (hardware accelerated)
- Local storage for theme preference

### Backend Optimization
- Parallel scraping where possible
- Timeout handling for slow sources
- Error recovery and logging
- Deduplication for efficiency

### Caching
- Browser caching for static assets
- GitHub Gist caching via API
- Local storage for user preferences

## Accessibility

### Keyboard Navigation
- Tab through all interactive elements
- Enter to activate buttons
- Focus indicators visible

### Screen Readers
- Semantic HTML structure
- ARIA labels where needed
- Descriptive link text

### Visual Accessibility
- High contrast in both themes
- Readable font sizes
- Clear visual hierarchy
- Icons complement text (not replace)

## Browser Compatibility

### Supported Browsers
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Opera (latest)

### Required Features
- ES6 JavaScript support
- CSS Grid and Flexbox
- Local Storage
- Fetch API

## Future Enhancements

Potential features for future releases:
- Email notifications for new articles
- RSS feed generation
- Article bookmarking
- Category filters
- Export to PDF/CSV
- Article reading time estimation
- Share on social media
- Custom news source selection
- Multi-language support
- Article sentiment analysis

## Troubleshooting

### Articles Not Loading
- Check internet connection
- Verify Gist is accessible
- Check browser console for errors
- Try refreshing the page

### Weather Not Working
- Verify city name spelling
- Try a major city first
- Check browser console for API errors
- Ensure internet connectivity

### Dark Mode Not Persisting
- Check if cookies/localStorage are enabled
- Try clearing browser cache
- Re-toggle the theme

### Search Not Working
- Clear the search box and try again
- Ensure you have articles loaded
- Check if date has articles available

## Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check existing issues first
- Provide detailed description
- Include browser and OS information

## Credits

### APIs & Services Used
- Open-Meteo API for weather data
- GitHub Gist API for data storage
- Wikipedia/Wikimedia APIs for special content
- Various RSS feeds for news content

### Technologies
- HTML5, CSS3, JavaScript (ES6+)
- Python 3.7+ for scrapers
- BeautifulSoup4 for parsing
- GitHub Actions for automation
- GitHub Pages for hosting
