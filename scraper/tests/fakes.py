from bs4 import BeautifulSoup


class FakeElement:
    def __init__(self, el):
        self._el = el

    def inner_text(self, timeout: int | None = None):  # ignore timeout for compatibility
        return self._el.get_text(separator="", strip=False)

    def get_attribute(self, name: str):
        return self._el.get(name)


class FakeLocator:
    def __init__(self, soup: BeautifulSoup, selector: str):
        self._matches = soup.select(selector)

    def count(self) -> int:
        return len(self._matches)

    @property
    def first(self):
        return FakeElement(self._matches[0]) if self._matches else None


class FakePage:
    def __init__(self, html: str):
        self._soup = BeautifulSoup(html or "", "lxml")

    def set_default_timeout(self, timeout_ms: int) -> None:
        """Mock implementation of set_default_timeout for testing."""
        pass

    def is_visible(self, selector: str) -> bool:
        return len(self._soup.select(selector)) > 0

    def inner_text(self, selector: str) -> str:
        els = self._soup.select(selector)
        if not els:
            return ""
        # Join text from all matches to emulate Playwright's behavior in our use cases
        return "".join(FakeElement(el).inner_text() for el in els)

    def locator(self, selector: str) -> FakeLocator:
        return FakeLocator(self._soup, selector)

    def query_selector(self, selector: str):
        el = self._soup.select_one(selector)
        return FakeElement(el) if el is not None else None

    def query_selector_all(self, selector: str):
        return [FakeElement(el) for el in self._soup.select(selector)]




