# Phoenix Backend – Small Business Portal API

The backend component of Project **Phoenix**, providing RESTful services for business operations (services, customers, bookings, billing) and operational probes for DevOps automation and Disaster Recovery verification.

---

## 1. Technology Stack
- **Framework**: FastAPI (asynchronous REST framework)
- **ASGI Server**: Uvicorn
- **ORM & Data Layer**: SQLAlchemy 2.0 with SQLite 3 (WAL mode & foreign keys enabled)
- **Data Validation & Schemas**: Pydantic v2
- **Authentication**: Salted bcrypt hashing + signed HMAC-SHA256 JWT tokens
- **Testing**: pytest & FastAPI TestClient (HTTPX)

---

## 2. Installation & Setup

### Prerequisites
- Python 3.11 or Python 3.12+
- `pip`

### Step 1: Install Dependencies
From the `backend/` directory:
```bash
pip install -r requirements.txt
```

### Step 2: Seed the Database
Initialize tables and seed default users (Admin, Staff, Customer, Inactive) and sample services:
```bash
python seed.py
```

**Default Seeded Credentials:**
| Role | Email | Password | Status |
|---|---|---|---|
| **Admin** | `admin@phoenix.local` | `AdminPass123!` | Active |
| **Staff** | `staff@phoenix.local` | `StaffPass123!` | Active |
| **Customer** | `customer@phoenix.local` | `CustomerPass123!` | Active |
| **Blocked User** | `inactive@phoenix.local` | `InactivePass123!` | Inactive (403 blocked) |

---

## 3. Running the Server

Start the Uvicorn development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Once running:
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check Probe**: [http://localhost:8000/health](http://localhost:8000/health)
- **Readiness Probe**: [http://localhost:8000/ready](http://localhost:8000/ready)
- **System Status Dashboard**: [http://localhost:8000/api/status](http://localhost:8000/api/status)

---

## 4. Operational Endpoints

### Health & Readiness Probes (Nagios & Ansible)
- `GET /health`: Shallow probe returning HTTP 200 with `status: "healthy"` and `db: "ok"` when operational. Returns HTTP 503 if database check fails.
- `GET /ready`: Deep probe testing database connectivity, table integrity, and engine readiness.
- `GET /api/status`: Operational metrics detailing total registered entities, latest backup metadata, and recent self-healing/recovery events.

### Authentication & Core CRUD
- `POST /auth/login`: Authenticates credentials and returns a short-lived bearer token.
- `GET /auth/me`: Profile of the currently logged-in user.
- `GET /api/services`, `POST /api/services`: Service catalog CRUD (Admin only for modifications).
- `GET /api/customers`, `POST /api/customers`: Customer profile management.
- `GET /api/bookings`, `POST /api/bookings`: Booking management with auto-generated identifiers (`BK-YYYY-XXXX`).
- `PATCH /api/bookings/{id}/status`: Validated status transitions (`pending` $\to$ `confirmed` $\to$ `completed` / `cancelled`).
- `POST /api/invoices`: Invoice generation (strictly restricted to bookings in `completed` status).

---

## 5. Running Automated Tests

Run the full pytest suite:
```bash
pytest -v tests/
```

To run individual test modules:
```bash
pytest -v tests/test_auth.py
pytest -v tests/test_roles.py
pytest -v tests/test_bookings.py
pytest -v tests/test_invoices.py
pytest -v tests/test_backups.py
pytest -v tests/test_validation.py
```
