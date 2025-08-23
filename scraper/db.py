from __future__ import annotations

import os
import psycopg2
from psycopg2.extras import execute_batch
from typing import List, Dict, Any, Set


def _connect():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        # Fallback compose from discrete vars (optional)
        host = os.environ.get("DB_HOST", "postgres-service")
        port = os.environ.get("DB_PORT", "5432")
        name = os.environ.get("DB_NAME", "price_tracker_db")
        user = os.environ.get("DB_USER", "price_tracker_user")
        pwd = os.environ.get("DB_PASSWORD", "")
        database_url = f"postgresql://{user}:{pwd}@{host}:{port}/{name}"
    return psycopg2.connect(database_url)


def get_or_create_search(search_term: str, website: str) -> int:
    """Upsert a search term and return its id."""
    sql = (
        """
        INSERT INTO price_tracker.searches (search_term, website, created_at, updated_at, last_scraped_at)
        VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (search_term, website) DO UPDATE SET
            updated_at = CURRENT_TIMESTAMP,
            last_scraped_at = CURRENT_TIMESTAMP
        RETURNING id
        """
    )
    conn = _connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (search_term, website))
                row = cur.fetchone()
                return int(row[0])
    finally:
        conn.close()


def fetch_existing_listing_ids(search_id: int, website: str) -> Set[str]:
    """Return set of listing_id for a given search and website."""
    sql = (
        """
        SELECT listing_id
        FROM price_tracker.listings
        WHERE search_id = %s AND website = %s AND listing_id IS NOT NULL
        """
    )
    conn = _connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (search_id, website))
                return {r[0] for r in cur.fetchall()}
    finally:
        conn.close()


def mark_missing_inactive(search_id: int, website: str, active_listing_ids: Set[str]) -> int:
    """Mark listings not present in active_listing_ids as inactive.

    Safety: if active_listing_ids is empty, skip to avoid deactivating everything on blocked runs.
    Returns number of rows updated.
    """
    if not active_listing_ids:
        return 0
    placeholders = ",".join(["%s"] * len(active_listing_ids))
    sql = (
        f"""
        UPDATE price_tracker.listings
        SET is_active = FALSE,
            ended_at = COALESCE(ended_at, CURRENT_TIMESTAMP)
        WHERE search_id = %s
          AND website = %s
          AND listing_id IS NOT NULL
          AND listing_id NOT IN ({placeholders})
          AND is_active = TRUE
        """
    )
    params: List[Any] = [search_id, website, *list(active_listing_ids)]
    conn = _connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.rowcount or 0
    finally:
        conn.close()


def upsert_listings(listings: List[Dict[str, Any]], search_id: int | None = None) -> int:
    if not listings:
        return 0

    # Normalize and project to the DB columns
    rows: List[tuple] = []
    for l in listings:
        rows.append(
            (
                search_id,
                l.get("title"),
                l.get("url"),
                (l.get("website") or "ebay"),
                l.get("listing_id"),
                l.get("price"),
                l.get("currency", "USD"),
                l.get("original_price"),
                l.get("shipping_cost"),
                l.get("brand"),
                l.get("model"),
                l.get("type"),
                l.get("condition"),
                l.get("seller_location") or l.get("location_text"),
                l.get("shipping_info"),
                bool(l.get("has_best_offer")) if l.get("has_best_offer") is not None else None,
                l.get("auction_end_time"),
                None,  # watchers_count
                None,  # sold_quantity
                None,  # available_quantity
                None,  # date_listed
                None,  # notes
            )
        )

    sql = """
    INSERT INTO price_tracker.listings (
        search_id,
        title, url, website, listing_id,
        price, currency, original_price, shipping_cost,
        brand, model, type, condition,
        seller_location, shipping_info, has_best_offer, auction_end_time,
        watchers_count, sold_quantity, available_quantity, date_listed, notes,
        first_seen_at, last_seen_at, is_active
    ) VALUES (
        %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, TRUE
    )
    ON CONFLICT (website, listing_id) DO UPDATE SET
        search_id = COALESCE(EXCLUDED.search_id, price_tracker.listings.search_id),
        title = EXCLUDED.title,
        url = EXCLUDED.url,
        price = EXCLUDED.price,
        currency = EXCLUDED.currency,
        original_price = EXCLUDED.original_price,
        shipping_cost = EXCLUDED.shipping_cost,
        brand = EXCLUDED.brand,
        model = EXCLUDED.model,
        type = EXCLUDED.type,
        condition = EXCLUDED.condition,
        seller_location = EXCLUDED.seller_location,
        shipping_info = EXCLUDED.shipping_info,
        has_best_offer = EXCLUDED.has_best_offer,
        auction_end_time = EXCLUDED.auction_end_time,
        last_seen_at = CURRENT_TIMESTAMP,
        is_active = TRUE,
        scraped_at = CURRENT_TIMESTAMP
    """

    conn = _connect()
    try:
        with conn:
            with conn.cursor() as cur:
                execute_batch(cur, sql, rows, page_size=100)
        return len(rows)
    finally:
        conn.close()


