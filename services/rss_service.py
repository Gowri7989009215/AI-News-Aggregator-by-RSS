"""
RSS Service Module
Handles RSS feed fetching, parsing, and caching
"""

import feedparser
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RSSService:
    """Service for fetching and parsing RSS feeds with caching"""
    
    def __init__(self, cache_duration_minutes: int = 5):
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        self.cache = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # RSS feed sources
        self.rss_sources = {
            'Reuters': {
                'url': 'https://feeds.reuters.com/reuters/topNews',
                'category': 'general'
            },
            'BBC': {
                'url': 'http://feeds.bbci.co.uk/news/rss.xml',
                'category': 'general'
            },
            'CNN': {
                'url': 'http://rss.cnn.com/rss/edition.rss',
                'category': 'general'
            },
            'Al Jazeera': {
                'url': 'https://www.aljazeera.com/xml/rss/all.xml',
                'category': 'world'
            },
            'Google News': {
                'url': 'https://news.google.com/rss',
                'category': 'general'
            }
        }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key]['timestamp']
        return datetime.now() - cached_time < self.cache_duration
    
    def _fetch_single_feed(self, source_name: str, source_info: Dict[str, str]) -> Dict[str, Any]:
        """Fetch and parse a single RSS feed"""
        cache_key = f"{source_name}_{source_info['url']}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            logger.info(f"Using cached data for {source_name}")
            return {
                'source': source_name,
                'articles': self.cache[cache_key]['articles'],
                'cached': True
            }
        
        try:
            logger.info(f"Fetching RSS feed for {source_name}")
            
            # Fetch RSS feed
            response = self.session.get(source_info['url'], timeout=10)
            response.raise_for_status()
            
            # Parse RSS feed
            feed = feedparser.parse(response.content)
            
            # Extract articles
            articles = []
            for entry in feed.entries[:20]:  # Limit to 20 most recent articles
                # Validate entry has required fields
                if not hasattr(entry, 'title') or not hasattr(entry, 'link'):
                    continue
                
                title = entry.get('title', '').strip()
                link = entry.get('link', '').strip()
                
                # Skip if no title or link
                if not title or not link:
                    continue
                
                article = {
                    'title': title,
                    'link': link,
                    'description': self._clean_html(entry.get('description', '')),
                    'summary': self._clean_html(entry.get('summary', '')),
                    'published': entry.get('published', ''),
                    'published_parsed': entry.get('published_parsed'),
                    'category': entry.get('category', source_info['category']),
                    'source': source_name
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
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text).strip()
    
    def fetch_all_feeds(self) -> List[Dict[str, Any]]:
        """Fetch all RSS feeds concurrently"""
        results = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all feed fetching tasks
            future_to_source = {
                executor.submit(self._fetch_single_feed, source_name, source_info): source_name
                for source_name, source_info in self.rss_sources.items()
            }
            
            # Collect results as they complete
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
        """Get all articles from all sources"""
        feeds = self.fetch_all_feeds()
        all_articles = []
        
        for feed in feeds:
            all_articles.extend(feed.get('articles', []))
        
        # Production-safe sorting by publication date (most recent first)
        def safe_date(item):
            published = item.get("published_parsed")
            if published and isinstance(published, tuple) and len(published) >= 6:
                try:
                    return datetime(*published[:6])
                except (TypeError, ValueError):
                    pass
            return datetime.min  # Items with no dates go to bottom
        
        all_articles = sorted(all_articles, key=safe_date, reverse=True)
        
        return all_articles
    
    def get_articles_by_source(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get articles grouped by source"""
        feeds = self.fetch_all_feeds()
        articles_by_source = {}
        
        for feed in feeds:
            source_name = feed['source']
            articles_by_source[source_name] = feed.get('articles', [])
        
        return articles_by_source
    
    def clear_cache(self):
        """Clear the RSS cache"""
        self.cache.clear()
        logger.info("RSS cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache"""
        return {
            'cache_size': len(self.cache),
            'cache_duration_minutes': self.cache_duration.total_seconds() / 60,
            'cached_sources': list(self.cache.keys())
        }
