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
uv run python -m hybrid_scraper
```

### Option C: uvx quick run (no local venv)

Run directly from GitHub via console script (ephemeral env):

```bash
uvx --from git+https://github.com/halr9000/hybrid-scraper.git \
  hybrid-scraper --url "https://example.com"
```

## Usage

Basic run (interactive prompts):
```bash
python -m hybrid_scraper
```

Start at a specific URL:
```bash
python -m hybrid_scraper --url "https://example.com"
```

Run directly via uvx from GitHub (no clone):
```bash
# Latest default branch
uvx --from git+https://github.com/halr9000/hybrid-scraper.git hybrid-scraper --url "https://example.com"

# Pin a tag or branch
uvx --from git+https://github.com/halr9000/hybrid-scraper.git@v0.1.0 hybrid-scraper
uvx --from git+https://github.com/halr9000/hybrid-scraper.git@main hybrid-scraper

# Pin a specific commit
uvx --from git+https://github.com/halr9000/hybrid-scraper.git@<commit-sha> hybrid-scraper

# Change output directory, enable debug HTML, or watch mode
uvx --from git+https://github.com/halr9000/hybrid-scraper.git \
  hybrid-scraper --output-dir scraped --debug-html --watch
```

Choose output directory (default is `output/`):
```bash
# Use default: saves to output/<domain>/
python -m hybrid_scraper

# Custom folder (e.g., scraped/): saves to scraped/<domain>/
python -m hybrid_scraper --output-dir scraped

# Combine with other options
python -m hybrid_scraper --url "https://example.com" --watch --debug-html --output-dir scraped
```

Also save raw HTML next to Markdown:
```bash
python -m hybrid_scraper --debug-html
```

Start directly in true auto-capture watch mode:
```bash
python -m hybrid_scraper --watch
```
You can combine with a starting URL:
```bash
python -m hybrid_scraper --watch --url "https://example.com"
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

This repo includes a `.vscode/launch.json` with launch profiles. If you prefer running as a module, set the program to `-m` and the module to `hybrid_scraper`, and place arguments (e.g., `--url`, `--debug-html`) in the args field.

## Notes

- ChromeDriver is auto-managed by `webdriver-manager`.
- If Chrome auto-updates and you hit driver mismatch issues, rerun and it will re-download.
