#!/usr/bin/env python3
"""
Playwright-based eBay scraper for Price Tracker

Rationale:
- Real browser automation to reduce bot detection
- Handles client-side rendering and dynamic content

Usage (local):
  1) pip install -r scraper/requirements.txt
  2) python -m playwright install chromium
  3) python scraper/playwright_ebay_scraper.py
"""

from typing import Dict, List, Optional, Any
import signal
from datetime import datetime
import logging
import os
import re
import time
import random
import pathlib

# Import extracted utilities
from scraper.config import settings
from scraper.utils.bot_detection import is_block_page, save_debug_snapshot
from scraper.utils.timeout_manager import TimeoutManager
from scraper.extractors.results_parser import parse_listing_elements, clean_ebay_url
from scraper.extractors.listing_enricher import ListingEnricher

import importlib
try:
    from scraper.db import upsert_listings, get_or_create_search, fetch_existing_listing_ids, mark_missing_inactive
except Exception:
    upsert_listings = None
    get_or_create_search = None
    fetch_existing_listing_ids = None
    mark_missing_inactive = None


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _extract_price_from_text(price_text: str) -> Optional[float]:
    if not price_text:
        return None
    normalized = price_text.replace(",", "").strip()
    match = re.search(r"[\d]+\.?\d*", normalized)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None
    return None


class EbayBrowserScraper:
    def __init__(
        self,
        search_term: str,
        max_pages: int = 2,
        delay_seconds: float = 2.0,
        headless: bool = True,
        proxy_url: Optional[str] = None,
        timeout_ms: int = 30000,
        browser_name: str = "chromium",
        device_name: Optional[str] = None,
        user_data_dir: Optional[str] = None,
        slow_mo_ms: int = 0,
        debug_snapshot_dir: Optional[str] = None,
        snapshot_dir: Optional[str] = None,
        enrich_limit: int = 0,
        screenshot_timeout_ms: int = 10000,
        content_timeout_ms: int = 5000,
    ) -> None:
        self.search_term = search_term
        self.max_pages = max_pages
        self.delay_seconds = delay_seconds
        self.headless = headless
        self.proxy_url = proxy_url or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
        self.timeout_ms = timeout_ms
        self.browser_name = browser_name.lower()
        self.device_name = device_name
        self.debug_snapshot_dir = debug_snapshot_dir
        self.user_data_dir = user_data_dir
        self.slow_mo_ms = slow_mo_ms
        self.snapshot_dir = snapshot_dir
        self.enrich_limit = enrich_limit
        self.screenshot_timeout_ms = screenshot_timeout_ms
        self.content_timeout_ms = content_timeout_ms
        # Track last results page URL and load time for referer-aware enrichment and delay
        self._last_results_url: Optional[str] = None
        self._last_results_loaded_at: Optional[float] = None
        
        # Initialize timeout manager
        self.timeout_manager = TimeoutManager(extraction_timeout_seconds=240)
        
        # Initialize listing enricher
        self.enricher = ListingEnricher(
            snapshot_dir=snapshot_dir,
            debug_snapshot_dir=debug_snapshot_dir,
            timeout_ms=timeout_ms,
            screenshot_timeout_ms=screenshot_timeout_ms,
            content_timeout_ms=content_timeout_ms
        )

    def _build_search_url(self, page_number: int) -> str:
        base_url = "https://www.ebay.com/sch/i.html"
        params = {
            "_nkw": self.search_term,
            "_pgn": page_number,
            "_sacat": 0,
            "LH_TitleDesc": 0,
            "LH_Sold": 0,
        }
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query}"

    def _new_context(self, browser: Any, device: Optional[Dict] = None) -> Any:
        chrome_major = random.choice([121, 122, 123, 124, 125])
        if self.browser_name == "firefox":
            user_agent = (
                f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{random.randint(115, 129)}.0) "
                f"Gecko/20100101 Firefox/{random.randint(115, 129)}.0"
            )
        elif self.browser_name == "webkit":
            user_agent = (
                f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                f"AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
            )
        else:
            user_agent = (
                f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                f"AppleWebKit/537.36 (KHTML, like Gecko) "
                f"Chrome/{chrome_major}.0.0.0 Safari/537.36"
            )
        viewport = {"width": random.randint(1280, 1920), "height": random.randint(720, 1080)}
        base_ctx_args: Dict = {
            "user_agent": user_agent,
            "viewport": viewport,
            "locale": "en-US",
            "timezone_id": "America/New_York",
        }
        if device:
            base_ctx_args.update(device)
        context = browser.new_context(**base_ctx_args)
        context.set_default_timeout(self.timeout_ms)
        # Extra headers to look more like a real browser
        context.set_extra_http_headers(
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "max-age=0",
                "Upgrade-Insecure-Requests": "1",
                "DNT": "1",
                "Referer": "https://www.ebay.com/",
                # Client hints (best-effort)
                "Sec-CH-UA": '"Chromium";v="124", "Not.A/Brand";v="24", "Google Chrome";v="124"',
                "Sec-CH-UA-Mobile": "?0",
                "Sec-CH-UA-Platform": '"Windows"',
            }
        )
        # Stealth-like evasions
        context.add_init_script(
            """
            // Pass the WebDriver test
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            // Pass the Chrome test
            window.chrome = { runtime: {} };
            // Pass the Plugins Length test
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            // Pass the Languages test
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            // WebGL vendor spoofing (best-effort)
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
              if (parameter === 37445) { return 'Intel Inc.'; }
              if (parameter === 37446) { return 'Intel Iris OpenGL Engine'; }
              return getParameter.call(this, parameter);
            };
            """
        )
        return context

    def _clean_ebay_url(self, url: Optional[str]) -> Optional[str]:
        """Return canonical https://www.ebay.com/itm/<id> if an item id is present."""
        return clean_ebay_url(url)

    def _navigate_to_listing(self, page: Any, item: Dict, nav_mode: str) -> None:
        """Navigate to a listing detail page using click-through when possible.

        Falls back to direct goto with an appropriate Referer header.
        """
        url = item.get("url")
        listing_id = item.get("listing_id")
        # Small human-like pause before navigation
        time.sleep(0.4 + random.random() * 0.5)
        # Try click-through if requested/auto and we can find the anchor on the page
        if nav_mode in ("click", "auto") and listing_id:
            try:
                anchor = page.locator(f"a[href*='/itm/{listing_id}']")
                if anchor.count() > 0:
                    try:
                        anchor.first.scroll_into_view_if_needed(timeout=2000)
                    except Exception:
                        pass
                    try:
                        page.mouse.move(200 + random.randint(0, 200), 200 + random.randint(0, 200))
                    except Exception:
                        pass
                    anchor.first.click(timeout=self.timeout_ms)
                    page.wait_for_load_state("domcontentloaded", timeout=self.timeout_ms)
                    return
            except Exception:
                # Fall through to goto
                pass
        # Fallback: direct navigation with referer
        referer = self._last_results_url or "https://www.ebay.com/"
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms, referer=referer)
        except TypeError:
            # Some Playwright versions may not accept referer kwarg here; degrade gracefully
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)

    def _is_block_page(self, page: Any) -> bool:
        """Detect anti-bot challenge using visible body text and strong structural hints."""
        return is_block_page(page)

    def _snapshot_debug(self, page: Any, label: str) -> None:
        """Save debug snapshots using extracted utility."""
        save_debug_snapshot(page, self.debug_snapshot_dir, label)

    def _parse_listing_elements(self, page: Any) -> List[Dict]:
        """Parse listing elements using extracted results parser."""
        return parse_listing_elements(page)

    def _accept_cookies_if_present(self, page: Any) -> None:
        try:
            # Common eBay cookie banners
            candidates = [
                "button:has-text('Accept all')",
                "button:has-text('Accept All')",
                "button:has-text('Accept')",
                "#gdpr-banner-accept",
                "#gdpr-banner-accept-button",
            ]
            for selector in candidates:
                try:
                    locator = page.locator(selector)
                    if locator.count() > 0:
                        locator.first.click(timeout=2000)
                        time.sleep(0.5)
                        break
                except Exception:
                    continue
        except Exception:
            pass

    def _perform_search_flow(self, page: Any) -> None:
        logger.info("Opening eBay home and performing search via UI flow")
        page.goto("https://www.ebay.com/", wait_until="domcontentloaded")
        self._accept_cookies_if_present(page)

        # Wait for the search box and type query
        page.wait_for_selector("#gh-ac", timeout=self.timeout_ms)
        page.click("#gh-ac")
        for ch in self.search_term:
            page.keyboard.type(ch, delay=50 + int(random.random() * 50))
        time.sleep(0.6 + random.random() * 0.8)
        # Submit using Enter to avoid flaky button overlays
        page.keyboard.press("Enter")
        try:
            page.wait_for_selector(".s-item", timeout=self.timeout_ms)
        except Exception:
            logger.warning("Results not visible after UI search; falling back to direct URL")
            url = self._build_search_url(1)
            page.goto(url, wait_until="domcontentloaded")
            try:
                page.wait_for_selector(".s-item", timeout=self.timeout_ms)
            except Exception:
                logger.warning("Results still not visible after fallback navigation")
        try:
            for _ in range(3):
                page.mouse.move(100 + random.randint(0, 600), 200 + random.randint(0, 400))
                page.mouse.wheel(0, 300 + random.randint(0, 300))
                time.sleep(0.4 + random.random() * 0.6)
            first = page.query_selector(".s-item__link")
            if first:
                first.hover()
                time.sleep(0.5 + random.random() * 0.8)
        except Exception:
            pass

    def scrape_page(self, page_num: int, page: Any) -> List[Dict]:
        # For first page, prefer UI-based navigation to get cookies/session
        if page_num == 1 and "ebay.com/sch/" not in page.url:
            self._perform_search_flow(page)
        else:
            url = self._build_search_url(page_num)
            logger.info(f"Navigating to page {page_num}: {url}")
            page.goto(url, wait_until="domcontentloaded")

        # Mild human-like delay
        time.sleep(1.0 + min(self.delay_seconds, 2.0) + random.random() * 0.5)

        # Wait for results grid (best-effort)
        try:
            page.wait_for_selector(".s-item", timeout=self.timeout_ms)
        except Exception:
            logger.warning("Results selector not found within timeout; attempting to parse whatever loaded")
            self._snapshot_debug(page, f"p{page_num}_no_results_selector")

        # Save a snapshot of the results page for debugging/auditing
        try:
            if self.debug_snapshot_dir:
                self._snapshot_debug(page, f"p{page_num}_results")
        except Exception:
            pass

        # Always try to parse first; if we get listings, accept them
        listings = self._parse_listing_elements(page)
        logger.info(f"Parsed {len(listings)} listings from page {page_num}")
        # Remember results URL and load time for later referer-aware enrichment and delay
        try:
            self._last_results_url = page.url
            self._last_results_loaded_at = time.monotonic()
        except Exception:
            pass
        if listings:
            return listings

        # If no listings parsed, then check for block indicators
        if self._is_block_page(page):
            logger.warning("Likely hit a bot-detection page; returning no results for this page")
            self._snapshot_debug(page, f"p{page_num}_block_page")
            return []

        self._snapshot_debug(page, f"p{page_num}_zero_listings")
        return []

    def scrape(self) -> List[Dict]:
        results: List[Dict] = []
        sp = importlib.import_module("playwright.sync_api").sync_playwright
        with sp() as p:
            browser_args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ]

            launch_kwargs = {
                "headless": self.headless,
                "args": browser_args,
            }
            # Prefer Chromium's newer headless mode for closer fingerprint
            if self.headless and self.browser_name == "chromium":
                try:
                    if "--headless=new" not in launch_kwargs["args"]:
                        launch_kwargs["args"].append("--headless=new")
                except Exception:
                    pass
            if self.proxy_url:
                launch_kwargs["proxy"] = {"server": self.proxy_url}

            context = None
            browser = None
            try:
                # Persistent context if user data dir provided (chromium/firefox)
                if self.user_data_dir and self.browser_name in ("chromium", "firefox"):
                    bt = getattr(p, self.browser_name)
                    persist_kwargs = dict(launch_kwargs)
                    if self.slow_mo_ms:
                        persist_kwargs["slow_mo"] = self.slow_mo_ms
                    context = bt.launch_persistent_context(self.user_data_dir, **persist_kwargs)
                    page = context.new_page()
                else:
                    if self.browser_name == "firefox":
                        if self.slow_mo_ms:
                            launch_kwargs["slow_mo"] = self.slow_mo_ms
                        browser = p.firefox.launch(**launch_kwargs)
                    elif self.browser_name == "webkit":
                        browser = p.webkit.launch(**launch_kwargs)
                    else:
                        if self.slow_mo_ms:
                            launch_kwargs["slow_mo"] = self.slow_mo_ms
                        browser = p.chromium.launch(**launch_kwargs)
                    device_descriptor = None
                    device_name_env = os.environ.get("DEVICE") or self.device_name
                    if device_name_env:
                        device_descriptor = p.devices.get(device_name_env)
                    context = self._new_context(browser, device=device_descriptor)
                    page = context.new_page()
                # Stealth plugin removed to simplify dependencies and avoid import issues
                # Light human-like activity to warm up session
                try:
                    page.goto("https://www.ebay.com/", wait_until="domcontentloaded")
                    self._accept_cookies_if_present(page)
                    page.mouse.move(200 + random.randint(0, 200), 300 + random.randint(0, 200))
                    page.mouse.wheel(delta_x=0, delta_y=300)
                    time.sleep(0.8 + random.random() * 0.5)
                except Exception:
                    pass
                if self.max_pages and self.max_pages > 0:
                    for page_num in range(1, self.max_pages + 1):
                        page_results = self.scrape_page(page_num, page)
                        results.extend(page_results)
                        if page_num < self.max_pages:
                            delay = self.delay_seconds + (0.5)
                            logger.info(f"Sleeping {delay:.1f}s before next page...")
                            time.sleep(delay)
                else:
                    # Unlimited paging: continue until a page returns zero listings
                    page_num = 1
                    while True:
                        page_results = self.scrape_page(page_num, page)
                        if not page_results:
                            break
                        results.extend(page_results)
                        page_num += 1
                        delay = self.delay_seconds + (0.5)
                        logger.info(f"Sleeping {delay:.1f}s before next page...")
                        time.sleep(delay)
                # Optional enrichment and snapshots for a small subset
                self._maybe_enrich_and_snapshot(page, results)
                # Incremental DB operations
                if upsert_listings and get_or_create_search and fetch_existing_listing_ids and mark_missing_inactive:
                    try:
                        website = "ebay"
                        search_id = get_or_create_search(self.search_term, website)
                        # Upsert all parsed listings with search_id
                        upsert_count = upsert_listings(results, search_id=search_id)
                        logger.info(f"Upserted {upsert_count} listings into DB (with search_id)")
                        # Mark missing as inactive based on listing_id set
                        active_ids = {l.get("listing_id") for l in results if l.get("listing_id")}
                        changed = mark_missing_inactive(search_id, website, active_ids)
                        logger.info(f"Marked {changed} listings inactive (missing this run)")
                    except Exception as e:
                        logger.warning(f"Incremental DB update failed: {e}")
            finally:
                try:
                    if context:
                        context.close()
                except Exception:
                    pass
                try:
                    if browser:
                        browser.close()
                except Exception:
                    pass
        logger.info(f"Scrape complete. Total listings: {len(results)}")
        return results

    def _sanitize_filename(self, text: str) -> str:
        text = re.sub(r"[^A-Za-z0-9._-]+", "_", text)[:100]
        return text or "listing"

    def _maybe_enrich_and_snapshot(self, page: Any, listings: List[Dict]) -> None:
        """Enrich listings using extracted listing enricher."""
        self.enricher.enrich_and_snapshot(page, listings, self.enrich_limit)


def main() -> None:
    """Main entry point for the scraper when run as a module."""
    from scraper.config import settings
    
    search_term = settings.get_search_term()
    max_pages = settings.get_max_pages()
    headless = settings.is_headless()
    browser_name = settings.get_browser_type()
    user_data_dir = settings.get_user_data_dir()
    slow_mo_ms = settings.get_slow_mo_ms()
    debug_snapshot_dir = settings.get_debug_snapshot_dir()
    snapshot_dir = settings.get_snapshot_dir()
    enrich_limit = settings.get_enrich_limit()
    timeout_ms = settings.get_timeout_ms()
    
    scraper = EbayBrowserScraper(
        search_term=search_term,
        max_pages=max_pages,
        delay_seconds=2.5,  # Default delay
        headless=headless,
        browser_name=browser_name,
        user_data_dir=user_data_dir,
        slow_mo_ms=slow_mo_ms,
        debug_snapshot_dir=debug_snapshot_dir,
        snapshot_dir=snapshot_dir,
        enrich_limit=enrich_limit,
        timeout_ms=timeout_ms,
    )
    
    listings = scraper.scrape()

    print(f"\nFound {len(listings)} listings")
    for i, listing in enumerate(listings[:5], 1):
        print(f"\n{i}. {listing['title']}")
        print(f"   Price: ${listing['price']}")
        print(f"   Condition: {listing['condition']}")
        print(f"   Location: {listing['seller_location']}")
        print(f"   URL: {listing['url']}")


if __name__ == "__main__":
    main()

