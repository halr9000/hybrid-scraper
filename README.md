# Hybrid Page Scraper

Save Markdown from sites that are hard to scrape (e.g., heavy JS and client‑side routing). You browse; it captures.

## Quickstart (uvx)
Requires Google Chrome installed.

```bash
# Run directly from GitHub (ephemeral env)
uvx --from git+https://github.com/halr9000/hybrid-scraper hybrid-scraper --watch
```

- `--watch` enables auto-capture as you navigate. Add `--url https://example.com` to open a starting page.

## Usage (CLI)
```bash
hybrid-scraper [--url URL] [--watch] [--debug-html] [--output-dir DIR] [--verbose]
```
- `--url`           Optional starting URL to open
- `--watch`         Auto-capture when navigation stabilizes
- `--debug-html`    Also save raw HTML next to Markdown
- `--output-dir`    Output directory (default: `output`)
- `--verbose`       Show verbose Chrome/Driver logs

Workflow:
- A real Chrome window opens; navigate normally.
- Commands: `capture`, `auto`, `watch`, `help`, `quit`.

## Output
- Saved under `output/<domain>/<title>.md`.
- Header includes source URL, timestamp, content length, meta description (if available).
- With `--debug-html`, also writes `debug-<title>.html`.

## Dev Setup (uv)
```bash
# Create venv and install (uv only)
uv venv
uv pip install -e .

# Run locally
hybrid-scraper --watch
# or
python -m hybrid_scraper --watch
```

## License
MIT
