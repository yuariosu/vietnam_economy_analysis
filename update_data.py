#!/usr/bin/env python3
"""
update_data.py – Vietnam Economy Analysis: Data Updater
=======================================================
1. Checks GitHub for the latest gso-macro-monitor release
2. Downloads & extracts extracted_database.json if a newer release exists
3. Reports data freshness for all files

Usage:
    python3 update_data.py            # check and update if needed
    python3 update_data.py --force    # force re-download even if up-to-date
    python3 update_data.py --check    # dry-run: report status only

Data sources:
  SDMX archive  : https://github.com/thanhqtran/gso-macro-monitor/releases
  E02.xx files  : GSO Vietnam PxWeb (manual download required — see below)

Manual update for E02.xx files (PxWeb is not publicly accessible via API):
  1. Visit https://www.gso.gov.vn/en/px-web/ or https://www.nso.gov.vn/en/px-web/
  2. Navigate to Chapter 2 (Population)
  3. Download each table as JSON-stat and replace the files in this directory
"""

import os
import sys
import json
import zipfile
import tempfile
import hashlib
import argparse
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

BASE = os.path.dirname(os.path.abspath(__file__))
RELEASES_API = "https://api.github.com/repos/thanhqtran/gso-macro-monitor/releases"
META_FILE    = os.path.join(BASE, ".data_meta.json")

# ── Data files and their expected freshness ──────────────────────────────────
E02_FILES = {
    "E02.01.json":   "Area, population, density by province",
    "E02.02.json":   "National avg population by sex & residence",
    "E02.03-07.json":"Province avg population by sex & residence",
    "E02.08.json":   "Sex ratio by residence",
}

ANSI_GREEN  = "\033[92m"
ANSI_YELLOW = "\033[93m"
ANSI_RED    = "\033[91m"
ANSI_RESET  = "\033[0m"
ANSI_BOLD   = "\033[1m"

def ok(msg):    print(f"  {ANSI_GREEN}✓{ANSI_RESET} {msg}")
def warn(msg):  print(f"  {ANSI_YELLOW}!{ANSI_RESET} {msg}")
def err(msg):   print(f"  {ANSI_RED}✗{ANSI_RESET} {msg}")
def info(msg):  print(f"  {ANSI_BOLD}→{ANSI_RESET} {msg}")


def _load_meta():
    if os.path.exists(META_FILE):
        with open(META_FILE) as f:
            return json.load(f)
    return {}

def _save_meta(meta):
    with open(META_FILE, "w") as f:
        json.dump(meta, f, indent=2)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _fetch_json(url):
    req = Request(url, headers={"User-Agent": "vietnam-economy-updater/1.0"})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def check_sdmx_release():
    """Return (latest_tag, latest_date, download_url) from GitHub releases."""
    print("\nChecking gso-macro-monitor releases …")
    try:
        releases = _fetch_json(RELEASES_API)
    except (URLError, HTTPError) as e:
        err(f"Cannot reach GitHub API: {e}")
        return None, None, None

    if not releases:
        warn("No releases found")
        return None, None, None

    latest = releases[0]
    tag    = latest["tag_name"]
    date   = latest["published_at"][:10]
    assets = latest.get("assets", [])
    url    = next((a["browser_download_url"] for a in assets
                   if a["name"].endswith(".json.zip")), None)
    return tag, date, url


def download_sdmx(url, tag, force=False):
    """Download and extract extracted_database.json. Returns True if updated."""
    meta = _load_meta()
    current_tag = meta.get("sdmx_tag")

    if not force and current_tag == tag:
        ok(f"SDMX archive already up-to-date: {tag}")
        return False

    info(f"Downloading {tag} …")
    try:
        req = Request(url, headers={"User-Agent": "vietnam-economy-updater/1.0"})
        with urlopen(req, timeout=120) as resp:
            data = resp.read()
    except (URLError, HTTPError) as e:
        err(f"Download failed: {e}")
        return False

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        with zipfile.ZipFile(tmp_path) as zf:
            names = zf.namelist()
            json_files = [n for n in names if n.endswith(".json")]
            if not json_files:
                err("No JSON file found in archive")
                return False
            target = json_files[0]
            dest   = os.path.join(BASE, "extracted_database.json")
            with zf.open(target) as src, open(dest, "wb") as dst:
                dst.write(src.read())
            ok(f"extracted_database.json updated ({os.path.getsize(dest)//1024}KB)")
    finally:
        os.unlink(tmp_path)

    # Update metadata
    meta["sdmx_tag"]          = tag
    meta["sdmx_updated"]      = datetime.now(timezone.utc).isoformat()
    meta["sdmx_release_date"] = tag
    _save_meta(meta)
    return True


def report_e02_freshness():
    """Print freshness info for each E02.xx JSON-stat file."""
    print("\nE02.xx Population files (JSON-stat):")
    all_ok = True
    for fname, desc in E02_FILES.items():
        path = os.path.join(BASE, fname)
        if not os.path.exists(path):
            err(f"{fname} — MISSING")
            all_ok = False
            continue
        with open(path, encoding="utf-8") as f:
            content = f.read().rstrip("\x00").strip()
        ds = json.loads(content)["dataset"]
        updated = ds.get("updated", "unknown")
        yr_labels = ds["dimension"].get("Year", {}).get("category", {}).get("label", {})
        latest_yr = list(yr_labels.values())[-1] if yr_labels else "?"
        mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d")
        ok(f"{fname}  updated={updated[:10]}  latest_year={latest_yr}  file_mtime={mtime}")
    if not all_ok:
        warn("Some E02.xx files missing — download manually from GSO PxWeb")
    return all_ok


def report_sdmx_freshness():
    """Print freshness info for extracted_database.json."""
    print("\nSDMX archive (extracted_database.json):")
    path = os.path.join(BASE, "extracted_database.json")
    if not os.path.exists(path):
        err("extracted_database.json — MISSING")
        return False

    meta = _load_meta()
    tag  = meta.get("sdmx_tag", "unknown (pre-metadata)")
    upd  = meta.get("sdmx_updated", "unknown")[:10]
    size = os.path.getsize(path) // 1024
    mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d")
    ok(f"extracted_database.json  release={tag}  downloaded={upd}  size={size}KB  mtime={mtime}")
    return True


def report_output_freshness():
    """List output PNGs and their generation times."""
    print("\nOutput charts (output/):")
    out_dir = os.path.join(BASE, "output")
    pngs = sorted(p for p in os.listdir(out_dir) if p.endswith(".png")) if os.path.isdir(out_dir) else []
    if not pngs:
        warn("No charts generated yet — run: python3 analyze.py")
        return
    newest = max(os.path.getmtime(os.path.join(out_dir, p)) for p in pngs)
    oldest = min(os.path.getmtime(os.path.join(out_dir, p)) for p in pngs)
    ok(f"{len(pngs)} charts found  |  "
       f"oldest={datetime.fromtimestamp(oldest).strftime('%Y-%m-%d')}  "
       f"newest={datetime.fromtimestamp(newest).strftime('%Y-%m-%d')}")


def main():
    parser = argparse.ArgumentParser(description="Update Vietnam economy data")
    parser.add_argument("--force",  action="store_true", help="Force re-download")
    parser.add_argument("--check",  action="store_true", help="Dry-run: report only")
    parser.add_argument("--regen",  action="store_true", help="Regenerate charts after update")
    args = parser.parse_args()

    print(f"{ANSI_BOLD}Vietnam Economy Data Updater{ANSI_RESET}")
    print(f"Current time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 55)

    # ── Step 1: Check SDMX release ────────────────────────────────────────
    tag, date, url = check_sdmx_release()
    if tag:
        info(f"Latest release: {tag} ({date})")
        meta = _load_meta()
        current = meta.get("sdmx_tag", "none")
        if current == tag:
            ok(f"Already on latest: {tag}")
        else:
            warn(f"Update available: {current} → {tag}")
            if not args.check:
                download_sdmx(url, tag, force=args.force)

    # ── Step 2: Report file freshness ────────────────────────────────────
    report_sdmx_freshness()
    report_e02_freshness()
    report_output_freshness()

    # ── Step 3: Regenerate charts if requested ───────────────────────────
    if args.regen and not args.check:
        print(f"\n{ANSI_BOLD}Regenerating charts …{ANSI_RESET}")
        import subprocess
        result = subprocess.run(
            [sys.executable, os.path.join(BASE, "analyze.py")],
            capture_output=False
        )
        if result.returncode == 0:
            ok("Charts regenerated successfully")
        else:
            err("Chart generation failed — check output above")

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 55)
    meta = _load_meta()
    sdmx_tag = meta.get("sdmx_tag", "unknown")
    print(f"SDMX data:  {sdmx_tag}")
    print(f"E02 data:   2024 (preliminary) — manual update required")
    print(f"\n{ANSI_YELLOW}To update E02.xx files:{ANSI_RESET}")
    print("  1. Visit https://www.gso.gov.vn/en/px-web/")
    print("  2. Navigate: Population → Download as JSON-stat")
    print("  3. Replace E02.01.json, E02.02.json, E02.03-07.json, E02.08.json")
    print(f"\n{ANSI_YELLOW}To regenerate all charts after update:{ANSI_RESET}")
    print("  python3 update_data.py --regen")


if __name__ == "__main__":
    main()
