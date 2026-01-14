# Aurora OSI v3 - Configuration Reference

## Overview

Aurora OSI v3 uses environment variables for configuration across all deployments (local, staging, production).

## Configuration Files

### .env (Local Development)
Local environment variables. **Never commit to Git.**

### .env.example
Template showing all available configuration options. **Committed to Git.**

### .env.production
Production environment variables (Railway only). Managed via Railway dashboard.

### .env.staging
Staging environment variables. For pre-production testing.

---

## Environment Variables

### Core Settings

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ENVIRONMENT` | string | Yes | - | `development`, `staging`, `production` |
| `DEBUG` | boolean | No | false | Enable debug mode (development only) |
| `LOG_LEVEL` | string | No | INFO | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

### API Settings

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `API_HOST` | string | No | 0.0.0.0 | API host binding |
| `API_PORT` | integer | No | 8000 | API port |
| `API_WORKERS` | integer | No | 4 | Number of Gunicorn workers |
| `API_TIMEOUT` | integer | No | 120 | Request timeout in seconds |
| `SECRET_KEY` | string | Yes | - | Secret key for session/JWT signing (min 32 chars) |
| `CORS_ORIGINS` | string | No | * | Comma-separated CORS allowed origins |

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Example:
```
SECRET_KEY=VdJ8p2K9mZqRxT5nLpO1BwC3yH6sV4aE9jF2gU7kJ1dM8nQ
```

### Database Settings

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `DATABASE_URL` | string | Yes | - | PostgreSQL connection string |
| `DB_POOL_SIZE` | integer | No | 20 | Connection pool size |
| `DB_MAX_OVERFLOW` | integer | No | 40 | Max overflow connections |
| `DB_ECHO` | boolean | No | false | Log all SQL queries |

**DATABASE_URL Formats:**

Local (Docker):
```
postgresql://postgres:postgres@localhost:5432/aurora_osi_v3
```

Local (psql):
```
postgresql://user:password@localhost:5432/aurora_osi_v3
```

Neon Cloud:
```
postgresql://user:password@endpoint.neon.tech/aurora_osi_v3
```

Railway:
```
postgresql://user:password@railway.internal:5432/aurora_osi_v3
```

### Redis Settings

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `REDIS_URL` | string | No | redis://localhost:6379/0 | Redis connection string |
| `REDIS_CACHE_TTL` | integer | No | 3600 | Cache TTL in seconds |

**REDIS_URL Formats:**

Local:
```
redis://localhost:6379/0
```

With password:
```
redis://:password@localhost:6379/0
```

Railway:
```
redis://:password@railway.internal:6379
```

### Satellite Integration

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `EE_PROJECT_ID` | string | No | - | Google Earth Engine project ID |
| `EE_PRIVATE_KEY_ID` | string | No | - | Earth Engine private key ID |
| `EE_PRIVATE_KEY` | string | No | - | Earth Engine private key (JSON) |
| `EE_CLIENT_EMAIL` | string | No | - | Earth Engine client email |
| `PLANET_API_KEY` | string | No | - | Planet Labs API key |
| `PLANET_BUCKET` | string | No | - | Planet data S3 bucket |
| `MAXAR_API_KEY` | string | No | - | Maxar imagery API key |

**Earth Engine Setup:**

1. Create GCP project
2. Enable Earth Engine API
3. Create service account
4. Download JSON credentials
5. Extract values for EE_* variables

```bash
# Parse credentials JSON
cat credentials.json | jq '.private_key'  # → EE_PRIVATE_KEY
cat credentials.json | jq '.private_key_id'  # → EE_PRIVATE_KEY_ID
cat credentials.json | jq '.client_email'  # → EE_CLIENT_EMAIL
```

### Quantum Backend

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `QUANTUM_BACKEND` | string | No | simulator | `simulator`, `qaoa`, `annealing`, `hybrid` |
| `QUANTUM_DEVICE` | string | No | - | Device name (varies by backend) |
| `IBM_QUANTUM_TOKEN` | string | No | - | IBM Quantum token (if using IBM) |
| `AWS_BRAKET_DEVICE_ARN` | string | No | - | AWS Braket device ARN (if using AWS) |

**Quantum Backend Options:**

- `simulator`: Classical tensor network simulation
- `qaoa`: Quantum Approximate Optimization Algorithm (QAOA)
- `annealing`: D-Wave quantum annealing
- `hybrid`: Hybrid classical-quantum approach

### AWS S3 Settings

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `AWS_ACCESS_KEY_ID` | string | No | - | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | string | No | - | AWS secret key |
| `AWS_REGION` | string | No | us-east-1 | AWS region |
| `S3_BUCKET` | string | No | aurora-osi-v3 | S3 bucket name |

### Monitoring & Analytics

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `SENTRY_DSN` | string | No | - | Sentry error tracking URL |
| `DATADOG_API_KEY` | string | No | - | Datadog API key |
| `METRICS_ENABLED` | boolean | No | true | Enable metrics collection |

### Feature Flags

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `ENABLE_SPECTRAL_DETECTION` | boolean | No | true | Enable mineral spectral detection |
| `ENABLE_DIGITAL_TWIN` | boolean | No | true | Enable 4D digital twin |
| `ENABLE_SATELLITE_TASKING` | boolean | No | true | Enable satellite tasking |
| `ENABLE_SEISMIC` | boolean | No | true | Enable seismic processing |
| `ENABLE_QUANTUM` | boolean | No | false | Enable quantum acceleration |
| `ENABLE_PHYSICS_CONSTRAINTS` | boolean | No | true | Enable physics constraint enforcement |

---

## Sample Configuration Files

### .env.example (Template)
```bash
# Environment
ENVIRONMENT=development
DEBUG=false
LOG_LEVEL=INFO

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_TIMEOUT=120
SECRET_KEY=your-secret-key-here-min-32-chars-generate-with-python
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aurora_osi_v3
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_ECHO=false

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=3600

# Satellite Integration
EE_PROJECT_ID=
EE_PRIVATE_KEY_ID=
EE_PRIVATE_KEY=
EE_CLIENT_EMAIL=
PLANET_API_KEY=
PLANET_BUCKET=
MAXAR_API_KEY=

# Quantum Backend
QUANTUM_BACKEND=simulator
QUANTUM_DEVICE=
IBM_QUANTUM_TOKEN=
AWS_BRAKET_DEVICE_ARN=

# AWS S3
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
S3_BUCKET=aurora-osi-v3

# Monitoring
SENTRY_DSN=
DATADOG_API_KEY=
METRICS_ENABLED=true

# Feature Flags
ENABLE_SPECTRAL_DETECTION=true
ENABLE_DIGITAL_TWIN=true
ENABLE_SATELLITE_TASKING=true
ENABLE_SEISMIC=true
ENABLE_QUANTUM=false
ENABLE_PHYSICS_CONSTRAINTS=true
```

### .env.development (Local)
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
API_TIMEOUT=120
SECRET_KEY=dev-secret-key-not-for-production-min-32-char
CORS_ORIGINS=*

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aurora_osi_v3
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_ECHO=true

REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=300

QUANTUM_BACKEND=simulator
ENABLE_QUANTUM=true
```

### .env.production (Railway)
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_TIMEOUT=300
SECRET_KEY=<generated-secret-key-32-chars>
CORS_ORIGINS=https://aurora-osi-v3.vercel.app

DATABASE_URL=postgresql://$USER:$PASSWORD@$NEON_ENDPOINT/aurora_osi_v3
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=60
DB_ECHO=false

REDIS_URL=redis://:$REDIS_PASSWORD@$REDIS_HOST:6379/0
REDIS_CACHE_TTL=3600

EE_PROJECT_ID=your-gee-project
EE_PRIVATE_KEY_ID=your-key-id
EE_PRIVATE_KEY=your-private-key
EE_CLIENT_EMAIL=your-service-account@project.iam.gserviceaccount.com
PLANET_API_KEY=your-planet-api-key
MAXAR_API_KEY=your-maxar-key

QUANTUM_BACKEND=qaoa
ENABLE_QUANTUM=true

SENTRY_DSN=https://your-sentry-dsn
DATADOG_API_KEY=your-datadog-key
METRICS_ENABLED=true

ENABLE_SPECTRAL_DETECTION=true
ENABLE_DIGITAL_TWIN=true
ENABLE_SATELLITE_TASKING=true
ENABLE_SEISMIC=true
ENABLE_QUANTUM=true
ENABLE_PHYSICS_CONSTRAINTS=true
```

---

## Loading Configuration

### Python

```python
import os
from dotenv import load_dotenv

# Load from .env file
load_dotenv()

# Access variables
environment = os.getenv("ENVIRONMENT", "development")
database_url = os.getenv("DATABASE_URL")
api_port = int(os.getenv("API_PORT", "8000"))

# With defaults
debug = os.getenv("DEBUG", "false").lower() == "true"
log_level = os.getenv("LOG_LEVEL", "INFO")
```

### TypeScript/JavaScript

```typescript
// Frontend (.env.local)
const API_URL = import.meta.env.VITE_API_URL
const ENV = import.meta.env.VITE_ENV

// In component
const response = await fetch(`${API_URL}/detect/mineral`, {...})
```

### Docker

```dockerfile
# Load from .env file
ENV PATH="/app/venv/bin:$PATH"
COPY .env .env
RUN python -c "from dotenv import load_dotenv; load_dotenv()"
```

---

## Configuration Validation

### Startup Checks

Backend automatically validates:
- DATABASE_URL is accessible
- REDIS_URL is accessible (if configured)
- SECRET_KEY is at least 32 characters
- ENVIRONMENT is valid

```python
# In main.py
if not app.state.db.is_connected():
    raise RuntimeError("Database connection failed")
```

### Custom Validation

```python
def validate_config():
    required_vars = [
        "DATABASE_URL",
        "SECRET_KEY",
        "ENVIRONMENT"
    ]
    
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        raise ValueError(f"Missing required: {', '.join(missing)}")
```

---

## Secrets Management

### Development

Store in `.env` (not committed):
```bash
echo ".env" >> .gitignore
```

### Production (Railway)

Use Railway's **Variables** dashboard:
1. Go to project settings
2. Click **Variables**
3. Add secrets as environment variables
4. Railway encrypts and isolates per environment

### Production (Vercel)

Use Vercel's **Environment Variables**:
1. Go to project settings
2. Click **Environment Variables**
3. Add with proper scope (Development/Preview/Production)

### Sensitive Values

Never log or expose:
- `SECRET_KEY`
- `DATABASE_URL` (contains password)
- API keys (EE_PRIVATE_KEY, PLANET_API_KEY, etc.)
- `AWS_SECRET_ACCESS_KEY`

---

## Configuration Profiles

### Local Development
```bash
cp .env.example .env
# Edit .env with localhost addresses
npm run dev && cd backend && uvicorn main:app --reload
```

### Docker Development
```bash
docker-compose up -d
# Uses compose environment variables
```

### Staging
```bash
# Railway staging environment
git push origin staging
# Deploys to staging with .env.staging
```

### Production
```bash
# Railway production
git push origin main
# Deploys with production variables from Railway dashboard
```

---

## Troubleshooting

### Variables Not Loading

**Check if .env exists:**
```bash
ls -la .env
```

**Verify format (no spaces):**
```bash
# ❌ Wrong
API_PORT = 8000

# ✅ Correct
API_PORT=8000
```

**Reload Python environment:**
```bash
deactivate
source venv/bin/activate
python -c "import os; print(os.getenv('API_PORT'))"
```

### Database Connection Failed

**Verify DATABASE_URL:**
```bash
psql "$DATABASE_URL"
```

**Check if PostgreSQL is running:**
```bash
docker-compose ps postgres
```

### API Key Invalid

**Check format:**
```bash
echo $PLANET_API_KEY
# Should be exactly as provided (no quotes)
```

**Re-export variable:**
```bash
export PLANET_API_KEY="your-key-value"
```

---

## Best Practices

1. **Generate unique SECRET_KEY for each environment**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Rotate keys regularly** (quarterly minimum)

3. **Use separate databases per environment**
   - Development: Local PostgreSQL
   - Staging: Neon staging instance
   - Production: Neon production instance

4. **Enable Neon automated backups** for production

5. **Use Railway's native environment management** instead of .env files in production

6. **Audit who has access** to production variables

7. **Log configuration on startup** (exclude secrets)
   ```python
   logger.info(f"Environment: {os.getenv('ENVIRONMENT')}")
   logger.info(f"Database: {os.getenv('DATABASE_URL').split('@')[1]}")
   # Don't log password part!
   ```

---

**Last Updated:** January 14, 2026  
**Version:** 3.1.0
