# NewsHub RSS Aggregator 📰⚡

> A modern, production-grade news aggregation platform combining official publisher RSS feeds, ethical web scraping, automated topic classification, canonical URL deduplication, and verified data integrity with instant Light/Dark mode theming.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Feedparser](https://img.shields.io/badge/Feedparser-6.0.10-orange?style=flat)](https://feedparser.readthedocs.io)
[![BeautifulSoup4](https://img.shields.io/badge/BeautifulSoup-4.12.2-green?style=flat)](https://www.crummy.com/software/BeautifulSoup/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.2-7952B3?style=flat&logo=bootstrap&logoColor=white)](https://getbootstrap.com)
[![Tests](https://img.shields.io/badge/Tests-11%20Passing-brightgreen?style=flat)](tests/test_app.py)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📑 Table of Contents
1. [Overview & Philosophy](#-overview--philosophy)
2. [Key Features](#-key-features)
3. [Architecture Overview](#-architecture-overview)
4. [Technology Stack](#-technology-stack)
5. [Verified RSS Sources & Trust Tiers](#-verified-rss-sources--trust-tiers)
6. [News Accuracy & Validation Pipeline](#-news-accuracy--validation-pipeline)
7. [Deduplication Logic & Multi-Factor Engine](#-deduplication-logic--multi-factor-engine)
8. [Legal & Ethical Web Scraping Workflow](#-legal--ethical-web-scraping-workflow)
9. [System Capabilities, Boundaries & Limitations](#-system-capabilities-boundaries--limitations)
10. [End-to-End Data Flow](#-end-to-end-data-flow)
11. [Installation & Setup](#-installation--setup)
12. [Configuration & Customization](#-configuration--customization)
13. [REST API Documentation](#-rest-api-documentation)
14. [Production Deployment](#-production-deployment)
15. [Troubleshooting & FAQ](#-troubleshooting--faq)

---

## 🌟 Overview & Philosophy

Modern news consumption is broken: algorithmic echo chambers prioritize outrage, syndicated wire reports duplicate identical headlines across feeds, unverified claims masquerade as breaking news, and intrusive trackers compromise privacy.

**NewsHub** returns news consumption to verified, open standards:
- **Accuracy & Reliability**: Links undergo strict syntactic audits; tracking parameters are stripped; canonical URLs resolve duplicate wire stories; authentic publication dates are preserved; and speculative assertions are flagged.
- **Editorial Integrity**: Breaking news is restricted to verified, recent reports (< 6 hours). Speculative claims and unconfirmed rumors are explicitly separated from confirmed news.
- **Zero Fabrication Policy**: The system never manufactures verification badges, never fakes missing timestamps as "Just now", and never fabricates claims.
- **Open Standards First**: Built directly on public RSS 2.0 and Atom syndication feeds from 10 world-class institutions.
- **Pristine Reading Experience**: High-contrast typography, interactive Light and Dark modes, instant client-side search, and offline article bookmarking.

The website is structured into two clean pages:
1. **Home / News Feed (`/`)**: Real-time marquee (displaying verified breaking alerts or top stories), hero feature story, trending pulse ranking, live search, category pills, source dropdown, and an interactive article grid.
2. **About NewsHub (`/about`)**: Complete architectural breakdown, verification pipeline, deduplication logic, trust tiers, legal scraping principles, feed directory, and system limitations.

---

## 🚀 Key Features

### 🛡️ Accuracy & Data Integrity
- **Canonical URL Normalization**: Strips tracking query parameters (`utm_*`, `at_*`, `ocid`, `ref`, `fbclid`, fragments) to establish clean canonical identifiers.
- **Headline Deduplication**: Removes publisher suffixes and calculates token Jaccard similarity (&ge; 0.72) to merge syndicated wire reports while citing alternative sources.
- **Publication Date Preservation**: Preserves original publisher timestamps, distinguishing between when an event was published versus when it was fetched, and flagging outdated stories (&gt; 48 hours).
- **Claim Disambiguation**: Scans headlines for speculative phrases (*"unconfirmed reports"*, *"claims without evidence"*, *"alleged"*) to display a *Developing / Unverified Claim* badge and prevent false breaking news categorization.
- **Source Trust Tiers**: Prioritizes Tier 1 primary news publishers over Tier 2 aggregators and extracts underlying publishers from aggregated feeds.

### 🎨 Modern Design & UI/UX
- **Full Light and Dark Modes**: Tailored CSS custom properties (`data-theme="light"` / `data-theme="dark"`) with zero-flash persistence via `localStorage` and system preference detection.
- **Editorial Typography**: Pairing modern sans-serifs (*Plus Jakarta Sans*, *Inter*) with high-contrast serif headlines for a premium magazine feel.
- **Marquee Ticker**: GPU-accelerated horizontal ticker distinguishing verified *BREAKING* news from *TOP STORIES*.
- **Responsive Layout**: Fluid breakpoints optimized for mobile phones (375px+), tablets, and ultra-wide desktops.
- **Visual Fallbacks**: When feeds omit thumbnails, branded geometric cards with publisher branding colors and category icons display cleanly.

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
| - 10 RSS Sources    |          | - Context Rules   |  | - OpenGraph     |
| - ThreadPool (8-way)|          | - Breaking Guards |  | - Twitter Cards |
| - Image Extractor   |          | - Negative Filters|  | - Lead Text     |
| - Date Normalizer   |          | - Trending Score  |  | - Polite UA     |
+---------------------+          +-------------------+  +-----------------+
        │                                                        │
        ├────────────────────────┐                               │
        ▼                        ▼                               ▼
+---------------------+  +------------------------------------------------+
| ValidationService   |  |            IN-MEMORY CACHING LAYER             |
| - URL Normalization |  |   Feed Cache: 5-minute TTL                     |
| - Deduplication     |  |   Metadata Cache: 30-minute TTL                |
| - Claim Detection   |  +------------------------------------------------+
| - Staleness Checks  |
+---------------------+
```

### Module Breakdown
- `app.py`: Application entry point, routing, error handlers, and context processors.
- `services/validation_service.py`: URL sanitization, canonical normalization, headline tokenization, deduplication, claim evaluation, and date integrity checks.
- `services/rss_service.py`: Multi-threaded fetcher, XML parsing, image extraction, relative date formatting, and source health diagnostics.
- `services/category_service.py`: Rule-based NLP classifier with negative keyword guards, recency checks, and trending velocity ranking.
- `services/scraper_service.py`: Ethical web scraper extracting OpenGraph metadata, lead paragraphs, and author attribution.
- `static/css/style.css`: Comprehensive design system with light and dark mode variables, animations, and responsive rules.
- `static/js/main.js`: Client-side logic for theme switching, bookmarks, instant search, preview modals, and auto-refresh.

---

## 💻 Technology Stack

| Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | Python / Flask | 3.11+ / 2.3.3 | Lightweight WSGI web server and REST API |
| **RSS Engine** | feedparser | 6.0.10 | Universal feed parser for RSS 2.0, Atom, and RDF |
| **HTTP Client** | requests | 2.31.0 | Robust connection pooling, timeouts, and headers |
| **Date Processing** | python-dateutil | 2.8.2 | Parsing heterogeneous ISO/RFC-822 timestamps |
| **Web Scraping** | BeautifulSoup4 / lxml | 4.12.2 / 4.9.3 | HTML parsing, OpenGraph tag extraction, sanitization |
| **Frontend Framework** | Bootstrap (CSS/JS) | 5.3.2 | Grid system, modals, dropdowns, and base layout |
| **Icons** | Bootstrap Icons | 1.11.3 | High-fidelity vector glyphs |
| **Styling** | Vanilla CSS3 | Standard | CSS Custom Properties, Glassmorphism, Marquee animations |
| **Client Scripting** | Vanilla JavaScript | ES6+ | State management, LocalStorage, event handling |

---

## 📡 Verified RSS Sources & Trust Tiers

NewsHub establishes a transparent reliability hierarchy:

| Source Name | Trust Tier | Editorial Classification | Official RSS Feed URL | Accent Color |
| :--- | :--- | :--- | :--- | :--- |
| **BBC News** | Tier 1 | Public Broadcaster (Statutory Impartiality) | `http://feeds.bbci.co.uk/news/rss.xml` | `#bb1919` |
| **CNN** | Tier 1 | International News Network | `http://rss.cnn.com/rss/edition.rss` | `#cc0000` |
| **The Guardian** | Tier 1 | Independent Global Journalism | `https://www.theguardian.com/world/rss` | `#052962` |
| **Al Jazeera** | Tier 1 | Global News Network | `https://www.aljazeera.com/xml/rss/all.xml` | `#fa6400` |
| **NPR News** | Tier 1 | Public National Broadcaster | `https://feeds.npr.org/1001/rss.xml` | `#2b78c5` |
| **TechCrunch** | Tier 1 | Specialized Tech & Venture Journalism | `https://techcrunch.com/feed/` | `#00a562` |
| **Ars Technica** | Tier 1 | Deep-dive Technology & Science | `https://feeds.arstechnica.com/arstechnica/index` | `#ff4e00` |
| **CNBC** | Tier 1 | Financial Markets & Economic Media | `https://www.cnbc.com/id/100003114/device/rss/rss.html` | `#005594` |
| **DW News** | Tier 1 | Public International Broadcaster | `https://rss.dw.com/rdf/rss-en-all` | `#002d62` |
| **Google News** | Tier 2 | Algorithmic News Aggregator | `https://news.google.com/rss` | `#4285f4` |

*Note on Tier 2 Aggregators: For Google News entries, NewsHub dynamically extracts the underlying original publisher from title suffixes (e.g. `Headline - The Guardian` -> credited to The Guardian).*

---

## 🛡️ News Accuracy & Validation Pipeline

Every ingested news item undergoes four validation checks:

```
Raw RSS Entry
      │
      ▼
1. LINK AUDIT & CANONICALIZATION
   - Validates http/https protocol and hostname structure
   - Strips tracking query parameters (utm_*, at_*, ocid, ref, fbclid)
   - Discards fragment hashes (#...)
      │
      ▼
2. DATE INTEGRITY & STALENESS
   - Extracts authentic published_parsed or ISO pubDate
   - Records true published_dt vs local fetched_dt
   - Flags articles > 48 hours old as "Published X days ago"
   - Never fabricates missing timestamps as "Just now"
      │
      ▼
3. SPECULATIVE CLAIM DETECTION
   - Scans text for unverified markers ("unconfirmed reports", "alleged", "sources claim")
   - Applies "Developing / Unverified Claim" badge
      │
      ▼
4. BREAKING NEWS QUALIFICATION GUARDS
   - Requires explicit publisher marker (BREAKING:, ALERT:, JUST IN:) OR emergency disaster context
   - Requires recency: published_dt <= 6 hours old
   - Requires zero unverified claim flags
   - Outdated, speculative, sports, and entertainment stories are strictly blocked
```

---

## 🧩 Deduplication Logic & Multi-Factor Engine

When major news breaks, multiple outlets syndicate the same wire story. NewsHub deduplicates repetitive articles while preserving cross-outlet coverage:

### 1. Canonical URL Collisions
If two entries point to the same canonical URL after tracking parameters are stripped, they are merged immediately.

### 2. Headline Normalization
- Removes publisher attribution suffixes (e.g., `- BBC News`, `| Reuters`, `- CNN`).
- Converts characters to lowercase and strips non-alphanumeric punctuation.
- Filters out common English stopwords (`the`, `a`, `is`, `on`, `with`, etc.).

### 3. Jaccard Token Similarity
For headlines $A$ and $B$, the similarity coefficient is calculated:
$$J(A, B) = \frac{|A \cap B|}{|A \cup B|}$$

- **Threshold**: When $J(A, B) \ge 0.72$ with at least 3 shared tokens, the articles are identified as duplicate reports of the same event.
- **Priority Resolution**: Tier 1 direct publishers (e.g. BBC, The Guardian) take precedence over Tier 2 aggregators (Google News).
- **Cross-Source Attribution**: Duplicate stories are merged into the primary card with an *"Also reported by: [Source 2]"* badge, providing transparency without clutter.

---

## 📜 Legal & Ethical Web Scraping Workflow

NewsHub complies with copyright law, robots.txt directives, and Fair Use standards:

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
    - Size Cap: Stream chunks up to 256KB max (never downloads entire page)
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

## ⚖️ System Capabilities, Boundaries & Limitations

### What NewsHub DOES Verify
- **Feed Origin Authenticity**: Validates that feeds originate from official, publisher-owned endpoints.
- **Link Health & Security**: Audits link syntax and normalizes canonical links, discarding malicious protocols.
- **Deduplication Integrity**: Detects and merges cross-syndicated articles to prevent repetitive feeds.
- **Timestamp Accuracy**: Preserves authentic publication dates, identifying stale stories older than 48 hours.
- **Speculative Language Detection**: Flags headlines containing unverified assertions or rumors.

### What NewsHub CANNOT Verify (Limitations)
- **Primary Investigative Truth**: Automated software cannot conduct on-the-ground investigative reporting. We rely on the established editorial standards of Tier 1 publishers.
- **Real-World Retractions**: If a publisher updates an article after publication without updating their RSS feed, there may be a cache delay of up to 5 minutes before changes reflect.
- **Paywalled Article Full-Text**: In adherence with copyright law, NewsHub never scrapes full text behind subscription paywalls.
- **Zero Fabrication Policy**: NewsHub will never fabricate news or label an unverified claim as confirmed without direct evidence from trusted primary feeds.

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
4. VALIDATION PIPELINE ─► ValidationService:
                         - Validates & canonicalizes URLs
                         - Preserves authentic published dates; flags staleness (> 48h)
                         - Evaluates speculative assertions & unverified claims
                         - Normalizes headlines & extracts original publisher
                                │
                                ▼
5. DEDUPLICATION ──────► Deduplicates via canonical URLs & Jaccard token overlap
                         Merges alternative sources and elevates Tier 1 publishers
                                │
                                ▼
6. CLASSIFICATION ─────► CategoryService:
                         - Applies contextual phrase matching & negative rules
                         - Enforces breaking news qualification guards (< 6h)
                         - Ranks trending pulse velocity
                                │
                                ▼
7. RENDER & DELIVER ───► Jinja2 injects data into base.html & index.html
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
# 1. Navigate to project directory
cd d:\rss\news_aggregator

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
.\venv\Scripts\Activate.ps1
# Or in cmd.exe: venv\Scripts\activate.bat

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run tests to verify setup
pytest -v

# 6. Start the application
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

# 5. Run tests
pytest -v

# 6. Start the application
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
    'homepage': 'https://www.bloomberg.com',
    'tier': 1,
    'tier_label': 'Tier 1: Financial Media'
}
```

### Adjusting Deduplication Sensitivity
Open `services/validation_service.py` and modify similarity threshold:

```python
# Default is 0.72 (72% token overlap)
if sim >= 0.72 and len(token_set & existing_tokens) >= 3:
    duplicate_found = True
```

### Adjusting Outdated Story Threshold
Open `services/validation_service.py` and modify `check_staleness`:

```python
# Default is 48 hours:
if age > timedelta(hours=48):
    return True, f"Published {days}d ago"
```

---

## 📊 REST API Documentation

### 1. Get Articles
Retrieve aggregated, deduplicated articles with optional filtering and search:
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
      "canonical_url": "https://techcrunch.com/article",
      "description": "Anthropic today revealed expanded AI capabilities...",
      "source": "TechCrunch",
      "trust_tier": 1,
      "trust_label": "Tier 1: Tech Journalism",
      "category": "Technology",
      "image": "https://techcrunch.com/thumb.jpg",
      "published": "Oct 13, 2026 11:45",
      "published_relative": "15m ago",
      "is_verified_date": true,
      "fetched_at": "2026-10-13T12:00:00",
      "is_recently_published": true,
      "is_outdated": false,
      "is_unverified": false,
      "claim_label": "Verified Publisher Report",
      "reading_time": 3,
      "alternative_sources": []
    }
  ]
}
```

### 2. System Statistics
Retrieve real-time metrics on feeds, categories, sources, and verification diagnostics:
```http
GET /api/stats
```

**Sample Response:**
```json
{
  "success": true,
  "stats": {
    "total_articles": 218,
    "total_sources": 10,
    "category_distribution": {
      "World": 82,
      "Technology": 40,
      "Business": 36,
      "Breaking News": 4
    },
    "source_distribution": {
      "BBC News": 25,
      "CNN": 24,
      "TechCrunch": 20
    },
    "verification_metrics": {
      "verified_reports": 212,
      "developing_claims": 6,
      "outdated_articles": 14,
      "cross_reported_stories": 18
    },
    "last_updated": "2026-10-13T12:35:00"
  }
}
```

### 3. Article Preview (Scraper)
Extract OpenGraph metadata and article lead text on-demand:
```http
GET /api/preview?url=https://www.bbc.com/news/articles/example
```

---

## 🧪 Testing & Verification

Run the test suite with verbose output:
```bash
pytest -v
```

The comprehensive test suite covers:
1. **Canonical URL Validation (`test_url_validation_and_tracking_stripping`)**: Rejects illegal schemes (`javascript:`, `file:`, `ftp:`) and strips tracking parameters (`utm_*`, `at_*`, `ocid`, `ref`, fragments).
2. **Headline Normalization & Deduplication (`test_headline_normalization_and_deduplication`)**: Strips publisher suffixes, tokenizes headlines, calculates Jaccard token similarity (&ge; 0.72), and merges duplicate syndicated reports while citing alternate sources.
3. **Date Preservation & Staleness Flagging (`test_date_preservation_and_staleness`)**: Normalizes timestamps in UTC to avoid machine timezone skew, preserves authentic publisher dates, prevents old news from displaying as "Just now", and flags stale (> 48h) or archived (> 7d) stories.
4. **Claim Verification (`test_claim_verification_and_unverified_flagging`)**: Detects speculative phrases (*"unconfirmed reports"*, *"sources allege"*) and tags articles with developing claim badges while preventing unverified items from becoming breaking news.
5. **Breaking News Guardrails (`test_breaking_news_contextual_guardrails`)**: Enforces strict contextual checks blocking stale events (> 6h), entertainment ("movie shooting"), sports ("baseball strike"), or unverified reports from the breaking ticker.
6. **Compound Category Scoring (`test_accurate_category_scoring`)**: Validates accurate multi-keyword topic classification across Technology, Business, and Science & Health.
7. **Cross-Source Category Accuracy (`test_cross_source_category_accuracy`)**: Verifies that specific topic keywords override source defaults (e.g., Ars Technica measles articles classify as `Science & Health`, not `Technology`; BBC growth forecast articles classify as `Business`, not `World`).
8. **Home Page Route & Verification Indicators (`test_home_page_elements`)**: Confirms live feed aggregation, hero card rendering, and ticker bar generation.
9. **About Page Architecture Documentation (`test_about_page_verification_sections`)**: Validates rendering of the verification pipeline, deduplication math, trust tiers, and system limitations.
10. **System Diagnostics & Verification Metrics API (`test_api_stats_verification_metrics`)**: Ensures `/api/stats` accurately calculates real-time verified reports, developing claims, and outdated articles.
11. **REST Articles API Filtering (`test_api_articles_filtering`)**: Verifies clean JSON serialization, category filtering, search querying, and limit parameters.

---

## 🚀 Production Deployment

### Option 1: Gunicorn WSGI Server (Linux/macOS)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Option 2: Docker Container
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

---

## ❓ Troubleshooting & FAQ

### Q: Why do some stories show "Developing Claim"?
**A:** NewsHub's verification engine detected speculative phrases (*"claims without evidence"*, *"unconfirmed reports"*, *"alleged"*) in the headline or summary. This informs readers that the situation is developing and has not yet been verified.

### Q: Why are some articles marked "Published X days ago"?
**A:** NewsHub preserves authentic publisher timestamps. If a publisher keeps an older article in their feed, NewsHub flags stories older than 48 hours to prevent readers from confusing archival background pieces with fresh breaking news.

### Q: Why do duplicate articles disappear?
**A:** NewsHub's deduplication engine identifies wire stories syndicated across multiple outlets. The primary Tier 1 publisher is displayed, with alternative outlets cited in the *"Also reported by"* badge.

---

## 📜 License & Acknowledgements

- **NewsHub Core**: Distributed under the MIT License.
- **Content Rights**: All aggregated headlines, excerpts, and images remain the intellectual property of their respective publishers (BBC, CNN, The Guardian, Al Jazeera, NPR, TechCrunch, Ars Technica, CNBC, DW News, Google News).
- Built with Python, Flask, Feedparser, BeautifulSoup4, and modern CSS.
