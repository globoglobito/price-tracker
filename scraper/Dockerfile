# Use official Playwright image with browsers and system deps preinstalled
FROM mcr.microsoft.com/playwright/python:v1.46.0-jammy

WORKDIR /app

# Copy scraper requirements and install
COPY scraper/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy scraper code
COPY scraper/ /app/scraper/

# Environment defaults (can be overridden via K8s envs)
ENV HEADLESS=true \
    MAX_PAGES=1 \
    SEARCH_TERM="Selmer Mark VI" \
    BROWSER=chromium

# Non-root already configured in base image (user pwuser)
USER pwuser

# Run the scraper
CMD ["python", "scraper/playwright_ebay_scraper.py"]


