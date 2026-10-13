"""
Category Service Module
Handles news categorization, keyword heuristics, and trending algorithms.
"""

import re
from typing import List, Dict, Any, Set
from datetime import datetime, timedelta

class CategoryService:
    """Service for classifying news articles and determining trending topics"""
    
    def __init__(self):
        # Primary category definitions with weighted keywords and priority
        self.category_keywords = {
            'Breaking News': {
                'keywords': [
                    'breaking', 'urgent', 'alert', 'emergency', 'crisis', 'disaster', 'explosion',
                    'fatal', 'earthquake', 'wildfire', 'shooting', 'evacuate', 'casualty', 'hostage',
                    'missile', 'strike', 'lockdown'
                ],
                'priority': 0
            },
            'World': {
                'keywords': [
                    'world', 'global', 'international', 'diplomacy', 'diplomatic', 'treaty',
                    'europe', 'asia', 'africa', 'middle east', 'latin america', 'ukraine',
                    'russia', 'china', 'taiwan', 'gaza', 'israel', 'lebanon', 'united nations',
                    'nato', 'summit', 'prime minister', 'foreign minister', 'ambassador'
                ],
                'priority': 1
            },
            'Business': {
                'keywords': [
                    'business', 'economy', 'economic', 'market', 'markets', 'stocks', 'wall street',
                    'dow', 'nasdaq', 's&p', 'inflation', 'interest rate', 'fed', 'federal reserve',
                    'banking', 'bank', 'investor', 'investment', 'earnings', 'revenue', 'profit',
                    'ceo', 'crypto', 'bitcoin', 'trade', 'tariff', 'acquisition', 'merger', 'retail'
                ],
                'priority': 2
            },
            'Technology': {
                'keywords': [
                    'technology', 'tech', 'ai', 'artificial intelligence', 'openai', 'chatgpt',
                    'google', 'apple', 'microsoft', 'nvidia', 'semiconductor', 'chip', 'cybersecurity',
                    'hacker', 'malware', 'software', 'hardware', 'smartphone', 'robotics', 'cloud',
                    'startup', 'venture', 'algorithm', 'meta', 'app', 'computing', 'crypto'
                ],
                'priority': 3
            },
            'Science & Health': {
                'keywords': [
                    'science', 'scientific', 'health', 'medical', 'medicine', 'hospital', 'cancer',
                    'disease', 'vaccine', 'virus', 'clinical', 'nasa', 'space', 'astronomy', 'planet',
                    'moon', 'telescope', 'climate', 'environment', 'biology', 'physics', 'energy'
                ],
                'priority': 4
            },
            'Politics': {
                'keywords': [
                    'politics', 'political', 'election', 'vote', 'voter', 'president', 'white house',
                    'congress', 'senate', 'house', 'supreme court', 'democrat', 'republican',
                    'biden', 'trump', 'legislation', 'bill', 'governor', 'mayor', 'campaign', 'poll'
                ],
                'priority': 5
            },
            'Sports & Culture': {
                'keywords': [
                    'sport', 'sports', 'football', 'soccer', 'nfl', 'nba', 'premier league',
                    'olympic', 'olympics', 'tennis', 'championship', 'hollywood', 'movie',
                    'film', 'actor', 'music', 'album', 'grammy', 'oscar', 'celebrity', 'culture'
                ],
                'priority': 6
            }
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for categorization"""
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()
    
    def _calculate_category_score(self, text: str, category_keywords: List[str]) -> int:
        """Calculate match score for a given category"""
        score = 0
        words = set(text.split())
        
        for keyword in category_keywords:
            keyword_lower = keyword.lower()
            if ' ' in keyword_lower:
                # Phrase match
                if keyword_lower in text:
                    score += 3
            else:
                # Word match
                if keyword_lower in words:
                    score += 2
        return score
    
    def classify_article(self, article: Dict[str, Any]) -> str:
        """Classify a single article into the most appropriate category"""
        title = article.get('title', '')
        desc = article.get('description', '')
        summary = article.get('summary', '')
        existing_cat = (article.get('category') or '').lower()
        
        combined_text = f"{title} {title} {desc} {summary}"
        cleaned = self._clean_text(combined_text)
        
        # Check explicit feed hints
        if 'tech' in existing_cat or 'gadget' in existing_cat:
            return 'Technology'
        if 'business' in existing_cat or 'market' in existing_cat or 'money' in existing_cat:
            return 'Business'
        if 'science' in existing_cat or 'health' in existing_cat:
            return 'Science & Health'
        if 'sport' in existing_cat or 'culture' in existing_cat:
            return 'Sports & Culture'
            
        # Score calculation
        best_category = None
        highest_score = 0
        lowest_priority = 999
        
        for category, config in self.category_keywords.items():
            score = self._calculate_category_score(cleaned, config['keywords'])
            if score > 0:
                priority = config['priority']
                # Breaking news gets high threshold to avoid false positives
                if category == 'Breaking News' and score < 4:
                    continue
                
                if score > highest_score or (score == highest_score and priority < lowest_priority):
                    highest_score = score
                    lowest_priority = priority
                    best_category = category
        
        if best_category:
            return best_category
        
        # Fallback to source category if defined
        if article.get('category') and article['category'] in self.category_keywords:
            return article['category']
            
        return 'World'
    
    def categorize_articles(self, articles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize a list of articles, ensuring consistent category sorting"""
        categorized: Dict[str, List[Dict[str, Any]]] = {}
        
        for article in articles:
            # Ensure article has its assigned category updated
            cat = self.classify_article(article)
            article['assigned_category'] = cat
            
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(article)
            
        # Sort each bucket by publication date
        def date_key(item):
            dt = item.get('published_dt')
            if dt and isinstance(dt, datetime):
                return dt
            return datetime.min
            
        for cat in categorized:
            categorized[cat].sort(key=date_key, reverse=True)
            
        return categorized
    
    def get_available_categories(self, articles: List[Dict[str, Any]]) -> List[str]:
        """Get ordered list of active categories present in the articles"""
        categorized = self.categorize_articles(articles)
        categories = list(categorized.keys())
        
        # Defined preferred ordering
        order = ['Breaking News', 'World', 'Business', 'Technology', 'Science & Health', 'Politics', 'Sports & Culture', 'General']
        sorted_cats = [c for c in order if c in categories]
        # Append any extras
        for c in categories:
            if c not in sorted_cats:
                sorted_cats.append(c)
                
        return sorted_cats
    
    def filter_by_category(self, articles: List[Dict[str, Any]], category: str) -> List[Dict[str, Any]]:
        """Filter articles by category name"""
        if not category or category.lower() == 'all':
            return articles
            
        categorized = self.categorize_articles(articles)
        return categorized.get(category, [])
    
    def get_category_stats(self, articles: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get count statistics per category"""
        categorized = self.categorize_articles(articles)
        return {cat: len(arts) for cat, arts in categorized.items()}
    
    def get_trending_articles(self, articles: List[Dict[str, Any]], limit: int = 6) -> List[Dict[str, Any]]:
        """
        Identify trending stories based on recency, headline velocity, and diversity of publishers.
        """
        if not articles:
            return []
            
        now = datetime.now()
        scored_articles = []
        seen_titles: Set[str] = set()
        
        for article in articles:
            title_norm = self._clean_text(article.get('title', ''))[:40]
            if title_norm in seen_titles:
                continue
            seen_titles.add(title_norm)
            
            score = 10.0
            
            # Recency boost
            dt = article.get('published_dt')
            if dt and isinstance(dt, datetime):
                hours_old = (now - dt).total_seconds() / 3600
                if hours_old < 2:
                    score += 50
                elif hours_old < 6:
                    score += 35
                elif hours_old < 12:
                    score += 20
                elif hours_old < 24:
                    score += 10
            
            # Image presence boost (visual appeal)
            if article.get('image'):
                score += 15
                
            # Breaking news boost
            if article.get('assigned_category') == 'Breaking News':
                score += 30
                
            scored_articles.append((score, article))
            
        # Sort by score descending
        scored_articles.sort(key=lambda x: x[0], reverse=True)
        
        # Select top articles while maintaining source variety
        selected = []
        sources_used: Dict[str, int] = {}
        
        for score, art in scored_articles:
            src = art.get('source', '')
            if sources_used.get(src, 0) < 2 or len(selected) < limit // 2:
                selected.append(art)
                sources_used[src] = sources_used.get(src, 0) + 1
                if len(selected) >= limit:
                    break
                    
        # If still under limit, backfill
        if len(selected) < limit:
            for score, art in scored_articles:
                if art not in selected:
                    selected.append(art)
                    if len(selected) >= limit:
                        break
                        
        return selected
