"""
Tests for results parser module.
"""
from scraper.extractors.results_parser import extract_price_from_text, clean_ebay_url


def test_extract_price_from_text_valid():
    """Test price extraction from valid price strings."""
    assert extract_price_from_text("$1,234.56") == 1234.56
    assert extract_price_from_text("US $1,299.00") == 1299.00
    assert extract_price_from_text("£1,299") == 1299.0
    assert extract_price_from_text("1234") == 1234.0
    assert extract_price_from_text("99.99") == 99.99


def test_extract_price_from_text_invalid():
    """Test price extraction from invalid or empty strings."""
    assert extract_price_from_text("") is None
    assert extract_price_from_text(None) is None
    assert extract_price_from_text("No price") is None
    assert extract_price_from_text("Free shipping") is None
    assert extract_price_from_text("Call for price") is None


def test_clean_ebay_url_valid():
    """Test URL cleaning for valid eBay URLs."""
    # URL with parameters should be cleaned
    assert clean_ebay_url("https://www.ebay.com/itm/277260906969?_skw=foo&hash=bar") == "https://www.ebay.com/itm/277260906969"
    
    # Simple URL should remain the same
    assert clean_ebay_url("https://www.ebay.com/itm/123456789") == "https://www.ebay.com/itm/123456789"
    
    # Different domain but with /itm/ should be normalized
    assert clean_ebay_url("https://ebay.co.uk/itm/987654321/some-title") == "https://www.ebay.com/itm/987654321"


def test_clean_ebay_url_invalid():
    """Test URL cleaning for invalid URLs."""
    assert clean_ebay_url(None) is None
    assert clean_ebay_url("") == ""
    assert clean_ebay_url("not-a-url") == "not-a-url"
    assert clean_ebay_url("https://www.amazon.com/product/123") == "https://www.amazon.com/product/123"


def test_clean_ebay_url_no_item_id():
    """Test URL cleaning for eBay URLs without item IDs."""
    # URL without /itm/ should be returned as-is
    url = "https://www.ebay.com/sch/i.html?_nkw=saxophone"
    assert clean_ebay_url(url) == url


if __name__ == "__main__":
    test_extract_price_from_text_valid()
    test_extract_price_from_text_invalid()
    test_clean_ebay_url_valid()
    test_clean_ebay_url_invalid()
    test_clean_ebay_url_no_item_id()
    print("✅ All results parser tests passed!")
