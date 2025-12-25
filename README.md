# GitHub Talent Scout - Production

A full-stack machine learning application that analyzes 900+ GitHub developer profiles and matches them to job descriptions using custom ML algorithms and vector similarity search.

## Overview

GitHub Talent Scout uses machine learning algorithms implemented from scratch to analyze developer profiles and match them to job requirements. The system combines traditional ML classification with modern vector embeddings for fast, accurate developer search.

## Key Features

### ML-Powered Analysis
- **Code Quality Scoring**: Custom Random Forest classifier (100% training accuracy)
- **Complexity Prediction**: Random Forest model predicting project sophistication (99.14% accuracy)
- **Vector Embeddings**: HuggingFace sentence-transformers for semantic search
- **Pgvector Integration**: Sub-second similarity search across 900+ profiles

### Real GitHub Data
- 927 real developer profiles scraped from GitHub API
- Companies: Microsoft, Google, Meta, OpenAI, Amazon, Netflix, and more
- Individual developers: Andrej Karpathy, Guido van Rossum, and 900+ others
- Live data including repositories, stars, followers, and commit history

### Full-Stack Architecture
- **Backend**: FastAPI with RESTful endpoints
- **Database**: PostgreSQL with Pgvector extension
- **Frontend**: Streamlit web interface
- **ML Pipeline**: Custom implementations from scratch

## Technology Stack

### Machine Learning
- Custom Random Forest (from scratch implementation)
- HuggingFace sentence-transformers (all-MiniLM-L6-v2)
- NumPy for numerical operations
- Scikit-learn metrics for evaluation

### Backend
- FastAPI for REST API
- PostgreSQL 16 with Pgvector extension
- Supabase for managed database
- psycopg2 for database connectivity

### Frontend
- Streamlit for web interface
- Real-time API integration
- Interactive search and filtering

## Installation

### Prerequisites
- Python 3.10+
- PostgreSQL with Pgvector (or Supabase account)
- GitHub API token

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/GitHub-Talent-Scout-Production.git
cd GitHub-Talent-Scout-Production

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create `.env` file:

```
DATABASE_URL=postgresql://user:password@host:5432/database
GITHUB_TOKEN=your_github_token_here
```

### Database Setup

The database schema includes:
- `developers` table with vector embeddings
- ML score columns (quality, complexity)
- Pgvector indexes for fast similarity search

Run the initialization SQL:
```sql
-- See backend/database/init.sql
```

## Usage

### Start the API

```bash
python backend/api/main.py
```

API runs on http://localhost:8000

Endpoints:
- `GET /` - API information
- `GET /stats` - Database statistics
- `GET /developer/{username}` - Get developer profile
- `POST /search` - Search developers by job description

### Start the Frontend

```bash
streamlit run frontend/app.py
```

Frontend runs on http://localhost:8501

### Scrape Additional Developers

```bash
python backend/scraper/github_scraper.py
```

### Score Developers with ML

```bash
python backend/ml_pipeline/score_all_developers.py
```

### Generate Embeddings

```bash
python backend/ml_pipeline/embedding_generator.py
```

## Project Structure

```
GitHub-Talent-Scout-Production/
├── backend/
│   ├── api/
│   │   └── main.py              # FastAPI application
│   ├── database/
│   │   ├── init.sql             # Database schema
│   │   └── db_connection.py     # Database manager
│   ├── ml_pipeline/
│   │   ├── code_quality_scorer.py      # Neural Network (backup)
│   │   ├── complexity_predictor.py     # Random Forest for complexity
│   │   ├── quality_predictor_rf.py     # Random Forest for quality
│   │   ├── embedding_generator.py      # HuggingFace embeddings
│   │   └── score_all_developers.py     # Batch scoring
│   └── scraper/
│       └── github_scraper.py    # GitHub data collection
├── frontend/
│   └── app.py                   # Streamlit interface
├── data/
├── .env                         # Configuration
├── requirements.txt
└── README.md
```