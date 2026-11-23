# Jyohar Tech × Innollege — Company Management Platform

A production-grade, full-stack company management system with Founder and Employee portals.

---

## 🏗️ Architecture

```
React (Vite + TypeScript + Tailwind) → Nginx → FastAPI (Python 3.12)
                                                    ↓
                                              MySQL 8 + Redis 7 + MinIO
```

## 📋 Prerequisites

- **Docker** 24+ and **Docker Compose** v2+
- **Node.js** 20+ (for local frontend development)
- **Python** 3.12+ (for local backend development)
- Ports available: 80, 3000, 3306, 5173, 6379, 8000, 9000, 9001

---

## 🚀 Quick Start (Docker — Recommended)

### 1. Clone and configure environment

```bash
git clone <repo-url>
cd jyohar-platform

# Copy env template
cp .env.example .env

# Edit .env — change passwords before running in any shared environment
# At minimum change: SECRET_KEY, MYSQL_ROOT_PASSWORD, MYSQL_PASSWORD, REDIS_PASSWORD
```

### 2. Start all services

```bash
docker-compose up -d
```

This will:
- Start MySQL 8, Redis 7, MinIO
- Apply all database migrations (`alembic upgrade head`)
- Seed the founder account
- Start the FastAPI backend on port 8000
- Start the React frontend on port 3000
- Start Nginx reverse proxy on port 80

### 3. Access the application

| Service | URL |
|---------|-----|
| **Main App** | http://localhost |
| **Backend API** | http://localhost/api/v1/ |
| **API Docs** (Swagger) | http://localhost/api/docs |
| **MinIO Console** | http://localhost:9001 |

### 4. Default Login Credentials

| Role | Email | Password |
|------|-------|----------|
| **Founder** | founder@jyohartech.com | Jyohar@2024 |

> ⚠️ **Change these credentials immediately in production.**

---

## 💻 Local Development (Without Docker)

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env to point to your local MySQL and Redis instances

# Apply migrations
alembic upgrade head

# Seed founder account
python seed.py

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server (proxies /api to localhost:8000)
npm run dev
```

Frontend runs at: http://localhost:5173

---

## 🗄️ Database

### Migrations

```bash
cd backend

# Apply all pending migrations
alembic upgrade head

# Check current migration version
alembic current

# Create a new migration
alembic revision --autogenerate -m "description"

# Rollback one step
alembic downgrade -1
```

### Seed Data

```bash
cd backend
python seed.py
```

Creates:
- Founder user account
- Default leave types (Annual, Sick, Casual, Unpaid)

---

## 🧪 Running Tests

```bash
cd backend

# Install test dependencies (included in requirements.txt)
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v
pytest tests/test_authorization.py -v

# With coverage
pytest tests/ --cov=app --cov-report=term-missing
```

---

## 📁 Project Structure

```
jyohar-platform/
├── docker-compose.yml          # All services
├── docker-compose.prod.yml     # Production overrides
├── .env.example                # Environment template
├── nginx/
│   └── nginx.conf              # Reverse proxy config
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/           # Database migrations
│   ├── app/
│   │   ├── main.py             # FastAPI app
│   │   ├── config.py           # Settings
│   │   ├── database.py         # DB engine + session
│   │   ├── dependencies.py     # Auth guards
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── routers/            # API route handlers
│   │   ├── services/           # Business logic
│   │   ├── core/               # Security, Redis, exceptions
│   │   └── workers/            # Celery background jobs
│   ├── tests/                  # pytest test suite
│   └── seed.py                 # Database seeder
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.ts
    └── src/
        ├── pages/              # Route pages
        ├── components/         # Reusable components
        ├── hooks/              # TanStack Query hooks
        ├── store/              # Zustand state
        ├── lib/                # API client, utils
        └── router/             # React Router config
```

---

## 🔐 Security Notes

- Passwords are hashed with **Argon2id** (never stored plain)
- JWT access tokens expire in **15 minutes**
- Refresh tokens expire in **7 days** and are stored as hashes
- All tokens stored in **httpOnly cookies** (not localStorage)
- OTP: 6 digits, 10-minute TTL, max 5 attempts
- Role-based access control enforced **server-side** on every request
- Employees cannot access other employees' data via any API manipulation
- File downloads use **time-limited signed URLs** (1-hour TTL)

---

## 📡 API Reference

Full interactive API documentation available at: http://localhost/api/docs

### Auth Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Email + password login |
| POST | `/api/v1/auth/otp/request` | Request phone OTP |
| POST | `/api/v1/auth/otp/verify` | Verify OTP |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout + revoke session |
| GET | `/api/v1/auth/me` | Current user info |

### WebSocket

Connect to `/ws?token={access_token}` for real-time events.

---

## 🌍 Environment Variables

See `.env.example` for the complete list with descriptions.

Key variables:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | JWT signing key (must be random, 32+ chars) |
| `DATABASE_URL` | MySQL connection string |
| `REDIS_URL` | Redis connection string |
| `OTP_STUB_MODE` | `true` = log OTP to console (dev), `false` = send SMS |
| `MINIO_ENDPOINT` | MinIO/S3 endpoint |

---

## 🚢 Deployment

### Production Checklist

- [ ] Generate a strong `SECRET_KEY` (32+ random chars)
- [ ] Change all default passwords in `.env`
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `OTP_STUB_MODE=false` and configure SMS provider
- [ ] Configure SMTP for email notifications
- [ ] Enable HTTPS in `nginx/nginx.conf` (see commented section)
- [ ] Set up SSL certificates (Let's Encrypt / Certbot)
- [ ] Configure MySQL backups
- [ ] Set MinIO to production storage or switch to AWS S3

---

## 📞 Support

**Jyohar Tech × Innollege**
Platform Version: 1.0.0 (Phase 1)
