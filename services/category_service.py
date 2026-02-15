"""
Category Service Module
Handles news categorization and filtering logic
"""

import re
from typing import List, Dict, Any, Set
from datetime import datetime

class CategoryService:
    """Service for categorizing news articles"""
    
    def __init__(self):
        # Define category keywords for classification
        self.category_keywords = {
            'World': {
                'keywords': [
                    'world', 'global', 'international', 'foreign', 'europe', 'asia', 'africa',
                    'middle east', 'latin america', 'uk', 'britain', 'france', 'germany', 'china',
                    'japan', 'india', 'russia', 'united nations', 'diplomatic', 'embassy'
                ],
                'priority': 1
            },
            'Business': {
                'keywords': [
                    'business', 'economy', 'economic', 'market', 'markets', 'stocks', 'finance',
                    'financial', 'investment', 'investing', 'trade', 'trading', 'company', 'corporate',
                    'earnings', 'profit', 'revenue', 'merger', 'acquisition', 'ceo', 'executive'
                ],
                'priority': 2
            },
            'Technology': {
                'keywords': [
                    'technology', 'tech', 'software', 'hardware', 'internet', 'digital', 'ai',
                    'artificial intelligence', 'machine learning', 'cybersecurity', 'data', 'cloud',
                    'mobile', 'smartphone', 'computer', 'startup', 'innovation', 'gadget', 'app'
                ],
                'priority': 3
            },
            'Domestic': {
                'keywords': [
                    'domestic', 'national', 'local', 'government', 'politics', 'policy', 'election',
                    'congress', 'senate', 'president', 'white house', 'court', 'supreme court',
                    'federal', 'state', 'city', 'mayor', 'governor', 'senator', 'representative'
                ],
                'priority': 4
            },
            'Breaking News': {
                'keywords': [
                    'breaking', 'urgent', 'alert', 'emergency', 'crisis', 'disaster', 'accident',
                    'explosion', 'fire', 'shooting', 'attack', 'terror', 'natural disaster'
                ],
                'priority': 0  # Highest priority
            }
        }
        
        # Additional categories for broader classification
        self.secondary_categories = {
            'Sports': ['sport', 'sports', 'football', 'soccer', 'basketball', 'baseball', 'tennis', 'olympics'],
            'Entertainment': ['entertainment', 'movie', 'movies', 'music', 'celebrity', 'hollywood', 'film'],
            'Health': ['health', 'medical', 'medicine', 'covid', 'virus', 'disease', 'hospital', 'doctor'],
            'Science': ['science', 'research', 'study', 'space', 'nasa', 'climate', 'environment', 'weather']
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for analysis"""
        if not text:
            return ""
        
        # Convert to lowercase and remove special characters
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _calculate_category_score(self, text: str, category_keywords: List[str]) -> int:
        """Calculate score for a category based on keyword matches"""
        score = 0
        words = text.split()
        
        for keyword in category_keywords:
            keyword_lower = keyword.lower()
            # Exact word match
            if keyword_lower in words:
                score += 2
            # Partial match
            elif keyword_lower in text:
                score += 1
        
        return score
    
    def classify_article(self, article: Dict[str, Any]) -> str:
        """Classify a single article into a category"""
        # Combine title and description for better classification
        title = article.get('title', '')
        description = article.get('description', '')
        summary = article.get('summary', '')
        
        combined_text = f"{title} {description} {summary}"
        cleaned_text = self._clean_text(combined_text)
        
        # Check existing category from RSS feed first
        existing_category = article.get('category', '').lower()
        if existing_category:
            # Map common RSS categories to our categories
            category_mapping = {
                'world': 'World',
                'business': 'Business',
                'technology': 'Technology',
                'tech': 'Technology',
                'politics': 'Domestic',
                'national': 'Domestic',
                'breaking': 'Breaking News',
                'urgent': 'Breaking News'
            }
            
            if existing_category in category_mapping:
                return category_mapping[existing_category]
        
        # Calculate scores for each category
        category_scores = {}
        
        for category, config in self.category_keywords.items():
            score = self._calculate_category_score(cleaned_text, config['keywords'])
            if score > 0:
                category_scores[category] = {
                    'score': score,
                    'priority': config['priority']
                }
        
        # Check secondary categories if no primary category matches
        if not category_scores:
            for category, keywords in self.secondary_categories.items():
                score = self._calculate_category_score(cleaned_text, keywords)
                if score > 0:
                    category_scores[category] = {
                        'score': score,
                        'priority': 10  # Lower priority for secondary categories
                    }
        
        # Select best category
        if category_scores:
            # Sort by score (descending) then by priority (ascending)
            best_category = min(
                category_scores.items(),
                key=lambda x: (-x[1]['score'], x[1]['priority'])
            )[0]
            return best_category
        
        return 'General'  # Default category
    
    def categorize_articles(self, articles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize a list of articles"""
        categorized = {}
        
        for article in articles:
            category = self.classify_article(article)
            
            if category not in categorized:
                categorized[category] = []
            
            categorized[category].append(article)
        
        # Sort articles within each category by publication date
        def safe_date(item):
            published = item.get("published_parsed")
            if published and isinstance(published, tuple) and len(published) >= 6:
                try:
                    return datetime(*published[:6])
                except (TypeError, ValueError):
                    pass
            return datetime.min  # Items with no dates go to bottom
        
        for category in categorized:
            categorized[category] = sorted(categorized[category], key=safe_date, reverse=True)
        
        return categorized
    
    def get_available_categories(self, articles: List[Dict[str, Any]]) -> List[str]:
        """Get list of available categories from articles"""
        categorized = self.categorize_articles(articles)
        categories = list(categorized.keys())
        
        # Sort categories: Breaking News first, then alphabetically
        if 'Breaking News' in categories:
            categories.remove('Breaking News')
            categories = ['Breaking News'] + sorted(categories)
        else:
            categories = sorted(categories)
        
        return categories
    
    def filter_by_category(self, articles: List[Dict[str, Any]], category: str) -> List[Dict[str, Any]]:
        """Filter articles by specific category"""
        if category.lower() == 'all':
            return articles
        
        categorized = self.categorize_articles(articles)
        return categorized.get(category, [])
    
    def get_category_stats(self, articles: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get statistics about article distribution across categories"""
        categorized = self.categorize_articles(articles)
        
        stats = {}
        for category, category_articles in categorized.items():
            stats[category] = len(category_articles)
        
        return stats
    
    def get_trending_articles(self, articles: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending articles based on recency and category importance"""
        # Sort by publication date first (production-safe)
        def safe_date(item):
            published = item.get("published_parsed")
            if published and isinstance(published, tuple) and len(published) >= 6:
                try:
                    return datetime(*published[:6])
                except (TypeError, ValueError):
                    pass
            return datetime.min  # Items with no dates go to bottom
        
        sorted_articles = sorted(articles, key=safe_date, reverse=True)
        
        # Boost breaking news and recent articles
        boosted_articles = []
        current_time = datetime.now()
        
        for article in sorted_articles:
            score = 0
            
            # Base score from recency (newer = higher score)
            published_time = article.get('published_parsed')
            if published_time:
                try:
                    if isinstance(published_time, tuple):
                        published_dt = datetime(*published_time[:6])
                    else:
                        published_dt = published_time
                    
                    hours_old = (current_time - published_dt).total_seconds() / 3600
                    if hours_old < 1:
                        score += 100
                    elif hours_old < 6:
                        score += 50
                    elif hours_old < 24:
                        score += 20
                    elif hours_old < 72:
                        score += 10
                except:
                    pass
            
            # Category boost
            category = self.classify_article(article)
            if category == 'Breaking News':
                score += 200
            elif category == 'World':
                score += 30
            elif category == 'Business':
                score += 25
            elif category == 'Technology':
                score += 20
            
            article['trending_score'] = score
            boosted_articles.append(article)
        
        # Sort by trending score and return top articles
        boosted_articles.sort(key=lambda x: x.get('trending_score', 0), reverse=True)
        return boosted_articles[:limit]
