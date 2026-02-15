# NewsHub RSS Aggregator 📰

A professional, production-ready RSS news aggregation web application built with Flask. Fetches real-time news from top sources like Reuters, BBC, and CNN with smart categorization and a beautiful modern UI.

## 🚀 Features

### Core Features
- **Multi-source Aggregation**: Fetches news from Reuters, BBC, and CNN RSS feeds
- **Smart Categorization**: Automatically categorizes articles into World, Business, Technology, Domestic, and Breaking News
- **Real-time Updates**: Live RSS feed fetching with configurable auto-refresh
- **No Database Required**: All data fetched dynamically from RSS feeds
- **In-memory Caching**: 5-minute cache to optimize performance
- **Responsive Design**: Beautiful mobile-friendly interface using Bootstrap 5

### Advanced Features
- **Parallel Feed Loading**: Uses ThreadPoolExecutor for concurrent RSS fetching
- **Trending Articles**: Smart algorithm to highlight trending news
- **Category Filtering**: Filter news by category with live counts
- **Source Filtering**: View news from specific sources
- **Auto-refresh**: Optional 10-minute auto-refresh functionality
- **Share Functionality**: Native share API with clipboard fallback
- **Statistics Dashboard**: Real-time statistics about news distribution
- **Professional UI**: Modern, clean interface with smooth animations

## 🛠️ Installation & Setup Guide

### Prerequisites
- Python 3.11 or higher
- Internet connection (for RSS feeds)
- Command line/terminal

### Step 1: Verify Python Installation
Open Command Prompt or PowerShell and check your Python version:
```bash
python --version
```
If you see Python 3.11+ installed, you're ready to proceed.

### Step 2: Create Virtual Environment
Creating a virtual environment is **highly recommended** to avoid conflicts with other Python packages.

#### On Windows (Command Prompt):
```bash
# Create virtual environment
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate
```

#### On Windows (PowerShell):
```bash
# Create virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate.ps1
```

#### On macOS/Linux:
```bash
# Create virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

**You'll know it's working when you see `(venv)` at the beginning of your command prompt.**

### Step 3: Install Dependencies
With the virtual environment activated, install all required packages:
```bash
pip install -r requirements.txt
```

This will install:
- Flask (web framework)
- feedparser (RSS parsing)
- requests (HTTP requests)
- beautifulsoup4 (HTML cleaning)
- And other required packages

### Step 4: Run the Application
Now you can start the application:
```bash
python app.py
```

### Step 5: Access the Application
Open your web browser and navigate to:
```
http://localhost:5000
```

You should see the NewsHub RSS Aggregator with the latest news from Reuters, BBC, and CNN!

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Issue 1: "ModuleNotFoundError: No module named 'flask'"
**Problem**: Flask is not installed or virtual environment is not activated.

**Solution**:
1. Make sure your virtual environment is activated (you should see `(venv)` in your prompt)
2. If not activated, run: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (macOS/Linux)
3. Install dependencies again: `pip install -r requirements.txt`

#### Issue 2: "python is not recognized" 
**Problem**: Python is not in your system PATH.

**Solution**:
1. Use `python3` instead of `python`: `python3 app.py`
2. Or install Python properly from python.org and ensure "Add to PATH" is checked during installation

#### Issue 3: RSS feeds not loading
**Problem**: Network connectivity issues or RSS feed URLs are down.

**Solution**:
1. Check your internet connection
2. Try refreshing the page manually
3. Wait a few minutes and try again (RSS feeds might be temporarily unavailable)

#### Issue 4: Port 5000 already in use
**Problem**: Another application is using port 5000.

**Solution**:
1. Stop the other application using port 5000
2. Or modify the port in `app.py`:
   ```python
   app.run(host='0.0.0.0', port=5001, debug=True)
   ```

#### Issue 5: PowerShell activation error
**Problem**: PowerShell execution policy prevents running activation script.

**Solution**:
```powershell
# Allow scripts for current session
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Then activate
.\venv\Scripts\Activate.ps1
```

### Quick Start Commands (Windows)

If you're having trouble, here are the exact commands to copy and paste:

```batch
# Step 1: Create virtual environment
python -m venv venv

# Step 2: Activate virtual environment
venv\Scripts\activate

# Step 3: Install dependencies
pip install -r requirements.txt

# Step 4: Run the application
python app.py
```

### Quick Start Commands (macOS/Linux)

```bash
# Step 1: Create virtual environment
python3 -m venv venv

# Step 2: Activate virtual environment
source venv/bin/activate

# Step 3: Install dependencies
pip install -r requirements.txt

# Step 4: Run the application
python app.py
```

## 🌐 Using the Application

### Main Features

#### Navigation
- **Home Button**: Return to main page with all news
- **Refresh Button**: Manually refresh RSS feeds
- **Auto-Refresh Toggle**: Enable/disable automatic updates every 10 minutes

#### Category Filtering
- Click on category buttons to filter news:
  - 🔴 **Breaking News**: Urgent and breaking stories
  - 🌍 **World**: International news
  - 💼 **Business**: Business and economy
  - 💻 **Technology**: Tech and innovation
  - 🏠 **Domestic**: National and local news

#### Source Filtering
- Click on source badges to view news from specific sources:
  - **Reuters** (orange badge)
  - **BBC** (blue badge) 
  - **CNN** (red badge)

#### Article Features
- **Read More**: Opens full article in new tab
- **Share Button**: Share article link
- **Publication Time**: Shows when article was published

#### Statistics
- Click "Statistics" in footer to see:
  - Total article count
  - Category distribution
  - Source distribution
  - Cache information

### Keyboard Shortcuts
- **Ctrl+R** (or **Cmd+R**): Refresh feeds
- **Esc**: Close modals
- **Click "Back to Top" button**: Scroll to top of page

## 📱 Mobile Usage

The application is fully responsive and works great on:
- 📱 Smartphones
- 📱 Tablets  
- 💻 Desktop computers

On mobile devices:
- Tap category buttons to filter
- Swipe to scroll through articles
- Tap menu button for navigation options

## 🔧 Advanced Configuration

### Adding New RSS Sources
Edit `services/rss_service.py` and add new sources:

```python
'New Source': {
    'url': 'https://example.com/rss.xml',
    'category': 'general'
}
```

### Changing Cache Duration
Edit `services/rss_service.py`:

```python
def __init__(self, cache_duration_minutes: int = 10):  # Change 10 to desired minutes
```

### Changing Auto-Refresh Interval
Edit `static/js/main.js`:

```javascript
autoRefreshInterval = setInterval(() => {
    refreshFeeds();
}, 900000); // 15 minutes in milliseconds
```

## 🚀 Production Deployment

### Using Gunicorn (Recommended)
```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 📊 API Endpoints

### Available Endpoints
- `GET /` - Main news page
- `GET /category/<category_name>` - Filter by category
- `GET /source/<source_name>` - Filter by source
- `GET /api/refresh` - Refresh RSS feeds
- `GET /api/articles` - Get articles with filtering
- `GET /api/stats` - Get statistics

### API Examples
```bash
# Get all Technology articles
curl "http://localhost:5000/api/articles?category=Technology"

# Get articles from BBC only
curl "http://localhost:5000/api/articles?source=BBC"

# Refresh feeds
curl http://localhost:5000/api/refresh
```

## 🎨 Customization

### Changing Colors
Edit `static/css/style.css` and modify CSS variables:

```css
:root {
    --primary-color: #0d6efd;    /* Change primary color */
    --success-color: #198754;    /* Change success color */
    /* etc. */
}
```

### Adding Categories
Edit `services/category_service.py` and add new categories:

```python
'New Category': {
    'keywords': ['keyword1', 'keyword2', 'keyword3'],
    'priority': 5
}
```

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-flask

# Run tests
pytest

# Run with coverage
pytest --cov=services
```

## 📞 Support

### Getting Help
1. Check this README first
2. Review the troubleshooting section above
3. Check the application logs for error messages
4. Verify your internet connection for RSS feeds

### Common Questions

**Q: Why do I see "No articles found"?**
A: This usually means RSS feeds couldn't be fetched. Check your internet connection and try refreshing.

**Q: How often does the app update news?**
A: By default, feeds are cached for 5 minutes. Auto-refresh (if enabled) updates every 10 minutes.

**Q: Can I add my own RSS sources?**
A: Yes! Edit the `rss_service.py` file to add new RSS feed URLs.

**Q: Is my data stored anywhere?**
A: No! The app doesn't use a database. All data is fetched live from RSS feeds and cached temporarily in memory.

---

## 🎉 Ready to Start!

1. Open your command prompt/terminal
2. Navigate to the `news_aggregator` folder
3. Follow the installation steps above
4. Run `python app.py`
5. Open `http://localhost:5000` in your browser

Enjoy your professional RSS News Aggregator! 🚀

**Built with ❤️ using Python, Flask, and modern web technologies**
