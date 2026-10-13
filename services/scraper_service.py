"""
Scraper Service Module
Handles ethical and legal web scraping for metadata extraction,
OpenGraph preview generation, and article enrichment.
"""

import re
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScraperService:
    """
    Ethical web scraping service designed to extract article metadata,
    OpenGraph tags, reading time, and previews while respecting publisher resources.
    
    Ethical guidelines followed:
    - Custom polite User-Agent with contact/about information.
    - Caching with TTL to prevent redundant requests.
    - Strict timeouts to avoid hanging publisher connections.
    - Only extracts public metadata (OpenGraph/Twitter Cards/Lead paragraphs).
    - Preserves links back to original publisher articles (no full-text piracy).
    """

    def __init__(self, cache_duration_minutes: int = 30, timeout_seconds: int = 4):
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        self.timeout = timeout_seconds
        self.metadata_cache: Dict[str, Dict[str, Any]] = {}
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NewsHub-Aggregator/2.0 (Ethical RSS & News Metadata Aggregator; +http://localhost:5000/about)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        })

    def _is_cache_valid(self, url: str) -> bool:
        """Check if cached metadata is still valid"""
        if url not in self.metadata_cache:
            return False
        timestamp = self.metadata_cache[url].get('timestamp')
        if not timestamp:
            return False
        return datetime.now() - timestamp < self.cache_duration

    def extract_metadata(self, url: str) -> Dict[str, Any]:
        """
        Extract OpenGraph, Twitter Card, and semantic metadata from a public article URL.
        Returns a dict with image, description, author, reading_time, and lead_text.
        """
        if not url or not url.startswith(('http://', 'https://')):
            return {}

        # Check cache
        if self._is_cache_valid(url):
            logger.debug(f"Cache hit for metadata: {url}")
            return self.metadata_cache[url].get('data', {})

        result: Dict[str, Any] = {
            'url': url,
            'image': None,
            'description': None,
            'author': None,
            'reading_time_minutes': 1,
            'lead_text': None,
            'domain': urlparse(url).netloc
        }

        try:
            # Polite GET request with short timeout
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True, stream=True)
            
            # Content-type check to prevent downloading large non-HTML blobs
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type and 'application/xhtml+xml' not in content_type:
                return result

            # Only read up to first 250KB of HTML to be polite and fast
            html_chunk = b""
            for chunk in response.iter_content(chunk_size=32768):
                html_chunk += chunk
                if len(html_chunk) >= 262144:  # 256KB max
                    break

            soup = BeautifulSoup(html_chunk, 'html.parser')

            # 1. Image extraction (OpenGraph -> Twitter -> Link tag -> First article img)
            og_img = soup.find('meta', property=['og:image', 'og:image:url', 'og:image:secure_url'])
            if og_img and og_img.get('content'):
                result['image'] = og_img['content'].strip()
            
            if not result['image']:
                tw_img = soup.find('meta', attrs={'name': ['twitter:image', 'twitter:image:src']})
                if tw_img and tw_img.get('content'):
                    result['image'] = tw_img['content'].strip()

            # 2. Description extraction
            og_desc = soup.find('meta', property='og:description')
            if og_desc and og_desc.get('content'):
                result['description'] = og_desc['content'].strip()
            
            if not result['description']:
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc and meta_desc.get('content'):
                    result['description'] = meta_desc['content'].strip()

            # 3. Author extraction
            author_meta = soup.find('meta', attrs={'name': ['author', 'article:author', 'byl', 'twitter:creator']})
            if author_meta and author_meta.get('content'):
                result['author'] = author_meta['content'].strip()

            # 4. Lead text extraction from article body (first 1-2 paragraphs)
            article_tag = soup.find('article') or soup.find('main') or soup
            paragraphs = article_tag.find_all('p', limit=4)
            clean_paragraphs = []
            word_count = 0
            for p in paragraphs:
                text = p.get_text().strip()
                if len(text) > 40 and not text.startswith(('©', 'Copyright', 'Sign up', 'Subscribe')):
                    clean_paragraphs.append(text)
                    word_count += len(text.split())

            if clean_paragraphs:
                result['lead_text'] = " ".join(clean_paragraphs[:2])
                result['reading_time_minutes'] = max(1, round(word_count / 180))

            # Store in cache
            self.metadata_cache[url] = {
                'data': result,
                'timestamp': datetime.now()
            }
            return result

        except requests.RequestException as e:
            logger.debug(f"HTTP request failed for {url}: {e}")
            # Cache failure for shorter duration to avoid retry storm
            self.metadata_cache[url] = {
                'data': result,
                'timestamp': datetime.now() - self.cache_duration + timedelta(minutes=5)
            }
            return result
        except Exception as e:
            logger.debug(f"Error scraping {url}: {e}")
            return result

    def enrich_article(self, article: Dict[str, Any], fetch_remote_image: bool = False) -> Dict[str, Any]:
        """
        Enrich an article dictionary with reading time, clean snippets,
        and fallback image/metadata.
        """
        if not article:
            return article

        # Calculate estimated reading time based on description/summary
        content = (article.get('description') or '') + ' ' + (article.get('summary') or '') + ' ' + (article.get('title') or '')
        words = len(content.split())
        article['reading_time'] = max(1, round(words / 45))  # Estimate for snippet or full

        # Ensure image field exists
        if not article.get('image'):
            # If fetch_remote_image is enabled and no image was parsed from RSS, scrape it
            if fetch_remote_image and article.get('link'):
                meta = self.extract_metadata(article['link'])
                if meta.get('image'):
                    article['image'] = meta['image']
                if not article.get('description') and meta.get('description'):
                    article['description'] = meta['description']
                if meta.get('author'):
                    article['author'] = meta['author']

        return article
