#!/usr/bin/env python3
"""
Hybrid Page Scraper (module entrypoint)
This module defines `main()` for console script execution and mirrors the behavior of hybrid-scraper.py.
"""

import html2text
import time
import re
import argparse
import os
import subprocess
import logging
from functools import lru_cache
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, InvalidSessionIdException, NoSuchWindowException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_cached_chromedriver_path() -> str:
    """Cache ChromeDriver installation to avoid repeated downloads."""
    try:
        driver_path = ChromeDriverManager().install()
        logger.info(f"ChromeDriver cached at: {driver_path}")
        return driver_path
    except Exception as e:
        logger.error(f"Failed to install ChromeDriver: {e}")
        raise


class ScraperConfig:
    """Configuration class for the hybrid scraper."""
    
    def __init__(self):
        # Browser settings
        self.window_size = "1400,1000"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        # Content processing settings
        self.max_filename_length = 100
        self.file_buffer_size = 8192
        self.content_preview_lines = 10
        self.content_preview_width = 70
        
        # Watch mode settings
        self.default_debounce_seconds = 1.5
        self.default_same_url_cooldown = 10.0
        self.default_poll_interval = 0.5
        self.min_poll_interval = 0.25
        
        # Content extraction selectors
        self.unwanted_selectors = [
            'script', 'style', 'noscript',
            '.v-navigation-drawer', '.v-app-bar', '.v-footer',
            'nav', 'header', 'footer',
            '[role="banner"]', '[role="navigation"]', '[role="contentinfo"]',
            '.advertisement', '.ads', '.sidebar'
        ]
        
        self.main_content_selectors = [
            'main',
            '[role="main"]',
            '#main',
            '.main-content',
            '#content',
            '.content',
            '#app',
            'body'
        ]


class HybridScraper:
    def __init__(self, debug_html: bool = False, start_url: str | None = None, start_watch: bool = False, output_dir: str = "output", verbose: bool = False, config: ScraperConfig | None = None):
        self.driver = None
        self.debug_html = debug_html
        self.start_url = start_url
        self.start_watch = start_watch
        self.output_dir = Path(output_dir)
        self.verbose = verbose
        self.config = config or ScraperConfig()

        # Configure html2text converter
        self.h = html2text.HTML2Text()
        self.h.ignore_links = False
        self.h.ignore_images = False
        self.h.body_width = 0

    def setup_browser(self):
        """Set up a visible Chrome browser for human interaction."""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument(f'--window-size={self.config.window_size}')
            chrome_options.add_argument(f'--user-agent={self.config.user_agent}')
            
            # Use cached ChromeDriver path
            driver_path = get_cached_chromedriver_path()
            
            if not self.verbose:
                # Reduce noisy Chrome/Chromedriver logging to STDERR
                chrome_options.add_argument('--log-level=3')  # 0=INFO,1=WARNING,2=ERROR,3=FATAL
                chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

                # Suppress TensorFlow/absl logs if any dependencies trigger them
                os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')  # 0=all,1=warn,2=error,3=fatal
                logging.getLogger('absl').setLevel(logging.ERROR)

                # Send ChromeDriver logs to DEVNULL to avoid console noise
                service = Service(driver_path, log_output=subprocess.DEVNULL)
            else:
                # Verbose mode: show normal logs
                os.environ['TF_CPP_MIN_LOG_LEVEL'] = '0'
                logging.getLogger('absl').setLevel(logging.INFO)
                service = Service(driver_path)
                
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Browser setup completed successfully")
            print("🌐 Browser opened - ready for manual navigation!")
            return self.driver
            
        except Exception as e:
            logger.error(f"Failed to setup browser: {e}")
            raise WebDriverException(f"Browser setup failed: {e}")

    def _is_browser_alive(self) -> bool:
        """Best-effort check if the browser session is still alive."""
        try:
            if not self.driver:
                return False
            # Access a lightweight property to trigger session validation
            _ = self.driver.title
            return True
        except (InvalidSessionIdException, NoSuchWindowException, WebDriverException):
            return False

    def start_session(self):
        """Start the hybrid scraping session."""
        print("🚀 Hybrid Page Scraper")
        print("=" * 50)
        print("HOW IT WORKS:")
        print("1. A browser window will open")
        print("2. YOU navigate to the pages you want")
        print("3. Use commands here to capture content")
        print(f"4. Content is saved under '{self.output_dir}/<domain>/' in this folder")
        print("=" * 50)

        try:
            # Setup browser
            self.setup_browser()

            # Optional: navigate to a starting URL
            if self.start_url is None:
                entered = input("Enter a URL to open (or press Enter to skip): ").strip()
                if entered:
                    self.start_url = entered
            if self.start_url:
                print(f"📍 Navigating to: {self.start_url}")
                self.driver.get(self.start_url)
                time.sleep(2)
                print("✅ Initial page loaded")

            # Start session in selected mode
            if self.start_watch:
                self.auto_watch_navigation()
            else:
                self.interactive_session()

        except KeyboardInterrupt:
            print("\n👋 Session interrupted by user")
        except (InvalidSessionIdException, NoSuchWindowException, WebDriverException):
            print("🔒 Browser closed")
        except Exception as e:
            # Keep error concise without Selenium's long embedded stacktrace
            print(f"❌ Error: {e.__class__.__name__}: {e}")
        finally:
            if self.driver:
                try:
                    if self._is_browser_alive():
                        self.driver.quit()
                except (InvalidSessionIdException, NoSuchWindowException, WebDriverException):
                    pass
                finally:
                    print("🔒 Browser closed")

    def interactive_session(self):
        """Main interactive session loop."""
        print("\n🎮 INTERACTIVE MODE STARTED")
        print("-" * 30)
        self.show_help()

        while True:
            try:
                # Get current page info
                try:
                    current_url = self.driver.current_url
                    page_title = self.driver.title
                except (InvalidSessionIdException, NoSuchWindowException, WebDriverException):
                    print("🔒 Browser closed")
                    break

                print(f"\n📍 Current: {page_title}")
                print(f"🔗 URL: {current_url}")

                # Get user command
                cmd = input("\n⌨️  Command (help/capture/auto/watch/quit): ").strip().lower()

                if cmd in ['q', 'quit', 'exit']:
                    break
                elif cmd in ['h', 'help']:
                    self.show_help()
                elif cmd in ['c', 'capture']:
                    self.capture_current_page()
                elif cmd in ['a', 'auto']:
                    self.auto_capture_all()
                elif cmd in ['w', 'watch', 'autocapture']:
                    self.auto_watch_navigation()
                elif cmd == '':
                    continue
                else:
                    print(f"❓ Unknown command: {cmd}")
                    self.show_help()

            except KeyboardInterrupt:
                break

        print("👋 Interactive session ended")

    def show_help(self):
        """Show available commands."""
        print("\n📋 AVAILABLE COMMANDS:")
        print("  capture (c) - Capture current page content")
        print("  auto (a)    - Semi-auto: press Enter to capture each page")
        print("  watch (w)   - True auto: capture on navigation change (Ctrl+C to stop)")
        print("  help (h)    - Show this help")
        print("  quit (q)    - Exit the scraper")
        print("\n💡 TIP: Navigate to any page, then use 'capture' to save it!")

    def capture_current_page(self):
        """Capture the current page content."""
        try:
            # Get current page info
            current_url = self.driver.current_url
            page_title = self.driver.title

            print(f"\n📸 Capturing: {page_title}")

            # Get page source
            html_source = self.driver.page_source
            print(f"📄 Captured {len(html_source)} characters")

            # Process and save
            title = self.detect_title(current_url, page_title)
            self.process_and_save(html_source, title, current_url)

        except (InvalidSessionIdException, NoSuchWindowException, WebDriverException):
            print("🔒 Browser closed")
        except Exception as e:
            print(f"❌ Capture failed: {e.__class__.__name__}: {e}")

    def auto_capture_all(self):
        """Auto-capture mode - you navigate, script captures."""
        print("\n🔄 AUTO-CAPTURE MODE")
        print("-" * 20)
        print("Navigate to each page you want to capture.")
        print("Press Enter after each page loads to capture it.")
        print("Type 'done' when finished.")
        print("")

        captured_count = 0

        while True:
            try:
                current_url = self.driver.current_url
                page_title = self.driver.title
            except (InvalidSessionIdException, NoSuchWindowException, WebDriverException):
                print("🔒 Browser closed")
                break

            print(f"📍 Ready to capture: {page_title}")
            cmd = input("Press Enter to capture, or 'done' to finish: ").strip().lower()

            if cmd == 'done':
                break
            elif cmd == '':
                try:
                    # Determine title
                    title = self.detect_title(current_url, page_title)

                    # Capture content
                    html_source = self.driver.page_source
                    self.process_and_save(html_source, title, current_url)
                    captured_count += 1

                    print(f"✅ Captured! ({captured_count} total)")
                    print("👆 Navigate to next page...")

                except (InvalidSessionIdException, NoSuchWindowException, WebDriverException):
                    print("🔒 Browser closed")
                    break
                except Exception as e:
                    print(f"❌ Capture failed: {e.__class__.__name__}: {e}")

        print(f"\n🎉 Auto-capture completed! Saved {captured_count} pages.")

    def auto_watch_navigation(self, debounce_seconds: float | None = None, same_url_cooldown: float | None = None, poll_interval: float | None = None):
        """True auto-capture: watches for navigation changes and captures automatically.

        - Debounce: waits for the URL to remain stable for `debounce_seconds`.
        - Duplicate filter: won't recapture the same URL within `same_url_cooldown` seconds.
        - Stop: press Ctrl+C to exit this mode and return to the main prompt.
        """
        # Use configuration defaults if not provided
        debounce_seconds = debounce_seconds or self.config.default_debounce_seconds
        same_url_cooldown = same_url_cooldown or self.config.default_same_url_cooldown
        poll_interval = poll_interval or self.config.default_poll_interval
        
        print("\n🕵️ WATCH MODE (auto-capture on navigation)")
        print("-" * 20)
        print(f"Debounce: {debounce_seconds}s • Same-URL cooldown: {same_url_cooldown}s")
        print("Navigate freely in the browser; captures will trigger automatically.")
        print("Press Ctrl+C here to stop and return to the menu.\n")

        last_seen_url = None
        last_seen_time = 0.0
        last_captured_time_by_url = {}
        captured_count = 0

        try:
            while True:
                try:
                    url = self.driver.current_url
                    title = self.driver.title
                except (InvalidSessionIdException, NoSuchWindowException, WebDriverException):
                    print("🔒 Browser closed")
                    break

                # Check if the page is fully loaded to reduce partial captures
                try:
                    ready_state = self.driver.execute_script("return document.readyState")
                except Exception:
                    ready_state = 'complete'  # if script fails, fall back to assume ready

                now = time.time()

                # Track last seen URL and the time it stabilized
                if url != last_seen_url:
                    last_seen_url = url
                    last_seen_time = now

                stable_for = now - last_seen_time

                # Determine if eligible to capture
                last_cap = last_captured_time_by_url.get(url, 0.0)
                cool_ok = (now - last_cap) >= same_url_cooldown
                debounce_ok = stable_for >= debounce_seconds
                ready_ok = (ready_state == 'complete')

                if debounce_ok and cool_ok and ready_ok:
                    try:
                        detected_title = self.detect_title(url, title)
                        html_source = self.driver.page_source
                        self.process_and_save(html_source, detected_title, url)
                        last_captured_time_by_url[url] = now
                        captured_count += 1
                        print(f"✅ Auto-captured ({captured_count} total)")
                    except (InvalidSessionIdException, NoSuchWindowException, WebDriverException):
                        print("🔒 Browser closed")
                        break
                    except Exception as e:
                        print(f"❌ Auto-capture failed: {e.__class__.__name__}: {e}")

                    # After capture, wait a short grace period before checking again
                    time.sleep(max(poll_interval, 0.25))

                time.sleep(poll_interval)
        except KeyboardInterrupt:
            print(f"\n🛑 Watch mode stopped. Saved {captured_count} pages in this session.")

    def detect_title(self, url, title):
        """Determine a reasonable title for the page."""
        # Prefer the browser's page title when available
        if title and title.strip():
            return title.strip()
        # Fallback to URL path segment
        try:
            path = re.sub(r"[?#].*$", "", url)  # remove query/fragment
            last = path.rstrip('/').split('/')[-1] or 'index'
            last = last.replace('-', ' ').replace('_', ' ')
            # Decode common encodings
            last = last.replace('%20', ' ')
            return last or f"unknown-{int(time.time())}"
        except Exception:
            return f"unknown-{int(time.time())}"

    def process_and_save(self, html_source: str, title: str, url: str) -> bool:
        """Process HTML and save as markdown. Returns True if successful."""
        try:
            logger.info(f"Processing page: {title} ({len(html_source)} chars)")
            
            # Parse HTML with error handling
            try:
                soup = BeautifulSoup(html_source, 'html.parser')
            except Exception as e:
                logger.error(f"HTML parsing failed: {e}")
                return False

            # Remove unwanted elements using configuration
            for selector in self.config.unwanted_selectors:
                for element in soup.select(selector):
                    element.decompose()

            # Find main content using configuration selectors
            main_content = None
            for selector in self.config.main_content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break

            if not main_content:
                logger.warning("No main content found, using full document")
                main_content = soup

            # Extract meta description more efficiently
            meta_desc = self._extract_meta_description(soup)

            # Convert to markdown
            try:
                markdown = self.h.handle(str(main_content))
                markdown = re.sub(r'\n{3,}', '\n\n', markdown).strip()
            except Exception as e:
                logger.error(f"Markdown conversion failed: {e}")
                return False

            # Create content with header
            final_content = self._create_content_with_header(title, url, markdown, meta_desc)

            # Create safe file paths
            try:
                base_dir, filename = self._create_safe_paths(url, title)
            except Exception as e:
                logger.error(f"Path creation failed: {e}")
                return False

            # Save files efficiently
            try:
                self._save_files(final_content, html_source, base_dir, filename, title)
                logger.info(f"Successfully saved: {filename}")
                
                # Show content preview
                self._show_content_preview(final_content, filename)
                return True
                
            except Exception as e:
                logger.error(f"File saving failed: {e}")
                return False

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            print(f"❌ Processing failed: {e}")
            return False

    def _extract_meta_description(self, soup: BeautifulSoup) -> str | None:
        """Extract meta description from HTML."""
        # Standard meta description
        tag = soup.find('meta', attrs={'name': 'description'})
        if tag and tag.get('content'):
            return tag.get('content').strip()
        
        # OpenGraph description fallback
        tag = soup.find('meta', attrs={'property': 'og:description'})
        if tag and tag.get('content'):
            return tag.get('content').strip()
            
        return None

    def _create_content_with_header(self, title: str, url: str, markdown: str, meta_desc: str | None) -> str:
        """Create final content with header."""
        header_parts = [
            f"# {title}",
            "",
            f"*Source: {url}*",
            "",
            f"*Scraped on: {time.strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            f"*Content length: {len(markdown)} characters*",
            ""
        ]
        
        if meta_desc:
            header_parts.extend([f"*Meta description: {meta_desc}*", ""])
            
        header_parts.extend(["---", "", ""])
        
        return "\n".join(header_parts) + markdown

    def _create_safe_paths(self, url: str, title: str) -> tuple[Path, Path]:
        """Create safe directory and file paths."""
        parsed = urlparse(url)
        domain = parsed.netloc or "unknown-domain"
        
        # Normalize domain (strip common www.)
        if domain.lower().startswith("www."):
            domain = domain[4:]
            
        # Sanitize domain for filesystem
        safe_domain = re.sub(r'[^\w\-_.]', '-', domain.lower())
        
        base_dir = Path.cwd() / self.output_dir / safe_domain
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create safe filename using configuration
        safe_name = re.sub(r'[<>:"/\\|?*]', '', title.lower())
        safe_name = re.sub(r'[^\w\-_.]', '-', safe_name)
        safe_name = safe_name[:self.config.max_filename_length]
        
        filename = base_dir / f"{safe_name}.md"
        
        return base_dir, filename

    def _save_files(self, final_content: str, html_source: str, base_dir: Path, filename: Path, title: str) -> None:
        """Save markdown and optionally HTML files using configuration settings."""
        # Save markdown file with configured buffer size
        with open(filename, 'w', encoding='utf-8', buffering=self.config.file_buffer_size) as f:
            f.write(final_content)

        # Optionally save debug HTML
        if self.debug_html:
            safe_name = filename.stem
            debug_filename = base_dir / f"debug-{safe_name}.html"
            with open(debug_filename, 'w', encoding='utf-8', buffering=self.config.file_buffer_size) as f:
                f.write(html_source)
            print(f"🔍 Debug: {debug_filename}")

    def _show_content_preview(self, final_content: str, filename: Path) -> None:
        """Show content preview using configuration settings."""
        print(f"💾 Saved: {filename} ({len(final_content)} characters)")
        
        lines = final_content.split('\n')[:self.config.content_preview_lines]
        print("\n📖 CONTENT PREVIEW:")
        for i, line in enumerate(lines, 1):
            if line.strip():
                preview = line[:self.config.content_preview_width]
                if len(line) > self.config.content_preview_width:
                    preview += '...'
                print(f"   {i:2d}| {preview}")
        if len(lines) >= self.config.content_preview_lines:
            print("   ...and more")


def main() -> None:
    parser = argparse.ArgumentParser(description="Hybrid Page Scraper: manual navigation + automated content capture")
    parser.add_argument("--url", dest="url", help="Optional starting URL to open", default=None)
    parser.add_argument("--debug-html", dest="debug_html", help="Also save raw HTML next to Markdown", action="store_true")
    parser.add_argument("--watch", dest="watch", help="Start in watch mode (auto-capture on navigation)", action="store_true")
    parser.add_argument("--output-dir", dest="output_dir", help="Directory to save output (default: 'output')", default="output")
    parser.add_argument("--verbose", dest="verbose", help="Show verbose logs (Chrome/Driver/TF)", action="store_true")
    args = parser.parse_args()

    # Validate --url: if provided, require an explicit http(s) scheme.
    # Exit early (no browser) if the value is missing or not an http/https URL.
    if args.url is not None:
        url_val = (args.url or "").strip()
        if not url_val.lower().startswith(("http://", "https://")):
            print("❗ --url must start with http:// or https://\n")
            parser.print_help()
            return

    scraper = HybridScraper(debug_html=args.debug_html, start_url=args.url, start_watch=args.watch, output_dir=args.output_dir, verbose=args.verbose)
    scraper.start_session()


if __name__ == "__main__":
    main()
