# Deployment Checklist ✅

## All Issues Fixed

### ✅ Centralized API Configuration
- **Created**: `frontend/src/config.ts` - Single source of truth for API URLs
- **Updated**: All 10 files now import from config instead of hardcoded URLs
- **Benefits**: Update once in config.ts instead of 10 different files

### ✅ Removed Terser Dependency
- **Problem**: Vite config used `minify: 'terser'` but terser wasn't installed
- **Fix**: Simplified vite.config.ts to match working portfolio (default minification)

### ✅ Fixed TypeScript Errors
- **Problem**: Unused variables causing build failures
- **Fixed**:
  - Removed `toggleSolved` function (TechnicalInterview.tsx)
  - Removed `behavioralScore` state and all references (JobSimulator.tsx)
  - Removed `notes` state and all references (ResumeReview.tsx)
  - Fixed type checking for `selectedJob.real` property

### ✅ Simplified Build Configuration
- **package.json**: Removed unnecessary scripts (build:prod, clean)
- **vite.config.ts**: Removed complex build options, matches portfolio config
- **vercel.json**: Simplified to essential configuration only

### ✅ Deployment Configuration
- **.vercelignore**: Excludes all Python backend files
- **vercel.json**: Builds only frontend, outputs to frontend/dist
- **Rewrites**: SPA routing configured for client-side navigation

## 🚀 How to Update API URLs

**You only need to update ONE file now!**

### When backend is deployed:

1. Open `frontend/src/config.ts`
2. Replace the placeholder URLs:
   ```typescript
   export const API_BASE_URL = import.meta.env.PROD 
     ? 'https://your-backend.railway.app' // ← Update this
     : 'http://localhost:8000'

   export const WS_BASE_URL = import.meta.env.PROD
     ? 'wss://your-backend.railway.app' // ← Update this
     : 'ws://localhost:8000'
   ```

3. Commit and push - done!

All 10 files automatically use the config:
- ✅ TechnicalInterview.tsx
- ✅ BehavioralInterview.tsx
- ✅ BehavioralInterviewLive.tsx
- ✅ BehavioralInterviewLiveV2.tsx
- ✅ JobSimulator.tsx
- ✅ ResumeReview.tsx

## Deploy Steps

1. **Commit and push changes**:
   ```bash
   git add .
   git commit -m "Centralize API configuration"
   git push
   ```

2. **Vercel will automatically**:
   - Clone repo
   - Run `cd frontend && npm install`
   - Run `cd frontend && npm run build` (tsc + vite build)
   - Deploy frontend/dist to CDN

3. **After frontend deploys**:
   - Deploy backend separately to Railway/Render
   - Update `frontend/src/config.ts` with production backend URL
   - Commit and push - Vercel auto-redeploys

## Build Should Succeed Now ✅
All TypeScript errors fixed, configuration simplified, API URLs centralized.
