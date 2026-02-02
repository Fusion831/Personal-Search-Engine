# Installation & Setup Guide

Complete instructions for deploying the Personal Search Engine.

---

## Prerequisites

### Option 1: Docker (Recommended)
- Docker 20.10+
- Docker Compose 1.29+
- 4GB RAM minimum, 8GB recommended
- 10GB disk space

### Option 2: Local Development
- Python 3.11+
- Node.js 20+
- PostgreSQL 16+
- Redis 6.0+
- 4GB RAM

---

## Quick Start with Docker

### 1. Clone Repository

```bash
git clone https://github.com/Fusion831/Personal-Search-Engine.git
cd Personal-Search-Engine
```

### 2. Create Environment File

Create `backend/.env`:

```bash
# Google Gemini API - Required
GOOGLE_API_KEY=your_api_key_here

# Database - Change password for production!
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change_me_in_production
POSTGRES_DB=personal_search_engine

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Optional: Application Settings
LOG_LEVEL=INFO
```

### 3. Build & Start Services

```bash
docker-compose up --build
```

**This starts:**
- Frontend (React): http://localhost:5173
- Backend API (FastAPI): http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- Database (PostgreSQL): localhost:5432
- Cache (Redis): localhost:6379
- Worker (Celery): background processing

### 4. Verify Installation

```bash
# Check backend health
curl http://localhost:8000/health

# Check API docs
open http://localhost:8000/docs

# View logs
docker-compose logs -f backend
```

### 5. First Use

1. Open http://localhost:5173
2. Upload a PDF file
3. Wait for processing (watch backend logs)
4. Ask a question in the chat

---

## Manual Setup (Development)

### Backend Setup

#### 1. Create Virtual Environment

```bash
cd backend
python -m venv .venv

# Activate
# Linux/macOS:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Configure Environment

Create `.env` in `backend/`:

```bash
GOOGLE_API_KEY=your_key_here
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=personal_search_engine
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

#### 4. Setup Database

**Option A: With Docker (Easy)**
```bash
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=personal_search_engine \
  -p 5432:5432 \
  postgres:16

docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7
```

**Option B: Local Installation**
- macOS: `brew install postgresql redis`
- Ubuntu: `sudo apt-get install postgresql redis-server`
- Windows: Use PostgreSQL installer + Redis download

#### 5. Initialize Database

```bash
python -c "from database import engine; from models import Base; Base.metadata.create_all(bind=engine)"
```

#### 6. Start FastAPI Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 7. Start Celery Worker (In New Terminal)

```bash
# Make sure you're in the backend directory and venv is activated
celery -A worker.celery_app worker --loglevel=info
```

### Frontend Setup

#### 1. Install Dependencies

```bash
cd frontend
npm install
```

#### 2. Configure API Endpoint (if not localhost)

Edit `frontend/src/main.jsx`:

```javascript
const API_URL = 'http://localhost:8000'; // Change if needed
```

#### 3. Start Development Server

```bash
npm run dev
```

Frontend will be at http://localhost:5173

---

## Production Deployment

### Docker Compose Production

#### 1. Update Environment

```bash
# backend/.env - Use strong passwords!
GOOGLE_API_KEY=your_production_key
POSTGRES_PASSWORD=very_strong_password_here
LOG_LEVEL=WARNING
```

#### 2. Build Production Images

```bash
docker-compose -f docker-compose.yml build --no-cache
```

#### 3. Deploy with Volume Persistence

```bash
docker-compose up -d

# Verify all services are running
docker-compose ps
```

#### 4. Setup Reverse Proxy (Nginx)

The `nginx.conf` is already configured. Access through:
- Frontend: http://your-domain.com
- API: http://your-domain.com/api

#### 5. Monitor Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend
docker-compose logs -f worker
```

### Kubernetes Deployment

See `ROADMAP.md` for planned Kubernetes support (Phase 3).

---

## Configuration Guide

### Environment Variables

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `GOOGLE_API_KEY` | ✓ | - | Get from Google Cloud Console |
| `POSTGRES_USER` | ✓ | postgres | Database user |
| `POSTGRES_PASSWORD` | ✓ | - | Change for production! |
| `POSTGRES_DB` | ✓ | personal_search_engine | Database name |
| `POSTGRES_HOST` | | localhost | DB hostname |
| `POSTGRES_PORT` | | 5432 | DB port |
| `CELERY_BROKER_URL` | ✓ | redis://localhost:6379/0 | Redis connection |
| `CELERY_RESULT_BACKEND` | ✓ | redis://localhost:6379/0 | Results storage |
| `LOG_LEVEL` | | INFO | DEBUG, INFO, WARNING, ERROR |

### Application Settings

Edit in `backend/main.py`:

```python
# Query routing threshold (0.0-1.0)
ROUTING_THRESHOLD = 0.8  # Lower = favor summaries

# Context window size
MAX_CONTEXT_TOKENS = 2048  # Max tokens for LLM context

# HyDe transformation
USE_HYDE = True  # Enable/disable hypothetical doc embeddings

# Chunk sizes
CHILD_CHUNK_SIZE = 500  # Characters
CHILD_CHUNK_OVERLAP = 100  # Characters
MIN_PARENT_LENGTH = 50  # Minimum characters for parent chunks
```

---

## Troubleshooting

### Database Connection Error

```
Error: could not connect to server: Connection refused
```

**Solution:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Start PostgreSQL
docker run -d --name postgres -e POSTGRES_PASSWORD=password \
  -p 5432:5432 postgres:16
```

### API Key Not Working

```
Error: Invalid API key provided
```

**Solution:**
1. Get key from https://makersuite.google.com/app/apikey
2. Set in `.env`: `GOOGLE_API_KEY=sk_...`
3. Restart services: `docker-compose restart`

### Port Already in Use

```
Error: bind: address already in use
```

**Solution:**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port in docker-compose
# Change "8000:8000" to "8001:8000"
```

### Celery Worker Not Processing Tasks

```
No tasks being processed
```

**Solution:**
```bash
# Verify Redis is running
docker ps | grep redis

# Check Celery logs
docker-compose logs celery

# Restart worker
docker-compose restart worker
```

### Out of Memory

```
Container killed due to out of memory
```

**Solution:**
```bash
# Reduce batch size in backend/worker.py
# Or increase Docker memory allocation
# In docker-compose.yml:
services:
  worker:
    deploy:
      resources:
        limits:
          memory: 2G
```

---

## Getting Help

### Documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [CONCEPTS.md](CONCEPTS.md) - Core ideas
- [PERFORMANCE.md](PERFORMANCE.md) - Scaling & optimization

### Resources
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.io/)
- [PostgreSQL pgvector](https://github.com/pgvector/pgvector)

### Issues
Open a GitHub issue with:
- Full error message
- Reproduction steps
- Environment details (OS, Docker version, etc.)
- Logs from affected service

