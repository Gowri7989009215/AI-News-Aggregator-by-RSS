"""
RSS News Aggregator Flask Application
A professional news aggregation platform with real-time RSS feed processing
"""

from flask import Flask, render_template, jsonify, request
import os
import logging
from datetime import datetime
from services.rss_service import RSSService
from services.category_service import CategoryService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure app
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['DEBUG'] = True

# Initialize services
rss_service = RSSService(cache_duration_minutes=5)
category_service = CategoryService()

@app.route('/')
def index():
    """Main page - display all news articles"""
    try:
        # Get all articles from RSS feeds
        all_articles = rss_service.get_all_articles()
        
        # Categorize articles
        categorized_articles = category_service.categorize_articles(all_articles)
        
        # Get available categories
        categories = category_service.get_available_categories(all_articles)
        
        # Get trending articles
        trending_articles = category_service.get_trending_articles(all_articles, limit=5)
        
        # Get articles by source
        articles_by_source = rss_service.get_articles_by_source()
        
        # Get cache info
        cache_info = rss_service.get_cache_info()
        
        return render_template(
            'index.html',
            categorized_articles=categorized_articles,
            all_articles=all_articles,
            categories=categories,
            trending_articles=trending_articles,
            articles_by_source=articles_by_source,
            cache_info=cache_info,
            current_time=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error loading main page: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/category/<category_name>')
def filter_by_category(category_name):
    """Filter articles by category"""
    try:
        # Get all articles
        all_articles = rss_service.get_all_articles()
        
        # Filter by category
        filtered_articles = category_service.filter_by_category(all_articles, category_name)
        
        # Get available categories
        categories = category_service.get_available_categories(all_articles)
        
        return render_template(
            'index.html',
            categorized_articles={category_name: filtered_articles},
            all_articles=filtered_articles,
            categories=categories,
            selected_category=category_name,
            articles_by_source=rss_service.get_articles_by_source(),  # Add this
            cache_info=rss_service.get_cache_info(),  # Add this
            trending_articles=category_service.get_trending_articles(filtered_articles, 5),  # Add this
            current_time=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error filtering by category {category_name}: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/source/<source_name>')
def filter_by_source(source_name):
    """Filter articles by source"""
    try:
        # Get articles by source
        articles_by_source = rss_service.get_articles_by_source()
        
        # Get articles for the specified source
        source_articles = articles_by_source.get(source_name, [])
        
        # Categorize the source articles
        categorized_articles = category_service.categorize_articles(source_articles)
        
        # Get available categories
        categories = category_service.get_available_categories(source_articles)
        
        return render_template(
            'index.html',
            categorized_articles=categorized_articles,
            all_articles=source_articles,
            categories=categories,
            selected_source=source_name,
            articles_by_source=articles_by_source,
            cache_info=rss_service.get_cache_info(),  # Add this
            trending_articles=category_service.get_trending_articles(source_articles, 5),  # Add this
            current_time=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error filtering by source {source_name}: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/api/refresh')
def refresh_feeds():
    """Refresh RSS feeds (clear cache and reload)"""
    try:
        # Clear cache
        rss_service.clear_cache()
        
        # Get fresh articles
        all_articles = rss_service.get_all_articles()
        
        # Categorize articles
        categorized_articles = category_service.categorize_articles(all_articles)
        
        # Get trending articles
        trending_articles = category_service.get_trending_articles(all_articles, limit=5)
        
        # Get articles by source
        articles_by_source = rss_service.get_articles_by_source()
        
        # Get cache info
        cache_info = rss_service.get_cache_info()
        
        return jsonify({
            'success': True,
            'message': 'Feeds refreshed successfully',
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
    """API endpoint to get articles with optional filtering"""
    try:
        # Get query parameters
        category = request.args.get('category', 'all')
        source = request.args.get('source', 'all')
        limit = int(request.args.get('limit', 50))
        
        # Get all articles
        all_articles = rss_service.get_all_articles()
        
        # Apply filters
        filtered_articles = all_articles
        
        if category != 'all':
            filtered_articles = category_service.filter_by_category(filtered_articles, category)
        
        if source != 'all':
            filtered_articles = [article for article in filtered_articles if article.get('source') == source]
        
        # Limit results
        filtered_articles = filtered_articles[:limit]
        
        return jsonify({
            'success': True,
            'articles': filtered_articles,
            'total': len(filtered_articles),
            'filters': {
                'category': category,
                'source': source,
                'limit': limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error in API endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats')
def get_stats():
    """API endpoint to get statistics"""
    try:
        # Get all articles
        all_articles = rss_service.get_all_articles()
        
        # Get category stats
        category_stats = category_service.get_category_stats(all_articles)
        
        # Get source stats
        articles_by_source = rss_service.get_articles_by_source()
        source_stats = {source: len(articles) for source, articles in articles_by_source.items()}
        
        # Get cache info
        cache_info = rss_service.get_cache_info()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_articles': len(all_articles),
                'category_distribution': category_stats,
                'source_distribution': source_stats,
                'cache_info': cache_info,
                'last_updated': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('error.html', error='Internal server error'), 500

@app.context_processor
def inject_globals():
    """Inject global variables into templates"""
    return {
        'app_name': 'NewsHub',
        'current_year': datetime.now().year
    }

if __name__ == '__main__':
    # Create required directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Run the Flask application
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )
