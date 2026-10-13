"""
Validation & Verification Service Module
Ensures news accuracy, link integrity, canonical URL deduplication,
headline similarity detection, publication date validation,
and distinction between verified news and unverified/developing claims.
"""

import re
import logging
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Set, Tuple, Optional
import dateutil.parser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stop words for headline tokenization
STOPWORDS: Set[str] = {
    'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'is', 'are',
    'was', 'were', 'with', 'by', 'as', 'it', 'from', 'that', 'this', 'after',
    'over', 'into', 'about', 'out', 'up', 'down', 'be', 'has', 'have', 'had',
    'will', 'says', 'said', 'amid', 'new', 'how', 'why', 'who', 'what'
}

# Tracking query parameters to strip for canonical URL normalization
TRACKING_PARAMS: Set[str] = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'at_medium', 'at_campaign', 'at_custom1', 'at_custom2', 'at_custom3', 'at_custom4',
    'ocid', 'ref', 'rss', 'feed', 'fbclid', 'gclid', 'ved', 'usqp', 'cmpid',
    'mbid', 'taid', 'intcid', 'source', 'ncid', 'ito', 'ns_mchannel', 'ns_source'
}

# Phrases that indicate unverified or speculative claims
UNVERIFIED_CLAIM_PATTERNS = [
    r'\bunconfirmed\s+reports?\b',
    r'\bclaims?\s+without\s+evidence\b',
    r'\bunsubstantiated\s+claims?\b',
    r'\bunbacked\s+claims?\b',
    r'\balleged\b',
    r'\ballegedly\b',
    r'\ballegations?\b',
    r'\bsources?\s+claims?\b',
    r'\bunverified\b',
    r'\brumors?\s+that\b',
    r'\brumoured\b',
    r'\bspeculat(?:ion|ive)\b',
    r'\bpurported\b',
    r'\bpurportedly\b'
]

# Explicit publisher breaking news prefixes
EXPLICIT_BREAKING_PREFIXES = [
    'BREAKING:', 'BREAKING NEWS:', 'ALERT:', 'NEWS ALERT:',
    'JUST IN:', 'DEVELOPING:', 'URGENT:'
]

class ValidationService:
    """Service providing link verification, deduplication, date integrity, and claim validation"""

    def __init__(self):
        self.trust_tiers = {
            'BBC News': {'tier': 1, 'type': 'Primary Broadcaster', 'verified': True},
            'CNN': {'tier': 1, 'type': 'Primary International Network', 'verified': True},
            'The Guardian': {'tier': 1, 'type': 'Independent News Publisher', 'verified': True},
            'Al Jazeera': {'tier': 1, 'type': 'Primary International Network', 'verified': True},
            'NPR News': {'tier': 1, 'type': 'Public National Broadcaster', 'verified': True},
            'TechCrunch': {'tier': 1, 'type': 'Specialized Tech Journalism', 'verified': True},
            'Ars Technica': {'tier': 1, 'type': 'Specialized Science & Tech', 'verified': True},
            'CNBC': {'tier': 1, 'type': 'Financial News Organization', 'verified': True},
            'DW News': {'tier': 1, 'type': 'Public International Broadcaster', 'verified': True},
            'Google News': {'tier': 2, 'type': 'Algorithmic News Aggregator', 'verified': False}
        }

    def validate_url(self, url: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate URL format and return (is_valid, canonical_url, error_message).
        Rejects non-HTTP schemes and abnormal structures.
        """
        if not url or not isinstance(url, str):
            return False, "", "Empty or invalid URL type"

        url = url.strip()
        try:
            parsed = urlparse(url)
            # Only allow http and https schemes
            if parsed.scheme.lower() not in ('http', 'https'):
                return False, "", f"Disallowed scheme: {parsed.scheme}"

            netloc = parsed.netloc.lower()
            if not netloc or '.' not in netloc and netloc != 'localhost':
                return False, "", "Invalid host or domain name"

            # Strip port if standard
            if netloc.endswith(':80') and parsed.scheme.lower() == 'http':
                netloc = netloc[:-3]
            elif netloc.endswith(':443') and parsed.scheme.lower() == 'https':
                netloc = netloc[:-4]

            # Filter out tracking query parameters
            query_pairs = parse_qsl(parsed.query, keep_blank_values=False)
            clean_query = [
                (k, v) for k, v in query_pairs
                if k.lower() not in TRACKING_PARAMS and not k.lower().startswith(('utm_', 'at_'))
            ]
            
            # Normalize path: remove trailing slash unless root
            clean_path = parsed.path.rstrip('/') or '/'
            
            # Reconstruct canonical URL (discarding fragments)
            canonical = urlunparse((
                parsed.scheme.lower(),
                netloc,
                clean_path,
                '',
                urlencode(clean_query),
                ''  # Drop fragments (#...)
            ))
            return True, canonical, None

        except Exception as e:
            return False, "", f"URL parse failure: {str(e)}"

    def normalize_headline(self, title: str) -> Tuple[Set[str], str]:
        """
        Normalize headline for similarity and deduplication:
        - Strips publisher attribution suffixes (e.g. ' - BBC News', ' | Reuters')
        - Lowercases and removes punctuation
        - Returns (set of clean tokens, normalized headline string)
        """
        if not title:
            return set(), ""

        # 1. Remove trailing publisher branding (e.g. ' - BBC News', ' | CNBC')
        cleaned = re.sub(r'\s*[-|–—:]\s*[A-Za-z0-9\s\.\&]+$', '', title.strip())
        # If removal wiped out the title, revert to original
        if len(cleaned) < 5:
            cleaned = title.strip()

        # 2. Lowercase and remove non-alphanumeric characters
        cleaned_text = cleaned.lower()
        cleaned_text = re.sub(r'[^a-z0-9\s]', ' ', cleaned_text)
        
        # 3. Filter stopwords
        tokens = [w for w in cleaned_text.split() if w not in STOPWORDS and len(w) > 1]
        token_set = set(tokens)
        normalized_str = " ".join(tokens)
        return token_set, normalized_str

    def calculate_headline_similarity(self, tokens_a: Set[str], tokens_b: Set[str]) -> float:
        """
        Calculate Jaccard similarity score between two tokenized headlines.
        Returns a float between 0.0 and 1.0.
        """
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = len(tokens_a & tokens_b)
        union = len(tokens_a | tokens_b)
        if union == 0:
            return 0.0
        return intersection / union

    def parse_publication_date(self, entry: Any) -> Tuple[Optional[datetime], str, bool]:
        """
        Extract original publication timestamp from RSS entry without fabricating current time.
        Returns (published_dt, relative_string, is_verified_date).
        """
        dt = None
        # Try entry parsed dates first
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                dt = datetime(*entry.published_parsed[:6])
            except (TypeError, ValueError):
                pass
        
        if dt is None and hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            try:
                dt = datetime(*entry.updated_parsed[:6])
            except (TypeError, ValueError):
                pass

        # Try raw string parsing via dateutil
        if dt is None:
            raw_date = entry.get('published') or entry.get('pubDate') or entry.get('updated')
            if raw_date and isinstance(raw_date, str):
                try:
                    parsed_dt = dateutil.parser.parse(raw_date)
                    if parsed_dt.tzinfo is not None:
                        # Convert to naive local for consistency
                        dt = parsed_dt.astimezone(timezone.utc).replace(tzinfo=None)
                    else:
                        dt = parsed_dt
                except Exception:
                    pass

        if dt is None:
            return None, "Publication date unverified", False

        # Compute difference against CURRENT UTC TIME (not machine local time!)
        utc_now = datetime.now(timezone.utc).replace(tzinfo=None)
        diff = utc_now - dt
        total_seconds = int(diff.total_seconds())

        # Guard against clock skew and future-dated posts:
        if total_seconds < -300:
            # More than 5 minutes in future: timezone discrepancy or publisher future schedule
            rel_str = dt.strftime("%b %d, %Y")
        elif total_seconds < 60:
            # Published between -300s (minor skew) and +60s
            rel_str = "Just now"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            rel_str = f"{minutes}m ago"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            rel_str = f"{hours}h ago"
        elif total_seconds < 604800:
            days = total_seconds // 86400
            rel_str = f"{days}d ago"
        else:
            rel_str = dt.strftime("%b %d, %Y")

        return dt, rel_str, True

    def check_staleness(self, published_dt: Optional[datetime]) -> Tuple[bool, Optional[str]]:
        """
        Flag outdated stories (> 48 hours old) to prevent misleading users about breaking news.
        Returns (is_outdated, label).
        """
        if not published_dt:
            return False, None

        utc_now = datetime.now(timezone.utc).replace(tzinfo=None)
        age = utc_now - published_dt
        if age > timedelta(days=7):
            return True, f"Archived ({age.days}d old)"
        elif age > timedelta(hours=48):
            days = age.days or (age.seconds // 86400)
            return True, f"Published {days}d ago"
        
        return False, None

    def evaluate_claim_verification(self, title: str, description: str) -> Tuple[bool, str]:
        """
        Examine text for speculative or unverified assertions.
        Returns (is_unverified, label).
        """
        combined = f"{title} {description}".lower()
        for pattern in UNVERIFIED_CLAIM_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                return True, "Developing / Unverified Claim"
        return False, "Verified Publisher Report"

    def extract_original_publisher(self, title: str, source_name: str) -> str:
        """
        Extract original publisher for aggregator feeds (e.g. Google News)
        where titles end with ' - Publisher Name'.
        """
        if source_name == 'Google News' and ' - ' in title:
            parts = title.rsplit(' - ', 1)
            candidate = parts[-1].strip()
            if 2 <= len(candidate) <= 30:
                return candidate
        return source_name

    def deduplicate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect and merge duplicate articles using canonical URLs and normalized headline similarity.
        Prioritizes Tier 1 primary news publishers over aggregators.
        """
        seen_canonical_urls: Dict[str, Dict[str, Any]] = {}
        unique_articles: List[Dict[str, Any]] = []

        for article in articles:
            canon_url = article.get('canonical_url') or article.get('link', '')
            token_set = article.get('normalized_tokens', set())
            title_norm = article.get('normalized_headline', '')

            # 1. Exact Canonical URL match check
            if canon_url in seen_canonical_urls:
                existing = seen_canonical_urls[canon_url]
                self._merge_source_reference(existing, article)
                continue

            # 2. Headline token similarity check
            duplicate_found = False
            for existing in unique_articles:
                existing_tokens = existing.get('normalized_tokens', set())
                # Exact normalized headline string match
                if title_norm and title_norm == existing.get('normalized_headline', ''):
                    duplicate_found = True
                    self._resolve_duplicate_priority(existing, article)
                    break

                # High Jaccard similarity match (same story across feeds)
                sim = self.calculate_headline_similarity(token_set, existing_tokens)
                if sim >= 0.72 and len(token_set & existing_tokens) >= 3:
                    duplicate_found = True
                    self._resolve_duplicate_priority(existing, article)
                    break

            if not duplicate_found:
                seen_canonical_urls[canon_url] = article
                unique_articles.append(article)

        return unique_articles

    def _resolve_duplicate_priority(self, existing: Dict[str, Any], candidate: Dict[str, Any]):
        """
        When two articles are identified as duplicates, determine which one to keep
        based on publisher trust tier and date recency, merging alternative sources.
        """
        existing_tier = self.trust_tiers.get(existing.get('source'), {}).get('tier', 2)
        candidate_tier = self.trust_tiers.get(candidate.get('source'), {}).get('tier', 2)

        # If candidate has higher trust (Tier 1 vs Tier 2), promote candidate
        if candidate_tier < existing_tier:
            # Save existing as alternative
            self._merge_source_reference(candidate, existing)
            # Swap content in-place
            existing.update(candidate)
        else:
            # Keep existing, add candidate as alternative reference
            self._merge_source_reference(existing, candidate)

    def _merge_source_reference(self, primary: Dict[str, Any], duplicate: Dict[str, Any]):
        """Add duplicate source link to primary article for cross-source transparency"""
        if 'alternative_sources' not in primary:
            primary['alternative_sources'] = []

        dup_src = duplicate.get('source', '')
        dup_link = duplicate.get('link', '')
        if dup_src and dup_src != primary.get('source'):
            # Avoid duplicate references
            if not any(alt['source'] == dup_src for alt in primary['alternative_sources']):
                primary['alternative_sources'].append({
                    'source': dup_src,
                    'link': dup_link
                })
