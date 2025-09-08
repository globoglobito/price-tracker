"""
Results page parsing utilities for eBay search results.
"""
import re
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def extract_price_from_text(price_text: str) -> Optional[float]:
    """Extract numeric price from price text string."""
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


def clean_ebay_url(url: Optional[str]) -> Optional[str]:
    """Clean and normalize eBay URLs to remove tracking parameters."""
    if not url:
        return url
    try:
        # Extract item ID and create clean URL
        m = re.search(r"/itm/(\d+)", url)
        if m:
            return f"https://www.ebay.com/itm/{m.group(1)}"
    except Exception:
        pass
    return url


def parse_listing_elements(page: Any) -> List[Dict]:
    """
    Parse listing elements from eBay search results page.
    
    Handles both old (.s-item) and new (.s-card) eBay formats.
    
    Args:
        page: Playwright page object containing search results
        
    Returns:
        List of parsed listing dictionaries
    """
    # Try both old (.s-item) and new (.s-card) eBay formats
    items = page.query_selector_all(".s-item, .s-card")
    listings: List[Dict] = []
    
    for item in items:
        try:
            # Try new format first, then fall back to old format
            title_elem = (item.query_selector(".s-card__title .su-styled-text") or 
                        item.query_selector(".s-card__title a .su-styled-text") or 
                        item.query_selector(".s-item__title"))
            if not title_elem:
                continue

            title = (title_elem.inner_text() or "").strip()
            if title == "Shop on eBay":
                continue

            # Try new format link, then old format
            link_elem = item.query_selector("a[href*='/itm/']") or item.query_selector(".s-item__link")
            url = link_elem.get_attribute("href") if link_elem else None

            # Try new format price, then old format
            price_elem = (item.query_selector(".s-card__price .su-styled-text") or 
                        item.query_selector(".s-card__attribute-row .su-styled-text.s-card__price") or
                        item.query_selector(".s-item__price"))
            price_text = price_elem.inner_text().strip() if price_elem else ""
            price = extract_price_from_text(price_text)
            if price is None:
                continue

            # Try new format condition, then old format
            condition_elem = (item.query_selector(".s-card__subtitle .su-styled-text") or 
                            item.query_selector(".s-item__condition, .s-item__subtitle, .s-item__details"))
            condition_text = (condition_elem.inner_text() if condition_elem else "").lower()
            condition: Optional[str] = None
            if "used" in condition_text or "pre-owned" in condition_text:
                condition = "Used"
            elif "new" in condition_text or "brand new" in condition_text:
                condition = "New"
            elif "open box" in condition_text:
                condition = "Open box"
            elif "for parts" in condition_text or "not working" in condition_text:
                condition = "For parts or not working"
            elif "refurbished" in condition_text:
                condition = "Certified - Refurbished"
            else:
                condition = "Not Specified"

            # Try new format location, then old format  
            location_elem = (item.query_selector(".s-card__attribute-row:has-text('Located in') .su-styled-text") or
                           item.query_selector(".s-item__location"))
            seller_location = (location_elem.inner_text().strip() if location_elem else None)
            # Clean up "Located in " prefix from new format
            if seller_location and seller_location.startswith("Located in "):
                seller_location = seller_location[11:]

            # Try new format shipping, then old format
            shipping_elem = (item.query_selector(".s-card__attribute-row:has-text('delivery') .su-styled-text, .s-card__attribute-row:has-text('Shipping') .su-styled-text") or
                           item.query_selector(".s-item__shipping"))
            shipping_info = (shipping_elem.inner_text().strip() if shipping_elem else None)

            listing_id = None
            if url:
                match = re.search(r"/itm/(\d+)", url)
                if match:
                    listing_id = match.group(1)
            cleaned_url = clean_ebay_url(url)

            # Extract brand and model information
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
            elif "king" in tl:
                brand = "King"
                if "super 20" in tl:
                    if "silversonic" in tl:
                        model = "Super 20 Silversonic"
                    else:
                        model = "Super 20"
                elif "super 21" in tl:
                    model = "Super 21"
                elif "zephyr" in tl:
                    if "special" in tl:
                        model = "Zephyr Special"
                    else:
                        model = "Zephyr"
                elif "empire" in tl:
                    model = "Empire"
            elif "eastern" in tl:
                brand = "Eastern Music"
            elif "ic/" in tl or "precision" in tl:
                brand = "IC/Precision"
            elif "conn" in tl:
                brand = "Conn"
                if "6m" in tl or "6 m" in tl:
                    model = "6M"
                elif "10m" in tl or "10 m" in tl:
                    model = "10M"
                elif "new wonder" in tl:
                    model = "New Wonder"
                elif "director" in tl:
                    model = "Director"
                elif "lady face" in tl:
                    model = "Lady Face"
            elif "sml" in tl:
                brand = "SML"
            elif "keilwerth" in tl:
                brand = "Keilwerth"
                if "sx90" in tl:
                    model = "SX90"
                elif "sx90r" in tl:
                    model = "SX90R"
                elif "shadow" in tl:
                    model = "Shadow"
            elif "couf" in tl:
                brand = "Couf"
                if "superba" in tl:
                    model = "Superba"
                elif "studio" in tl:
                    model = "Studio"
            elif "buffet" in tl:
                brand = "Buffet"
                if "super dynaction" in tl:
                    model = "Super Dynaction"
                elif "dynaction" in tl:
                    model = "Dynaction"
                elif "s1" in tl:
                    model = "S1"
            elif "yanagisawa" in tl:
                brand = "Yanagisawa"
                if "wo1" in tl or "wo-1" in tl:
                    model = "WO1"
                elif "wo2" in tl or "wo-2" in tl:
                    model = "WO2"
                elif "wo10" in tl or "wo-10" in tl:
                    model = "WO10"
                elif "a991" in tl:
                    model = "A991"
                elif "t991" in tl:
                    model = "T991"
            elif "martin" in tl:
                brand = "Martin"
                if "committee" in tl:
                    model = "Committee"
                elif "handcraft" in tl:
                    model = "Handcraft"
                elif "indiana" in tl:
                    model = "Indiana"
                elif "magna" in tl:
                    model = "Magna"

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
                    "url": cleaned_url if listing_id else url,
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
