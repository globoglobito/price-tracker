from scraper.playwright_ebay_scraper import EbayBrowserScraper
from scraper.extractors.results_parser import extract_price_from_text


def test_clean_ebay_url():
    print("[test] URL canonicalization: normalizes listing links to https://www.ebay.com/itm/<id>")
    s = EbayBrowserScraper("x")
    assert s._clean_ebay_url("https://www.ebay.com/itm/277260906969?_skw=foo&hash=bar") == "https://www.ebay.com/itm/277260906969"
    assert s._clean_ebay_url("https://www.ebay.com/itm/123") == "https://www.ebay.com/itm/123"
    assert s._clean_ebay_url(None) is None


def test_extract_price():
    print("[test] Price extraction: parses US/UK formats; returns None when absent")
    assert extract_price_from_text("US $1,299.00") == 1299.00
    assert extract_price_from_text("£1,299") == 1299.00
    assert extract_price_from_text("No price") is None



