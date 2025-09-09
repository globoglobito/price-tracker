"""
Tests for configuration settings module.
"""
import os
from scraper.config import settings


def test_get_search_term_default():
    """Test default search term when env var not set."""
    # Clear environment
    if 'SEARCH_TERM' in os.environ:
        del os.environ['SEARCH_TERM']
    
    assert settings.get_search_term() == "Selmer Mark VI"


def test_get_search_term_from_env():
    """Test search term from environment variable."""
    os.environ['SEARCH_TERM'] = "Test Search"
    assert settings.get_search_term() == "Test Search"
    
    # Cleanup
    del os.environ['SEARCH_TERM']


def test_get_max_pages_default():
    """Test default max pages when env var not set."""
    if 'MAX_PAGES' in os.environ:
        del os.environ['MAX_PAGES']
    
    assert settings.get_max_pages() == 0


def test_get_max_pages_from_env():
    """Test max pages from environment variable."""
    os.environ['MAX_PAGES'] = "5"
    assert settings.get_max_pages() == 5
    
    # Cleanup
    del os.environ['MAX_PAGES']


def test_get_max_pages_invalid():
    """Test max pages with invalid value defaults to 0."""
    os.environ['MAX_PAGES'] = "invalid"
    assert settings.get_max_pages() == 0
    
    # Cleanup
    del os.environ['MAX_PAGES']


def test_is_headless_default():
    """Test default headless mode."""
    if 'HEADLESS' in os.environ:
        del os.environ['HEADLESS']
    
    assert settings.is_headless() is True


def test_is_headless_false():
    """Test headless mode set to false."""
    os.environ['HEADLESS'] = "false"
    assert settings.is_headless() is False
    
    # Cleanup
    del os.environ['HEADLESS']


def test_get_browser_type():
    """Test browser type configuration."""
    if 'BROWSER' in os.environ:
        del os.environ['BROWSER']
    
    assert settings.get_browser_type() == "chromium"
    
    os.environ['BROWSER'] = "firefox"
    assert settings.get_browser_type() == "firefox"
    
    # Cleanup
    del os.environ['BROWSER']


def test_get_block_detection_config():
    """Test block detection configuration."""
    # Clear environment
    for key in ['BLOCK_RECHECK', 'BLOCK_MAX_RETRIES', 'BLOCK_WAIT_MIN_S', 'BLOCK_WAIT_MAX_S', 'BLOCK_RELOAD']:
        if key in os.environ:
            del os.environ[key]
    
    config = settings.get_block_detection_config()
    
    assert config['recheck'] is True
    assert config['max_retries'] == 3
    assert config['wait_min_s'] == 5.0
    assert config['wait_max_s'] == 10.0
    assert config['reload'] is True


def test_get_enrich_jitter():
    """Test enrichment jitter configuration."""
    if 'ENRICH_JITTER_MIN_S' in os.environ:
        del os.environ['ENRICH_JITTER_MIN_S']
    if 'ENRICH_JITTER_MAX_S' in os.environ:
        del os.environ['ENRICH_JITTER_MAX_S']
    
    jitter_min, jitter_max = settings.get_enrich_jitter()
    assert jitter_min == 0.5
    assert jitter_max == 2.0


if __name__ == "__main__":
    test_get_search_term_default()
    test_get_search_term_from_env()
    test_get_max_pages_default()
    test_get_max_pages_from_env()
    test_get_max_pages_invalid()
    test_is_headless_default()
    test_is_headless_false()
    test_get_browser_type()
    test_get_block_detection_config()
    test_get_enrich_jitter()
    print("✅ All config settings tests passed!")
