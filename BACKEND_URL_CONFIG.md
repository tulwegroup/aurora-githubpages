# Backend URL Configuration Guide

## Local Development (Automatic Persistence)

When you enter your Railway backend URL in the **ConfigView** and click **RE-SYNC**:
- ✅ URL is automatically saved to browser **localStorage**
- ✅ URL persists across page reloads
- ✅ No need to re-enter it every time

**How it works:**
1. Go to **System Config** in the app
2. Enter your Railway backend URL (e.g., `https://aurora-backend-production.up.railway.app`)
3. Click **RE-SYNC** button
4. Button changes to green **SAVED** confirmation
5. URL is automatically loaded on next page visit

---

## Production on Vercel (Environment Variable)

For production deployment, set the environment variable so the URL loads automatically:

### Step 1: Set Vercel Environment Variable

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project (`aurora-githubpages`)
3. Go to **Settings** → **Environment Variables**
4. Add new variable:
   - **Name:** `VITE_API_URL`
   - **Value:** `https://your-railway-backend.up.railway.app`
   - **Environments:** Production, Preview, Development (all checked)

5. Click **Save**
6. Trigger a new deployment (redeploy)

### Step 2: Verify in Code

Your app automatically reads this environment variable:

```typescript
// In api.ts - this is already configured
const rawUrl = override || APP_CONFIG.API.BASE_URL || 'https://aurora-backend-production.up.railway.app';
```

The fallback order is:
1. **localStorage override** (from ConfigView manual entry)
2. **VITE_API_URL env variable** (from Vercel)
3. **Hardcoded fallback** (emergency backup)

---

## Your Railway URLs

Replace with your actual Railway backend URL:
- **Railway Backend:** `https://aurora-backend-production.up.railway.app` (replace with your URL)
- **Neon Database:** Connected via Railway (automatic)

---

## Summary

| Scenario | Solution |
|----------|----------|
| **Local dev, never want to enter URL again** | Use ConfigView Save button once - localStorage persists |
| **Production on Vercel** | Set `VITE_API_URL` env var in Vercel settings |
| **Quick testing with different URLs** | Use ConfigView to override temporarily |

No more repetitive manual entry needed! 🚀
