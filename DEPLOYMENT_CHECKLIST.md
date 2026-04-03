# ROSHNI Deployment Checklist

## Pre-Deployment ✅

- [ ] Code committed and pushed to GitHub/GitLab
- [ ] All environment files created (`.env.production`)
- [ ] Database plan decided (SQLite → PostgreSQL recommended for production)
- [ ] Algorand testnet account set up with funds
- [ ] API keys collected:
  - [ ] Algorand mnemonic/private key
  - [ ] Gemini API key
  - [ ] ElevenLabs API key (if using voice)

## Backend Setup on Render 🚀

### Configuration
- [ ] Create Render account
- [ ] Create PostgreSQL database on Render
- [ ] Copy PostgreSQL connection string

### Service Creation
- [ ] Create Web Service (Python 3.11)
- [ ] Set Root Directory: `backend/`
- [ ] Set Build Command: `pip install -r requirements.txt`
- [ ] Set Start Command: `cd backend && gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app`

### Environment Variables
Add these in Render Service → Environment:

```
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO
BACKEND_URL=https://<your-service-name>.onrender.com
FRONTEND_URL=https://<your-vercel-app>.vercel.app
ALLOWED_HOSTS=<your-service-name>.onrender.com,<your-vercel-app>.vercel.app
DATABASE_URL=postgresql://user:pass@host:5432/roshni
ALGORAND_NETWORK=testnet
ALGORAND_NODE_URL=https://testnet-api.algonode.cloud
ALGORAND_INDEXER_URL=https://testnet-idx.algonode.cloud
ALGORAND_ADMIN_MNEMONIC=<your-algorand-mnemonic>
SUN_ASA_ID=756341116
ELEVENLABS_API_KEY=<your-key>
GEMINI_API_KEY=<your-key>
DISCOM_FIXED_CHARGE=100.0
DISCOM_ADMIN_FEE_PERCENT=2.0
DISCOM_EXPORT_RATE=8.0
DISCOM_GRID_RATE=12.0
SOLAR_EXPORT_RATE=10.0
SOLAR_POOL_RATE=9.0
IOT_AUTH_TOKEN=<secure-token>
```

### Verification
- [ ] Backend URL accessible: `https://<your-service>.onrender.com/docs`
- [ ] Swagger documentation loads
- [ ] No 502 Bad Gateway errors
- [ ] Logs show successful startup

## Frontend Setup on Vercel 🌐

### Configuration
- [ ] Create Vercel account
- [ ] Import GitHub repository

### Project Settings
- [ ] Framework: Vite
- [ ] Root Directory: `frontend/`
- [ ] Build Command: `npm run build`
- [ ] Output Directory: `dist`

### Environment Variables
Add in Vercel Project Settings:

```
VITE_BACKEND_URL=https://<your-service-name>.onrender.com
```

### Deployment
- [ ] Click Deploy
- [ ] Wait for build completion
- [ ] Frontend URL accessible

### Verification
- [ ] Frontend loads: `https://<your-app>.vercel.app`
- [ ] No CORS errors in browser console
- [ ] API calls reach backend in Network tab
- [ ] Dashboard displays data

## Post-Deployment 🔍

### Testing
- [ ] Test user login/signup
- [ ] Test wallet operations
- [ ] Test IoT data submission
- [ ] Test blockchain transactions
- [ ] Test billing calculations
- [ ] Test voice functionality (if voice API connected)

### Monitoring
- [ ] Set up Render logs monitoring
- [ ] Set up Vercel logs monitoring
- [ ] Configure error notifications (optional)
- [ ] Monitor database usage

### DNS & Security (Optional)
- [ ] Configure custom domains (if desired)
- [ ] Enable HTTPS (automatic on both platforms)
- [ ] Review CORS settings
- [ ] Test with different origins

## Troubleshooting 🔧

If deployment fails:

1. **Backend won't start:**
   - Check Render logs for error messages
   - Verify Procfile exists and correct
   - Verify all required env vars are set
   - Check database connection

2. **Frontend requests fail:**
   - Check `VITE_BACKEND_URL` is set correctly
   - Verify backend CORS allows frontend origin
   - Check Network tab in browser DevTools

3. **Database connection errors:**
   - Verify PostgreSQL connection string
   - Check database exists
   - Verify credentials are correct

4. **Algorand operations fail:**
   - Check mnemonic/private key is valid
   - Verify testnet has funds
   - Check node URL accessibility

## When Everything Works ✨

- [ ] Users can access https://<your-app>.vercel.app
- [ ] Dashboard shows live data
- [ ] API responses are fast (<500ms)
- [ ] No console errors
- [ ] All actions working (buy/sell energy, wallet, etc.)

---

**Keep this checklist handy for future deployments!**
