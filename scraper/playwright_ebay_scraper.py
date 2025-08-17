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
import pathlib

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
try:
    from playwright_stealth import stealth_sync
except Exception:
    stealth_sync = None  # Optional dependency
try:
    from scraper.db import upsert_listings
except Exception:
    upsert_listings = None


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

    def _snapshot_debug(self, page: Page, label: str) -> None:
        if not self.debug_snapshot_dir:
            return
        try:
            os.makedirs(self.debug_snapshot_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            base = os.path.join(self.debug_snapshot_dir, f"{ts}_{label}")
            # Screenshot
            try:
                page.screenshot(path=f"{base}.png", full_page=True)
            except Exception:
                pass
            # HTML
            try:
                with open(f"{base}.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
            except Exception:
                pass
            logger.info(f"Saved debug snapshot: {base}.[png|html]")
        except Exception:
            pass

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
            self._snapshot_debug(page, f"p{page_num}_no_results_selector")

        # Always try to parse first; if we get listings, accept them
        listings = self._parse_listing_elements(page)
        logger.info(f"Parsed {len(listings)} listings from page {page_num}")
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
                # Optional enrichment and snapshots for a small subset
                self._maybe_enrich_and_snapshot(page, results)
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

    def _maybe_enrich_and_snapshot(self, page: Page, listings: List[Dict]) -> None:
        
        def _human_like_settle(max_seconds: float) -> None:
            """Perform a short, bounded, human-like settling routine.

            Ensures we never exceed max_seconds. Uses only short, exception-safe
            interactions and avoids known blocking primitives.
            """
            start_time = time.perf_counter()
            # Small idle to mimic reading time (bounded)
            try:
                remaining = max(0.0, max_seconds - (time.perf_counter() - start_time))
                if remaining <= 0:
                    return
                time.sleep(min(0.8 + random.random(), remaining))
            except Exception:
                pass

            try:
                # Attempt a very short network idle wait to nudge stability
                try:
                    page.wait_for_load_state("networkidle", timeout=1000)
                except Exception:
                    pass

                # Keep iterations small and check time budget frequently
                iterations = min(3, max(1, random.randint(2, 3)))
                for i in range(iterations):
                    if (time.perf_counter() - start_time) >= max_seconds:
                        break

                    # Gentle mouse move to a random viewport point
                    try:
                        x = random.randint(80, 900)
                        y = random.randint(200, 800)
                        page.mouse.move(x, y, steps=random.randint(6, 12))
                    except Exception:
                        pass

                    if (time.perf_counter() - start_time) >= max_seconds:
                        break

                    # Light keyboard scrolls like a user tapping keys
                    try:
                        if i == 0:
                            page.keyboard.press("PageDown")
                        elif random.random() < 0.6:
                            page.keyboard.press("ArrowDown")
                    except Exception:
                        pass

                    if (time.perf_counter() - start_time) >= max_seconds:
                        break

                    # JS-based scroll as a reliable nudge to load lazy content
                    try:
                        delta = random.randint(200, 500)
                        page.evaluate(f"window.scrollBy(0, {delta})")
                    except Exception:
                        pass

                    # Short, bounded sleep; never exceed budget
                    try:
                        remaining = max(0.0, max_seconds - (time.perf_counter() - start_time))
                        if remaining <= 0:
                            break
                        time.sleep(min(0.25 + random.random() * 0.35, remaining))
                    except Exception:
                        pass

                elapsed = time.perf_counter() - start_time
                logger.info(f"Step 4: Human-like settle completed in {elapsed:.2f}s (budget {max_seconds:.2f}s)")
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                logger.info(f"Step 4: Human-like settle partial after {elapsed:.2f}s due to: {e}")

        # Environment-driven behavior
        snapshot_dir = os.environ.get("SNAPSHOT_DIR")
        enrich_limit = int(os.environ.get("ENRICH_LIMIT", "0"))
        # Bound or disable settle via env
        disable_settle_env = os.environ.get("DISABLE_SETTLE", "false").lower() in ("1", "true", "yes")
        try:
            human_settle_max_s = float(os.environ.get("HUMAN_SETTLE_MAX_S", "3"))
        except Exception:
            human_settle_max_s = 3.0
        allowed_conditions_env = os.environ.get(
            "ALLOWED_CONDITIONS",
            "Used,For parts or not working,Not Specified",
        )
        allowed_conditions = {c.strip().lower() for c in allowed_conditions_env.split(",")}

        # Filter by allowed conditions
        filtered = [
            l for l in listings
            if (l.get("condition") or "").lower() in allowed_conditions
        ]
        if enrich_limit == 0 and not snapshot_dir:
            # Only filtering requested – replace the list contents
            listings[:] = filtered
            logger.info(
                f"Filtered listings by condition. Before: {len(listings)} After: {len(filtered)}"
            )
            return

        listings[:] = filtered
        if not snapshot_dir or enrich_limit <= 0:
            return

        pathlib.Path(snapshot_dir).mkdir(parents=True, exist_ok=True)
        subset = listings[:enrich_limit]
        logger.info(f"Enriching {len(subset)} listings with snapshots → {snapshot_dir}")

        for idx, item in enumerate(subset, 1):
            url = item.get("url")
            if not url:
                continue
            try:
                logger.info(f"Enriching listing {idx}/{len(subset)}: {item.get('title', 'Unknown')[:50]}...")
                logger.info(f"Step 1: Loading page: {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                logger.info(f"Step 2: Page loaded successfully")
                
                # Human-like settle to avoid bot detection and prevent hangs in headless
                if disable_settle_env or human_settle_max_s <= 0:
                    logger.info("Step 3: Human-like settle disabled by env; proceeding")
                else:
                    logger.info(f"Step 3: Human-like settle (max {human_settle_max_s:.1f}s)")
                    _human_like_settle(human_settle_max_s)
                
                # Save screenshot and html
                logger.info(f"Step 5: Preparing to save snapshots")
                base = f"{idx:02d}_" + self._sanitize_filename(item.get("title") or "listing")
                png_path = os.path.join(snapshot_dir, base + ".png")
                html_path = os.path.join(snapshot_dir, base + ".html")
                
                logger.info(f"Step 6: Taking screenshot")
                try:
                    page.screenshot(path=png_path, full_page=True, timeout=self.screenshot_timeout_ms)
                    logger.info(f"Step 7: Screenshot saved successfully")
                except Exception as e:
                    logger.info(f"Step 7: Screenshot failed: {e}")
                
                logger.info(f"Step 8: Saving HTML content")
                try:
                    with open(html_path, "w", encoding="utf-8") as f:
                        # Set a shorter timeout for getting page content
                        page.set_default_timeout(self.content_timeout_ms)
                        f.write(page.content())
                        page.set_default_timeout(self.timeout_ms)  # Reset to default
                    logger.info(f"Step 9: HTML content saved successfully")
                except Exception as e:
                    page.set_default_timeout(self.timeout_ms)  # Reset on error too
                    logger.info(f"Step 9: HTML save failed: {e}")
                
                logger.info(f"Step 10: Snapshots complete - {png_path}")
                # Lightweight enrichment on detail page
                logger.info(f"Step 11: Starting data extraction")
                # Shipping cost
                logger.info(f"Step 12: Getting page body text")
                try:
                    page.set_default_timeout(self.content_timeout_ms)
                    ship_txt = page.inner_text('body') if page.is_visible('body') else ''
                    page.set_default_timeout(self.timeout_ms)  # Reset to default
                    logger.info(f"Step 13: Body text retrieved, length: {len(ship_txt)}")
                except Exception as e:
                    page.set_default_timeout(self.timeout_ms)  # Reset on error
                    ship_txt = ''
                    logger.info(f"Step 13: Body text failed: {e}")
                
                shipping_cost = None
                try:
                    logger.info(f"Step 14: Scanning for shipping cost in elements")
                    page.set_default_timeout(self.content_timeout_ms)
                    elements = page.query_selector_all('span, div')[:1500]
                    page.set_default_timeout(self.timeout_ms)  # Reset to default
                    logger.info(f"Step 15: Found {len(elements)} elements to scan")
                    for el in elements:
                        try:
                            # Add timeout for individual element text extraction
                            t = (el.inner_text(timeout=self.element_timeout_ms) or '').strip()
                            tl = t.lower()
                            if ('shipping' in tl or 'postage' in tl) and ('handling' not in tl):
                                if 'free' in tl:
                                    shipping_cost = 0.0
                                    break
                                m = re.search(r"\$[\d,]+\.?\d*", t)
                                if m:
                                    try:
                                        shipping_cost = float(m.group().replace('$', '').replace(',', ''))
                                        break
                                    except Exception:
                                        pass
                        except Exception:
                            # Skip elements that timeout or fail
                            continue
                except Exception as e:
                    page.set_default_timeout(self.timeout_ms)  # Reset on error
                    logger.info(f"Step 16: Shipping cost extraction failed: {e}")
                logger.info(f"Step 17: Shipping cost extraction complete: {shipping_cost}")
                # Location and region
                location_text = None
                region = None
                try:
                    loc_sel = [
                        'div.ux-seller-section__itemLocation span.ux-textspans',
                        'div.ux-seller-section__itemLocation',
                        'div.d-item-location',
                        '#itemLocation',
                        'span[itemprop="availableAtOrFrom"]',
                        'div#RightSummaryPanel div.u-flL.iti-eu-bld-gry',
                    ]
                    for s in loc_sel:
                        el = page.query_selector(s)
                        if el:
                            location_text = (el.inner_text() or '').strip()
                            if location_text:
                                break
                    if not location_text:
                        for el in page.query_selector_all('span, div, li')[:2000]:
                            t = (el.inner_text() or '').strip()
                            tl = t.lower()
                            if not t:
                                continue
                            if tl.startswith('located in'):
                                location_text = t.replace('Located in', '').strip(); break
                            if 'item location' in tl:
                                parts = t.split(':', 1)
                                location_text = parts[1].strip() if len(parts) > 1 else t; break
                    if location_text:
                        ll = location_text.lower()
                        if any(term in ll for term in ['united states', 'usa', 'u.s.a', 'us']):
                            region = 'USA'
                        elif any(term in ll for term in [
                            'united kingdom','england','scotland','wales','northern ireland','ireland','republic of ireland',
                            'france','germany','italy','spain','portugal','belgium','netherlands','luxembourg','austria','switzerland',
                            'sweden','norway','denmark','finland','iceland','poland','czech','czech republic','slovakia','hungary','greece',
                            'romania','bulgaria','croatia','slovenia','estonia','latvia','lithuania','serbia','bosnia','montenegro',
                            'albania','north macedonia','moldova','ukraine'
                        ]):
                            region = 'Europe'
                        else:
                            region = 'Other'
                except Exception:
                    pass
                # Attach to item for DB
                if shipping_cost is not None:
                    item['shipping_cost'] = shipping_cost
                if location_text:
                    item['seller_location'] = location_text
                    item['location_text'] = location_text
                if region:
                    item['region'] = region
                # Small cooldown
                time.sleep(1.0 + random.random())
            except Exception as e:
                if "timeout" in str(e).lower() or "timeouterror" in str(type(e).__name__).lower():
                    logger.warning(f"Enrichment timeout for listing {idx}/{len(subset)} ({url}): {e}")
                    logger.warning(f"Continuing to next listing after timeout...")
                else:
                    logger.warning(f"Enrichment failed for listing {idx}/{len(subset)} ({url}): {e}")
        # DB upsert if available
        if upsert_listings:
            try:
                count = upsert_listings(listings)
                logger.info(f"Upserted {count} listings into DB")
            except Exception as e:
                logger.warning(f"DB upsert failed: {e}")


def main() -> None:
    search_term = os.environ.get("SEARCH_TERM", "Selmer Mark VI")
    pages = int(os.environ.get("MAX_PAGES", "2"))
    headless_env = os.environ.get("HEADLESS", "true").lower() in ("1", "true", "yes")
    delay = float(os.environ.get("REQUEST_DELAY", "2.5"))
    browser_name = os.environ.get("BROWSER", "chromium").lower()
    user_data_dir = os.environ.get("USER_DATA_DIR")
    slow_mo_ms = int(os.environ.get("SLOW_MO_MS", "0"))
    debug_snapshot_dir = os.environ.get("DEBUG_SNAPSHOT_DIR")
    timeout_ms = int(os.environ.get("PAGE_TIMEOUT_MS", "30000"))
    screenshot_timeout_ms = int(os.environ.get("SCREENSHOT_TIMEOUT_MS", "10000"))
    content_timeout_ms = int(os.environ.get("CONTENT_TIMEOUT_MS", "5000"))
    element_timeout_ms = int(os.environ.get("ELEMENT_TIMEOUT_MS", "1000"))

    scraper = EbayBrowserScraper(
        search_term=search_term,
        max_pages=pages,
        delay_seconds=delay,
        headless=headless_env,
        browser_name=browser_name,
        user_data_dir=user_data_dir,
        slow_mo_ms=slow_mo_ms,
        debug_snapshot_dir=debug_snapshot_dir,
        timeout_ms=timeout_ms,
    )
    # Store additional timeout values for enrichment
    scraper.screenshot_timeout_ms = screenshot_timeout_ms
    scraper.content_timeout_ms = content_timeout_ms
    scraper.element_timeout_ms = element_timeout_ms
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


