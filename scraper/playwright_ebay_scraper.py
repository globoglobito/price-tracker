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

from typing import Dict, List, Optional
from datetime import datetime
import logging
import os
import re
import time
import random

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
try:
    from playwright_stealth import stealth_sync
except Exception:
    stealth_sync = None  # Optional dependency


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
    ) -> None:
        self.search_term = search_term
        self.max_pages = max_pages
        self.delay_seconds = delay_seconds
        self.headless = headless
        self.proxy_url = proxy_url or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
        self.timeout_ms = timeout_ms
        self.browser_name = browser_name.lower()
        self.device_name = device_name

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

    def _new_context(self, browser: Browser, device: Optional[Dict] = None) -> BrowserContext:
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

    def _is_block_page(self, page: Page) -> bool:
        text = page.content().lower()
        block_markers = [
            "verify you're a human",
            "not a robot",
            "enter the characters you see",
            "access to this page has been denied",
            "captcha",
        ]
        return any(marker in text for marker in block_markers)

    def _parse_listing_elements(self, page: Page) -> List[Dict]:
        items = page.query_selector_all(".s-item")
        listings: List[Dict] = []
        for item in items:
            try:
                title_elem = item.query_selector(".s-item__title")
                if not title_elem:
                    continue

                title = (title_elem.inner_text() or "").strip()
                if title == "Shop on eBay":
                    continue

                link_elem = item.query_selector(".s-item__link")
                url = link_elem.get_attribute("href") if link_elem else None

                price_elem = item.query_selector(".s-item__price")
                price_text = price_elem.inner_text().strip() if price_elem else ""
                price = _extract_price_from_text(price_text)
                if price is None:
                    continue

                condition_elem = item.query_selector(".s-item__condition, .s-item__subtitle, .s-item__details")
                condition_text = (condition_elem.inner_text() if condition_elem else "").lower()
                condition: Optional[str] = None
                if "used" in condition_text:
                    condition = "Used"
                elif "new" in condition_text:
                    condition = "New"
                elif "open box" in condition_text:
                    condition = "Open box"
                elif "for parts" in condition_text or "not working" in condition_text:
                    condition = "For parts or not working"
                elif "refurbished" in condition_text:
                    condition = "Certified - Refurbished"
                else:
                    condition = "Not Specified"

                location_elem = item.query_selector(".s-item__location")
                seller_location = (location_elem.inner_text().strip() if location_elem else None)

                shipping_elem = item.query_selector(".s-item__shipping")
                shipping_info = (shipping_elem.inner_text().strip() if shipping_elem else None)

                listing_id = None
                if url:
                    match = re.search(r"/itm/(\d+)", url)
                    if match:
                        listing_id = match.group(1)

                brand = None
                model = None
                type_info = None
                tl = title.lower()
                if "selmer" in tl:
                    brand = "Selmer"
                    if "mark vi" in tl:
                        model = "Mark VI"
                elif "yamaha" in tl:
                    brand = "Yamaha"
                    model_match = re.search(r"Y[AT]S?[-\s]?(\d+)", title, re.IGNORECASE)
                    if model_match:
                        model = f"YTS-{model_match.group(1)}"

                if "tenor" in tl:
                    type_info = "Tenor"
                elif "alto" in tl:
                    type_info = "Alto"
                elif "soprano" in tl:
                    type_info = "Soprano"
                elif "baritone" in tl:
                    type_info = "Baritone"

                listings.append(
                    {
                        "title": title,
                        "price": price,
                        "url": url,
                        "listing_id": listing_id,
                        "condition": condition,
                        "seller_location": seller_location,
                        "shipping_info": shipping_info,
                        "brand": brand,
                        "model": model,
                        "type": type_info,
                        "currency": "USD",
                        "website": "ebay",
                        "scraped_at": datetime.now().isoformat(),
                    }
                )
            except Exception as parse_err:
                logger.debug(f"Parse error for an item: {parse_err}")

        return listings

    def _accept_cookies_if_present(self, page: Page) -> None:
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

    def _perform_search_flow(self, page: Page) -> None:
        logger.info("Opening eBay home and performing search via UI flow")
        page.goto("https://www.ebay.com/", wait_until="domcontentloaded")
        self._accept_cookies_if_present(page)

        # Wait for the search box and type query
        page.wait_for_selector("#gh-ac", timeout=self.timeout_ms)
        page.fill("#gh-ac", self.search_term)
        # Random small delay to mimic typing pause
        time.sleep(0.3 + random.random() * 0.4)
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

    def scrape_page(self, page_num: int, page: Page) -> List[Dict]:
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

        if self._is_block_page(page):
            logger.warning("Likely hit a bot-detection page; returning no results for this page")
            return []

        listings = self._parse_listing_elements(page)
        logger.info(f"Parsed {len(listings)} listings from page {page_num}")
        return listings

    def scrape(self) -> List[Dict]:
        results: List[Dict] = []
        with sync_playwright() as p:
            browser_args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ]

            launch_kwargs = {
                "headless": self.headless,
                "args": browser_args,
            }
            if self.proxy_url:
                launch_kwargs["proxy"] = {"server": self.proxy_url}

            if self.browser_name == "firefox":
                browser = p.firefox.launch(**launch_kwargs)
            elif self.browser_name == "webkit":
                browser = p.webkit.launch(**launch_kwargs)
            else:
                browser = p.chromium.launch(**launch_kwargs)
            try:
                # Optional device emulation: try a common desktop or mobile
                device_descriptor = None
                device_name_env = os.environ.get("DEVICE") or self.device_name
                if device_name_env:
                    device_descriptor = p.devices.get(device_name_env)
                context = self._new_context(browser, device=device_descriptor)
                page = context.new_page()
                # Apply stealth if available
                if stealth_sync is not None:
                    try:
                        stealth_sync(page)
                    except Exception:
                        pass
                # Light human-like activity to warm up session
                try:
                    page.goto("https://www.ebay.com/", wait_until="domcontentloaded")
                    self._accept_cookies_if_present(page)
                    page.mouse.move(200 + random.randint(0, 200), 300 + random.randint(0, 200))
                    page.mouse.wheel(delta_x=0, delta_y=300)
                    time.sleep(0.8 + random.random() * 0.5)
                except Exception:
                    pass
                for page_num in range(1, self.max_pages + 1):
                    page_results = self.scrape_page(page_num, page)
                    results.extend(page_results)
                    if page_num < self.max_pages:
                        delay = self.delay_seconds + (0.5)
                        logger.info(f"Sleeping {delay:.1f}s before next page...")
                        time.sleep(delay)
            finally:
                browser.close()
        logger.info(f"Scrape complete. Total listings: {len(results)}")
        return results


def main() -> None:
    search_term = os.environ.get("SEARCH_TERM", "Selmer Mark VI")
    pages = int(os.environ.get("MAX_PAGES", "2"))
    headless_env = os.environ.get("HEADLESS", "true").lower() in ("1", "true", "yes")
    delay = float(os.environ.get("REQUEST_DELAY", "2.5"))
    browser_name = os.environ.get("BROWSER", "chromium").lower()

    scraper = EbayBrowserScraper(
        search_term=search_term,
        max_pages=pages,
        delay_seconds=delay,
        headless=headless_env,
        browser_name=browser_name,
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


