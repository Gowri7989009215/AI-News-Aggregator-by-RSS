"""
Comprehensive Unit & Integration Test Suite for NewsHub RSS Aggregator
Tests news accuracy, validation, canonical deduplication, date preservation,
claim verification, category accuracy, and error handling.
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import json
from app import app
from services.validation_service import ValidationService
from services.category_service import CategoryService
from services.scraper_service import ScraperService
from services.rss_service import RSSService

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# ==============================================================================
# 1. LINK VALIDATION & CANONICAL URL TESTS
# ==============================================================================

def test_url_validation_and_tracking_stripping():
    """Verify that URL validation rejects illegal schemes and strips tracking parameters"""
    validator = ValidationService()
    
    # Valid URL with tracking parameters
    url_with_tracking = "https://www.bbc.co.uk/news/articles/c12345?utm_source=rss&utm_medium=feed&at_campaign=rss#comments"
    is_valid, canonical, err = validator.validate_url(url_with_tracking)
    assert is_valid is True
    assert canonical == "https://www.bbc.co.uk/news/articles/c12345"
    assert err is None
    assert "utm_source" not in canonical
    assert "at_campaign" not in canonical
    assert "#comments" not in canonical
    
    # Disallowed non-HTTP schemes
    assert validator.validate_url("javascript:alert(1)")[0] is False
    assert validator.validate_url("file:///etc/passwd")[0] is False
    assert validator.validate_url("ftp://ftp.example.com")[0] is False
    assert validator.validate_url("")[0] is False
    assert validator.validate_url(None)[0] is False

# ==============================================================================
# 2. DEDUPLICATION & HEADLINE SIMILARITY TESTS
# ==============================================================================

def test_headline_normalization_and_deduplication():
    """Verify that publisher suffixes and stopwords are stripped, and identical stories detected"""
    validator = ValidationService()
    
    t1 = "US Election 2026: Polls open across key battleground states - BBC News"
    t2 = "US Election 2026: Polls Open Across Key Battleground States - The Guardian"
    t3 = "Stocks tumble as inflation fears grip Wall Street - CNBC"
    
    tok1, norm1 = validator.normalize_headline(t1)
    tok2, norm2 = validator.normalize_headline(t2)
    tok3, norm3 = validator.normalize_headline(t3)
    
    assert norm1 == norm2
    sim_1_2 = validator.calculate_headline_similarity(tok1, tok2)
    sim_1_3 = validator.calculate_headline_similarity(tok1, tok3)
    
    assert sim_1_2 >= 0.95
    assert sim_1_3 < 0.20
    
    # Test deduplicate_articles
    articles = [
        {
            'title': t1,
            'link': 'https://www.bbc.com/news/1',
            'canonical_url': 'https://www.bbc.com/news/1',
            'normalized_tokens': tok1,
            'normalized_headline': norm1,
            'source': 'BBC News',
            'published_dt': datetime.now() - timedelta(minutes=10)
        },
        {
            'title': t2,
            'link': 'https://news.google.com/articles/2',
            'canonical_url': 'https://news.google.com/articles/2',
            'normalized_tokens': tok2,
            'normalized_headline': norm2,
            'source': 'Google News',
            'published_dt': datetime.now() - timedelta(minutes=5)
        },
        {
            'title': t3,
            'link': 'https://www.cnbc.com/market/3',
            'canonical_url': 'https://www.cnbc.com/market/3',
            'normalized_tokens': tok3,
            'normalized_headline': norm3,
            'source': 'CNBC',
            'published_dt': datetime.now() - timedelta(minutes=30)
        }
    ]
    
    deduped = validator.deduplicate_articles(articles)
    # The duplicate story should be merged
    assert len(deduped) == 2
    # Verify primary BBC article preserved alternative source reference
    bbc_article = next(a for a in deduped if 'Election' in a['title'])
    assert bbc_article['source'] == 'BBC News'
    assert len(bbc_article.get('alternative_sources', [])) >= 1
    assert bbc_article['alternative_sources'][0]['source'] == 'Google News'

# ==============================================================================
# 3. DATE INTEGRITY & STALENESS FLAGGING TESTS
# ==============================================================================

def test_date_preservation_and_staleness():
    """Verify that original publication dates are preserved and stale stories (>48h) flagged"""
    validator = ValidationService()
    
    # 1. Fresh article (15m old)
    fresh_date = datetime.now() - timedelta(minutes=15)
    is_outdated, label = validator.check_staleness(fresh_date)
    assert is_outdated is False
    assert label is None
    
    # 2. Stale article (3 days old)
    stale_date = datetime.now() - timedelta(days=3, hours=4)
    is_outdated, label = validator.check_staleness(stale_date)
    assert is_outdated is True
    assert "3d ago" in label or "Published" in label
    
    # 3. Archived article (10 days old)
    archived_date = datetime.now() - timedelta(days=10)
    is_outdated, label = validator.check_staleness(archived_date)
    assert is_outdated is True
    assert "Archived" in label
    
    # 4. Missing date must return None, not fake current time
    fake_entry = {'title': 'Undated article'}
    dt, rel_str, is_verified = validator.parse_publication_date(fake_entry)
    assert dt is None
    assert is_verified is False
    assert rel_str == "Publication date unverified"

# ==============================================================================
# 4. CLAIM VERIFICATION & BREAKING NEWS RIGOR TESTS
# ==============================================================================

def test_claim_verification_and_unverified_flagging():
    """Ensure speculative claims are flagged and never marked verified breaking news"""
    validator = ValidationService()
    categorizer = CategoryService()
    
    # Speculative article
    speculative_title = "Unconfirmed reports claim foreign minister resigned amid controversy"
    is_unverified, label = validator.evaluate_claim_verification(speculative_title, "")
    assert is_unverified is True
    assert label == "Developing / Unverified Claim"
    
    # An unverified claim must NOT be categorized as Breaking News
    article = {
        'title': speculative_title,
        'description': 'Sources allege the minister stepped down.',
        'published_dt': datetime.now() - timedelta(minutes=10),
        'is_unverified': True,
        'source': 'Google News'
    }
    cat = categorizer.classify_article(article)
    assert cat != 'Breaking News'

def test_breaking_news_contextual_guardrails():
    """Ensure sports, entertainment, and stale events are never classified as Breaking News"""
    categorizer = CategoryService()
    
    # 1. Movie shooting should be Sports & Culture, NOT Breaking News
    movie_article = {
        'title': 'Director begins shooting new sci-fi film in London with star actor',
        'description': 'Production started on the upcoming Hollywood cinema release.',
        'published_dt': datetime.now() - timedelta(hours=1),
        'source': 'BBC News'
    }
    assert categorizer.classify_article(movie_article) == 'Sports & Culture'
    
    # 2. Baseball strike should be Sports & Culture
    sports_article = {
        'title': 'Baseball players union debates potential strike over league contract',
        'description': 'Championship tournament dates could be affected.',
        'published_dt': datetime.now() - timedelta(hours=2),
        'source': 'CNN'
    }
    assert categorizer.classify_article(sports_article) == 'Sports & Culture'
    
    # 3. An earthquake from 2 days ago must NOT be Breaking News
    old_earthquake = {
        'title': 'Major earthquake struck regional coast as recovery operations continue',
        'description': 'Rescue teams work through debris after the disaster.',
        'published_dt': datetime.now() - timedelta(days=2),  # 48 hours old
        'source': 'The Guardian'
    }
    assert categorizer.classify_article(old_earthquake) != 'Breaking News'
    
    # 4. Genuine verified breaking news (< 6h with explicit marker)
    genuine_breaking = {
        'title': 'BREAKING: State of emergency declared following catastrophic coastal explosion',
        'description': 'Evacuation orders issued immediately for residents.',
        'published_dt': datetime.now() - timedelta(minutes=20),
        'is_unverified': False,
        'source': 'BBC News'
    }
    assert categorizer.classify_article(genuine_breaking) == 'Breaking News'

# ==============================================================================
# 5. CATEGORY CLASSIFICATION ACCURACY TESTS
# ==============================================================================

def test_accurate_category_scoring():
    """Verify accurate topic classification without isolated keyword bleed"""
    categorizer = CategoryService()
    
    # Tech with compound context
    tech_article = {
        'title': 'Nvidia reveals new semiconductor microchip architecture for generative AI models',
        'description': 'The tech company announced breakthroughs in neural network computing.',
        'source': 'TechCrunch'
    }
    assert categorizer.classify_article(tech_article) == 'Technology'
    
    # Business earnings
    biz_article = {
        'title': 'Federal Reserve signals interest rate decision as Wall Street stocks rally',
        'description': 'Investors welcomed inflation trends and treasury yield reports.',
        'source': 'CNBC'
    }
    assert categorizer.classify_article(biz_article) == 'Business'
    
    # Science & Health
    health_article = {
        'title': 'Clinical trial demonstrates breakthrough in medical cancer treatment research',
        'description': 'Researchers find genetic markers aiding hospital therapy programs.',
        'source': 'NPR News'
    }
    assert categorizer.classify_article(health_article) == 'Science & Health'

def test_cross_source_category_accuracy():
    """Verify that specific topics override publisher defaults (e.g. measles on Ars Technica -> Science & Health, growth forecast on BBC -> Business)"""
    categorizer = CategoryService()
    
    # Ars Technica measles story should classify as Science & Health, NOT Technology
    ars_measles = {
        'title': 'Measles outbreak spreads across three states as vaccination rates fall',
        'description': 'Public health officials and hospital doctors urge parents to get children vaccinated.',
        'source': 'Ars Technica'
    }
    assert categorizer.classify_article(ars_measles) == 'Science & Health'
    
    # BBC growth forecast story should classify as Business, NOT World
    bbc_growth = {
        'title': 'IMF cuts global growth forecast as energy prices and inflation squeeze households',
        'description': 'Central banks navigate interest rates and economic headwinds.',
        'source': 'BBC News'
    }
    assert categorizer.classify_article(bbc_growth) == 'Business'
    
    # TechCrunch generic startup article should retain Technology
    tc_generic = {
        'title': 'Demo Day highlights latest batch of startup founders in Silicon Valley',
        'description': 'Founders pitch their developer api and cloud computing tools.',
        'source': 'TechCrunch'
    }
    assert categorizer.classify_article(tc_generic) == 'Technology'

# ==============================================================================
# 6. FLASK ROUTE & API VERIFICATION TESTS
# ==============================================================================

def test_home_page_elements(client):
    """Test Home page renders with verification indicators"""
    response = client.get('/')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert 'NewsHub' in html
    assert 'ticker-bar' in html
    assert 'live-search-input' in html

def test_about_page_verification_sections(client):
    """Test About page renders validation, deduplication, and trust tier documentation"""
    response = client.get('/about')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert 'Verification &amp; Validation Pipeline' in html or 'Verification & Validation Pipeline' in html or 'Validation Pipeline' in html
    assert 'Deduplication' in html
    assert 'Source Reliability &amp; Trust Tiers' in html or 'Trust Tiers' in html
    assert 'Limitations' in html

def test_api_stats_verification_metrics(client):
    """Test /api/stats includes verification metrics"""
    response = client.get('/api/stats')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    metrics = data['stats']['verification_metrics']
    assert 'verified_reports' in metrics
    assert 'developing_claims' in metrics
    assert 'outdated_articles' in metrics

def test_api_articles_filtering(client):
    """Test /api/articles JSON serialization and filtering"""
    response = client.get('/api/articles?limit=5')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert len(data['articles']) <= 5
    for a in data['articles']:
        assert 'title' in a
        assert 'canonical_url' in a
        assert 'published_relative' in a
        assert 'fetched_at' in a
