# ROSHNI Deployment - Quick Start Summary

## What's Ready ✅

Your ROSHNI project is now configured for deployment to:
- **Frontend:** Vercel (https://vercel.com)
- **Backend:** Render (https://render.com)

## Files Created/Updated

### Backend
```
backend/
├── Procfile                    ← NEW: Tells Render how to run app
├── requirements.txt            ← UPDATED: Added gunicorn
├── .env.production            ← NEW: Production environment variables (fill in your keys)
├── config.py                  ← Already supports environment variables ✓
└── main.py                    ← Already configured for production CORS ✓
```

### Frontend
```
frontend/
├── .env.production            ← NEW: Production environment variables
├── vercel.json               ← NEW: Vercel deployment config
├── vite.config.js            ← Already configured for production ✓
└── src/services/api.js       ← Already uses VITE_BACKEND_URL ✓
```

### Documentation
```
├── DEPLOYMENT_GUIDE.md       ← Detailed step-by-step guide
├── DEPLOYMENT_CHECKLIST.md   ← Checklist to track progress
└── THIS FILE
```

---

## Next Steps (In Order)

### 1️⃣ **Push to GitHub** (5 minutes)
```bash
cd c:\om's\ roshni
git add .
git commit -m "Add production deployment configuration"
git push origin main
```

### 2️⃣ **Deploy Backend on Render** (15 minutes)

1. Go to https://render.com/dashboard
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Configuration:
   - Name: `roshni-backend`
   - Root Directory: `backend/`
   - Build: `pip install -r requirements.txt`
   - Start: `cd backend && gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app`

5. Add Environment Variables (from [backend/.env.production](backend/.env.production)):
   - Update YOUR_RENDER_BACKEND_URL with actual Render URL
   - Add your API keys (Algorand, Gemini, ElevenLabs)
   - Add PostgreSQL connection string

6. Click Deploy and wait for "Live" status

### 3️⃣ **Deploy Frontend on Vercel** (10 minutes)

1. Go to https://vercel.com/dashboard
2. Click **Add New** → **Project**
3. Import your GitHub repository
4. Configuration:
   - Framework: `Vite`
   - Root Directory: `frontend/`
   - Build: `npm run build`
   - Output: `dist`

5. Add Environment Variable:
   - `VITE_BACKEND_URL=https://roshni-backend-xxx.onrender.com`
   - (Use your actual Render backend URL)

6. Click Deploy and wait for completion

### 4️⃣ **Test & Verify** (5 minutes)

- Backend: Visit `https://roshni-backend-xxx.onrender.com/docs`
- Frontend: Visit `https://your-app-xxx.vercel.app`
- Check browser console for errors
- Test API calls in Network tab

---

## Important Notes 🔔

### Environment Variables to Set

Edit these files and replace placeholders:

**[backend/.env.production](backend/.env.production)**
```
BACKEND_URL=https://YOUR_RENDER_BACKEND_URL.onrender.com
FRONTEND_URL=https://your-vercel-frontend.vercel.app
DATABASE_URL=postgresql://user:password@host:5432/roshni
ALGORAND_ADMIN_MNEMONIC=your-mnemonic
GEMINI_API_KEY=your-key
ELEVENLABS_API_KEY=your-key
```

**Vercel Project Settings**
```
VITE_BACKEND_URL=https://YOUR_RENDER_BACKEND_URL.onrender.com
```

### Database

- **Development:** SQLite (local, single-file database)
- **Production:** PostgreSQL (on Render) ← Recommended

Create a PostgreSQL database in Render and update `DATABASE_URL`.

### API Keys Needed

1. **Algorand:** Account & mnemonic (testnet)
2. **Gemini:** API key from https://makersuite.google.com
3. **ElevenLabs:** API key from https://www.elevenlabs.io (optional)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "502 Bad Gateway" on backend | Check Render logs for errors. Verify Procfile and start command. |
| Frontend can't reach backend | Check `VITE_BACKEND_URL` env var. Verify CORS in backend config. |
| Database connection failed | Verify `DATABASE_URL` is correct. Check PostgreSQL is running. |
| Algorand transactions fail | Verify mnemonic is valid. Check testnet has funds. |

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed troubleshooting.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Browser                                                │
│  https://your-app.vercel.app (React Frontend)          │
│                       ↓                                 │
│              ┌────────────────────┐                     │
│              │ Vercel CDN         │                     │
│              │ (dist/ files)      │                     │
│              └────────────────────┘                     │
│                       ↓                                 │
│              ┌────────────────────────┐                 │
│              │ API Requests           │                 │
│              │ https://render.com     │                 │
│              └────────────────────────┘                 │
│                       ↓                                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Render.com - Backend                             │  │
│  │ FastAPI Application                              │  │
│  │ - User Authentication                            │  │
│  │ - Wallet Management                              │  │
│  │ - IoT Data Processing                            │  │
│  │ - Blockchain Integration                         │  │
│  │ - Billing & Pricing                              │  │
│  │                                                  │  │
│  │ PostgreSQL Database (Render)                     │  │
│  │ Algorand Blockchain (Testnet)                    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Performance Tips

1. **Database:** Use connection pooling (already enabled in FastAPI)
2. **Gunicorn Workers:** Currently 4 workers, adjust if needed: `-w 8` for more traffic
3. **Frontend:** Vite auto-optimizes, run `npm run build` before deploying
4. **Monitoring:** Check Render analytics for uptime and performance

---

## Keep Reference Files Handy

- 📄 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Complete guide with all steps
- ✅ [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Checklist to track progress
- ⚙️ [backend/.env.production](backend/.env.production) - Backend environment template
- ⚙️ [frontend/.env.production](frontend/.env.production) - Frontend environment template

---

## Support Resources

- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/
- Render Docs: https://render.com/docs
- Vercel Docs: https://vercel.com/docs
- Algorand SDK: https://developer.algorand.org
- Vite Build: https://vitejs.dev/guide/static-deploy.html

---

**You're all set! Follow the "Next Steps" above to deploy your ROSHNI project.** 🚀

Questions? Refer to [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed explanations.
