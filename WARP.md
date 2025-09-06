# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Hybrid Page Scraper is a Python tool that combines manual navigation with automated content capture. It opens a real Chrome browser for human navigation while providing programmatic content extraction and markdown conversion.

### Core Architecture

- **Single-module design**: Primary logic in `hybrid_scraper.py` (584 lines)
- **Selenium-based**: Uses Chrome WebDriver for browser automation
- **Content pipeline**: HTML → BeautifulSoup → html2text → Markdown with metadata headers
- **Three operational modes**: Interactive, semi-auto, and watch mode with auto-capture

### Key Components

1. **ScraperConfig**: Centralized configuration for browser settings, content processing, and timing parameters
2. **HybridScraper**: Main orchestrator class handling browser lifecycle, content extraction, and file operations
3. **Content processing pipeline**: Configurable selectors for unwanted element removal and main content extraction
4. **File management**: Domain-based output organization with safe filename sanitization

## Development Commands

### Environment Setup

Clone the repository, then:
```powershell
# Create virtual environment and install dependencies (uv > pip)
uv sync
```

### Running the Application
```powershell

# Run as module
python -m hybrid_scraper --watch

# Run from github
uvx --from git+https://github.com/halr9000/hybrid-scraper hybrid-scraper
```

### Available CLI Options
- `--url URL`: Starting URL to open
- `--watch`: Auto-capture mode (recommended)
- `--debug-html`: Save raw HTML alongside markdown
- `--output-dir DIR`: Custom output directory (default: `output`)
- `--verbose`: Show Chrome/Driver logs

### Testing the Build
```powershell
# Test console script installation
python -m hybrid-scraper --help
```

## Architecture Deep Dive

### Browser Management
- **ChromeDriver caching**: Uses `@lru_cache` to avoid repeated downloads
- **Session lifecycle**: Comprehensive error handling for browser close/crash scenarios
- **Logging control**: Configurable verbosity for Chrome/Selenium noise reduction

### Content Extraction Strategy
The scraper uses a two-phase approach:
1. **Element removal**: Strips navigation, ads, scripts using configurable CSS selectors
2. **Main content detection**: Progressive fallback through semantic selectors (`main`, `[role="main"]`, `#content`, etc.)

### File Organization
```
output/
└── <domain>/
    ├── <page-title>.md          # Processed markdown
    └── debug-<page-title>.html  # Raw HTML (if --debug-html)
```

### Watch Mode Implementation
- **Debouncing**: Waits for URL stability (default: 1.5s) to avoid partial captures
- **Cooldown logic**: Prevents duplicate captures of the same URL within configurable timeframe
- **Ready state checking**: Ensures DOM completion before capture

### Error Handling Philosophy
- **Graceful degradation**: Browser crashes don't terminate the program
- **User-friendly errors**: Selenium stacktraces are condensed to essential information
- **Session recovery**: Browser state is validated before each operation

## Configuration Points

Key configuration values in `ScraperConfig`:
- **Timing**: `default_debounce_seconds` (1.5s), `default_same_url_cooldown` (10s)
- **Content**: `unwanted_selectors`, `main_content_selectors` arrays
- **Files**: `max_filename_length` (100 chars), `content_preview_lines` (10)

## Development Notes

- **Windows-specific**: Uses PowerShell commands and Windows path conventions
- **Chrome dependency**: Requires Google Chrome installation
- **uvx compatibility**: Supports direct execution via `uvx --from git+https://github.com/halr9000/hybrid-scraper`
- **Package management**: Uses modern uv workflow with pyproject.toml as single source of truth

## Output Format

Generated markdown includes structured metadata header:
```markdown
# <Page Title>

*Source: <URL>*
*Scraped on: <timestamp>*
*Content length: <chars> characters*
*Meta description: <description>* (if available)

---

<converted content>
```
