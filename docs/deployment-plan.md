# Deployment Plan

This document outlines the deployment strategy for the Navi Mutual Fund FAQ Assistant.

## Architecture Overview

- **Backend:** FastAPI application deployed on Render
- **Frontend:** Next.js application deployed on Vercel
- **Scheduler:** GitHub Actions for daily data ingestion
- **Vector Database:** Local Chroma with PersistentClient (no Chroma Cloud)

## Backend Deployment (Render)

### Prerequisites
- Render account (free tier available)
- GitHub repository with code
- Environment variables configured

### Environment Variables Required
```bash
GROQ_API_KEY=your_groq_api_key
INGEST_CHROMA_DIR=data/chroma
INGEST_CHROMA_COLLECTION=mf_faq_chunks
PORT=8000
API_HOST=0.0.0.0
RUNTIME_API_DEBUG=0
```

### Deployment Steps

1. **Prepare Render Configuration**
   - Create `render.yaml` in project root:
   ```yaml
   services:
     - type: web
       name: navi-mf-faq-api
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: python -m runtime.phase_9_api
       envVars:
         - key: GROQ_API_KEY
           sync: false
         - key: INGEST_CHROMA_DIR
           value: data/chroma
         - key: INGEST_CHROMA_COLLECTION
           value: mf_faq_chunks
         - key: PORT
           value: 8000
         - key: API_HOST
           value: 0.0.0.0
         - key: RUNTIME_API_DEBUG
           value: 0
   ```

2. **Push Code to GitHub**
   - Ensure all code is pushed to the repository
   - Verify `requirements.txt` includes all dependencies

3. **Connect Render to GitHub**
   - Go to Render dashboard
   - Click "New +" → "Web Service"
   - Connect to your GitHub repository
   - Select branch (main)
   - Configure build and start commands:
     - Build: `pip install -r requirements.txt`
     - Start: `python -m runtime.phase_9_api`

4. **Set Environment Variables**
   - Add `GROQ_API_KEY` (from Groq console)
   - Add `INGEST_CHROMA_DIR=data/chroma`
   - Add `INGEST_CHROMA_COLLECTION=mf_faq_chunks`
   - Add `PORT=8000`
   - Add `API_HOST=0.0.0.0`
   - Add `RUNTIME_API_DEBUG=0`

5. **Deploy**
   - Click "Create Web Service"
   - Monitor deployment logs
   - Wait for deployment to complete

6. **Verify Deployment**
   - Access health endpoint: `https://your-app.onrender.com/health`
   - Check that all components are initialized

### Handling Chroma Data

**Local Chroma Integration**
- Chroma uses local PersistentClient for vector storage
- GitHub Actions scheduler builds local Chroma index during ingest
- Chroma data stored in `data/chroma/` directory
- GitHub Actions uploads `data/chroma/` as workflow artifact
- Render backend downloads artifact on deployment or uses local copy
- Data persists in artifact storage - no external vector DB needed

### Render Service Configuration

- **Plan:** Free tier (512MB RAM, 0.1 CPU)
- **Region:** Oregon (closest to GitHub Actions)
- **Branch:** main
- **Auto-deploy:** Enabled

## Frontend Deployment (Vercel)

### Prerequisites
- Vercel account (free tier available)
- GitHub repository with code
- Backend API URL

### Environment Variables Required
```bash
NEXT_PUBLIC_API_URL=https://your-app.onrender.com
```

### Deployment Steps

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Deploy from Project Root**
   ```bash
   cd web
   vercel
   ```

3. **Follow Vercel Prompts**
   - Link to existing project or create new
   - Set project name: `navi-mf-faq-ui`
   - Set build command: `npm run build`
   - Set output directory: `.next`
   - Set environment variable: `NEXT_PUBLIC_API_URL`

4. **Configure Environment Variables**
   - In Vercel dashboard → Settings → Environment Variables
   - Add `NEXT_PUBLIC_API_URL` = backend Render URL

5. **Deploy**
   - Vercel will automatically deploy on push to main branch
   - Monitor deployment logs

6. **Verify Deployment**
   - Access frontend: `https://your-project.vercel.app`
   - Test chat functionality
   - Verify API connectivity

### Vercel Configuration

Create `vercel.json` in `web/` directory:
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "env": {
    "NEXT_PUBLIC_API_URL": "@backend-url"
  }
}
```

## GitHub Actions Scheduler

### Current Configuration
- **Schedule:** Daily at 09:15 IST (03:45 UTC)
- **Trigger:** Cron + Manual workflow_dispatch
- **Target:** Local Chroma (builds index and uploads as artifact)

### Local Chroma Integration

**GitHub Actions Secrets Required:**
- `GROQ_API_KEY`: Groq API key (for generation phase testing)

**Workflow:**
1. GitHub Actions triggers daily
2. Runs ingest pipeline (scrape → normalize → chunk → embed → index)
3. Phase 4.3 (indexing) builds local Chroma index in `data/chroma/`
4. Uploads `data/chroma/` directory as workflow artifact (retained for 90 days)
5. Optional: Uploads to Render via API or manual deployment trigger
6. Application connects to local Chroma at `data/chroma/` for retrieval

## Deployment Workflow

### Initial Deployment

1. **Backend First**
   - Deploy FastAPI to Render
   - Verify health endpoint
   - Test API endpoints manually

2. **Frontend Second**
   - Deploy Next.js to Vercel
   - Configure API URL
   - Test full chat flow

3. **Scheduler**
   - GitHub Actions already configured
   - Verify workflow runs successfully
   - Check artifact uploads

### CI/CD Pipeline

```
Push to GitHub
  ↓
GitHub Actions (Scheduler) - Daily at 09:15 IST
  ↓
Runs ingest pipeline (scrape → normalize → chunk → embed → index)
  ↓
Builds local Chroma index in data/chroma/
  ↓
Uploads data/chroma/ as workflow artifact
  ↓
Render (Backend) - Auto-deploy on push
  ↓
Downloads latest Chroma artifact on deployment
  ↓
Vercel (Frontend) - Auto-deploy on push
  ↓
Production Live
```

## Monitoring and Logging

### Backend (Render)
- **Logs:** Available in Render dashboard
- **Metrics:** CPU, Memory, Response time
- **Alerts:** Configure for deployment failures

### Frontend (Vercel)
- **Logs:** Available in Vercel dashboard
- **Analytics:** Built-in analytics
- **Error Tracking:** Vercel provides error monitoring

### GitHub Actions
- **Logs:** Available in Actions tab
- **Artifacts:** Chroma data retained for 90 days
- **Failure Alerts:** Email notifications

## Rollback Strategy

### Backend Rollback
- Render maintains previous deployments
- Roll back via Render dashboard
- Re-deploy previous commit

### Frontend Rollback
- Vercel maintains deployment history
- Roll back via Vercel dashboard
- Re-deploy previous commit

### Data Rollback
- Chroma artifacts stored in GitHub Actions (90-day retention)
- Restore previous artifact if needed
- Download artifact from GitHub Actions
- Extract to `data/chroma/` directory
- Re-deploy backend with restored data

## Scaling Considerations

### Backend Scaling
- **Free Tier:** 512MB RAM, 0.1 CPU
- **Starter ($7/mo):** 1GB RAM, 0.5 CPU
- **Scale Up:** Upgrade Render plan if needed
- **Load Balancing:** Render handles automatically

### Frontend Scaling
- Vercel handles scaling automatically
- Edge caching for static assets
- No manual scaling needed

## Security Considerations

### Environment Variables
- Never commit API keys to repository
- Use Render/Vercel environment variables
- Rotate keys regularly

### API Security
- Add rate limiting to FastAPI
- Implement CORS for frontend domain
- Add authentication if needed (currently public)

### Data Security
- Chroma data stored locally in `data/chroma/`
- Chroma artifacts uploaded to GitHub Actions (encrypted)
- No PII stored in database
- Logs redact sensitive information

## Cost Estimate

### Backend (Render)
- **Free Tier:** $0/month
- **Starter:** $7/month (if needed)

### Frontend (Vercel)
- **Hobby:** $0/month
- **Pro:** $20/month (if needed)

### GitHub Actions
- **Free Tier:** 2000 minutes/month
- **Pro:** $4/month (if exceeded)

### Total Estimated Cost
- **Minimum:** $0/month (free tiers)
- **Recommended:** $7-27/month (if scaling needed)

## Troubleshooting

### Backend Issues

**Problem:** Deployment fails
- Check Render logs
- Verify dependencies in requirements.txt
- Ensure Python version matches (3.11)

**Problem:** API returns 503
- Check if components initialized
- Verify Chroma index exists in `data/chroma/`
- Check if artifact was downloaded on deployment
- Verify environment variables

### Frontend Issues

**Problem:** Cannot connect to API
- Verify NEXT_PUBLIC_API_URL
- Check CORS settings
- Verify backend is running

**Problem:** Build fails
- Check npm install
- Verify Next.js version
- Check TypeScript errors

### Scheduler Issues

**Problem:** Workflow fails
- Check Actions logs
- Verify URL registry
- Check scraping failures

**Problem:** Artifacts not uploading
- Check artifact size limits
- Verify workflow configuration
- Check GitHub Actions permissions

## Post-Deployment Checklist

- [ ] Backend health endpoint returns 200
- [ ] Frontend loads without errors
- [ ] Chat functionality works end-to-end
- [ ] GitHub Actions scheduler runs successfully
- [ ] Chroma artifact is uploaded successfully
- [ ] Backend can access Chroma index from `data/chroma/`
- [ ] Environment variables are set correctly
- [ ] CORS is configured properly
- [ ] Error monitoring is set up
- [ ] Log retention is configured
- [ ] Rollback procedure is documented
- [ ] Artifact download mechanism is tested

## Maintenance

### Regular Tasks
- Monitor deployment logs weekly
- Check GitHub Actions runs
- Review error rates
- Update dependencies monthly
- Review and rotate API keys quarterly

### Updates
- Backend: Push to main branch → auto-deploy
- Frontend: Push to main branch → auto-deploy
- Scheduler: Update workflow in `.github/workflows/`

## Support and Documentation

- **Render Docs:** https://render.com/docs
- **Vercel Docs:** https://vercel.com/docs
- **GitHub Actions Docs:** https://docs.github.com/actions
- **Project Docs:** See `docs/` folder
