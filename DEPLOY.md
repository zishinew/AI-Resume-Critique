# Deployment Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- Google Gemini API key

## Setup

### 1. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Frontend Setup

```bash
cd frontend
npm install
```

### 3. Build Frontend for Production

```bash
cd frontend
npm run build:prod
```

This creates an optimized production build in `frontend/dist/`.

## Running in Production

### Backend

```bash
# Make sure you're in the project root
python backend.py
```

Backend runs on `http://localhost:8000`

### Frontend

#### Option 1: Preview the build locally
```bash
cd frontend
npm run preview
```

#### Option 2: Serve with a static file server
```bash
cd frontend/dist
python -m http.server 5173
```

#### Option 3: Deploy to hosting platform

**Vercel/Netlify (Frontend):**
- Build command: `cd frontend && npm run build:prod`
- Output directory: `frontend/dist`
- Note: Update hardcoded API URLs in code for production backend

**Backend Options:**
- **Railway/Render:** Deploy `backend.py` with `requirements.txt`
- **Heroku:** Add `Procfile` with `web: python backend.py`
- **VPS:** Use systemd or PM2 to run backend.py

## Environment Variables

### Backend (.env)
- `GEMINI_API_KEY` - Your Google Gemini API key

## Production Checklist

- [ ] Add GEMINI_API_KEY to backend .env
- [ ] Update VITE_API_URL for production backend
- [ ] Build frontend: `npm run build:prod`
- [ ] Test production build: `npm run preview`
- [ ] Configuhardcoded API URLs in frontend code (localhost:8000 → production URL)
- [ ] Build frontend: `npm run build:prod`
- [ ] Test production build: `npm run preview`
- [ ] Configure CORS in backend.py for production domain
- [ ] Set up HTTPS for production

```bash
# Remove development documentation (optional)
rm BEHAVIORAL_INTERVIEW_FIXES.md FRONTEND_DEBUG.md GEMINI_LIVE_SETUP.md \\
   IMPLEMENTATION_SUMMARY.md NEXT_STEPS.md test_voice_response.py test_audio.wav
```

Keep `README.md` and `SETUP_GUIDE.md` for reference.
