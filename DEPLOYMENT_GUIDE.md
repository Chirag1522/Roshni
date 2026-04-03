# ROSHNI Deployment Guide

Complete guide for deploying ROSHNI to **Vercel (Frontend)** and **Render (Backend)**.

---

## Prerequisites

- Git repository (GitHub, GitLab, or Bitbucket)
- Render account (https://render.com)
- Vercel account (https://vercel.com)
- Algorand testnet account with funds
- API keys: Gemini, ElevenLabs (optional)

---

## Part 1: Backend Deployment (Render)

### Step 1: Prepare Backend Repository

1. Update [backend/requirements.txt](backend/requirements.txt) - add gunicorn:

```bash
# Add this line to requirements.txt
gunicorn==21.2.0
uvicorn[standard]==0.24.0
```

2. Create [backend/Procfile](Procfile) (already done):
```
web: gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

3. Create `.env.production` with your keys (see [backend/.env.production](backend/.env.production))

4. Update [backend/config.py](backend/config.py) to load from `.env`:
```python
# Already configured with pydantic-settings
```

### Step 2: Push to GitHub

```bash
# From project root
git add .
git commit -m "Add deployment configuration"
git push origin main
```

### Step 3: Create Render Service

1. Go to **https://render.com/dashboard**
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name:** `roshni-backend`
   - **Environment:** `Python 3.11`
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `cd backend && gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app`
   - **Root Directory:** `backend/`

### Step 4: Set Environment Variables

In Render dashboard, go to **Service** → **Environment**:

```
ENVIRONMENT=production
DEBUG=False
BACKEND_URL=https://your-service-name.onrender.com
FRONTEND_URL=https://your-vercel-app.vercel.app
DATABASE_URL=postgresql://...  (Render postgres connection)
ALGORAND_ADMIN_MNEMONIC=your-mnemonic
GEMINI_API_KEY=your-key
ELEVENLABS_API_KEY=your-key
```

### Step 5: Create Database (PostgreSQL)

1. In Render, create a **PostgreSQL** database
2. Copy connection string to `DATABASE_URL` env var
3. Run migrations (if using Alembic):
   ```bash
   # In Render shell
   alembic upgrade head
   ```

**Important:** Update [backend/config.py](backend/config.py) to use PostgreSQL in production:
```python
@property
def database_url(self):
    if self.environment == "production":
        return os.getenv("DATABASE_URL", "postgresql://...")
    return os.getenv("DATABASE_URL", "sqlite:///./roshni.db")
```

---

## Part 2: Frontend Deployment (Vercel)

### Step 1: Update Frontend Configuration

2. Update [frontend/src/services/api.js](frontend/src/services/api.js):
```javascript
// Already configured to use import.meta.env.VITE_BACKEND_URL
const baseURL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
```

3. Create [frontend/.env.production](frontend/.env.production):
```
VITE_BACKEND_URL=https://roshni-backend.onrender.com
```

4. Create [frontend/vercel.json](frontend/vercel.json) (already done)

### Step 2: Push to GitHub

```bash
git add frontend/
git commit -m "Add frontend production config"
git push origin main
```

### Step 3: Deploy on Vercel

1. Go to **https://vercel.com/dashboard**
2. Click **"Add New"** → **"Project"**
3. Import your GitHub repository
4. Configure:
   - **Framework:** `Vite`
   - **Root Directory:** `frontend/`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`

### Step 4: Set Environment Variables

In Vercel Project Settings → **Environment Variables**:

```
VITE_BACKEND_URL=https://roshni-backend.onrender.com
```

### Step 5: Deploy

Click **Deploy** and wait for completion.

---

## Part 3: Post-Deployment

### Verify Backend

```bash
curl https://roshni-backend.onrender.com/docs
```

Should return Swagger API documentation.

### Verify Frontend

1. Visit `https://your-vercel-app.vercel.app`
2. Check browser console for API errors
3. Test API calls in Network tab

### Enable CORS

Update [backend/main.py](backend/main.py) CORS configuration:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-vercel-app.vercel.app",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Part 4: Monitoring & Logs

### Render Logs
- **Dashboard** → **Logs** tab in service details

### Vercel Logs
- Vercel **Dashboard** → **Project** → **Deployments** → click deployment → **Logs**

### Issues & Fixes

| Issue | Solution |
|-------|----------|
| 502 Bad Gateway | Check Render logs, verify `main:app` in Procfile |
| Backend endpoint not found | Verify `VITE_API_BASE_URL` in production env var |
| CORS errors | Update `frontend_url` in backend environment |
| Database connection failed | Verify `DATABASE_URL` connection string |
| Algorand operations fail | Check `ALGORAND_ADMIN_MNEMONIC` and testnet availability |

---

## Part 5: Custom Domain (Optional)

### Render
1. **Service Settings** → **Custom Domain**
2. Add your domain
3. Update DNS records

### Vercel
1. **Project Settings** → **Domains**
2. Add custom domain
3. Follow DNS configuration

---

## Development Workflow

### Local Testing Before Deployment

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### CI/CD Pipeline (Optional)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: cd backend && python -m pytest

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: cd frontend && npm run build
```

---

## Troubleshooting Quick Links

- Render Docs: https://render.com/docs
- Vercel Docs: https://vercel.com/docs
- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/
- Vite Deployment: https://vitejs.dev/guide/static-deploy.html

---

## Security Checklist

✅ Never commit `.env` files with real secrets  
✅ Use environment variables for all sensitive data  
✅ Enable HTTPS (automatic on both platforms)  
✅ Use strong database passwords  
✅ Rotate API keys regularly  
✅ Set `DEBUG=False` in production  
✅ Configure CORS properly  

---

**Questions?** Check logs first, then review the specific service documentation.
