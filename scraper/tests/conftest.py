import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    # Avoid running pytest under an event loop that breaks Playwright sync API in other suites
    return "asyncio"




