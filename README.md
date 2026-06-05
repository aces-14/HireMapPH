# HireMap PH

**Philippine job market intelligence — map, trends, and skill gap analysis. Updated daily.**

A full-stack data platform that aggregates job postings from multiple Philippine sources, maps them geographically, tracks hiring trends, and helps job seekers understand what skills the market actually demands.

Live: **[hiremaph.vercel.app](https://hiremaph.vercel.app)** &nbsp;·&nbsp; API: **[hiremaph-api.railway.app/docs](https://hiremaph-api.railway.app/docs)**

---

## What it does

- **Interactive choropleth map** — Philippines colored by job density per region, with city bubbles sized by listing count. Click a bubble to zoom in.
- **Skill Gap Analyzer** — Enter a target role and your current skills. The app compares your skillset against what Philippine employers actually ask for, shows your gap, and ranks what to learn next. Matching job listings are shown alongside so you can apply directly.
- **Trend tracking** — Week-over-week role and skill demand, fastest-growing roles, new listings this week vs last.
- **AI market insights** — One Groq call per day generates a structured market summary (fastest-growing roles, most in-demand skills, top hiring cities, notable shifts). Zero per-user AI cost, loads instantly.
- **Job listings table** — Filterable by role, city, work type, and experience level. Jobs from multiple sources are merged into one card with all available apply links labeled by platform.

---

## Tech stack

| Layer | Tech |
|---|---|
| Data pipeline | Python · BeautifulSoup · requests |
| Data storage | Parquet (pandas + PyArrow) |
| Scheduler | GitHub Actions (daily cron, 6AM PHT) |
| Geocoding | Hardcoded PH city lookup + geopy fallback |
| AI insights | Groq — Llama 3.1 8B Instant |
| Backend | FastAPI · uvicorn |
| Frontend | React 19 · Vite · Tailwind CSS · Plotly |
| Backend hosting | Railway |
| Frontend hosting | Vercel |

---

## Data sources

| Source | Method | Coverage |
|---|---|---|
| [DOLE Phil-JobNet](https://www.phil-jobnet.dol.gov.ph) | Scrape | Government / formal sector |
| [Kalibrr](https://www.kalibrr.com) | Scrape | Philippine-native job board |
| [JSearch via RapidAPI](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) | API | Indeed aggregation (legal) |

All sources scrape or access publicly available job listing data. API-based sources are used in accordance with their terms of service.

---

## Architecture

```
GitHub Actions (daily cron — 6AM PHT)
        │
        ▼
Data Pipeline
  ├── DOLE Phil-JobNet scraper
  ├── Kalibrr scraper
  └── JSearch API (RapidAPI)
        │
        ▼
Cleaner + Geocoder
  ├── Normalizes to unified schema
  ├── Extracts skills from descriptions
  ├── Deduplicates cross-source listings
  └── Maps location strings to PH city lat/lng
        │
        ▼
Parquet Storage (master.parquet + latest.parquet)
  ├── master.parquet — full history, first_seen + last_seen per job
  └── latest.parquet — active listings (last seen within 30 days)
        │
        ├── FastAPI Backend (Railway)
        │   ├── GET /health
        │   ├── GET /map-data
        │   ├── GET /jobs
        │   ├── GET /trending
        │   ├── GET /salary
        │   ├── GET /insights
        │   └── GET /skill-gap
        │
        └── Groq (one call/day)
            └── Generates insights.json → served from /insights
```

---

## Local development

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [RapidAPI](https://rapidapi.com) account with JSearch subscribed (free tier)
- A [Groq](https://console.groq.com) API key (free)

### 1. Backend

```bash
# Clone and enter the project
git clone https://github.com/YOUR_USERNAME/HireMapPH.git
cd HireMapPH

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your RAPIDAPI_KEY and GROQ_API_KEY

# Start the backend
uvicorn backend.main:app --port 8000
# API docs available at http://127.0.0.1:8000/docs
```

### 2. Run the data pipeline

```bash
python -m pipeline.run
```

This fetches from all three sources, cleans and geocodes the data, writes `data/latest.parquet` and `data/master.parquet`, then calls Groq once to generate `data/insights.json`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

The Vite dev server proxies all API calls to `http://127.0.0.1:8000` automatically.

---

## Project structure

```
HireMapPH/
├── pipeline/
│   ├── run.py              # Main pipeline entry point
│   ├── cleaner.py          # Schema normalization + deduplication
│   ├── geocoder.py         # PH city lookup + geopy fallback
│   ├── writer.py           # Parquet upsert writer
│   ├── insights.py         # Groq AI insights generator
│   └── sources/
│       ├── dole.py         # DOLE Phil-JobNet scraper
│       ├── kalibrr.py      # Kalibrr scraper
│       └── jsearch.py      # JSearch API client
├── backend/
│   ├── main.py             # FastAPI app + CORS config
│   ├── data_store.py       # In-memory Parquet cache (mtime reload)
│   └── routers/
│       ├── health.py
│       ├── map_data.py
│       ├── jobs.py
│       ├── trending.py
│       ├── salary.py
│       ├── insights.py
│       └── skill_gap.py
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Landing.jsx     # Landing page
│   │   │   └── Dashboard.jsx   # Main dashboard
│   │   ├── components/
│   │   │   ├── MapChart.jsx    # Plotly choropleth + bubble map
│   │   │   ├── MarketIntel.jsx # AI insight cards
│   │   │   ├── JobsTable.jsx   # Filterable job listings
│   │   │   └── SkillGap.jsx    # Skill gap analyzer
│   │   └── api.js              # Fetch client
│   └── public/
│       └── ph_regions_simple.geojson
├── data/
│   └── .gitkeep            # Parquets committed by GitHub Actions
├── .github/workflows/
│   └── pipeline.yml        # Daily cron pipeline
├── requirements.txt
├── Procfile
└── railway.toml
```

---

## Deployment

Deployed on **Railway** (FastAPI) + **Vercel** (React). The daily pipeline runs on **GitHub Actions**, commits fresh Parquet data to the repo, and Railway auto-redeploys.

Required secrets for GitHub Actions (`Settings → Secrets → Actions`):
- `RAPIDAPI_KEY`
- `GROQ_API_KEY`

Required environment variable for Railway:
- `RAPIDAPI_KEY`
- `GROQ_API_KEY`

Required environment variable for Vercel:
- `VITE_API_URL` → your Railway service URL

---

## Cost

| Service | Cost |
|---|---|
| Railway (Hobby) | ~$1–2/month (within $5/month credit) |
| Vercel (Hobby) | Free |
| GitHub Actions | Free (public repo) |
| RapidAPI JSearch | Free (500 req/month) |
| Groq | Free |
| **Total** | **~$2/month** |

---

## License

MIT
