import os
import re
import logging
from pathlib import Path
from hashlib import md5
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def load_html_articles(folder_path: str) -> list[dict]:
    """Extract clean article text from .html files."""
    articles = []
    folder = Path(folder_path)
    
    if not folder.exists():
        logger.error(f"Folder not found: {folder_path}")
        return articles
    
    html_files = list(folder.glob('*.html'))
    logger.info(f"[LOAD] Found {len(html_files)} HTML files")
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Remove unwanted tags
            for tag in soup.find_all(['script', 'style', 'noscript', 'iframe']):
                tag.decompose()
            
            # Extract title
            title = None
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                title = og_title['content']
            elif soup.find('h1'):
                title = soup.find('h1').get_text(strip=True)
            elif soup.find('title'):
                title = soup.find('title').get_text(strip=True)
            else:
                title = html_file.stem
            
            # Extract URL
            url = None
            og_url = soup.find('meta', property='og:url')
            if og_url and og_url.get('content'):
                url = og_url['content']
            else:
                canonical = soup.find('link', rel='canonical')
                if canonical and canonical.get('href'):
                    url = canonical['href']
            
            # Extract source
            source = 'Unknown'
            og_site = soup.find('meta', property='og:site_name')
            if og_site and og_site.get('content'):
                source = og_site['content']
            else:
                author_meta = soup.find('meta', attrs={'name': 'author'})
                if author_meta and author_meta.get('content'):
                    source = author_meta['content']
            
            # Extract published_at
            published_at = datetime.now().isoformat()
            pub_time = soup.find('meta', property='article:published_time')
            if pub_time and pub_time.get('content'):
                published_at = pub_time['content']
            else:
                time_tag = soup.find('time')
                if time_tag and time_tag.get('datetime'):
                    published_at = time_tag['datetime']
            
            # Extract content using fallback chain
            content = None
            method = 'unknown'
            
            # 1. article tag
            article_tag = soup.find('article')
            if article_tag:
                content = article_tag.get_text(separator=' ', strip=True)
                method = 'article'
            
            # 2. itemprop='articleBody'
            if not content:
                article_body = soup.find(itemprop='articleBody')
                if article_body:
                    content = article_body.get_text(separator=' ', strip=True)
                    method = 'itemprop'
            
            # 3. class matching article body/content/text
            if not content:
                article_class = soup.find(class_=re.compile(r'article.?(body|content|text)', re.I))
                if article_class:
                    content = article_class.get_text(separator=' ', strip=True)
                    method = 'article-class'
            
            # 4. class matching story/post/entry
            if not content:
                story_class = soup.find(class_=re.compile(r'(story|post|entry).?(body|content)', re.I))
                if story_class:
                    content = story_class.get_text(separator=' ', strip=True)
                    method = 'story-class'
            
            # 5. main tag
            if not content:
                main_tag = soup.find('main')
                if main_tag:
                    content = main_tag.get_text(separator=' ', strip=True)
                    method = 'main'
            
            # 6. All <p> tags with text > 80 chars
            if not content:
                paragraphs = []
                for p in soup.find_all('p'):
                    text = p.get_text(strip=True)
                    if len(text) > 80:
                        paragraphs.append(text)
                if paragraphs:
                    content = ' '.join(paragraphs)
                    method = 'paragraphs'
            
            # 7. Nuclear option
            if not content:
                content = soup.get_text(separator=' ', strip=True)
                method = 'nuclear'
            
            # Clean content
            original_content = content
            content = re.sub(r'\s+', ' ', content).strip()
            
            # For Times of India and Economic Times, remove language selector boilerplate
            if 'timesofindia' in html_file.name or 'economictimes' in html_file.name:
                cleaned = re.sub(r'^.*?(Edition IN|हिन्दी|ગુજરાત|मराठी).*?(?=\w{20,})', '', content, flags=re.DOTALL).strip()
                if len(cleaned) >= 50:
                    content = cleaned
            
            # Cap at 5000 chars
            content = content[:5000]
            
            # Skip if too short (lowered from 100 to 50)
            if len(content) < 50:
                logger.warning(f"[SKIP] {html_file.name}: {len(content)} chars after extraction "
                             f"(raw HTML: {len(html_content)} bytes) — likely JS-rendered")
                continue
            
            # Generate article ID
            article_id = f"art_{md5(html_file.name.encode()).hexdigest()[:8]}"
            
            article = {
                'id': article_id,
                'title': title,
                'content': content,
                'source': source,
                'published_at': published_at,
                'filename': html_file.name,
                'url': url  # Add URL field
            }
            
            articles.append(article)
            logger.info(f"[LOAD] {html_file.name}: {len(content)} chars (method: {method})")
            
        except Exception as e:
            logger.error(f"[LOAD] {html_file.name}: Error - {e}")
            continue
    
    logger.info(f"[LOAD] Loaded {len(articles)}/{len(html_files)} articles")
    return articles
