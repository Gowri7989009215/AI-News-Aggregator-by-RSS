"""
RSS Service Module
Handles fetching, parsing, caching, validation, media extraction,
and deduplication for reliable RSS news sources.
"""

import re
import html
import logging
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
import requests
import feedparser
from bs4 import BeautifulSoup

from services.scraper_service import ScraperService
from services.validation_service import ValidationService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RSSService:
    """Service for fetching, validating, and parsing reliable RSS news feeds"""
    
    def __init__(self, cache_duration_minutes: int = 5):
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.scraper_service = ScraperService(cache_duration_minutes=30)
        self.validation_service = ValidationService()
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NewsHub-Aggregator/2.0 (Ethical News Aggregator; +http://localhost:5000/about)',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*'
        })
        
        # 10 Reliable, Officially Maintained RSS Sources with Trust Tiers
        self.rss_sources: Dict[str, Dict[str, Any]] = {
            'BBC News': {
                'url': 'http://feeds.bbci.co.uk/news/rss.xml',
                'category': 'World',
                'description': 'British Broadcasting Corporation global coverage',
                'color': '#bb1919',
                'badge': 'BBC',
                'homepage': 'https://www.bbc.com/news',
                'tier': 1,
                'tier_label': 'Tier 1: Public Broadcaster'
            },
            'CNN': {
                'url': 'http://rss.cnn.com/rss/edition.rss',
                'category': 'World',
                'description': 'Cable News Network international headlines',
                'color': '#cc0000',
                'badge': 'CNN',
                'homepage': 'https://edition.cnn.com',
                'tier': 1,
                'tier_label': 'Tier 1: International Network'
            },
            'The Guardian': {
                'url': 'https://www.theguardian.com/world/rss',
                'category': 'World',
                'description': 'Independent international journalism and commentary',
                'color': '#052962',
                'badge': 'Guardian',
                'homepage': 'https://www.theguardian.com',
                'tier': 1,
                'tier_label': 'Tier 1: Independent Publisher'
            },
            'Al Jazeera': {
                'url': 'https://www.aljazeera.com/xml/rss/all.xml',
                'category': 'World',
                'description': 'Comprehensive news and perspectives from the global south',
                'color': '#fa6400',
                'badge': 'AJ',
                'homepage': 'https://www.aljazeera.com',
                'tier': 1,
                'tier_label': 'Tier 1: Global News Network'
            },
            'NPR News': {
                'url': 'https://feeds.npr.org/1001/rss.xml',
                'category': 'Politics',
                'description': 'National Public Radio independent US & world reporting',
                'color': '#2b78c5',
                'badge': 'NPR',
                'homepage': 'https://www.npr.org',
                'tier': 1,
                'tier_label': 'Tier 1: Public Broadcaster'
            },
            'TechCrunch': {
                'url': 'https://techcrunch.com/feed/',
                'category': 'Technology',
                'description': 'High-impact technology startups, AI, and venture capital',
                'color': '#00a562',
                'badge': 'TechCrunch',
                'homepage': 'https://techcrunch.com',
                'tier': 1,
                'tier_label': 'Tier 1: Tech Journalism'
            },
            'Ars Technica': {
                'url': 'https://feeds.arstechnica.com/arstechnica/index',
                'category': 'Technology',
                'description': 'Deep-dive technology, IT policy, science, and computing',
                'color': '#ff4e00',
                'badge': 'Ars',
                'homepage': 'https://arstechnica.com',
                'tier': 1,
                'tier_label': 'Tier 1: Science & Tech Journalism'
            },
            'CNBC': {
                'url': 'https://www.cnbc.com/id/100003114/device/rss/rss.html',
                'category': 'Business',
                'description': 'Global financial markets, business leaders, and economy',
                'color': '#005594',
                'badge': 'CNBC',
                'homepage': 'https://www.cnbc.com',
                'tier': 1,
                'tier_label': 'Tier 1: Financial Media'
            },
            'DW News': {
                'url': 'https://rss.dw.com/rdf/rss-en-all',
                'category': 'World',
                'description': 'Deutsche Welle unbiased international news from Germany',
                'color': '#002d62',
                'badge': 'DW',
                'homepage': 'https://www.dw.com',
                'tier': 1,
                'tier_label': 'Tier 1: Public Broadcaster'
            },
            'Google News': {
                'url': 'https://news.google.com/rss',
                'category': 'World',
                'description': 'Aggregated top trending headlines worldwide',
                'color': '#4285f4',
                'badge': 'Google',
                'homepage': 'https://news.google.com',
                'tier': 2,
                'tier_label': 'Tier 2: News Aggregator'
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
        """Remove HTML tags, decode entities, repair unicode replacements, and strip whitespace"""
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
        # Repair corrupted unicode replacement character in contractions and punctuation
        u = '\uFFFD'
        # Temperature / degree: 122°F
        clean = re.sub(r'(\d+)' + u + r'([FCfc])', r'\1°\2', clean)
        # Contractions: word's
        clean = re.sub(r'([a-zA-Z])' + u + r'([a-zA-Z])', r"\1'\2", clean)
        # Plural possessive: doctors'
        clean = re.sub(r'([sS])' + u + r'(\s+)', r"\1'\2", clean)
        # Separator with space: coast — Europe
        clean = re.sub(r'\s+' + u + r'\s*', r' — ', clean)
        clean = re.sub(r'\s*' + u + r'\s+', r' — ', clean)
        # Opening quotes: "word
        clean = re.sub(r'(^|\s)' + u + r'([a-zA-Z0-9])', r'\1"\2', clean)
        # Closing quotes: word"
        clean = re.sub(r'([a-zA-Z0-9])' + u, r'\1"', clean)
        clean = clean.replace(u, "'")
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    def _fetch_single_feed(self, source_name: str, source_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch, validate, and parse a single RSS feed with robust error recovery"""
        cache_key = f"{source_name}_{source_info['url']}"
        
        if self._is_cache_valid(cache_key):
            return {
                'source': source_name,
                'articles': self.cache[cache_key]['articles'],
                'cached': True,
                'status': 'Healthy'
            }
        
        try:
            logger.info(f"Fetching RSS feed for {source_name}")
            response = self.session.get(source_info['url'], timeout=8)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            if feed.bozo and not feed.entries:
                logger.warning(f"Feed parser warning for {source_name}: {feed.bozo_exception}")

            articles = []
            fetch_time_utc = datetime.now(timezone.utc).replace(tzinfo=None)
            fetch_time_local = datetime.now()
            
            for entry in feed.entries[:25]:
                if not hasattr(entry, 'title') or not hasattr(entry, 'link'):
                    continue
                
                title = self._clean_text(entry.get('title', ''))
                link = entry.get('link', '').strip()
                
                # 1. LINK VALIDATION & CANONICAL NORMALIZATION
                is_valid_url, canonical_url, err = self.validation_service.validate_url(link)
                if not is_valid_url or not title:
                    logger.debug(f"Skipping invalid article link {link}: {err}")
                    continue

                # 2. DATE INTEGRITY (True published date in UTC vs fetched date)
                published_dt, rel_time, is_verified_date = self.validation_service.parse_publication_date(entry)
                is_outdated, outdated_label = self.validation_service.check_staleness(published_dt)
                
                # Recently published: published within last 3 hours (UTC comparison, never negative)
                is_recently_published = False
                if published_dt:
                    age = fetch_time_utc - published_dt
                    if timedelta(seconds=0) <= age <= timedelta(hours=3):
                        is_recently_published = True

                # 3. TEXT SANITIZATION
                desc = self._clean_text(entry.get('description', '') or entry.get('summary', ''))
                if desc.lower() == title.lower():
                    desc = ""

                # 4. CLAIM VERIFICATION CHECK (Unverified/speculative claim vs verified report)
                is_unverified, claim_label = self.validation_service.evaluate_claim_verification(title, desc)

                # 5. SOURCE ATTRIBUTION & ORIGINAL PUBLISHER
                original_publisher = self.validation_service.extract_original_publisher(title, source_name)
                
                # 6. HEADLINE NORMALIZATION FOR DEDUPLICATION
                tokens, norm_title = self.validation_service.normalize_headline(title)

                # 7. IMAGE & READING TIME
                image_url = self._extract_image_from_entry(entry)
                word_count = len((title + " " + desc).split())
                reading_time = max(1, round(word_count / 35))
                author = entry.get('author') or original_publisher

                article = {
                    'title': title,
                    'link': link,
                    'canonical_url': canonical_url,
                    'normalized_tokens': tokens,
                    'normalized_headline': norm_title,
                    'description': desc,
                    'summary': desc,
                    'published': published_dt.strftime("%b %d, %Y %H:%M") if published_dt else "Unverified",
                    'published_dt': published_dt,
                    'published_relative': rel_time,
                    'published_iso': published_dt.isoformat() if published_dt else None,
                    'is_verified_date': is_verified_date,
                    'fetched_dt': fetch_time_local,
                    'fetched_relative': "Just now",
                    'is_recently_published': is_recently_published,
                    'is_outdated': is_outdated,
                    'outdated_label': outdated_label,
                    'is_unverified': is_unverified,
                    'claim_label': claim_label,
                    'trust_tier': source_info.get('tier', 1),
                    'trust_label': source_info.get('tier_label', 'Tier 1'),
                    'category': entry.get('category', source_info['category']),
                    'source': source_name,
                    'original_publisher': original_publisher,
                    'source_badge': source_info.get('badge', source_name[:3]),
                    'source_color': source_info.get('color', '#4F46E5'),
                    'source_homepage': source_info.get('homepage', '#'),
                    'image': image_url,
                    'reading_time': reading_time,
                    'author': author,
                    'alternative_sources': []
                }
                
                articles.append(article)
            
            # Cache results
            self.cache[cache_key] = {
                'articles': articles,
                'timestamp': fetch_time_local,
                'status': 'Healthy'
            }
            
            return {
                'source': source_name,
                'articles': articles,
                'cached': False,
                'status': 'Healthy'
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {source_name}: {str(e)}")
            # Stale-while-revalidate: if a previous healthy cache exists, return it as fallback
            if cache_key in self.cache and self.cache[cache_key].get('articles'):
                logger.info(f"Using stale cached fallback for {source_name} due to network error")
                return {
                    'source': source_name,
                    'articles': self.cache[cache_key]['articles'],
                    'cached': True,
                    'status': f'Recovered from cache (Network: {str(e)})'
                }
            return {
                'source': source_name,
                'articles': [],
                'error': str(e),
                'cached': False,
                'status': f'Error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error parsing {source_name}: {str(e)}")
            if cache_key in self.cache and self.cache[cache_key].get('articles'):
                return {
                    'source': source_name,
                    'articles': self.cache[cache_key]['articles'],
                    'cached': True,
                    'status': f'Recovered from cache (Parse Error: {str(e)})'
                }
            return {
                'source': source_name,
                'articles': [],
                'error': str(e),
                'cached': False,
                'status': f'Parse Error: {str(e)}'
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
                        'cached': False,
                        'status': 'Exception'
                    })
        
        return results
    
    def get_all_articles(self) -> List[Dict[str, Any]]:
        """
        Get all articles combined, deduplicated, and sorted by verified publication date.
        """
        feeds = self.fetch_all_feeds()
        all_articles = []
        
        for feed in feeds:
            all_articles.extend(feed.get('articles', []))
        
        # DEDUPLICATION: Canonical URLs & normalized headlines
        unique_articles = self.validation_service.deduplicate_articles(all_articles)
        
        # Sort by verified publication date (newest first)
        def sort_key(item):
            dt = item.get('published_dt')
            if dt and isinstance(dt, datetime):
                return dt
            return datetime.min
        
        unique_articles.sort(key=sort_key, reverse=True)
        return unique_articles
    
    def get_articles_by_source(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get articles grouped by source name after validation"""
        all_articles = self.get_all_articles()
        articles_by_source: Dict[str, List[Dict[str, Any]]] = {}
        
        # Initialize keys
        for src in self.rss_sources.keys():
            articles_by_source[src] = []
            
        for article in all_articles:
            src = article.get('source', '')
            if src in articles_by_source:
                articles_by_source[src].append(article)
            else:
                articles_by_source[src] = [article]
                
        return articles_by_source
    
    def clear_cache(self):
        """Clear all in-memory caches"""
        self.cache.clear()
        self.scraper_service.metadata_cache.clear()
        logger.info("NewsHub caches cleared successfully")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache diagnostic info with source health breakdown"""
        sources_status = {}
        for name, info in self.rss_sources.items():
            cache_key = f"{name}_{info['url']}"
            if cache_key in self.cache:
                sources_status[name] = self.cache[cache_key].get('status', 'Healthy')
            else:
                sources_status[name] = 'Pending'

        return {
            'cache_size': len(self.cache),
            'cache_duration_minutes': self.cache_duration.total_seconds() / 60,
            'cached_sources': list(self.cache.keys()),
            'metadata_cache_size': len(self.scraper_service.metadata_cache),
            'sources_health': sources_status
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
                'tier': info.get('tier', 1),
                'tier_label': info.get('tier_label', 'Tier 1: Official News Publisher'),
                'articles_count': article_count,
                'status': 'Online'
            })
        return sources_list
