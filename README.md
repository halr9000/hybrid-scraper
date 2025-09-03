# Hybrid Page Scraper

Human does the navigation, script does the content extraction.
Perfect for sites with JavaScript routing issues.

## Features

- Visible Chrome browser you control manually
- Capture current page, semi-auto capture, or true auto capture on navigation
- Converts page content to Markdown using `html2text`
- Optional raw HTML debug output

## Requirements

- Python 3.10+
- Google Chrome installed

The script uses these Python packages:
- `selenium`
- `webdriver-manager`
- `beautifulsoup4`
- `html2text`

## Installation

Use any of the following options.

### Option A: pip + virtualenv (recommended)

```bash
python -m venv .venv
.venv\\Scripts\\Activate.ps1  # Windows PowerShell
pip install -r requirements.txt
```

### Option B: uv (fast Python package manager)

```bash
# Create and activate project venv
uv venv
.venv\\Scripts\\Activate.ps1

# Install deps from requirements.txt
uv pip install -r requirements.txt

# (optional) Run through uv
uv run python hybrid-scraper.py
```

### Option C: uvx quick run (no local venv)

Runs in an ephemeral environment with required packages.

```bash
uvx \
  --with selenium \
  --with webdriver-manager \
  --with beautifulsoup4 \
  --with html2text \
  python hybrid-scraper.py --url "https://example.com"
```

## Usage

Basic run (interactive prompts):
```bash
python hybrid-scraper.py
```

Start at a specific URL:
```bash
python hybrid-scraper.py --url "https://example.com"
```

Choose output directory (default is `output/`):
```bash
# Use default: saves to output/<domain>/
python hybrid-scraper.py

# Custom folder (e.g., scraped/): saves to scraped/<domain>/
python hybrid-scraper.py --output-dir scraped

# Combine with other options
python hybrid-scraper.py --url "https://example.com" --watch --debug-html --output-dir scraped
```

Also save raw HTML next to Markdown:
```bash
python hybrid-scraper.py --debug-html
```

Start directly in true auto-capture watch mode:
```bash
python hybrid-scraper.py --watch
```
You can combine with a starting URL:
```bash
python hybrid-scraper.py --watch --url "https://example.com"
```

## Commands (inside the app)

- `capture` (or `c`) – Capture current page content
- `auto` (or `a`) – Semi-auto: press Enter to capture each page while you navigate
- `watch` (or `w`) – True auto: capture automatically on navigation change (Ctrl+C to stop)
- `help` (or `h`) – Show help
- `quit` (or `q`) – Exit

## Output

- By default, files are saved to `output/<domain>/` in the current working directory
- Markdown filenames are based on the page title (sanitized)
- Optional debug HTML is saved alongside the Markdown when `--debug-html` is enabled
- Use `--output-dir <folder>` to change the parent output directory (e.g., `scraped/<domain>/`)

## VS Code Debugging

This repo includes a `.vscode/launch.json` with:
- "Run hybrid-scraper" – runs the script normally
- "Run with URL" – lets you type or set a starting URL

You can edit arguments in the debug configuration to set `--url` and `--debug-html`.

## Notes

- ChromeDriver is auto-managed by `webdriver-manager`.
- If Chrome auto-updates and you hit driver mismatch issues, rerun and it will re-download.
