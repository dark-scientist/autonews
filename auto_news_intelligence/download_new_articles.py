#!/usr/bin/env python3
"""Download HTML articles from URLs in 25_02_links.txt"""

import requests
import hashlib
import time
from pathlib import Path
from urllib.parse import urlparse

def download_article(url, output_dir):
    """Download HTML from URL and save to file"""
    try:
        # Create filename from URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        domain = urlparse(url).netloc.replace('www.', '').replace('.', '_')
        filename = f"{domain}_{url_hash}.html"
        filepath = output_dir / filename
        
        # Skip if already exists
        if filepath.exists():
            print(f"✓ Skip (exists): {filename}")
            return True
        
        # Download with headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Save HTML
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"✓ Downloaded: {filename}")
        time.sleep(0.3)  # Be polite
        return True
        
    except Exception as e:
        print(f"✗ Failed {url}: {e}")
        return False

def main():
    # Setup paths
    links_file = Path('url_batches/all_links.txt')
    output_dir = Path('input/articles/articles')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Read URLs
    with open(links_file, 'r') as f:
        lines = f.readlines()
    
    urls = [line.strip() for line in lines if line.strip() and line.strip().startswith('http')]
    
    print(f"Found {len(urls)} URLs to download\n")
    
    # Download all
    success = 0
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] ", end='')
        if download_article(url, output_dir):
            success += 1
    
    print(f"\n✅ Downloaded {success}/{len(urls)} articles to {output_dir}")

if __name__ == '__main__':
    main()
