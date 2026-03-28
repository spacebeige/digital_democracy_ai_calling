# Docker Deployment Guide for Meera Multilingual Grievance System

## Overview

This guide provides instructions for containerizing and deploying the Meera multilingual grievance processing system using Docker and Docker Compose.

## Files Included

- **Dockerfile**: Production-ready Docker image build configuration
- **docker-compose.yml**: Production deployment orchestration
- **docker-compose.dev.yml**: Development environment with debugging tools
- **.dockerignore**: Excludes unnecessary files from Docker build context

## Quick Start (Development)

### 1. Clone and Setup

```bash
cd /home/parth/Desktop/delhi
```

### 2. Copy Environment Configuration

```bash
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 3. Run Development Environment

```bash
# Start all services (with debugging tools)
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f meera-main
```

### 4. Access Services

- **Main API**: http://localhost:8000
- **pgAdmin (Database)**: http://localhost:5050 (admin@meera.local / admin123)
- **Redis Commander**: http://localhost:8081

## Production Deployment

### 1. Build Docker Image

```bash
# Build the image
docker build -t meera-app:latest .

# Or with version tag
docker build -t meera-app:v1.0 .
```

### 2. Configure Environment

```bash
# Copy and customize .env file
cp .env.example .env
nano .env

# Ensure these are set:
# - GROQ_API_KEY
# - SARVAM_API_KEY (optional)
# - ELEVENLABS_API_KEY (optional)
# - DB_PASSWORD (change from default!)
```

### 3. Deploy Production Stack

```bash
# Start services
docker-compose up -d

# Verify all services are healthy
docker-compose ps

# Check logs
docker-compose logs -f
```

### 4. Access the Application

```bash
# Test the API
curl http://localhost:8000/health

# Submit a test complaint (via FastAPI endpoint)
curl -X POST http://localhost:8000/api/complaint \
  -H "Content-Type: application/json" \
  -d '{
    "text": "मेरा बिजली बिल बहुत ज्यादा आया है",
    "language": "hi"
  }'
```

## Docker Operations

### View Running Containers

```bash
docker-compose ps
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f meera-main

# Last 100 lines
docker-compose logs --tail 100
```

### Stop Services

```bash
# Stop (keeps data)
docker-compose stop

# Stop and remove containers (keeps volumes)
docker-compose down

# Complete cleanup (removes everything)
docker-compose down -v
```

### Execute Commands in Container

```bash
# Run Python commands
docker-compose exec meera-main python test_meera_direct.py

# Run bash shell
docker-compose exec meera-main bash

# Check database
docker-compose exec postgres psql -U meera -d grievances -c "SELECT * FROM complaints;"
```

## Configuration

### Environment Variables

Key variables (in .env):

```
# API Keys
GROQ_API_KEY=gsk_your_key_here
SARVAM_API_KEY=your_sarvam_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here

# Database
DB_USER=meera
DB_PASSWORD=meera123  # Change in production!
DATABASE_URL=postgresql://meera:meera123@postgres:5432/grievances

# System
STT_CONFIDENCE_THRESHOLD=0.3
TTS_PRIMARY=groq
LOG_LEVEL=INFO
```

### Port Mappings

| Service | Port | Purpose |
|---------|------|---------|
| Meera API | 8000 | Main application API |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache/session management |
| pgAdmin | 5050 | Database UI (dev only) |
| Redis Commander | 8081 | Cache UI (dev only) |

### Volume Mounts

```
volumes/
├── postgres_data/       # Database persistence
├── redis_data/          # Cache persistence
├── ./outputs/           # Grievance recordings & JSON
└── ./awaaz/             # Configuration files
```

## Troubleshooting

### Containers Won't Start

```bash
# Check specific service logs
docker-compose logs meera-main

# Inspect container
docker inspect meera-app

# Check resource constraints
docker stats
```

### Database Connection Failed

```bash
# Verify PostgreSQL is running
docker-compose exec postgres pg_isready

# Create database if missing
docker-compose exec postgres psql -U meera -c "CREATE DATABASE grievances;"
```

### Audio/Microphone Issues

Enable host audio device access (Linux):

```yaml
# In docker-compose.yml, add to meera-main service:
devices:
  - /dev/snd:/dev/snd

# Or use privileged mode:
privileged: true
```

### Out of Memory

Increase memory limit in docker-compose.yml:

```yaml
deploy:
  resources:
    limits:
      memory: 8G
```

## Multi-Architecture Build (ARM/x86)

Build for multiple architectures:

```bash
# Install buildx
docker buildx create --name mybuilder
docker buildx use mybuilder

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t meera-app:latest \
  --push .
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker image
        run: docker build -t meera-app:${{ github.sha }} .
      
      - name: Run tests
        run: docker run meera-app:${{ github.sha }} python -m pytest
      
      - name: Push to registry
        run: |
          docker tag meera-app:${{ github.sha }} registry.example.com/meera-app:latest
          docker push registry.example.com/meera-app:latest
```

## Health Checks

### Check Service Health

```bash
# API health
curl http://localhost:8000/health

# Database health
docker-compose exec postgres pg_isready

# Redis health
docker-compose exec redis redis-cli ping

# Check all services
docker-compose ps
```

### Custom Health Metrics

```bash
# View container metrics
docker stats

# View resource usage
docker-compose exec meera-main ps aux
```

## Backup and Restore

### Backup Database

```bash
# Export database
docker-compose exec postgres pg_dump -U meera grievances > backup.sql

# Or backup volume
docker run --rm -v meera_postgres_data:/data \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/postgres_backup.tar.gz /data
```

### Restore Database

```bash
# Import database
docker-compose exec -T postgres psql -U meera grievances < backup.sql

# Or restore volume
docker run --rm -v meera_postgres_data:/data \
  -v $(pwd):/backup \
  ubuntu tar xzf /backup/postgres_backup.tar.gz -C /
```

## Performance Optimization

### Resource Limits

```yaml
# In docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

### Network Optimization

```yaml
services:
  meera-main:
    networks:
      - meera-network
    
networks:
  meera-network:
    driver: bridge
```

## Security Considerations

1. **Change Default Passwords**
   - Database: Update DB_PASSWORD
   - pgAdmin: Change default credentials

2. **Secrets Management**
   - Use Docker Secrets for production
   - Never commit .env files to git
   - Use separate .env.production

3. **Network Security**
   - Use reverse proxy (Nginx included)
   - Enable SSL/TLS certificates
   - Restrict port access

4. **API Keys**
   - Rotate API keys regularly
   - Use environment variables (never hardcode)
   - Implement API rate limiting

## Production Checklist

- [ ] All API keys configured and validated
- [ ] Database password changed from default
- [ ] SSL/TLS certificates installed
- [ ] Backups configured and tested
- [ ] Monitoring and logging setup
- [ ] Resource limits defined
- [ ] Health checks enabled
- [ ] Docker registry credentials setup
- [ ] Network policies configured
- [ ] Tested failover scenarios

## Additional Resources

- Docker Docs: https://docs.docker.com/
- Docker Compose Docs: https://docs.docker.com/compose/
- PostgreSQL Docker: https://hub.docker.com/_/postgres
- Redis Docker: https://hub.docker.com/_/redis

## Support

For issues or questions:
1. Check Docker logs: `docker-compose logs`
2. Verify environment configuration: `cat .env`
3. Run health checks: `docker-compose ps`
4. Check resource usage: `docker stats`
