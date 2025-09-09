#!/usr/bin/env bash
set -euo pipefail

echo "[scraper-unit] Starting offline scraper tests (no network)"

# Prefer project venvs if present
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
  echo "[scraper-unit] Using venv: .venv"
elif [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
  echo "[scraper-unit] Using venv: venv"
else
  echo "[scraper-unit] No venv detected; running with system Python"
fi

export PYTHONPATH="$PWD"
python3 - <<'PY' || true
import sys, platform
print(f"[scraper-unit] Python: {sys.version.split()[0]} ({platform.system()} {platform.release()})")
try:
  import importlib.metadata as md
  # BeautifulSoup distro name is 'beautifulsoup4'
  packages = {
    'pytest': 'pytest',
    'bs4': 'beautifulsoup4',
    'lxml': 'lxml',
  }
  for mod, dist in packages.items():
    try:
      v = md.version(dist)
      print(f"[scraper-unit] dep {mod}=={v}")
    except Exception:
      print(f"[scraper-unit] dep {mod} not installed")
except Exception:
  pass
PY

# Check for required deps; skip gracefully if missing
if python3 -c "import importlib; [importlib.import_module(m) for m in ('pytest','bs4','lxml')]" >/dev/null 2>&1; then
  echo "[scraper-unit] Collecting tests..."
  pytest -q --collect-only scraper/tests | sed -n '1,200p'
  echo "[scraper-unit] Running tests verbosely..."
  pytest -vv -s --durations=10 scraper/tests
  echo "[scraper-unit] OK"
else
  echo "[scraper-unit] Dependencies missing (pytest/bs4/lxml). Skipping scraper unit tests."
  echo "[scraper-unit] To run locally: pip install -r tests/requirements-scraper.txt && pip install beautifulsoup4 lxml"
fi

