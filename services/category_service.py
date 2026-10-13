"""
Category Service Module
Accurate, context-aware news categorization, keyword heuristics,
and verification-informed trending algorithms.
"""

import re
from typing import List, Dict, Any, Set, Optional
from datetime import datetime, timedelta, timezone

class CategoryService:
    """Service for classifying news articles accurately without false positives"""
    
    def __init__(self):
        # Precise, contextual keyword definitions with negative exclusions
        self.category_rules = {
            'Breaking News': {
                'priority': 0,
                'explicit_markers': [
                    r'\bbreaking(?:\s+news)?\b',
                    r'\bnews\s+alert\b',
                    r'\bjust\s+in\b',
                    r'\bflash\b',
                    r'\burgent\b'
                ],
                'emergency_keywords': [
                    r'\bmass\s+shooting\b',
                    r'\bactive\s+shooter\b',
                    r'\bmajor\s+earthquake\b',
                    r'\btsunami\s+warning\b',
                    r'\bcatastrophic\s+(?:explosion|fire|collapse)\b',
                    r'\bevacuation\s+order\b',
                    r'\bplane\s+crash\b',
                    r'\bstate\s+of\s+emergency\b'
                ],
                'negative_patterns': [
                    r'\b(?:movie|film|filming|hollywood|actor|trailer|cinema)\b',
                    r'\b(?:shooting\s+guard|free\s+throw|penalty|field\s+goal)\b',
                    r'\b(?:cost\s+of\s+living|existential|identity|midlife)\s+crisis\b',
                    r'\b(?:baseball|bowling|strike\s+zone|labor\s+union\s+strike)\b',
                    r'\b(?:anniversary|history|memorial|retrospective)\b'
                ]
            },
            'World': {
                'priority': 1,
                'keywords': [
                    'international', 'diplomacy', 'diplomatic', 'treaty', 'foreign minister',
                    'prime minister', 'ambassador', 'united nations', 'un security council',
                    'nato', 'bilateral', 'geopolitics', 'summit', 'middle east', 'latin america',
                    'european union', 'asia pacific', 'ukraine', 'russia', 'china', 'taiwan',
                    'gaza', 'israel', 'lebanon', 'sudan', 'syria', 'north korea', 'cross border'
                ],
                'negative_patterns': [
                    r'\b(?:nfl|nba|premier\s+league|box\s+office)\b'
                ]
            },
            'Business': {
                'priority': 2,
                'keywords': [
                    'economy', 'economic', 'inflation', 'interest rate', 'interest rates', 'federal reserve',
                    'wall street', 'dow jones', 'nasdaq', 's&p 500', 'stock market', 'stocks',
                    'investors', 'earnings report', 'quarterly revenue', 'profit margin', 'quarterly profit',
                    'treasury yields', 'banking sector', 'central bank', 'central banks', 'merger', 'acquisition',
                    'ipo', 'venture capital', 'tariffs', 'cryptocurrency', 'bitcoin', 'etf',
                    'gdp growth', 'recession', 'commodities', 'crude oil', 'corporate buyout',
                    'growth forecast', 'energy prices', 'budget deficit', 'trade deficit', 'retail sales', 'imf', 'world bank'
                ],
                'negative_patterns': []
            },
            'Technology': {
                'priority': 3,
                'keywords': [
                    'artificial intelligence', 'machine learning', 'neural network', 'openai',
                    'chatgpt', 'generative ai', 'llm', 'semiconductor', 'microchip', 'nvidia',
                    'silicon valley', 'cybersecurity', 'ransomware', 'malware', 'zero day',
                    'software update', 'cloud computing', 'quantum computing', 'supercomputer',
                    'smartphone', 'iphone', 'android os', 'apple inc', 'google cloud',
                    'microsoft azure', 'metaverse', 'open source software', 'programming language',
                    'developer api', 'robotics automation', 'autonomous vehicles', 'cyberattack', 'hackers', 'ai startup', 'data breach', 'gpu'
                ],
                'negative_patterns': [
                    r'\b(?:apple\s+pie|apple\s+orchard|fruit|harvest)\b'
                ]
            },
            'Science & Health': {
                'priority': 4,
                'keywords': [
                    'scientific study', 'clinical trial', 'clinical trials', 'medical research', 'researchers find',
                    'laboratory', 'peer reviewed', 'cancer treatment', 'vaccine trial', 'vaccine', 'vaccines',
                    'vaccination', 'unvaccinated', 'measles', 'outbreak', 'epidemic', 'pandemic', 'disease',
                    'infectious disease', 'pathogen', 'fda approval', 'genome', 'dna sequencing',
                    'nasa', 'space telescope', 'james webb', 'mars rover', 'astronomy',
                    'supernova', 'solar eclipse', 'climate change', 'global warming',
                    'carbon emissions', 'renewable energy', 'biodiversity', 'ecosystem',
                    'species discovered', 'neuroscience', 'mental health', 'hospital', 'public health',
                    'cdc', 'who', 'medical study', 'virus', 'infection', 'space flight', 'astronaut', 'spacex', 'orbit', 'mars', 'biotech'
                ],
                'negative_patterns': []
            },
            'Politics': {
                'priority': 5,
                'keywords': [
                    'congress', 'senate', 'house of representatives', 'parliament', 'legislation',
                    'supreme court', 'bipartisan bill', 'presidential election', 'electoral college',
                    'campaign rally', 'white house', 'ballot', 'voter turnout', 'governor',
                    'executive order', 'attorney general', 'federal judge', 'impeachment',
                    'political party', 'democrats', 'republicans', 'cabinet secretary', 'caucus'
                ],
                'negative_patterns': [
                    r'\b(?:box\s+office|celebrity|entertainment\s+tonight)\b'
                ]
            },
            'Sports & Culture': {
                'priority': 6,
                'keywords': [
                    'premier league', 'champions league', 'football', 'soccer', 'nfl', 'nba',
                    'mlb', 'tennis tournament', 'grand slam', 'wimbledon', 'olympics', 'world cup',
                    'formula 1', 'championship', 'hollywood', 'box office', 'film premiere',
                    'movie review', 'actor', 'actress', 'director', 'academy awards', 'oscars',
                    'grammy awards', 'emmy', 'music album', 'billboard 100', 'celebrity'
                ],
                'negative_patterns': []
            }
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for analysis"""
        if not text:
            return ""
        text = text.lower()
        return re.sub(r'\s+', ' ', text).strip()
    
    def classify_article(self, article: Dict[str, Any]) -> str:
        """
        Classify article with verification guards:
        - Prevents false Breaking News triggers.
        - Respects feed topic tags and contextual phrase weighting.
        - Falls back gracefully to the source's native category if no strong match.
        """
        title = article.get('title', '')
        desc = article.get('description', '') or article.get('summary', '')
        existing_cat = (article.get('category') or '').strip().lower()
        source_name = article.get('source', '')
        
        # Check claim status & recency for Breaking News check
        is_unverified = article.get('is_unverified', False)
        hours_old = 999.0
        published_dt = article.get('published_dt')
        if published_dt and isinstance(published_dt, datetime):
            utc_now = datetime.now(timezone.utc).replace(tzinfo=None)
            hours_old = max(0.0, (utc_now - published_dt).total_seconds() / 3600.0)

        title_clean = self._clean_text(title)
        body_clean = self._clean_text(f"{title} {desc}")

        # 1. EVALUATE BREAKING NEWS STRICTLY
        breaking_rules = self.category_rules['Breaking News']
        has_negative_breaking = any(re.search(pat, body_clean) for pat in breaking_rules['negative_patterns'])

        if not is_unverified and not has_negative_breaking and hours_old <= 6.0:
            # Check explicit title markers (e.g. 'BREAKING:', 'JUST IN:')
            for pat in breaking_rules['explicit_markers']:
                if re.search(pat, title_clean):
                    return 'Breaking News'
            
            # Check major emergency disaster keywords in title
            for pat in breaking_rules['emergency_keywords']:
                if re.search(pat, title_clean):
                    return 'Breaking News'

        # 2. SCORE CATEGORIES WITH CONTEXTUAL PHRASE MATCHING FIRST
        # Real topic keywords always supersede publisher default niches (e.g., Ars Technica measles -> Science & Health)
        scores: Dict[str, int] = {}
        
        for category, rules in self.category_rules.items():
            if category == 'Breaking News':
                continue

            # Check negative patterns
            has_neg = any(re.search(pat, body_clean) for pat in rules.get('negative_patterns', []))
            if has_neg:
                continue

            score = 0
            for kw in rules.get('keywords', []):
                # Phrase in title gets 4 points
                if kw in title_clean:
                    score += 4
                # Phrase in description gets 2 points
                elif kw in body_clean:
                    score += 2
                    
            if score > 0:
                scores[category] = score

        if scores:
            # Pick highest score, breaking ties by configured priority
            best_cat = max(
                scores.items(),
                key=lambda item: (item[1], -self.category_rules[item[0]]['priority'])
            )[0]
            # If the score is meaningful (at least 2), adopt it
            if scores[best_cat] >= 2:
                return best_cat

        # 3. CHECK EXPLICIT SOURCE CATEGORY HINTS (When content score is ambiguous or generic)
        if source_name == 'TechCrunch':
            return 'Technology'
        elif source_name == 'Ars Technica':
            return 'Technology'
        elif source_name == 'CNBC' and not any(k in body_clean for k in ['premier league', 'nba', 'oscar']):
            return 'Business'

        # 4. FALLBACK TO RSS FEED METADATA CATEGORY IF VALID
        for cat_name in ['Technology', 'Business', 'World', 'Science & Health', 'Politics', 'Sports & Culture']:
            if cat_name.lower() in existing_cat:
                return cat_name

        # 5. DEFAULT TO SOURCE'S DESIGNATED PRIMARY TOPIC (NOT BLIND WORLD)
        source_fallbacks = {
            'TechCrunch': 'Technology',
            'Ars Technica': 'Technology',
            'CNBC': 'Business',
            'NPR News': 'Politics',
            'The Guardian': 'World',
            'BBC News': 'World',
            'Al Jazeera': 'World',
            'DW News': 'World',
            'CNN': 'World',
            'Google News': 'World'
        }
        return source_fallbacks.get(source_name, 'World')

    def categorize_articles(self, articles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize articles into clean buckets while enforcing verification rules"""
        categorized: Dict[str, List[Dict[str, Any]]] = {}

        for article in articles:
            cat = self.classify_article(article)
            article['assigned_category'] = cat

            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(article)

        # Sort each bucket by publication date (newest first)
        def date_sort(item):
            dt = item.get('published_dt')
            if dt and isinstance(dt, datetime):
                return dt
            return datetime.min

        for cat in categorized:
            categorized[cat].sort(key=date_sort, reverse=True)

        return categorized

    def get_available_categories(self, articles: List[Dict[str, Any]]) -> List[str]:
        """Get ordered list of non-empty categories"""
        categorized = self.categorize_articles(articles)
        order = [
            'Breaking News', 'World', 'Business', 'Technology',
            'Science & Health', 'Politics', 'Sports & Culture'
        ]
        return [c for c in order if c in categorized and len(categorized[c]) > 0]

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
        Rank trending articles with verification and diversity safeguards:
        - Down-ranks unverified or speculative claims.
        - Penalizes stale articles (> 48 hours).
        - Boosts recent verified Tier 1 reporting.
        """
        if not articles:
            return []

        now = datetime.now()
        scored_articles = []

        for article in articles:
            score = 10.0

            # 1. Recency scoring based on true published_dt
            dt = article.get('published_dt')
            if dt and isinstance(dt, datetime):
                age_hours = (now - dt).total_seconds() / 3600.0
                if age_hours < 2:
                    score += 50
                elif age_hours < 6:
                    score += 35
                elif age_hours < 12:
                    score += 20
                elif age_hours < 24:
                    score += 10
                elif age_hours > 48:
                    score -= 30  # Penalty for outdated stories
            else:
                score -= 15  # Penalty for missing publication dates

            # 2. Verification status scoring
            if article.get('is_unverified'):
                score -= 25  # Downrank speculative claims in trending list
            else:
                score += 10  # Reward verified publisher reports

            # 3. Source trust tier boost
            if article.get('trust_tier') == 1:
                score += 15

            # 4. Multi-source coverage boost (if multiple outlets covered this story)
            alt_sources = article.get('alternative_sources', [])
            if alt_sources:
                score += min(len(alt_sources) * 15, 45)

            # 5. Image boost for visual engagement
            if article.get('image'):
                score += 10

            scored_articles.append((score, article))

        scored_articles.sort(key=lambda x: x[0], reverse=True)

        # Select top items ensuring publisher diversity
        selected = []
        sources_count: Dict[str, int] = {}

        for score, art in scored_articles:
            src = art.get('source', '')
            if sources_count.get(src, 0) < 2 or len(selected) < limit // 2:
                selected.append(art)
                sources_count[src] = sources_count.get(src, 0) + 1
                if len(selected) >= limit:
                    break

        # Backfill if needed
        if len(selected) < limit:
            for score, art in scored_articles:
                if art not in selected:
                    selected.append(art)
                    if len(selected) >= limit:
                        break

        return selected
