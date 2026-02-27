"""URL management for master URL list (url_batches/all_links.txt)"""
import logging
import re
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

MASTER_FILE = Path('url_batches/all_links.txt')


def load_master_urls() -> set[str]:
    """Load existing URLs from master file."""
    if not MASTER_FILE.exists():
        logger.warning(f"{MASTER_FILE} not found, will create on first append")
        return set()
    
    with open(MASTER_FILE, 'r', encoding='utf-8') as f:
        urls = {line.strip() for line in f if line.strip() and line.strip().startswith('http')}
    
    logger.info(f"Loaded {len(urls)} URLs from {MASTER_FILE}")
    return urls


def parse_urls_from_text(text: str) -> list[str]:
    """Extract valid HTTP/HTTPS URLs from text, one per line."""
    lines = text.strip().split('\n')
    urls = []
    
    # Regex for http/https URLs
    url_pattern = re.compile(r'https?://[^\s]+')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Try direct match first (most common case)
        if line.startswith('http://') or line.startswith('https://'):
            urls.append(line)
        else:
            # Extract URLs from line
            matches = url_pattern.findall(line)
            urls.extend(matches)
    
    logger.info(f"Parsed {len(urls)} URLs from input text")
    return urls


def append_new_urls(new_urls: list[str]) -> tuple[int, int]:
    """
    Append new URLs to master file, deduplicating against existing.
    
    Returns:
        (added_count, skipped_count)
    """
    existing = load_master_urls()
    
    # Deduplicate
    to_add = [url for url in new_urls if url not in existing]
    skipped = len(new_urls) - len(to_add)
    
    if not to_add:
        logger.info(f"No new URLs to add (all {len(new_urls)} already exist)")
        return 0, skipped
    
    # Append to file
    with open(MASTER_FILE, 'a', encoding='utf-8') as f:
        for url in to_add:
            f.write(f"{url}\n")
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"[{timestamp}] Appended {len(to_add)} new URLs to {MASTER_FILE} (skipped {skipped} duplicates)")
    
    return len(to_add), skipped
