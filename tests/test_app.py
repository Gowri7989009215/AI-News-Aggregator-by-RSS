"""
Unit and Integration Tests for NewsHub RSS Aggregator
Tests routes, categorizer, scraper, and RSS service.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import json
from app import app
from services.category_service import CategoryService
from services.scraper_service import ScraperService

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    """Test that Home page loads with status 200 and required elements"""
    response = client.get('/')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert 'NewsHub' in html
    assert 'data-theme' in html
    assert 'live-search-input' in html

def test_about_page(client):
    """Test that dedicated About page renders with architecture and policy details"""
    response = client.get('/about')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert 'About' in html
    assert 'Ethical & Legal Web Scraping Policy' in html
    assert 'Directory of Feeds' in html
    assert 'How NewsHub Works Under the Hood' in html

def test_category_service_classification():
    """Test heuristic topic classification"""
    service = CategoryService()
    
    tech_article = {
        'title': 'OpenAI releases new GPT model with advanced reasoning capabilities',
        'description': 'The artificial intelligence company announced breakthrough technology in computing.',
        'category': ''
    }
    assert service.classify_article(tech_article) == 'Technology'
    
    biz_article = {
        'title': 'Wall Street stocks rise as Federal Reserve cuts interest rates',
        'description': 'Investors welcomed earnings and inflation forecasts across financial markets.',
        'category': ''
    }
    assert service.classify_article(biz_article) == 'Business'

def test_api_stats(client):
    """Test /api/stats endpoint"""
    response = client.get('/api/stats')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'stats' in data
    assert data['stats']['total_articles'] > 0
    assert data['stats']['total_sources'] == 10

def test_api_articles(client):
    """Test /api/articles with limit filter"""
    response = client.get('/api/articles?limit=5')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert len(data['articles']) <= 5

def test_scraper_service_cache():
    """Test scraper cache logic"""
    scraper = ScraperService(cache_duration_minutes=15)
    # Invalid or empty URL should return empty dict without crashing
    assert scraper.extract_metadata("") == {}
    assert scraper.extract_metadata("ftp://invalid") == {}
