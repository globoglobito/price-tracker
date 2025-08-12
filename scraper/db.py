from __future__ import annotations

import os
import psycopg2
from psycopg2.extras import execute_batch
from typing import List, Dict, Any


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


def upsert_listings(listings: List[Dict[str, Any]]) -> int:
    if not listings:
        return 0

    # Normalize and project to the DB columns
    rows: List[tuple] = []
    for l in listings:
        rows.append(
            (
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
        title, url, website, listing_id,
        price, currency, original_price, shipping_cost,
        brand, model, type, condition,
        seller_location, shipping_info, has_best_offer, auction_end_time,
        watchers_count, sold_quantity, available_quantity, date_listed, notes
    ) VALUES (
        %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s, %s
    )
    ON CONFLICT (website, listing_id) DO UPDATE SET
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


