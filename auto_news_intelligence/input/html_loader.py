from bs4 import BeautifulSoup
import os
import hashlib
import re
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_content(soup, filename):
    """Extract article content with smart fallback chain."""
    # Step 1: Remove only DEFINITE noise - be conservative here
    for tag in soup(['script', 'style', 'noscript', 'iframe']):
        tag.decompose()
    
    # Step 2: Try structured content selectors in order of reliability
    # Common article body selectors across sites
    selectors = [
        # Semantic HTML5
        {'name': 'article'},
        # Schema.org
        {'attrs': {'itemprop': 'articleBody'}},
        # Common class patterns - check one at a time
        {'attrs': {'class': re.compile(r'\barticle[\-_]?(body|content|text|detail)\b', re.I)}},
        {'attrs': {'class': re.compile(r'\b(story|post|news|entry)[\-_]?(body|content|text)\b', re.I)}},
        {'attrs': {'class': re.compile(r'\b(content[\-_]?body|body[\-_]?content)\b', re.I)}},
        # LiveMint specific
        {'attrs': {'class': re.compile(r'\bstory[\-_]?content\b|\barticle[\-_]?wrap\b', re.I)}},
        # MotorBeam specific
        {'attrs': {'class': re.compile(r'\bentry[\-_]?content\b|\bpost[\-_]?content\b', re.I)}},
        # PIB specific
        {'attrs': {'class': re.compile(r'\bcontent\b|\bmain[\-_]?content\b', re.I)}},
        # ID based
        {'attrs': {'id': re.compile(r'\b(article|content|story|main|post)[\-_]?(body|content|text)?\b', re.I)}},
        # Last tag resort
        {'name': 'main'},
    ]
    
    for selector in selectors:
        tag = soup.find(**selector)
        if tag:
            text = tag.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) > 150:
                return text[:5000], 'structured'
    
    # Step 3: Paragraph fallback - collect ALL paragraphs with real content
    paragraphs = []
    for p in soup.find_all(['p', 'div']):
        # Only direct text, not nested divs
        text = p.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Keep paragraphs that look like article text
        if (len(text) > 80 and len(text.split()) > 10 and
            not any(skip in text.lower() for skip in ['cookie', 'subscribe', 'newsletter',
                                                       'follow us', 'sign up', 'log in',
                                                       'terms of service', 'privacy policy',
                                                       'all rights reserved', 'advertisement'])):
            paragraphs.append(text)
    
    if paragraphs:
        # Take first 10 substantive paragraphs
        content = ' '.join(paragraphs[:10])
        return content[:5000], 'paragraph'
    
    # Step 4: Nuclear fallback - just get all text
    # Strip only script/style (already done)
    text = soup.get_text(separator=' ', strip=True)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:5000], 'nuclear'


def load_html_articles(folder_path: str) -> list[dict]:
    """Load and parse HTML articles from a folder."""
    articles = []
    
    if not os.path.exists(folder_path):
        raise ValueError(f"Folder not found: {folder_path}")
    
    html_files = [f for f in os.listdir(folder_path) if f.endswith('.html')]
    
    if not html_files:
        raise ValueError(f"No .html files found in {folder_path}")
    
    for filename in sorted(html_files):
        filepath = os.path.join(folder_path, filename)
        
        # Detect Google News redirect pages
        if 'news_google_com' in filename or 'news.google.com' in filename:
            logger.info(f"[SKIP] {filename}: Google News redirect page - no article content")
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                raw_html = f.read()
            
            soup = BeautifulSoup(raw_html, 'html.parser')
            
            # Extract title - try multiple selectors
            title = (soup.find('h1') or
                    soup.find('title') or
                    soup.find('meta', property='og:title'))
            
            if title:
                title = title.get_text(strip=True) if hasattr(title, 'get_text') else title.get('content', '')
            else:
                title = filename.replace('.html', '')
            
            # Extract source - try meta tags
            source = (soup.find('meta', property='og:site_name') or
                     soup.find('meta', {'name': 'author'}) or
                     soup.find('meta', {'name': 'publisher'}))
            source = source.get('content', 'Unknown') if source else 'Unknown'
            
            # Extract published date - try meta tags
            pub_date = (soup.find('meta', property='article:published_time') or
                       soup.find('meta', {'name': 'publish-date'}) or
                       soup.find('meta', {'name': 'date'}) or
                       soup.find('time'))
            
            if pub_date:
                published_at = (pub_date.get('content') or 
                              pub_date.get('datetime') or
                              pub_date.get_text(strip=True))
            else:
                published_at = datetime.now().isoformat()
            
            # Extract content using smart fallback chain
            content, method = extract_content(soup, filename)
            
            # Skip if content too short
            if len(content) < 150:
                if len(raw_html) > 1000:
                    logger.warning(f"[SKIP] {filename}: {len(content)} chars extracted. "
                                 f"Raw HTML size: {len(raw_html)} bytes. May be paywalled or JS-rendered.")
                else:
                    logger.info(f"[SKIP] {filename}: too short after extraction ({len(content)} chars)")
                continue
            
            # Log content length and method for debugging
            logger.info(f"[LOAD] {filename}: {len(content)} chars (method={method})")
            
            # Generate stable ID from filename
            article_id = f"art_{hashlib.md5(filename.encode()).hexdigest()[:8]}"
            
            articles.append({
                'id': article_id,
                'title': title[:500],
                'content': content,
                'source': source,
                'published_at': published_at,
                'filename': filename  # keep for debugging
            })
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to parse {filename}: {e}")
            continue
    
    logger.info(f"[LOAD] Loaded {len(articles)} articles from {len(html_files)} HTML files")
    return articles
