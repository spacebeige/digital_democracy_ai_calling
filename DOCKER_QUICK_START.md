# 🐳 Docker Quick Start Guide

## 5-Minute Setup

### Step 1: Verify Docker Installation

```bash
docker --version
docker-compose --version
```

### Step 2: Setup Environment

```bash
cd /home/parth/Desktop/delhi

# Create .env file (one-time)
./docker-manager.sh setup

# Edit with your API keys
nano .env
```

### Step 3: Build and Start

```bash
# Build image
./docker-manager.sh build

# Start services (production)
./docker-manager.sh start prod

# Or development (with debugging tools)
./docker-manager.sh start dev
```

### Step 4: Verify Services

```bash
# Check status
./docker-manager.sh status

# Run health check
./docker-manager.sh health
```

## ✨ What You Get

### Production (docker-compose.yml)

- **Meera Main API** (port 8000)
- **PostgreSQL** (port 5432) - Stores all complaints
- **Redis** (port 6379) - Session cache
- **Nginx** (port 80/443) - Reverse proxy

### Development (docker-compose.dev.yml)

Everything above, plus:

- **pgAdmin** (port 5050) - Database management UI
- **Redis Commander** (port 8081) - Cache inspection UI

## 🚀 Common Commands

```bash
cd /home/parth/Desktop/delhi

# View service status
./docker-manager.sh status

# View logs
./docker-manager.sh logs meera-main
./docker-manager.sh logs postgres
./docker-manager.sh logs redis

# Run tests
./docker-manager.sh test

# Open shell in container
./docker-manager.sh shell meera-main
./docker-manager.sh shell postgres

# Backup database
./docker-manager.sh backup

# Restore database
./docker-manager.sh restore backups/backup_20260327_133530.sql

# Stop services
./docker-manager.sh stop

# Full cleanup (removes everything)
./docker-manager.sh clean
```

## 🔌 Access Services

### Production

| Service | URL | Purpose |
|---------|-----|---------|
| API | http://localhost:8000 | Main application |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| Health | http://localhost:8000/health | Health check endpoint |

### Development (dev mode only)

| Service | URL | Credentials |
|---------|-----|-------------|
| pgAdmin | http://localhost:5050 | admin@meera.local / admin123 |
| Redis Commander | http://localhost:8081 | - |
| API | http://localhost:8000 | - |

## 📝 API Usage Examples

### Submit a Complaint

```bash
curl -X POST http://localhost:8000/api/complaint \
  -H "Content-Type: application/json" \
  -d '{
    "text": "मेरा बिजली बिल बहुत ज्यादा आया है",
    "language": "hi"
  }'
```

### Get Complaints by Urgency

```bash
curl http://localhost:8000/api/complaints?urgency=CRITICAL
```

### Get Complaint Status

```bash
curl http://localhost:8000/api/complaint/123e4567-e89b-12d3-a456-426614174000
```

## 🔍 Debugging

### View Application Logs

```bash
# Live logs
./docker-manager.sh logs meera-main

# Last 100 lines
docker-compose logs --tail 100 meera-main

# Save to file
docker-compose logs meera-main > logs.txt
```

### Execute Commands in Container

```bash
# Run Python script
./docker-manager.sh shell meera-main
python test_meera_direct.py

# Check database
docker-compose exec postgres psql -U meera -d grievances
SELECT * FROM complaints;

# Check Redis
docker-compose exec redis redis-cli
KEYS *
GET session_id
```

### Check Resource Usage

```bash
# View container stats
docker stats

# Specific container
docker stats meera-app
```

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check logs
./docker-manager.sh logs meera-main

# Check resources
docker stats

# Restart services
docker-compose restart
```

### Database Connection Error

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection
docker-compose exec postgres pg_isready

# View PostgreSQL logs
docker-compose logs postgres
```

### Out of Memory

Increase Docker memory limit in docker-compose.yml:

```yaml
deploy:
  resources:
    limits:
      memory: 8G  # Increase from 4G
```

### Port Already in Use

Find and stop conflicting service:

```bash
# Check port
lsof -i :8000

# Kill process (if not Docker)
kill -9 <PID>
```

## 🔄 Update Workflow

### Deploy New Code

```bash
# Pull latest changes
git pull origin main

# Rebuild image
./docker-manager.sh build

# Restart services
docker-compose restart meera-main
```

### Database Migrations

```bash
# Backup first
./docker-manager.sh backup

# Apply migrations
docker-compose exec meera-main python -m alembic upgrade head

# Verify
./docker-manager.sh health
```

## 📦 Production Deployment

### Pre-Production Checklist

- [ ] All API keys configured
- [ ] Database password changed from default
- [ ] Backups configured and tested
- [ ] SSL certificates installed
- [ ] Resource limits defined
- [ ] Health checks enabled
- [ ] Logging configured

### Deploy to Production

```bash
# Setup production environment
cp .env.example .env
# Edit .env with production values
nano .env

# Use production compose file
docker-compose -f docker-compose.yml up -d

# Verify
./docker-manager.sh health
```

### Monitor Production

```bash
# Check services
docker-compose ps

# View logs (tail last 50 lines)
docker-compose logs --tail 50 -f

# Monitor resources
docker stats

# Backup database regularly
0 2 * * * /home/parth/Desktop/delhi/docker-manager.sh backup
```

## 🛠️ Configuration

### Change API Keys

```bash
# Stop services
./docker-manager.sh stop

# Edit .env
nano .env

# Restart services
./docker-manager.sh start prod
```

### Change Ports

Edit docker-compose.yml:

```yaml
services:
  meera-main:
    ports:
      - "9000:8000"  # Changed from 8000
```

### Change Database Password

```bash
# Stop services
./docker-manager.sh stop

# Edit .env
DB_PASSWORD=your_secure_password

# Remove old data (be careful!)
docker-compose down -v

# Start fresh
./docker-manager.sh start prod
```

## 📚 Full Documentation

See [DOCKER_DEPLOYMENT_GUIDE.md](DOCKER_DEPLOYMENT_GUIDE.md) for complete Docker documentation.

## ❓ Getting Help

```bash
# Show all commands
./docker-manager.sh help

# View specific service logs
./docker-manager.sh logs postgres

# Open shell to investigate
./docker-manager.sh shell meera-main
```

## 🎯 Next Steps

1. ✅ Setup environment: `./docker-manager.sh setup`
2. ✅ Build image: `./docker-manager.sh build`
3. ✅ Start services: `./docker-manager.sh start dev`
4. ✅ Run tests: `./docker-manager.sh test`
5. ✅ Access API: http://localhost:8000/docs

---

**Happy Deploying!** 🚀

For issues or questions, check the logs:
```bash
./docker-manager.sh logs meera-main
```
