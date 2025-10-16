# Changelog

All notable changes to the Articlay project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-10-14

### Added
- **CLI Category Filters**: New command-line flags to view articles by category
  - `--foryou` - Curated selection from all sources
  - `--india` / `--indi` - India news
  - `--tamilnadu` / `--tn` - Tamil Nadu news
  - `--movie` - Movie reviews and film news
  - `--literature` / `--lit` - Literature and books
  - `--writing` - Writing tips and resources
  - `--reddit` - Popular Reddit posts
  - `--codetech` / `--tech` - Technology and programming
  - `--artculture` / `--art` - Art and culture
  - `--others` - All other categories
  - `--all` - Show all articles from today

- **Random Article Command**: New `articlay random` command to display one random article for serendipitous discovery

- **Article Limit Control**: New `--limit` / `-l` option to control how many articles are displayed (default: 5, use 0 for all)

- **CLI Guide Modal in UI**: Added a 💻 button in the web interface header that opens a comprehensive modal with:
  - Installation instructions (pip and from source)
  - Quick start guide
  - Feature highlights with code examples
  - All available category filters
  - Configuration instructions
  - Link to full CLI documentation

- **Comprehensive CLI Documentation**: Created `CLI_GUIDE.md` with detailed documentation including:
  - Installation methods
  - Command reference
  - Category filters
  - Usage examples
  - Configuration guide
  - Troubleshooting section
  - Tips and best practices

### Changed
- Updated `README.md` with CLI usage section and examples
- Enhanced package description in `setup.py` to reflect CLI capabilities
- Version bumped to 1.1.0

### Technical Details
- Added `fetch_gist_articles()` method to fetch articles from GitHub Gist
- Added `get_articles_by_category()` method to filter articles by category
- Added `display_articles_table()` method for formatted article display
- Improved error messages for Gist authentication issues
- Maintained backward compatibility with legacy Magzter mode

## [1.0.0] - 2024-01-15

### Added
- Initial release with web scraping from 100+ news sources
- GitHub Gist integration for article storage
- Beautiful web UI with responsive design
- Category organization (India, Tamil Nadu, Movie, Literature, etc.)
- Dark mode support
- Search functionality
- Daily automation via GitHub Actions
- IST timezone support

### Features
- Aggregates articles from 35+ reputable sources
- Deduplication to avoid duplicate content
- One article per source per day
- Date-wise article organization
- Statistics dashboard
- Touch gesture support for mobile

[1.1.0]: https://github.com/pappater/articlay/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/pappater/articlay/releases/tag/v1.0.0
