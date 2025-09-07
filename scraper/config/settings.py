"""
Configuration and environment variable handling for the eBay scraper.
"""
import os
from typing import Optional


def get_search_term() -> str:
    """Get the search term from environment or use default."""
    return os.environ.get("SEARCH_TERM", "Selmer Mark VI")


def get_max_pages() -> int:
    """Get maximum pages to scrape. 0 means unlimited."""
    try:
        return int(os.environ.get("MAX_PAGES", "0"))
    except ValueError:
        return 0


def get_enrich_limit() -> int:
    """Get maximum listings to enrich. 0 means unlimited."""
    try:
        return int(os.environ.get("ENRICH_LIMIT", "0"))
    except ValueError:
        return 0


def is_headless() -> bool:
    """Check if browser should run in headless mode."""
    return os.environ.get("HEADLESS", "true").lower() in ("1", "true", "yes")


def get_browser_type() -> str:
    """Get browser type to use."""
    return os.environ.get("BROWSER", "chromium")


def get_proxy_url() -> Optional[str]:
    """Get proxy URL if configured."""
    http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    return http_proxy or https_proxy


def get_user_data_dir() -> str:
    """Get browser user data directory."""
    return os.environ.get("USER_DATA_DIR", "/tmp/profile-ebay")


def get_snapshot_dir() -> str:
    """Get directory for listing snapshots."""
    return os.environ.get("SNAPSHOT_DIR", "/tmp/snapshots")


def get_debug_snapshot_dir() -> Optional[str]:
    """Get directory for debug snapshots."""
    return os.environ.get("DEBUG_SNAPSHOT_DIR")


def get_slow_mo_ms() -> int:
    """Get slow motion delay in milliseconds."""
    try:
        return int(os.environ.get("SLOW_MO_MS", "50"))
    except ValueError:
        return 50


def get_timeout_ms() -> int:
    """Get general timeout in milliseconds."""
    try:
        return int(os.environ.get("TIMEOUT_MS", "30000"))
    except ValueError:
        return 30000


def get_main_page_min_wait_s() -> float:
    """Get minimum wait after results page before enrichment."""
    try:
        return float(os.environ.get("MAIN_PAGE_MIN_WAIT_S", "6"))
    except ValueError:
        return 6.0


def get_enrich_jitter() -> tuple[float, float]:
    """Get enrichment jitter range (min, max) in seconds."""
    try:
        jitter_min = float(os.environ.get("ENRICH_JITTER_MIN_S", "0.5"))
        jitter_max = float(os.environ.get("ENRICH_JITTER_MAX_S", "2.0"))
        return jitter_min, jitter_max
    except ValueError:
        return 0.5, 2.0


def get_human_settle_range() -> tuple[float, float]:
    """Get human settle time range (min, max) in seconds."""
    try:
        settle_min = float(os.environ.get("HUMAN_SETTLE_MIN_S", "2"))
        settle_max = float(os.environ.get("HUMAN_SETTLE_MAX_S", "8"))
        return settle_min, settle_max
    except ValueError:
        return 2.0, 8.0


def is_settle_disabled() -> bool:
    """Check if human-like settling is disabled."""
    return os.environ.get("DISABLE_SETTLE", "false").lower() in ("1", "true", "yes")


def get_block_detection_config() -> dict:
    """Get block detection and retry configuration."""
    try:
        return {
            "recheck": os.environ.get("BLOCK_RECHECK", "true").lower() in ("1", "true", "yes"),
            "max_retries": int(os.environ.get("BLOCK_MAX_RETRIES", "3")),
            "wait_min_s": float(os.environ.get("BLOCK_WAIT_MIN_S", "5")),
            "wait_max_s": float(os.environ.get("BLOCK_WAIT_MAX_S", "10")),
            "reload": os.environ.get("BLOCK_RELOAD", "true").lower() in ("1", "true", "yes")
        }
    except ValueError:
        return {
            "recheck": True,
            "max_retries": 3,
            "wait_min_s": 5.0,
            "wait_max_s": 10.0,
            "reload": True
        }


def get_wait_on_page_s() -> float:
    """Get wait time on page in seconds."""
    try:
        return float(os.environ.get("WAIT_ON_PAGE_S", "8"))
    except ValueError:
        return 8.0


def get_listing_max_s() -> float:
    """Get maximum time to spend on each listing in seconds."""
    try:
        return float(os.environ.get("LISTING_MAX_S", "45"))
    except ValueError:
        return 45.0


def get_enrich_nav_mode() -> str:
    """Get enrichment navigation mode (click or goto)."""
    return os.environ.get("ENRICH_NAV_MODE", "click")
