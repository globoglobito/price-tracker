from scraper.playwright_ebay_scraper import EbayBrowserScraper
from scraper.tests.fakes import FakePage


def test_block_detection_true():
    print("[test] Block detection: should flag human verification text as a block page")
    html = "<body>Verify you're a human. Reference ID: 12345</body>"
    page = FakePage(html)
    s = EbayBrowserScraper("x")
    assert s._is_block_page(page) is True


def test_block_detection_false():
    print("[test] Block detection: normal page should not be flagged as a block")
    html = "<body><h1>Vintage saxophone</h1></body>"
    page = FakePage(html)
    s = EbayBrowserScraper("x")
    assert s._is_block_page(page) is False


