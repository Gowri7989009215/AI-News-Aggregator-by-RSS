# NewsHub RSS Aggregator 📰⚡

> A modern, production-grade news aggregation platform combining official publisher RSS feeds, ethical web scraping, automated topic classification, and instant Light/Dark mode theming.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Feedparser](https://img.shields.io/badge/Feedparser-6.0.10-orange?style=flat)](https://feedparser.readthedocs.io)
[![BeautifulSoup4](https://img.shields.io/badge/BeautifulSoup-4.12.2-green?style=flat)](https://www.crummy.com/software/BeautifulSoup/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.2-7952B3?style=flat&logo=bootstrap&logoColor=white)](https://getbootstrap.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📑 Table of Contents
1. [Overview & Philosophy](#-overview--philosophy)
2. [Key Features](#-key-features)
3. [Architecture Overview](#-architecture-overview)
4. [Technology Stack](#-technology-stack)
5. [Verified RSS Sources Directory](#-verified-rss-sources-directory)
6. [Legal & Ethical Web Scraping Workflow](#-legal--ethical-web-scraping-workflow)
7. [End-to-End Data Flow](#-end-to-end-data-flow)
8. [Installation & Setup](#-installation--setup)
9. [Configuration & Customization](#-configuration--customization)
10. [REST API Documentation](#-rest-api-documentation)
11. [Production Deployment](#-production-deployment)
12. [Troubleshooting & FAQ](#-troubleshooting--faq)

---

## 🌟 Overview & Philosophy

Modern news consumption is broken: algorithmic echo chambers prioritize outrage, intrusive advertising clutters articles, tracking scripts compromise privacy, and proprietary feed readers impose paywalls.

**NewsHub** returns news consumption to open standards:
- **Open Standards First**: Built directly on public RSS 2.0 and Atom syndication feeds.
- **Ethical & Legal Intelligence**: Uses gentle, polite OpenGraph web scraping for thumbnails and article excerpts without bypassing paywalls or republishing full copyrighted bodies.
- **Zero Tracking**: No tracking cookies, no surveillance beacons, and no persistent databases required.
- **Pristine Reading Experience**: High-contrast typography, interactive Light and Dark modes, instant client-side search, and offline article bookmarking.

The website is structured into two clean pages:
1. **Home / News Feed (`/`)**: Real-time breaking marquee, hero feature story, trending pulse ranking, live search, category pills, source dropdown, and an interactive article grid.
2. **About NewsHub (`/about`)**: Complete architectural breakdown, 6-step ingestion data pipeline, legal scraping principles, feed directory, and developer API references.

---

## 🚀 Key Features

### 🎨 Modern Design & UI/UX
- **Full Light and Dark Modes**: Tailored CSS custom properties (`data-theme="light"` / `data-theme="dark"`) with zero-flash persistence via `localStorage` and system preference detection.
- **Editorial Typography**: Pairing modern sans-serifs (*Plus Jakarta Sans*, *Inter*) with high-contrast serif headlines for a premium magazine feel.
- **Breaking News Marquee**: Smooth, GPU-accelerated horizontal ticker featuring active breaking alerts that pauses on hover.
- **Responsive Layout**: Fluid breakpoints optimized for mobile phones (375px+), tablets, and ultra-wide desktops.
- **Visual Fallbacks**: When feeds omit thumbnails, branded geometric gradients with publisher logos and category icons ensure cards never look broken.

### ⚡ Intelligence & Navigation
- **Concurrent Ingestion**: Multi-threaded feed processor (`ThreadPoolExecutor`) querying 10 news sources concurrently in under 3 seconds.
- **Smart Heuristic Categorization**: Algorithmic classifier categorizes articles into *Breaking News*, *World*, *Business*, *Technology*, *Science & Health*, *Politics*, and *Sports & Culture*.
- **Trending Pulse Algorithm**: Velocity and recency weighting highlights the most important stories across varied publishers.
- **Instant Client-Side Search**: Debounced live search across titles, summaries, and source tags without round-trip latency.
- **Saved Bookmarks**: Offline article saving stored locally in `localStorage` with a dedicated review drawer.
- **Quick Article Preview**: Ethical scraper extracts OpenGraph images, author attribution, reading time, and lead text in a reader popup.

---

## 🏛️ Architecture Overview

NewsHub uses a modular, decoupled service-oriented architecture:

```
+-------------------------------------------------------------------------+
|                              PRESENTATION LAYER                         |
|   templates/index.html (News Portal)      templates/about.html (About)  |
|   templates/base.html (Theme/Nav/Modal)   templates/error.html (Errors) |
|   static/css/style.css (CSS Variables)    static/js/main.js (Client Engine) |
+-------------------------------------------------------------------------+
                                     │
                                     ▼
+-------------------------------------------------------------------------+
|                              FLASK APP (app.py)                         |
|   Routes:  /   /about   /category/<name>   /source/<name>               |
|   REST APIs:  /api/articles   /api/refresh   /api/stats   /api/preview  |
+-------------------------------------------------------------------------+
        │                                  │                     │
        ▼                                  ▼                     ▼
+---------------------+          +-------------------+  +-----------------+
|   RSSService        |          | CategoryService   |  | ScraperService  |
| - 10 RSS Sources    |          | - Weighted Rules  |  | - OpenGraph     |
| - ThreadPool (8-way)|          | - Topic Classifier|  | - Twitter Cards |
| - Image Extractor   |          | - Trending Velocity| | - Lead Text     |
| - Date Normalizer   |          | - Category Stats  |  | - Polite UA     |
+---------------------+          +-------------------+  +-----------------+
        │                                                        │
        └────────────────────────┬───────────────────────────────┘
                                 ▼
+-------------------------------------------------------------------------+
|                        IN-MEMORY CACHING LAYER                          |
|   Feed Cache: 5-minute TTL             Metadata Cache: 30-minute TTL    |
+-------------------------------------------------------------------------+
```

### Module Breakdown
- `app.py`: Application entry point, routing, error handlers, and context processors.
- `services/rss_service.py`: Multi-threaded fetcher, XML parsing, image extraction, and relative date calculation.
- `services/category_service.py`: Rule-based NLP classifier, trending score engine, and distribution metrics.
- `services/scraper_service.py`: Ethical web scraper using BeautifulSoup to extract OpenGraph metadata and lead paragraphs.
- `static/css/style.css`: Comprehensive design system with light and dark mode variables, animations, and responsive rules.
- `static/js/main.js`: Client-side logic for theme switching, bookmarks, instant search, preview modals, and auto-refresh.

---

## 💻 Technology Stack

| Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | Python / Flask | 3.11+ / 2.3.3 | Lightweight, fast WSGI web server and REST API |
| **RSS Engine** | feedparser | 6.0.10 | Universal feed parser for RSS 2.0, Atom, and RDF |
| **HTTP Client** | requests | 2.31.0 | Robust connection pooling, timeouts, and headers |
| **Web Scraping** | BeautifulSoup4 / lxml | 4.12.2 / 4.9.3 | HTML parsing, OpenGraph tag extraction, sanitization |
| **Frontend Framework** | Bootstrap (CSS/JS) | 5.3.2 | Grid system, modals, dropdowns, and base layout |
| **Icons** | Bootstrap Icons | 1.11.3 | High-fidelity vector glyphs |
| **Styling** | Vanilla CSS3 | Standard | CSS Custom Properties, Glassmorphism, Marquee animations |
| **Client Scripting** | Vanilla JavaScript | ES6+ | State management, LocalStorage, event handling |

---

## 📡 Verified RSS Sources Directory

NewsHub ingests 10 officially maintained, high-availability RSS endpoints:

| Source Name | Primary Topic | Official RSS Feed URL | Accent Color | Update Interval |
| :--- | :--- | :--- | :--- | :--- |
| **BBC News** | World | `http://feeds.bbci.co.uk/news/rss.xml` | `#bb1919` | 5 min |
| **CNN** | General | `http://rss.cnn.com/rss/edition.rss` | `#cc0000` | 5 min |
| **The Guardian** | World | `https://www.theguardian.com/world/rss` | `#052962` | 5 min |
| **Al Jazeera** | World | `https://www.aljazeera.com/xml/rss/all.xml` | `#fa6400` | 5 min |
| **NPR News** | Domestic / US | `https://feeds.npr.org/1001/rss.xml` | `#2b78c5` | 5 min |
| **TechCrunch** | Technology | `https://techcrunch.com/feed/` | `#00a562` | 5 min |
| **Ars Technica** | Technology | `https://feeds.arstechnica.com/arstechnica/index` | `#ff4e00` | 5 min |
| **CNBC** | Business | `https://www.cnbc.com/id/100003114/device/rss/rss.html` | `#005594` | 5 min |
| **DW News** | World | `https://rss.dw.com/rdf/rss-en-all` | `#002d62` | 5 min |
| **Google News** | General | `https://news.google.com/rss` | `#4285f4` | 5 min |

---

## 🛡️ Legal & Ethical Web Scraping Workflow

NewsHub adheres strictly to digital copyright law, Fair Use principles, and ethical scraping standards:

```
[User Clicks "Quick Preview"]
              │
              ▼
    Check Metadata Cache
    (Is URL in memory < 30m?)
     ├── YES ──► Return cached OpenGraph payload instantly
     └── NO  ──┐
               ▼
    Dispatch Polite HTTP GET Request
    - User-Agent: NewsHub-Aggregator/2.0 (+http://localhost:5000/about)
    - Timeout: 4 seconds
    - Size Limit: Stream stream chunks up to 256KB max (never downloads full body)
               │
               ▼
    Parse with BeautifulSoup4
    - Extract <meta property="og:image"> or twitter:image
    - Extract <meta property="og:description">
    - Extract <meta name="author">
    - Extract lead 1-2 sentences for excerpt reading
               │
               ▼
    Cache Result with Timestamp
               │
               ▼
    Render in Modal with Source Badge + Outbound Publisher Link
```

### Ethical Standards
1. **No Paywall Circumvention**: The scraper never bypasses subscription paywalls, CAPTCHAs, or authentication layers.
2. **Attribution & Outbound Links**: Every article prominently features the source publisher and includes an outbound link to read the original story.
3. **Bandwidth Economy**: Requests stream only the first 256KB of HTML to read `<head>` metadata, minimizing bandwidth usage on publisher servers.
4. **Transparent User-Agent**: Every request clearly declares the application name and contact URL for publisher transparency.
5. **No Full-Text Theft**: NewsHub never scrapes or duplicates full article bodies, adhering to Fair Use for snippets and headlines.

---

## 🔄 End-to-End Data Flow

```
1. USER REQUEST ───────► Flask Route (e.g. GET / or GET /category/Technology)
                                │
                                ▼
2. CACHE EVALUATION ───► RSSService._is_cache_valid()
                                ├─ Cache Valid (< 5m): Return in-memory articles
                                └─ Cache Expired: Trigger ThreadPoolExecutor
                                        │
                                        ▼
3. CONCURRENT FETCH ───► 8 Parallel Workers fetch 10 publisher endpoints
                                │
                                ▼
4. PARSE & SANITIZE ───► feedparser extracts raw entries; BeautifulSoup cleans HTML
                         _extract_image_from_entry() recovers media thumbnails
                                │
                                ▼
5. CLASSIFICATION ─────► CategoryService.classify_article() calculates weighted scores
                         get_trending_articles() ranks recency and headline velocity
                                │
                                ▼
6. RENDER & DELIVER ───► Jinja2 injects data into base.html & index.html
                         Client applies user theme, search filters, and bookmarks
```

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.11 or higher
- Git
- Modern web browser (Chrome, Firefox, Safari, Edge)

### 🪟 Windows Setup (PowerShell / Command Prompt)

```powershell
# 1. Clone repository and navigate to folder
cd d:\rss\news_aggregator

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
.\venv\Scripts\Activate.ps1
# Or in cmd.exe: venv\Scripts\activate.bat

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start the application
python app.py
```

### 🍎 macOS / 🐧 Linux Setup

```bash
# 1. Navigate to project directory
cd news_aggregator

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start the application
python app.py
```

Open your browser and navigate to **`http://localhost:5000`**.

---

## ⚙️ Configuration & Customization

### Adding a New RSS Source
Open `services/rss_service.py` and add an entry to `self.rss_sources`:

```python
'Bloomberg': {
    'url': 'https://feeds.bloomberg.com/markets/news.rss',
    'category': 'Business',
    'description': 'Global financial and business reporting',
    'color': '#101010',
    'badge': 'Bloomberg',
    'homepage': 'https://www.bloomberg.com'
}
```

### Adjusting Cache Duration
Open `services/rss_service.py` and modify `cache_duration_minutes`:

```python
# Change from 5 minutes to 10 minutes:
rss_service = RSSService(cache_duration_minutes=10)
```

### Adding New Categories or Keywords
Open `services/category_service.py` and edit `self.category_keywords`:

```python
'Cybersecurity': {
    'keywords': ['malware', 'ransomware', 'cyberattack', 'zero-day', 'hacker', 'phishing'],
    'priority': 2
}
```

### Customizing CSS Themes
Open `static/css/style.css` and modify root design tokens:

```css
:root {
    --brand-primary: #2563EB;   /* Primary accent */
    --brand-crimson: #E11D48;   /* Breaking news alert */
}

[data-theme="dark"] {
    --bg-page: #0B0F19;         /* Dark mode background */
}
```

---

## 📊 REST API Documentation

### 1. Get Articles
Retrieve aggregated articles with optional filtering and search:
```http
GET /api/articles?category=Technology&source=TechCrunch&q=AI&limit=10
```

**Query Parameters:**
| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `category` | string | `all` | Filter by topic (e.g., `Technology`, `World`, `Business`) |
| `source` | string | `all` | Filter by publisher (e.g., `BBC News`, `CNN`, `The Guardian`) |
| `q` | string | `""` | Search keyword matching title or summary |
| `limit` | integer | `50` | Maximum number of results to return |

**Sample Response:**
```json
{
  "success": true,
  "total": 1,
  "limit": 10,
  "articles": [
    {
      "title": "Anthropic announces new Claude capabilities",
      "link": "https://techcrunch.com/article...",
      "description": "Anthropic today revealed expanded AI capabilities...",
      "source": "TechCrunch",
      "category": "Technology",
      "image": "https://techcrunch.com/thumb.jpg",
      "published": "Oct 13, 2026 11:45",
      "published_relative": "15m ago",
      "reading_time": 3
    }
  ]
}
```

### 2. Refresh Feeds
Invalidate cache and trigger immediate background re-fetch:
```http
GET /api/refresh
```

**Sample Response:**
```json
{
  "success": true,
  "message": "Feeds and metadata refreshed successfully",
  "total_articles": 225,
  "categories": ["Breaking News", "World", "Business", "Technology", "Science & Health", "Politics", "Sports & Culture"],
  "trending_count": 6,
  "cache_info": {
    "cache_size": 10,
    "cache_duration_minutes": 5.0
  }
}
```

### 3. System Statistics
Retrieve real-time metrics on feeds, categories, and sources:
```http
GET /api/stats
```

**Sample Response:**
```json
{
  "success": true,
  "stats": {
    "total_articles": 225,
    "total_sources": 10,
    "category_distribution": {
      "World": 85,
      "Technology": 42,
      "Business": 38,
      "Breaking News": 8
    },
    "source_distribution": {
      "BBC News": 25,
      "CNN": 25,
      "TechCrunch": 20
    },
    "last_updated": "2026-10-13T12:35:00"
  }
}
```

### 4. Article Preview (Scraper)
Extract OpenGraph metadata and article lead text on-demand:
```http
GET /api/preview?url=https://www.bbc.com/news/articles/example
```

**Sample Response:**
```json
{
  "success": true,
  "metadata": {
    "domain": "www.bbc.com",
    "image": "https://ichef.bbci.co.uk/sample.jpg",
    "description": "Global economic indicators rise amid energy shifts...",
    "author": "BBC Economics Correspondent",
    "reading_time_minutes": 2,
    "lead_text": "World financial leaders gathered today to review the annual forecast..."
  }
}
```

---

## 🚀 Production Deployment

### Option 1: Gunicorn WSGI Server (Linux/macOS)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Option 2: Docker Container
Create a `Dockerfile` in the root:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run:
```bash
docker build -t newshub-aggregator .
docker run -d -p 5000:5000 --name newshub newshub-aggregator
```

### Option 3: Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name news.example.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## ❓ Troubleshooting & FAQ

### Q: Why do some articles show a branded icon instead of a photograph?
**A:** Several RSS feeds do not embed full `media:content` or `enclosure` image tags directly in their XML feeds. When an image is unavailable in the feed, NewsHub displays a high-contrast branded card with the publisher's color and category icon to maintain visual consistency. When a user clicks **Quick Preview**, the scraper dynamically retrieves the publisher's `og:image` tag.

### Q: Why was Reuters replaced?
**A:** Reuters deprecated its public RSS feeds (`feeds.reuters.com`) and now requires authenticated enterprise API tokens. To ensure high availability, NewsHub aggregates active, official RSS endpoints from **The Guardian**, **BBC**, **CNN**, **Al Jazeera**, **TechCrunch**, **Ars Technica**, **CNBC**, **NPR**, **DW News**, and **Google News**.

### Q: Port 5000 is already in use
**A:** In `app.py`, change line 268 to another port:
```python
app.run(host='0.0.0.0', port=5001, debug=True)
```

---

## 📜 License & Acknowledgements

- **NewsHub Core**: Distributed under the MIT License.
- **Content Rights**: All aggregated headlines, excerpts, and images remain the intellectual property of their respective publishers (BBC, CNN, The Guardian, Al Jazeera, NPR, TechCrunch, Ars Technica, CNBC, DW News, Google News).
- Built with Python, Flask, Feedparser, BeautifulSoup4, and modern CSS.
