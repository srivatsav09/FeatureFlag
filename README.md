# Feature Flag & Experimentation Platform

A backend system that lets teams define feature flags, roll them out by user/percentage/environment, track exposure, and safely toggle features without redeploying.

## System Architecture

```
                    ┌──────────────────────────┐
                    │     Dashboard (UI)        │
                    │   localhost:8000          │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   FastAPI Application     │
                    │   ┌──────────────────┐   │
                    │   │  Auth Middleware  │   │
                    │   │  (JWT + RBAC)    │   │
                    │   └────────┬─────────┘   │
                    │            │              │
                    │   ┌────────▼─────────┐   │
                    │   │  Service Layer    │   │
                    │   │  - Evaluation    │   │
                    │   │  - Audit         │   │
                    │   │  - Auth          │   │
                    │   └──┬──────────┬────┘   │
                    └──────┼──────────┼────────┘
                           │          │
              ┌────────────▼──┐  ┌────▼────────────┐
              │   Redis       │  │   PostgreSQL     │
              │   (Cache)     │  │   (Persistence)  │
              │               │  │                  │
              │  Flag configs │  │  Users, Flags,   │
              │  TTL: 60s     │  │  Environments,   │
              └───────────────┘  │  Audit Logs      │
                                 └──────────────────┘
```

## Features

### Flag Management
- Create, update, and delete feature flags via REST API or dashboard
- Boolean flags (simple ON/OFF) and percentage-based rollouts
- Per-environment flag configurations (development, staging, production)

### Flag Evaluation
- **Hash-based bucketing** ensures the same user always gets the same flag value
- Consistent experience across sessions without storing per-user state
- Evaluation endpoint: `GET /evaluate/{flag_key}?environment_key=production&user_id=alice`

### Caching (Redis)
- Flag configurations cached with configurable TTL (default: 60s)
- Cache invalidation on flag updates
- Caches flag configs (not per-user results) to keep memory usage low

### Authentication & Authorization (RBAC)
- JWT-based authentication with Argon2 password hashing
- Three roles with different permissions:

| Role | Read Flags | Modify Dev/Staging | Modify Production | Delete Flags | Manage Users |
|------|-----------|-------------------|-------------------|-------------|-------------|
| Viewer | Yes | No | No | No | No |
| Developer | Yes | Yes | No | No | No |
| Admin | Yes | Yes | Yes | Yes | Yes |

### Audit Logs
- Tracks all flag changes (create, update, delete)
- Records who made the change, when, and what changed (old value -> new value)
- Queryable by flag key or recent activity

### Multi-Environment
- Three default environments: development, staging, production
- Same flag can have different configurations per environment
- Production environment is protected (admin-only modifications)

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Web Framework | FastAPI |
| Database | PostgreSQL 15 |
| ORM | SQLAlchemy 2.0 |
| Cache | Redis 7 |
| Auth | JWT (python-jose) + Argon2 |
| Validation | Pydantic v2 |
| Containerization | Docker Compose |

## Getting Started

### Prerequisites
- Python 3.11+
- Docker

### Setup

1. **Clone and create virtual environment:**
```bash
git clone https://github.com/srivatsav09/FeatureFlag.git
cd FeatureFlag
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Start PostgreSQL and Redis:**
```bash
docker-compose up -d
```

4. **Configure environment variables:**
```bash
# .env file is pre-configured for local development
# Update JWT_SECRET_KEY for production use
```

5. **Run the application:**
```bash
uvicorn app.main:app --reload --port 8000
```

6. **Create the first admin user:**
```bash
# First, register via API or dashboard at http://localhost:8000
# Then promote to admin:
python -m scripts.make_admin your-email@example.com
```

### Access Points

| URL | Description |
|-----|------------|
| `http://localhost:8000` | Dashboard UI |
| `http://localhost:8000/docs` | Swagger API Documentation |
| `http://localhost:8000/health` | Health Check |

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|---------|------------|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login, returns JWT token |
| GET | `/auth/me` | Get current user info |
| GET | `/auth/users` | List all users (admin) |
| PUT | `/auth/users/{id}/role` | Update user role (admin) |

### Environments
| Method | Endpoint | Description |
|--------|---------|------------|
| POST | `/environments` | Create environment |
| GET | `/environments` | List environments |
| GET | `/environments/{key}` | Get environment |
| DELETE | `/environments/{key}` | Delete environment |

### Flags
| Method | Endpoint | Description | Auth |
|--------|---------|------------|------|
| POST | `/flags` | Create flag | Developer+ |
| GET | `/flags` | List flags | Any role |
| GET | `/flags/{key}` | Get flag | Any role |
| PUT | `/flags/{key}` | Update flag | Developer+ |
| DELETE | `/flags/{key}` | Delete flag | Admin only |

### Evaluation
| Method | Endpoint | Description | Auth |
|--------|---------|------------|------|
| GET | `/evaluate/{flag_key}` | Evaluate flag for user | Public |

### Audit
| Method | Endpoint | Description | Auth |
|--------|---------|------------|------|
| GET | `/audit/` | Recent audit logs | Any role |
| GET | `/audit/flag/{key}` | Flag change history | Any role |

## How Flag Evaluation Works

```
Request: Is "new-checkout" enabled for user "alice" in production?

1. Check Redis cache for flag config
   → Cache HIT: use cached config
   → Cache MISS: query PostgreSQL, then cache result

2. Is flag enabled?
   → No: return {enabled: false}
   → Yes: check flag type

3. Flag type?
   → Boolean: return {enabled: true}
   → Percentage: calculate user bucket

4. Hash-based bucketing:
   hash("new-checkout:alice") % 100 = 3
   rollout_percentage = 50
   3 < 50? → Yes → {enabled: true}
```

The same user + flag combination always produces the same bucket, ensuring a consistent experience without storing per-user state.

## Project Structure

```
FeatureFlag/
├── app/
│   ├── main.py              # FastAPI app, startup, routing
│   ├── config.py             # Settings from environment variables
│   ├── database.py           # SQLAlchemy engine and session
│   ├── cache.py              # Redis caching service
│   ├── auth.py               # JWT verification, RBAC dependencies
│   ├── models/               # SQLAlchemy database models
│   │   ├── user.py           # User model with roles
│   │   ├── flag.py           # Feature flag model
│   │   ├── environment.py    # Environment model
│   │   └── audit_log.py      # Audit log model
│   ├── schemas/              # Pydantic request/response schemas
│   │   ├── user.py
│   │   ├── flag.py
│   │   ├── environment.py
│   │   └── audit.py
│   ├── routers/              # API route handlers
│   │   ├── auth.py
│   │   ├── flags.py
│   │   ├── environments.py
│   │   ├── evaluate.py
│   │   └── audit.py
│   └── services/             # Business logic
│       ├── auth.py           # Password hashing, JWT, user ops
│       ├── evaluation.py     # Flag evaluation + bucketing
│       └── audit.py          # Audit log recording
├── static/
│   └── dashboard.html        # Single-page dashboard UI
├── scripts/
│   └── make_admin.py         # CLI tool to bootstrap first admin
├── docker-compose.yml        # PostgreSQL + Redis
├── requirements.txt
└── .env                      # Environment configuration
```
