# Database Setup Guide

## Issue: Connection Refused

The error `ConnectionRefusedError: [WinError 1225]` means PostgreSQL is either:
1. Not installed
2. Not running
3. Not accessible on the configured port

## Option 1: Use PostgreSQL (Recommended for Production)

### Install PostgreSQL

1. **Download PostgreSQL:**
   - Visit: https://www.postgresql.org/download/windows/
   - Download and install PostgreSQL
   - Remember the password you set for the `postgres` user

2. **Start PostgreSQL Service:**
   ```powershell
   # Check if service exists
   Get-Service -Name "*postgresql*"
   
   # Start the service (replace with actual service name)
   Start-Service postgresql-x64-XX  # Replace XX with version
   ```

3. **Create Database:**
   ```sql
   -- Connect to PostgreSQL (using psql or pgAdmin)
   CREATE DATABASE postmeeting;
   ```

4. **Update .env file:**
   Create `backend/.env`:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/postmeeting
   ```

### Verify Connection

```bash
# Test connection (if psql is in PATH)
psql -U postgres -h localhost -d postmeeting
```

## Option 2: Use SQLite for Development (Quick Start)

If you want to get started quickly without PostgreSQL, you can use SQLite:

### Update Configuration

1. **Update `backend/app/core/config.py`:**
   ```python
   # Change this line:
   DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postmeeting"
   
   # To:
   DATABASE_URL: str = "sqlite+aiosqlite:///./postmeeting.db"
   ```

2. **Update `backend/app/core/database.py`:**
   ```python
   # Change from asyncpg to aiosqlite
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
   
   # Update engine creation
   engine = create_async_engine(
       settings.DATABASE_URL,
       echo=True,
       future=True,
   )
   ```

3. **Install SQLite driver:**
   ```bash
   pip install aiosqlite
   ```

4. **Update `backend/requirements.txt`:**
   Add: `aiosqlite==0.19.0`

### Limitations of SQLite

- ⚠️ SQLite doesn't support all PostgreSQL features
- ⚠️ Not recommended for production
- ✅ Good for development and testing

## Option 3: Use Docker PostgreSQL (Recommended)

### Quick Start with Docker

1. **Run PostgreSQL in Docker:**
   ```bash
   docker run --name postmeeting-db \
     -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=postmeeting \
     -p 5432:5432 \
     -d postgres:15
   ```

2. **Update .env:**
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/postmeeting
   ```

3. **Run migrations:**
   ```bash
   cd backend
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

## Troubleshooting

### Check if PostgreSQL is Running

```powershell
# Windows - Check services
Get-Service | Where-Object {$_.Name -like "*postgres*"}

# Check if port 5432 is listening
netstat -an | findstr :5432
```

### Common Issues

1. **Port 5432 already in use:**
   - Another PostgreSQL instance might be running
   - Change port in connection string

2. **Authentication failed:**
   - Check username/password in connection string
   - Verify `pg_hba.conf` allows local connections

3. **Database doesn't exist:**
   - Create it: `CREATE DATABASE postmeeting;`

### Test Connection Manually

```python
# test_db.py
import asyncio
import asyncpg

async def test():
    try:
        conn = await asyncpg.connect(
            'postgresql://postgres:postgres@localhost:5432/postmeeting'
        )
        print("✅ Connection successful!")
        await conn.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")

asyncio.run(test())
```

## Recommended: Docker Setup

For the easiest setup, use Docker:

```bash
# Start PostgreSQL
docker run --name postmeeting-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=postmeeting \
  -p 5432:5432 \
  -d postgres:15

# Stop when done
docker stop postmeeting-db

# Start again
docker start postmeeting-db
```

Then run migrations:
```bash
cd backend
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

