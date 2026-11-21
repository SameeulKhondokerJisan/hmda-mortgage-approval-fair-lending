"""Download the 2025 HMDA home-purchase records and two small lookup files into data/raw/.

Sources (public, no account needed):
* HMDA Data Browser API (CFPB / FFIEC): nationwide 2025 loan application records for home purchase
  loans that were originated, approved but not accepted, or denied (about 4.4 million rows, 1.7 GB).
* HMDA filers list for 2025: lender legal entity identifier (LEI) and name.
* Census Bureau 2020 county codes: county names for the FIPS codes in the records.

Usage:
    python -m src.download_data
"""
from __future__ import annotations

from src import config
from src._fetch import fetch, sha256, write_manifest


def main() -> None:
    files = [(config.LAR_URL, config.LAR_CSV), (config.FILERS_URL, config.FILERS_JSON),
             (config.COUNTY_URL, config.COUNTY_TXT)]
    entries = []
    for url, dest in files:
        path = fetch(url, dest)
        print(f"ok  {path.name:35s} {path.stat().st_size / 1e6:9.1f} MB")
        entries.append({"file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path), "url": url})
    write_manifest(config.RAW_DIR, entries)


if __name__ == "__main__":
    main()
