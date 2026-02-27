#!/usr/bin/env python3
"""Add URLs from a .txt file into url_batches/all_links.txt with deduplication."""

import argparse
from pathlib import Path

import url_manager


def main() -> int:
    parser = argparse.ArgumentParser(description="Append new URLs from a text file to the master URL list.")
    parser.add_argument("file", help="Path to .txt file containing URLs")
    args = parser.parse_args()

    source_file = Path(args.file).expanduser()
    if not source_file.exists():
        print(f"[ERROR] File not found: {source_file}")
        return 1

    content = source_file.read_text(encoding="utf-8", errors="ignore")
    parsed_urls = url_manager.parse_urls_from_text(content)
    if not parsed_urls:
        print("[INFO] No valid URLs found in input file.")
        return 0

    added, skipped = url_manager.append_new_urls(parsed_urls)
    print(f"[DONE] Parsed: {len(parsed_urls)} | Added: {added} | Skipped duplicates: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

