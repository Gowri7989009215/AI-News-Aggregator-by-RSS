"""
NewsHub RSS Aggregator - Flask Application
A professional, modern news aggregation platform combining official RSS feeds
and ethical web scraping with verified categorization, deduplication, and light/dark theme support.
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request

from services.rss_service import RSSService
from services.category_service import CategoryService
from services.scraper_service import ScraperService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'newshub-secure-production-key-2026')
app.config['DEBUG'] = True

# Initialize services
rss_service = RSSService(cache_duration_minutes=5)
category_service = CategoryService()
scraper_service = rss_service.scraper_service

@app.route('/')
def index():
    """Main Home page - display verified and deduplicated aggregated news"""
    try:
        all_articles = rss_service.get_all_articles()
        categorized_articles = category_service.categorize_articles(all_articles)
        categories = category_service.get_available_categories(all_articles)
        trending_articles = category_service.get_trending_articles(all_articles, limit=6)
        articles_by_source = rss_service.get_articles_by_source()
        cache_info = rss_service.get_cache_info()
        
        # Dedicated verified breaking news list for ticker
        breaking_candidates = categorized_articles.get('Breaking News', [])
        breaking_articles = [
            a for a in breaking_candidates
            if not a.get('is_unverified') and not a.get('is_outdated')
        ]
        
        ticker_is_breaking = len(breaking_articles) > 0
        if not breaking_articles:
            # Fallback to verified top trending stories (never fabricate breaking claims)
            breaking_articles = [a for a in trending_articles if not a.get('is_unverified')][:5]

        # Hero feature story
        hero_article = trending_articles[0] if trending_articles else (all_articles[0] if all_articles else None)
        sub_features = trending_articles[1:4] if len(trending_articles) > 1 else []

        return render_template(
            'index.html',
            categorized_articles=categorized_articles,
            all_articles=all_articles,
            categories=categories,
            trending_articles=trending_articles,
            breaking_articles=breaking_articles,
            ticker_is_breaking=ticker_is_breaking,
            hero_article=hero_article,
            sub_features=sub_features,
            articles_by_source=articles_by_source,
            cache_info=cache_info,
            sources_directory=rss_service.get_sources_directory(),
            current_time=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error loading main page: {str(e)}", exc_info=True)
        return render_template('error.html', error=str(e)), 500

@app.route('/about')
def about():
    """Dedicated About page explaining purpose, architecture, validation, ethics, and operation"""
    try:
        sources = rss_service.get_sources_directory()
        cache_info = rss_service.get_cache_info()
        all_articles = rss_service.get_all_articles()
        category_stats = category_service.get_category_stats(all_articles)
        
        return render_template(
            'about.html',
            sources=sources,
            cache_info=cache_info,
            total_articles=len(all_articles),
            category_stats=category_stats,
            current_time=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error loading about page: {str(e)}", exc_info=True)
        return render_template('error.html', error=str(e)), 500

@app.route('/category/<category_name>')
def filter_by_category(category_name):
    """Filter articles by category on the Home page"""
    try:
        all_articles = rss_service.get_all_articles()
        filtered_articles = category_service.filter_by_category(all_articles, category_name)
        categories = category_service.get_available_categories(all_articles)
        categorized = {category_name: filtered_articles}
        trending_articles = category_service.get_trending_articles(all_articles, limit=6)
        
        breaking_candidates = [a for a in all_articles if a.get('assigned_category') == 'Breaking News']
        breaking_articles = [
            a for a in breaking_candidates
            if not a.get('is_unverified') and not a.get('is_outdated')
        ][:5]
        
        ticker_is_breaking = len(breaking_articles) > 0
        if not breaking_articles:
            breaking_articles = [a for a in trending_articles if not a.get('is_unverified')][:5]

        return render_template(
            'index.html',
            categorized_articles=categorized,
            all_articles=filtered_articles,
            categories=categories,
            selected_category=category_name,
            trending_articles=trending_articles,
            breaking_articles=breaking_articles,
            ticker_is_breaking=ticker_is_breaking,
            hero_article=filtered_articles[0] if filtered_articles else None,
            sub_features=filtered_articles[1:4] if len(filtered_articles) > 1 else [],
            articles_by_source=rss_service.get_articles_by_source(),
            cache_info=rss_service.get_cache_info(),
            sources_directory=rss_service.get_sources_directory(),
            current_time=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error filtering by category {category_name}: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/source/<source_name>')
def filter_by_source(source_name):
    """Filter articles by source on the Home page"""
    try:
        articles_by_source = rss_service.get_articles_by_source()
        source_articles = articles_by_source.get(source_name, [])
        all_articles = rss_service.get_all_articles()
        
        categorized_articles = category_service.categorize_articles(source_articles)
        categories = category_service.get_available_categories(all_articles)
        trending_articles = category_service.get_trending_articles(source_articles, limit=6)
        
        breaking_candidates = [a for a in all_articles if a.get('assigned_category') == 'Breaking News']
        breaking_articles = [
            a for a in breaking_candidates
            if not a.get('is_unverified') and not a.get('is_outdated')
        ][:5]
        
        ticker_is_breaking = len(breaking_articles) > 0
        if not breaking_articles:
            breaking_articles = [a for a in trending_articles if not a.get('is_unverified')][:5]

        return render_template(
            'index.html',
            categorized_articles=categorized_articles,
            all_articles=source_articles,
            categories=categories,
            selected_source=source_name,
            trending_articles=trending_articles,
            breaking_articles=breaking_articles,
            ticker_is_breaking=ticker_is_breaking,
            hero_article=source_articles[0] if source_articles else None,
            sub_features=source_articles[1:4] if len(source_articles) > 1 else [],
            articles_by_source=articles_by_source,
            cache_info=rss_service.get_cache_info(),
            sources_directory=rss_service.get_sources_directory(),
            current_time=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error filtering by source {source_name}: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/api/refresh')
def refresh_feeds():
    """Refresh RSS feeds: clear cache and re-fetch fresh verified articles"""
    try:
        rss_service.clear_cache()
        all_articles = rss_service.get_all_articles()
        categorized_articles = category_service.categorize_articles(all_articles)
        trending_articles = category_service.get_trending_articles(all_articles, limit=6)
        cache_info = rss_service.get_cache_info()
        
        return jsonify({
            'success': True,
            'message': 'Feeds and metadata refreshed successfully',
            'total_articles': len(all_articles),
            'categories': list(categorized_articles.keys()),
            'trending_count': len(trending_articles),
            'cache_info': cache_info
        })
    except Exception as e:
        logger.error(f"Error refreshing feeds: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/articles')
def get_articles_api():
    """REST API endpoint to retrieve articles with optional filtering and search"""
    try:
        category = request.args.get('category', 'all')
        source = request.args.get('source', 'all')
        query = request.args.get('q', '').strip().lower()
        limit = int(request.args.get('limit', 50))
        
        all_articles = rss_service.get_all_articles()
        filtered = all_articles
        
        if category != 'all':
            filtered = category_service.filter_by_category(filtered, category)
        
        if source != 'all':
            filtered = [a for a in filtered if a.get('source', '').lower() == source.lower()]
            
        if query:
            filtered = [
                a for a in filtered
                if query in a.get('title', '').lower() or query in a.get('description', '').lower()
            ]
            
        total_matched = len(filtered)
        filtered = filtered[:limit]
        
        # Serialize datetime and set objects for clean JSON output
        serializable_articles = []
        for art in filtered:
            clean_art = dict(art)
            if 'published_dt' in clean_art:
                del clean_art['published_dt']
            if 'fetched_dt' in clean_art:
                clean_art['fetched_at'] = clean_art['fetched_dt'].isoformat()
                del clean_art['fetched_dt']
            if 'normalized_tokens' in clean_art:
                del clean_art['normalized_tokens']
            serializable_articles.append(clean_art)
            
        return jsonify({
            'success': True,
            'articles': serializable_articles,
            'total': total_matched,
            'limit': limit,
            'filters': {
                'category': category,
                'source': source,
                'q': query
            }
        })
    except Exception as e:
        logger.error(f"Error in articles API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """REST API endpoint to retrieve system aggregation and distribution statistics"""
    try:
        all_articles = rss_service.get_all_articles()
        category_stats = category_service.get_category_stats(all_articles)
        articles_by_source = rss_service.get_articles_by_source()
        source_stats = {source: len(articles) for source, articles in articles_by_source.items()}
        cache_info = rss_service.get_cache_info()
        
        # Verification breakdown
        unverified_count = sum(1 for a in all_articles if a.get('is_unverified'))
        outdated_count = sum(1 for a in all_articles if a.get('is_outdated'))
        multi_reported_count = sum(1 for a in all_articles if a.get('alternative_sources'))

        return jsonify({
            'success': True,
            'stats': {
                'total_articles': len(all_articles),
                'category_distribution': category_stats,
                'source_distribution': source_stats,
                'total_sources': len(source_stats),
                'verification_metrics': {
                    'verified_reports': len(all_articles) - unverified_count,
                    'developing_claims': unverified_count,
                    'outdated_articles': outdated_count,
                    'cross_reported_stories': multi_reported_count
                },
                'cache_info': cache_info,
                'last_updated': datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/preview')
def get_article_preview():
    """
    Ethical web scraping preview endpoint: extracts OpenGraph metadata,
    high-res lead image, and article snippet on demand.
    """
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({'success': False, 'error': 'Missing url parameter'}), 400
        
    try:
        metadata = scraper_service.extract_metadata(url)
        return jsonify({
            'success': True,
            'metadata': metadata
        })
    except Exception as e:
        logger.error(f"Error scraping preview for {url}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors"""
    return render_template('error.html', error='Page not found. The requested news item or page does not exist.'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors"""
    return render_template('error.html', error='Internal Server Error. Please refresh the page or try again in a moment.'), 500

@app.context_processor
def inject_globals():
    """Inject global variables into Jinja2 templates"""
    return {
        'app_name': 'NewsHub',
        'app_tagline': 'Real-Time News Intelligence & RSS Syndication',
        'current_year': datetime.now().year,
        'sources_count': len(rss_service.rss_sources)
    }

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )
