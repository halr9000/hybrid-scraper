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
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse


class HybridScraper:
    def __init__(self, debug_html: bool = False, start_url: str | None = None, start_watch: bool = False, output_dir: str = "output", verbose: bool = False):
        self.driver = None
        self.debug_html = debug_html
        self.start_url = start_url
        self.start_watch = start_watch
        self.output_dir = Path(output_dir)
        self.verbose = verbose

        # Configure html2text converter
        self.h = html2text.HTML2Text()
        self.h.ignore_links = False
        self.h.ignore_images = False
        self.h.body_width = 0

    def setup_browser(self):
        """Set up a visible Chrome browser for human interaction."""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1400,1000')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        if not self.verbose:
            # Reduce noisy Chrome/Chromedriver logging to STDERR
            chrome_options.add_argument('--log-level=3')  # 0=INFO,1=WARNING,2=ERROR,3=FATAL
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

            # Suppress TensorFlow/absl logs if any dependencies trigger them
            os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')  # 0=all,1=warn,2=error,3=fatal
            logging.getLogger('absl').setLevel(logging.ERROR)

            # Send ChromeDriver logs to DEVNULL to avoid console noise
            service = Service(ChromeDriverManager().install(), log_output=subprocess.DEVNULL)
        else:
            # Verbose mode: show normal logs
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '0'
            logging.getLogger('absl').setLevel(logging.INFO)
            service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        print("🌐 Browser opened - ready for manual navigation!")
        return self.driver

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
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 Browser closed")

    def interactive_session(self):
        """Main interactive session loop."""
        print("\n🎮 INTERACTIVE MODE STARTED")
        print("-" * 30)
        self.show_help()

        while True:
            try:
                # Get current page info
                current_url = self.driver.current_url
                page_title = self.driver.title

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

        except Exception as e:
            print(f"❌ Capture failed: {e}")

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
            current_url = self.driver.current_url
            page_title = self.driver.title

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

                except Exception as e:
                    print(f"❌ Capture failed: {e}")

        print(f"\n🎉 Auto-capture completed! Saved {captured_count} pages.")

    def auto_watch_navigation(self, debounce_seconds: float = 1.5, same_url_cooldown: float = 10.0, poll_interval: float = 0.5):
        """True auto-capture: watches for navigation changes and captures automatically.

        - Debounce: waits for the URL to remain stable for `debounce_seconds`.
        - Duplicate filter: won't recapture the same URL within `same_url_cooldown` seconds.
        - Stop: press Ctrl+C to exit this mode and return to the main prompt.
        """
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
                url = self.driver.current_url
                title = self.driver.title

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
                    except Exception as e:
                        print(f"❌ Auto-capture failed: {e}")

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

    def process_and_save(self, html_source, title, url):
        """Process HTML and save as markdown."""
        try:
            # Parse HTML
            soup = BeautifulSoup(html_source, 'html.parser')

            # Remove unwanted elements
            for element in soup.select('script, style, .v-navigation-drawer, .v-app-bar, .v-footer, nav, header, footer'):
                element.decompose()

            # Find main content
            main_content = soup.select_one('main')
            if not main_content:
                main_content = soup.select_one('#app')
            if not main_content:
                main_content = soup.find('body')

            # Capture meta descriptions if present
            meta_desc = None
            # Standard meta description
            tag = soup.find('meta', attrs={'name': 'description'})
            if tag and tag.get('content'):
                meta_desc = tag.get('content').strip()
            # OpenGraph description fallback
            if not meta_desc:
                tag = soup.find('meta', attrs={'property': 'og:description'})
                if tag and tag.get('content'):
                    meta_desc = tag.get('content').strip()

            # Convert to markdown
            markdown = self.h.handle(str(main_content))
            markdown = re.sub(r'\n{3,}', '\n\n', markdown)
            markdown = markdown.strip()

            # Create header
            header = f"# {title}\n\n"
            header += f"*Source: {url}*\n\n"
            header += f"*Scraped on: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
            header += f"*Content length: {len(markdown)} characters*\n\n"
            if meta_desc:
                header += f"*Meta description: {meta_desc}*\n\n"
            header += "---\n\n"

            final_content = header + markdown

            # Create safe paths (domain subfolder inside output dir)
            parsed = urlparse(url)
            domain = parsed.netloc or "unknown-domain"
            # Normalize domain (strip common www.)
            if domain.lower().startswith("www."):
                domain = domain[4:]
            # Sanitize domain for filesystem
            safe_domain = re.sub(r'[^\w\-_.]', '-', domain.lower())

            base_dir = (Path.cwd() / self.output_dir / safe_domain)
            base_dir.mkdir(parents=True, exist_ok=True)

            # Create safe filename
            safe_name = re.sub(r'[<>:"/\\|?*]', '', title.lower())
            safe_name = re.sub(r'[^\w\-_.]', '-', safe_name)
            filename = base_dir / f"{safe_name}.md"

            # Save file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(final_content)

            # Optionally save debug HTML
            if self.debug_html:
                debug_filename = base_dir / f"debug-{safe_name}.html"
                with open(debug_filename, 'w', encoding='utf-8') as f:
                    f.write(html_source)

            print(f"💾 Saved: {filename} ({len(final_content)} characters)")
            if self.debug_html:
                print(f"🔍 Debug: {debug_filename}")

            # Show content preview
            lines = final_content.split('\n')[:10]
            print("\n📖 CONTENT PREVIEW:")
            for i, line in enumerate(lines, 1):
                if line.strip():
                    print(f"   {i:2d}| {line[:70]}{'...' if len(line) > 70 else ''}")
            if len(lines) >= 10:
                print("   ...and more")

        except Exception as e:
            print(f"❌ Processing failed: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Hybrid Page Scraper: manual navigation + automated content capture")
    parser.add_argument("--url", dest="url", help="Optional starting URL to open", default=None)
    parser.add_argument("--debug-html", dest="debug_html", help="Also save raw HTML next to Markdown", action="store_true")
    parser.add_argument("--watch", dest="watch", help="Start in watch mode (auto-capture on navigation)", action="store_true")
    parser.add_argument("--output-dir", dest="output_dir", help="Directory to save output (default: 'output')", default="output")
    parser.add_argument("--verbose", dest="verbose", help="Show verbose logs (Chrome/Driver/TF)", action="store_true")
    args = parser.parse_args()

    scraper = HybridScraper(debug_html=args.debug_html, start_url=args.url, start_watch=args.watch, output_dir=args.output_dir, verbose=args.verbose)
    scraper.start_session()


if __name__ == "__main__":
    main()
