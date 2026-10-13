"""
RSS Service Module
Handles fetching, parsing, caching, and media extraction for reliable RSS sources.
"""

import re
import html
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
import requests
import feedparser
from bs4 import BeautifulSoup

from services.scraper_service import ScraperService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_relative_time(dt: Optional[datetime]) -> str:
    """Format datetime into a human-friendly relative string"""
    if not dt:
        return "Recently"
    now = datetime.now()
    diff = now - dt
    total_seconds = int(diff.total_seconds())
    
    if total_seconds < 0 or total_seconds < 60:
        return "Just now"
    minutes = total_seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days < 7:
        return f"{days}d ago"
    return dt.strftime("%b %d, %Y")

class RSSService:
    """Service for fetching and parsing reliable RSS news feeds with caching and media enrichment"""
    
    def __init__(self, cache_duration_minutes: int = 5):
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.scraper_service = ScraperService(cache_duration_minutes=30)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NewsHub-Aggregator/2.0 (Ethical News Aggregator; +http://localhost:5000/about)',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*'
        })
        
        # 10 Reliable, Officially Maintained RSS Sources
        self.rss_sources: Dict[str, Dict[str, Any]] = {
            'BBC News': {
                'url': 'http://feeds.bbci.co.uk/news/rss.xml',
                'category': 'World',
                'description': 'British Broadcasting Corporation global coverage',
                'color': '#bb1919',
                'badge': 'BBC',
                'homepage': 'https://www.bbc.com/news'
            },
            'CNN': {
                'url': 'http://rss.cnn.com/rss/edition.rss',
                'category': 'General',
                'description': 'Cable News Network international headlines',
                'color': '#cc0000',
                'badge': 'CNN',
                'homepage': 'https://edition.cnn.com'
            },
            'The Guardian': {
                'url': 'https://www.theguardian.com/world/rss',
                'category': 'World',
                'description': 'Independent international journalism and commentary',
                'color': '#052962',
                'badge': 'Guardian',
                'homepage': 'https://www.theguardian.com'
            },
            'Al Jazeera': {
                'url': 'https://www.aljazeera.com/xml/rss/all.xml',
                'category': 'World',
                'description': 'Comprehensive news and perspectives from the global south',
                'color': '#fa6400',
                'badge': 'AJ',
                'homepage': 'https://www.aljazeera.com'
            },
            'NPR News': {
                'url': 'https://feeds.npr.org/1001/rss.xml',
                'category': 'Domestic',
                'description': 'National Public Radio independent US & world reporting',
                'color': '#2b78c5',
                'badge': 'NPR',
                'homepage': 'https://www.npr.org'
            },
            'TechCrunch': {
                'url': 'https://techcrunch.com/feed/',
                'category': 'Technology',
                'description': 'High-impact technology startups, AI, and venture capital',
                'color': '#00a562',
                'badge': 'TechCrunch',
                'homepage': 'https://techcrunch.com'
            },
            'Ars Technica': {
                'url': 'https://feeds.arstechnica.com/arstechnica/index',
                'category': 'Technology',
                'description': 'Deep-dive technology, IT policy, science, and computing',
                'color': '#ff4e00',
                'badge': 'Ars',
                'homepage': 'https://arstechnica.com'
            },
            'CNBC': {
                'url': 'https://www.cnbc.com/id/100003114/device/rss/rss.html',
                'category': 'Business',
                'description': 'Global financial markets, business leaders, and economy',
                'color': '#005594',
                'badge': 'CNBC',
                'homepage': 'https://www.cnbc.com'
            },
            'DW News': {
                'url': 'https://rss.dw.com/rdf/rss-en-all',
                'category': 'World',
                'description': 'Deutsche Welle unbiased international news from Germany',
                'color': '#002d62',
                'badge': 'DW',
                'homepage': 'https://www.dw.com'
            },
            'Google News': {
                'url': 'https://news.google.com/rss',
                'category': 'General',
                'description': 'Aggregated top trending headlines worldwide',
                'color': '#4285f4',
                'badge': 'Google',
                'homepage': 'https://news.google.com'
            }
        }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        cached_time = self.cache[cache_key]['timestamp']
        return datetime.now() - cached_time < self.cache_duration
    
    def _extract_image_from_entry(self, entry: Any) -> Optional[str]:
        """Extract article thumbnail/image from multiple RSS metadata sources"""
        # 1. media_thumbnail
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            thumb = entry.media_thumbnail[0].get('url')
            if thumb and thumb.startswith('http'):
                return thumb
        
        # 2. media_content
        if hasattr(entry, 'media_content') and entry.media_content:
            for media in entry.media_content:
                url = media.get('url')
                medium = media.get('medium', '')
                mtype = media.get('type', '')
                if url and ('image' in mtype or medium == 'image' or not medium):
                    if url.startswith('http'):
                        return url
        
        # 3. enclosures (podcasts / RSS enclosures)
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enc in entry.enclosures:
                enc_type = enc.get('type', '')
                enc_url = enc.get('href', '') or enc.get('url', '')
                if 'image' in enc_type and enc_url.startswith('http'):
                    return enc_url
        
        # 4. Check embedded img in content / summary / description
        raw_html = ""
        if hasattr(entry, 'content') and entry.content:
            raw_html += entry.content[0].get('value', '')
        if hasattr(entry, 'summary'):
            raw_html += " " + (entry.summary or '')
        if hasattr(entry, 'description'):
            raw_html += " " + (entry.description or '')
            
        if '<img' in raw_html.lower():
            match = re.search(r'<img[^>]+src=[\'"]([^\'"]+)[\'"]', raw_html, re.IGNORECASE)
            if match:
                img_url = match.group(1).strip()
                if img_url.startswith('http') and not any(skip in img_url.lower() for skip in ['pixel', 'tracker', '1x1', 'feedburner', 'icon']):
                    return img_url
        
        return None

    def _clean_text(self, text: str) -> str:
        """Remove HTML tags, decode entities, and strip whitespace"""
        if not text:
            return ""
        if '<' in text and '>' in text:
            soup = BeautifulSoup(text, 'html.parser')
            for s in soup(['script', 'style', 'img', 'figure']):
                s.decompose()
            clean = soup.get_text(separator=' ').strip()
        else:
            clean = text.strip()
        clean = html.unescape(clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    def _parse_entry_datetime(self, entry: Any) -> tuple[Optional[datetime], str]:
        """Convert entry published or updated date into a datetime and relative string"""
        dt = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                dt = datetime(*entry.published_parsed[:6])
            except (TypeError, ValueError):
                pass
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            try:
                dt = datetime(*entry.updated_parsed[:6])
            except (TypeError, ValueError):
                pass
        
        if dt is None:
            dt = datetime.now()
            
        rel_time = format_relative_time(dt)
        return dt, rel_time

    def _fetch_single_feed(self, source_name: str, source_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch and parse a single RSS feed"""
        cache_key = f"{source_name}_{source_info['url']}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            return {
                'source': source_name,
                'articles': self.cache[cache_key]['articles'],
                'cached': True
            }
        
        try:
            logger.info(f"Fetching RSS feed for {source_name}")
            response = self.session.get(source_info['url'], timeout=8)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            articles = []
            
            for entry in feed.entries[:25]:  # Limit to 25 per source
                if not hasattr(entry, 'title') or not hasattr(entry, 'link'):
                    continue
                
                title = entry.get('title', '').strip()
                link = entry.get('link', '').strip()
                
                if not title or not link:
                    continue
                
                # Clean description / summary
                desc = self._clean_text(entry.get('description', '') or entry.get('summary', ''))
                # If description is identical to title, leave empty
                if desc.lower() == title.lower():
                    desc = ""
                
                # Image extraction
                image_url = self._extract_image_from_entry(entry)
                
                # Datetime extraction
                dt, rel_time = self._parse_entry_datetime(entry)
                
                # Estimated reading time
                word_count = len((title + " " + desc).split())
                reading_time = max(1, round(word_count / 35))
                
                # Author
                author = entry.get('author') or source_name
                
                article = {
                    'title': title,
                    'link': link,
                    'description': desc,
                    'summary': desc,
                    'published': dt.strftime("%b %d, %Y %H:%M") if dt else "Recent",
                    'published_dt': dt,
                    'published_relative': rel_time,
                    'published_iso': dt.isoformat() if dt else datetime.now().isoformat(),
                    'category': entry.get('category', source_info['category']),
                    'source': source_name,
                    'source_badge': source_info.get('badge', source_name[:3]),
                    'source_color': source_info.get('color', '#4F46E5'),
                    'source_homepage': source_info.get('homepage', '#'),
                    'image': image_url,
                    'reading_time': reading_time,
                    'author': author
                }
                
                articles.append(article)
            
            # Cache the results
            self.cache[cache_key] = {
                'articles': articles,
                'timestamp': datetime.now()
            }
            
            return {
                'source': source_name,
                'articles': articles,
                'cached': False
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {source_name}: {str(e)}")
            return {
                'source': source_name,
                'articles': [],
                'error': str(e),
                'cached': False
            }
        except Exception as e:
            logger.error(f"Error parsing {source_name}: {str(e)}")
            return {
                'source': source_name,
                'articles': [],
                'error': str(e),
                'cached': False
            }
    
    def fetch_all_feeds(self) -> List[Dict[str, Any]]:
        """Fetch all RSS feeds concurrently using ThreadPoolExecutor"""
        results = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_source = {
                executor.submit(self._fetch_single_feed, source_name, source_info): source_name
                for source_name, source_info in self.rss_sources.items()
            }
            
            for future in as_completed(future_to_source):
                source_name = future_to_source[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing {source_name}: {str(e)}")
                    results.append({
                        'source': source_name,
                        'articles': [],
                        'error': str(e),
                        'cached': False
                    })
        
        return results
    
    def get_all_articles(self) -> List[Dict[str, Any]]:
        """Get all articles combined and sorted by recency"""
        feeds = self.fetch_all_feeds()
        all_articles = []
        
        for feed in feeds:
            all_articles.extend(feed.get('articles', []))
        
        # Sort by publication date (newest first)
        def sort_key(item):
            dt = item.get('published_dt')
            if dt and isinstance(dt, datetime):
                return dt
            return datetime.min
        
        all_articles.sort(key=sort_key, reverse=True)
        return all_articles
    
    def get_articles_by_source(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get articles grouped by source name"""
        feeds = self.fetch_all_feeds()
        articles_by_source = {}
        for feed in feeds:
            source_name = feed['source']
            articles_by_source[source_name] = feed.get('articles', [])
        return articles_by_source
    
    def clear_cache(self):
        """Clear the RSS cache"""
        self.cache.clear()
        self.scraper_service.metadata_cache.clear()
        logger.info("NewsHub caches cleared successfully")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache diagnostic info"""
        return {
            'cache_size': len(self.cache),
            'cache_duration_minutes': self.cache_duration.total_seconds() / 60,
            'cached_sources': list(self.cache.keys()),
            'metadata_cache_size': len(self.scraper_service.metadata_cache)
        }

    def get_sources_directory(self) -> List[Dict[str, Any]]:
        """Return directory of all registered sources for About page and documentation"""
        sources_list = []
        for name, info in self.rss_sources.items():
            cache_key = f"{name}_{info['url']}"
            article_count = len(self.cache[cache_key]['articles']) if cache_key in self.cache else 0
            sources_list.append({
                'name': name,
                'url': info['url'],
                'category': info['category'],
                'description': info['description'],
                'badge': info.get('badge', name[:3]),
                'color': info.get('color', '#4F46E5'),
                'homepage': info.get('homepage', '#'),
                'articles_count': article_count,
                'status': 'Online'
            })
        return sources_list
