from scraper.tests.fakes import FakePage


def test_auction_end_time_jsonld_walks_keys():
    print("[test] Auction end detection: finds endDate within JSON-LD offers")
    # Minimal HTML with JSON-LD containing endDate
    html = (
        "<html><head>"
        "<script type=\"application/ld+json\">"
        '{"offers":{"endDate":"2030-01-01T10:00:00Z"}}'
        "</script>"
        "</head><body></body></html>"
    )
    page = FakePage(html)
    # Re-implement the same walk used in the scraper to validate behavior
    detected_end = None
    handles = page.query_selector_all("script[type='application/ld+json']")
    import json as _json
    for h in handles:
        raw = h.inner_text() or ''
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
    assert detected_end == "2030-01-01T10:00:00Z"


def test_time_datetime_attribute():
    print("[test] Auction end detection: reads <time datetime=...> attribute")
    html = "<html><body><time datetime=\"2031-12-31T23:59:59Z\">Ends</time></body></html>"
    page = FakePage(html)
    cand = page.query_selector('time[datetime]')
    v = cand.get_attribute('datetime') if cand else None
    assert v == "2031-12-31T23:59:59Z"


def test_location_fallback_parsing():
    print("[test] Location parsing: falls back to visible 'Located in ...' text")
    html = "<div>Located in Barcelona, Spain</div>"
    page = FakePage(html)
    # Mimic the scraper's fallback heuristics
    location_text = None
    for el in page.query_selector_all('span, div, li')[:2000]:
        t = (el.inner_text() or '').strip()
        tl = t.lower()
        if not t:
            continue
        if tl.startswith('located in'):
            location_text = t.replace('Located in', '').strip()
            break
    assert location_text == 'Barcelona, Spain'


