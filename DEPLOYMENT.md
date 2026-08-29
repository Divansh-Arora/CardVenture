# Cardventure — Railway Deployment Guide

## Prerequisites
- Railway account
- GitHub repo with this codebase
- NVIDIA API key from https://build.nvidia.com

---

## 1. Rotate Secrets (Required Before Deploy)

The current `backend/.env` contains real secrets. **Rotate all three:**

| Secret | How to Rotate |
|--------|---------------|
| **Neon DB Password** | Go to Neon Console → Project → Connection Details → Reset Password |
| **NVIDIA API Key** | Go to build.nvidia.com → API Keys → Regenerate |
| **JWT Secret** | Already generated: `5c7d6ea397015f4e27ee268cddd6ab5e1657ae2da97179afd70eadba1ab38866` (or run `python -c "import secrets; print(secrets.token_hex(32))"` for a new one) |

---

## 2. Create Railway Project

1. Go to https://railway.app → New Project
2. Select "Deploy from GitHub repo" → Choose your repo
3. Railway will detect two folders: `backend/` and `frontend/`

---

## 3. Add PostgreSQL Database

1. In your Railway project: **New Service** → **Database** → **PostgreSQL**
2. Wait for provisioning
3. Copy the `DATABASE_URL` from the Postgres service's "Connect" tab

---

## 4. Deploy Backend (Web Service)

1. **New Service** → **GitHub Repo** → Select your repo
2. **Root Directory**: `backend`
3. Railway auto-detects `Dockerfile` — confirm
4. **Environment Variables** (in Settings → Variables):

```
DATABASE_URL=<from Step 3>
NVIDIA_API_KEY=<your rotated NVIDIA key>
JWT_SECRET=5c7d6ea397015f4e27ee268cddd6ab5e1657ae2da97179afd70eadba1ab38866
CORS_ORIGINS=https://<your-frontend-domain>.railway.app,http://localhost:5173
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=nvidia/nemotron-3-ultra-550b-a55b
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

5. Deploy — Railway runs `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Note the backend URL: `https://<backend-name>.railway.app`

---

## 5. Deploy Frontend (Static Site)

**Option A: Railway Static Site (simplest)**
1. **New Service** → **GitHub Repo** → Select your repo
2. **Root Directory**: `frontend`
3. **Service Type**: Static Site
4. **Build Command**: `npm run build`
5. **Output Directory**: `dist`
6. **Environment Variables**:
```
VITE_API_URL=https://<your-backend-url>.railway.app
```
7. Deploy — Railway serves `dist/` automatically
8. Note the frontend URL: `https://<frontend-name>.railway.app`

**Option B: Vercel (recommended for frontend)**
1. Import repo in Vercel
2. **Root Directory**: `frontend`
3. **Build Command**: `npm run build`
4. **Output Directory**: `dist`
5. **Environment Variable**: `VITE_API_URL=https://<your-backend-url>.railway.app`
6. Deploy

---

## 6. Update CORS

After frontend deploys, update backend `CORS_ORIGINS`:
```
CORS_ORIGINS=https://<your-frontend-url>.railway.app,http://localhost:5173
```
Redeploy backend (auto on variable change).

---

## 7. Verify

| Check | URL |
|-------|-----|
| Backend health | `https://<backend>.railway.app/health` |
| API docs | `https://<backend>.railway.app/docs` |
| Frontend | `https://<frontend>.railway.app` |

Register an account, upload a PDF, study!

---

## Local Development

```bash
# Terminal 1 - Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Fill in your local values
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm install
cp .env.example .env
npm run dev
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000 (docs at /docs)

---

## Environment Variable Reference

### Backend (Required)
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Postgres connection string |
| `NVIDIA_API_KEY` | NVIDIA Nemotron API key |
| `JWT_SECRET` | 64-char hex string for JWT signing |

### Backend (Optional)
| Variable | Default |
|----------|---------|
| `NVIDIA_BASE_URL` | `https://integrate.api.nvidia.com/v1` |
| `NVIDIA_MODEL` | `nvidia/nemotron-3-ultra-550b-a55b` |
| `CORS_ORIGINS` | `http://localhost:5173` |
| `JWT_ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` |

### Frontend
| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend base URL (baked at build time) |

---

## Troubleshooting

**CORS errors**: Check `CORS_ORIGINS` includes your exact frontend URL (no trailing slash).

**PDF upload fails**: Ensure `NVIDIA_API_KEY` is valid and has quota.

**Database errors**: Verify `DATABASE_URL` format: `postgresql://user:pass@host/db?sslmode=require`

**Frontend can't reach backend**: Confirm `VITE_API_URL` matches backend URL exactly (rebuild frontend after changing).

---

## Architecture

```
┌─────────────────┐     HTTPS      ┌──────────────────┐
│   Frontend      │ ─────────────► │    Backend       │
│  (Static Site)  │  API calls     │  (Web Service)   │
│  Railway/Vercel │                │  + PostgreSQL    │
└─────────────────┘                └──────────────────┘
```

- Frontend: Static files (React + Vite build)
- Backend: FastAPI + Uvicorn in Docker
- Database: Railway PostgreSQL (or external)
- Auth: JWT in localStorage, sent via Authorization header