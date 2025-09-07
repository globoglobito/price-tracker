"""
Listing enrichment and detailed data extraction for individual eBay listings.
"""
import os
import re
import time
import random
import pathlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from scraper.utils.bot_detection import is_block_page, save_debug_snapshot
from scraper.utils.timeout_manager import TimeoutManager

logger = logging.getLogger(__name__)


class ListingEnricher:
    """Handles enrichment of listing data by visiting individual listing pages."""
    
    def __init__(self, 
                 snapshot_dir: Optional[str] = None,
                 debug_snapshot_dir: Optional[str] = None,
                 timeout_ms: int = 30000,
                 screenshot_timeout_ms: int = 10000,
                 content_timeout_ms: int = 5000):
        """
        Initialize the listing enricher.
        
        Args:
            snapshot_dir: Directory to save listing snapshots
            debug_snapshot_dir: Directory to save debug snapshots
            timeout_ms: General timeout for page operations
            screenshot_timeout_ms: Timeout for screenshot operations
            content_timeout_ms: Timeout for content operations
        """
        self.snapshot_dir = snapshot_dir
        self.debug_snapshot_dir = debug_snapshot_dir
        self.timeout_ms = timeout_ms
        self.screenshot_timeout_ms = screenshot_timeout_ms
        self.content_timeout_ms = content_timeout_ms
        self.timeout_manager = TimeoutManager(extraction_timeout_seconds=240)
        self._last_results_url: Optional[str] = None
        
    def sanitize_filename(self, text: str) -> str:
        """Sanitize text for use as filename."""
        text = re.sub(r"[^A-Za-z0-9._-]+", "_", text)[:100]
        return text.strip("_")
    
    def human_like_settle(self, page: Any, min_seconds: float, max_seconds: float) -> None:
        """
        Human-like settle with per-step time checks to enforce max duration.

        Keeps interactions (mouse/keys/JS) but checks elapsed after EVERY micro-step
        and immediately exits once max_seconds is reached.
        """
        start_time = time.perf_counter()

        def elapsed() -> float:
            return time.perf_counter() - start_time

        # Small initial idle without blocking browser events
        time.sleep(min(0.3, max_seconds))

        # Perform a few tiny human-like nudges with strict elapsed checks
        for i in range(3):
            if elapsed() >= max_seconds:
                break

            # Mouse move (best-effort)
            try:
                x = random.randint(80, 900)
                y = random.randint(200, 800)
                page.mouse.move(x, y, steps=random.randint(6, 12))
            except Exception:
                pass
            if elapsed() >= max_seconds:
                break

            # Tiny scroll or key nudge
            if i == 0:
                try:
                    if random.random() < 0.4:
                        page.keyboard.press("PageDown")
                    elif random.random() < 0.6:
                        page.keyboard.press("ArrowDown")
                except Exception:
                    pass
            elif i == 1:
                # Small scroll via JS
                try:
                    delta = random.randint(200, 500)
                    page.evaluate("window.requestAnimationFrame(() => window.scrollBy(0, arguments[0]));", delta)
                except Exception:
                    pass
            if elapsed() >= max_seconds:
                break

            # Tiny pause between steps
            time.sleep(min(0.1 + random.random() * 0.2, max_seconds - elapsed()))

        # Ensure minimum time elapsed
        if elapsed() < min_seconds:
            remaining = min_seconds - elapsed()
            time.sleep(remaining)
    
    def navigate_to_listing(self, page: Any, item: Dict, nav_mode: str) -> None:
        """Navigate to a listing detail page using click-through when possible."""
        url = item.get("url")
        if not url:
            return

        if nav_mode == "click":
            # Try to click through from results to preserve referer
            try:
                anchor = page.locator(f"a[href*='{url}'], a[href*='/itm/']").first
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
        referer = self._last_results_url or "https://www.ebay.com"
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms, referer=referer)
        except TypeError:
            # Some Playwright versions may not accept referer kwarg here; degrade gracefully
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
    
    def extract_listing_data(self, page: Any, item: Dict, listing_idx: int, total_listings: int) -> None:
        """Extract detailed data from an individual listing page."""
        self.timeout_manager.start_extraction_timer()
        
        logger.info(f"Step 11: Starting data extraction")
        
        # Check timeout before starting location extraction
        if self.timeout_manager.check_extraction_timeout("location extraction"):
            logger.warning(f"Data extraction timeout - skipping listing {listing_idx}/{total_listings}")
            return
            
        # Location and region extraction
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
                # Check timeout before expensive DOM query
                if self.timeout_manager.check_extraction_timeout("DOM query"):
                    return
                    
                for el_idx, el in enumerate(page.query_selector_all('span, div, li')[:2000]):
                    # Check timeout periodically during expensive loop
                    if el_idx % 100 == 0 and self.timeout_manager.check_extraction_timeout("DOM element iteration"):
                        break
                    t = (el.inner_text() or '').strip()
                    tl = t.lower()
                    if not t:
                        continue
                    if tl.startswith('located in'):
                        location_text = t.replace('Located in', '').strip()
                        break
                    if 'item location' in tl:
                        parts = t.split(':', 1)
                        location_text = parts[1].strip() if len(parts) > 1 else t
                        break
            
            # Region detection
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
                elif any(term in ll for term in ['china', 'hong kong', 'taiwan', 'japan', 'korea', 'singapore']):
                    region = 'Asia'
                
                item['seller_location'] = location_text
                if region:
                    item['region'] = region
        except Exception:
            pass

        # Best offer detection
        try:
            has_best_offer = False
            best_offer_sel = [
                'span:has-text("Best Offer")',
                'span:has-text("or Best Offer")',
                'div:has-text("Best Offer")',
                'button:has-text("Make Offer")',
                '[data-testid*="offer"]',
            ]
            for s in best_offer_sel:
                if page.locator(s).count() > 0:
                    has_best_offer = True
                    break
            
            if not has_best_offer:
                # Fallback: scan body text for "Best Offer"
                try:
                    if page.is_visible('body'):
                        body_text = (page.inner_text('body') or "").lower()
                        if "best offer" in body_text:
                            has_best_offer = True
                except Exception:
                    pass
            
            if has_best_offer:
                item['has_best_offer'] = True
        except Exception:
            pass

        # Check timeout before auction end time detection
        if self.timeout_manager.check_extraction_timeout("auction detection"):
            return
            
        # Detect auction end time (best-effort)
        try:
            detected_end: Optional[str] = None
            # Try JSON-LD offers
            try:
                handles = page.query_selector_all("script[type='application/ld+json']")
                for h in handles:
                    try:
                        raw = h.inner_text().strip()
                        if not raw or not (raw.startswith("{") or raw.startswith("[")):
                            continue
                        import json as _json
                        data = _json.loads(raw)
                        def _walk(obj):
                            nonlocal detected_end
                            if detected_end:
                                return
                            if isinstance(obj, dict):
                                for k, v in obj.items():
                                    if isinstance(v, (dict, list)):
                                        _walk(v)
                                    elif isinstance(v, str) and k.lower() in ("enddate", "availabilityends", "pricevaliduntil", "end_time", "end") and not detected_end:
                                        detected_end = v
                            elif isinstance(obj, list):
                                for it in obj:
                                    _walk(it)
                        _walk(data)
                        if detected_end:
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Try DOM attributes commonly used for timers
            if not detected_end:
                try:
                    cand = page.query_selector('div#vi-cdown')
                    if not cand:
                        cand = page.query_selector('[data-end-date], [data-endtime], [data-end_datetime]')
                    if cand:
                        v = cand.get_attribute('data-end-date') or cand.get_attribute('data-endtime') or cand.get_attribute('data-end_datetime')
                        if not v:
                            for el in cand.query_selector_all('*')[:20]:
                                v = el.get_attribute('data-end-date') or el.get_attribute('data-endtime') or el.get_attribute('data-end_datetime')
                                if v:
                                    break
                        if v:
                            detected_end = v
                except Exception:
                    pass

            # Try time[datetime]
            if not detected_end:
                try:
                    tnode = page.query_selector('time[datetime]')
                    if tnode:
                        v = tnode.get_attribute('datetime')
                        if v:
                            detected_end = v
                except Exception:
                    pass

            # Regex ISO in HTML as last resort
            if not detected_end:
                try:
                    page.set_default_timeout(self.content_timeout_ms)
                    html = page.content()
                    page.set_default_timeout(self.timeout_ms)
                except Exception:
                    html = ''
                if html:
                    m = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+\-]\d{2}:\d{2})?)", html)
                    if m:
                        detected_end = m.group(1)

            # Parse and store if seemingly ISO-like
            if detected_end:
                try:
                    from datetime import datetime
                    iso = detected_end.strip().replace('Z', '+00:00')
                    dt = None
                    try:
                        dt = datetime.fromisoformat(iso)
                    except Exception:
                        dt = None
                    if dt:
                        item['auction_end_time'] = dt.isoformat()
                except Exception:
                    pass
        except Exception:
            pass
    
    def enrich_and_snapshot(self, page: Any, listings: List[Dict], enrich_limit: int = 0) -> None:
        """
        Enrich listings by visiting individual pages and taking snapshots.
        
        Args:
            page: Playwright page object
            listings: List of listings to enrich (modified in place)
            enrich_limit: Maximum number of listings to enrich (0 = unlimited)
        """
        # Store reference to results page URL
        try:
            self._last_results_url = page.url
        except Exception:
            pass
            
        # Filter out invalid listings
        filtered = [l for l in listings if l.get("url") and l.get("price") is not None]
        if len(filtered) != len(listings):
            logger.info(f"Filtered {len(listings) - len(filtered)} invalid listings")
            
        listings[:] = filtered
        if not self.snapshot_dir:
            return

        pathlib.Path(self.snapshot_dir).mkdir(parents=True, exist_ok=True)
        subset = listings if enrich_limit <= 0 else listings[:enrich_limit]
        logger.info(f"Enriching {len(subset)} listings with snapshots → {self.snapshot_dir}")

        # Enforce minimum wait after results page before enrichment
        min_wait_s = float(os.environ.get("MAIN_PAGE_MIN_WAIT_S", "6"))
        if min_wait_s > 0:
            logger.info(f"Waiting {min_wait_s:.2f}s after results page before enrichment")
            time.sleep(min_wait_s)

        nav_mode = (os.environ.get("ENRICH_NAV_MODE", "auto") or "auto").lower()
        jitter_min = float(os.environ.get("ENRICH_JITTER_MIN_S", "0.5"))
        jitter_max = float(os.environ.get("ENRICH_JITTER_MAX_S", "2.0"))
        
        for idx, item in enumerate(subset, 1):
            url = item.get("url")
            if not url:
                continue
                
            logger.info(f"Enriching listing {idx}/{len(subset)}: {item.get('title', 'Unknown')[:50]}...")
            
            try:
                # Step 1: Navigate to listing
                logger.info(f"Step 1: Loading page: {url} (nav_mode={nav_mode})")
                self.navigate_to_listing(page, item, nav_mode)
                
                # Step 2: Check if page loaded
                logger.info(f"Step 2: Page loaded successfully")
                
                # Check for bot detection
                if is_block_page(page):
                    logger.warning(f"Bot detection page detected - saving debug snapshot")
                    if self.debug_snapshot_dir:
                        save_debug_snapshot(page, self.debug_snapshot_dir, f"listing_{idx}_BLOCKED")
                    continue
                
                # Step 3: Human-like settle
                settle_min_s = float(os.environ.get("HUMAN_SETTLE_MIN_S", "2"))
                settle_max_s = float(os.environ.get("HUMAN_SETTLE_MAX_S", "8"))
                logger.info(f"Step 3: Human-like settle (min {settle_min_s}s, max {settle_max_s}s)")
                
                settle_duration = settle_min_s + random.random() * (settle_max_s - settle_min_s)
                self.human_like_settle(page, settle_min_s, settle_max_s)
                logger.info(f"Step 4: Human-like settle completed in {settle_duration:.2f}s")
                
                # Step 5-10: Take snapshots
                logger.info(f"Step 5: Preparing to save snapshots")
                
                title_clean = self.sanitize_filename(item.get("title", "unknown"))
                base_name = f"{idx:02d}_{title_clean}"
                png_path = os.path.join(self.snapshot_dir, f"{base_name}.png")
                html_path = os.path.join(self.snapshot_dir, f"{base_name}.html")
                
                # Screenshot
                logger.info(f"Step 6: Taking screenshot")
                try:
                    page.screenshot(path=png_path, full_page=True, timeout=self.screenshot_timeout_ms)
                    logger.info(f"Step 7: Screenshot saved successfully")
                except Exception as e:
                    logger.info(f"Step 7: Screenshot failed: {e}")
                
                # HTML content
                logger.info(f"Step 8: Saving HTML content")
                try:
                    page.set_default_timeout(self.content_timeout_ms)
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(page.content())
                    page.set_default_timeout(self.timeout_ms)
                    logger.info(f"Step 9: HTML content saved successfully")
                except Exception as e:
                    page.set_default_timeout(self.timeout_ms)  # Reset on error too
                    logger.info(f"Step 9: HTML save failed: {e}")
                
                logger.info(f"Step 10: Snapshots complete - {png_path}")
                
                # Step 11: Extract detailed data
                self.extract_listing_data(page, item, idx, len(subset))
                
            except Exception as e:
                if "timeout" in str(e).lower() or "timeouterror" in str(type(e).__name__).lower():
                    logger.warning(f"Enrichment timeout for listing {idx}/{len(subset)} ({url}): {e}")
                    logger.warning(f"Continuing to next listing after timeout...")
                else:
                    logger.warning(f"Enrichment failed for listing {idx}/{len(subset)} ({url}): {e}")
            finally:
                # Return to results context for next listing
                try:
                    if self._last_results_url:
                        page.goto(self._last_results_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                        # Random jitter between enrichments
                        jitter = max(0.0, jitter_min) + random.random() * max(0.0, (jitter_max - jitter_min))
                        if jitter > 0:
                            time.sleep(jitter)
                except Exception:
                    pass
