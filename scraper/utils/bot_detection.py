"""
Bot detection and anti-bot evasion utilities for web scraping.
"""
from typing import Any


def is_block_page(page: Any) -> bool:
    """
    Detect anti-bot challenge using visible body text and strong structural hints.

    Args:
        page: Playwright page object

    Returns:
        True if page appears to be a bot detection/challenge page

    Avoid scanning raw HTML for generic tokens (like CSS class names) to reduce false positives.
    """
    body_text = ""
    try:
        # Only visible text content
        if page.is_visible('body'):
            body_text = (page.inner_text('body') or "").lower()
    except Exception:
        body_text = ""

    # Strong textual markers typically shown to users
    text_markers = [
        "verify you're a human",
        "not a robot",
        "enter the characters you see",
        "access to this page has been denied",
        "checking your browser before you access ebay",
        "pardon our interruption",
        "reference id:",
    ]
    if any(marker in body_text for marker in text_markers if marker):
        return True

    # Structural/metadata hints (best-effort, require at least one visible hint to be safer)
    try:
        if page.locator("form#destForm").count() > 0:
            return True
        if page.locator("script[src*=\"challenge-\"]").count() > 0 and (
            "checking your browser" in body_text or "reference id" in body_text
        ):
            return True
    except Exception:
        pass
    return False


def save_debug_snapshot(page: Any, debug_snapshot_dir: str, label: str) -> None:
    """
    Save debug snapshots of the current page for troubleshooting.

    Args:
        page: Playwright page object
        debug_snapshot_dir: Directory to save snapshots
        label: Label for the snapshot files
    """
    if not debug_snapshot_dir:
        return
        
    try:
        import os
        import datetime
        
        os.makedirs(debug_snapshot_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base = os.path.join(debug_snapshot_dir, f"{timestamp}_{label}")
        
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
        print(f"Saved debug snapshot: {base}.[png|html]")
    except Exception:
        pass
