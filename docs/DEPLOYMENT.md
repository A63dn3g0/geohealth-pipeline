# GeoHealth Pipeline - Deployment Guide

This document covers deployment options for the GeoHealth pipeline.

## Table of Contents

- [Local Development](#local-development)
- [Docker Compose Deployment](#docker-compose-deployment)
- [Production Deployment](#production-deployment)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Monitoring & Logging](#monitoring--logging)
- [Troubleshooting](#troubleshooting)

## Local Development

### Prerequisites

- Python 3.8+
- PostgreSQL 12+ with PostGIS extension (optional)
- Git

### Setup

1. Clone the repository
```bash
git clone https://github.com/your-org/geohealth-pipeline.git
cd geohealth-pipeline
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -e ".[dev]"
```

4. Run demo mode
```bash
python geohealth_pipeline_Project.py --demo
```

5. Run tests
```bash
pytest -v
```

## Docker Compose Deployment

### Quick Start

```bash
# Copy environment file
cp .env.example .env
# Edit .env with your settings
nano .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Services

- **PostgreSQL/PostGIS** (port 5432): Database backend
- **API** (port 8000): FastAPI REST endpoints
- **Dashboard** (port 8501): Streamlit web interface

### Verify Deployment

```bash
# Check service health
docker-compose ps

# API health check
curl http://localhost:8000/docs

# Dashboard access
open http://localhost:8501
```

## Production Deployment

### Using Production Compose File

```bash
cp .env.example .env

# Edit for production
nano .env
export ENVIRONMENT=production
export DEBUG=false

# Build and deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Prerequisites

- Docker & Docker Compose
- SSL certificates (for HTTPS)
- Reverse proxy (Nginx/Apache) - optional
- Backup strategy for database

### Recommended Architecture

```
┌─────────────────────────────────────────┐
│         Nginx/HAProxy (Reverse Proxy)   │
├─────────────────────────────────────────┤
│                                         │
├─────────────────┬───────────────────────┤
│                 │                       │
│   API (8000)    │   Dashboard (8501)    │
│                 │                       │
├─────────────────┴───────────────────────┤
│                                         │
│   PostgreSQL/PostGIS Database (5432)    │
│                                         │
└─────────────────────────────────────────┘
```

### Security Considerations

1. **Secrets Management**
   - Use `.env` file (not in git)
   - Use Docker secrets in production
   - Rotate passwords regularly

2. **Database**
   - Enable SSL connections
   - Restrict network access
   - Regular backups

3. **API**
   - Use HTTPS only
   - Enable CORS appropriately
   - Implement rate limiting
   - Add authentication/authorization

4. **Monitoring**
   - Set up logging aggregation
   - Monitor database performance
   - Track API response times
   - Alert on failures

## Environment Configuration

Create `.env` file from template:

```bash
cp .env.example .env
```

**Critical Variables:**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_PASSWORD` | ✅ | - | Database password |
| `POSTGRES_USER` | | geohealth | Database user |
| `POSTGRES_DB` | | geohealth | Database name |
| `ENVIRONMENT` | | development | `development` or `production` |
| `DEBUG` | | false | Enable debug mode |
| `LOG_LEVEL` | | INFO | Logging level |
| `API_WORKERS` | | 4 | Number of API workers |

## Database Setup

### Initial Schema

The database schema is initialized automatically from `docs/schema.sql` when using Docker Compose.

### Manual Setup

```bash
# Connect to database
psql -h localhost -U geohealth -d geohealth

# Run schema setup
\i docs/schema.sql

# Verify
\dt  # List tables
\dx # List extensions
```

### Backup & Restore

```bash
# Backup
docker-compose exec db pg_dump -U geohealth geohealth > backup.sql

# Restore
docker-compose exec -T db psql -U geohealth geohealth < backup.sql
```

## Monitoring & Logging

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f dashboard
docker-compose logs -f db

# Last N lines
docker-compose logs --tail 50
```

### Health Checks

Services include health checks:

- **API:** GET `/` endpoint (200 OK)
- **Database:** `pg_isready` command
- **Dashboard:** Process monitoring

```bash
# Check status
docker-compose ps
```

### Performance Monitoring

Monitor resource usage:

```bash
# CPU, memory, network
docker stats

# Specific container
docker stats geohealth-api
```

## Troubleshooting

### Database Connection Issues

```bash
# Test connection
docker-compose exec api python -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://geohealth:password@db:5432/geohealth')
print(engine.execute('SELECT 1'))
"
```

### API Not Responding

```bash
# Check logs
docker-compose logs api

# Restart service
docker-compose restart api

# Check health
curl http://localhost:8000/
```

### Dashboard Not Loading

```bash
# Check logs
docker-compose logs dashboard

# Restart
docker-compose restart dashboard

# Check database connection
docker-compose exec dashboard python -c "import streamlit; print('OK')"
```

### Performance Issues

1. **Database slow:** Check indexes and queries
2. **API slow:** Increase workers, check CPU/memory
3. **Memory leak:** Monitor with `docker stats`

### Resetting Everything

```bash
# Stop and remove containers, volumes, networks
docker-compose down -v

# Clean up dangling images
docker image prune

# Start fresh
docker-compose up -d
```

## Production Checklist

- [ ] Environment variables set correctly
- [ ] Database backups configured
- [ ] SSL certificates installed
- [ ] Reverse proxy configured
- [ ] Monitoring and alerting set up
- [ ] Logging aggregation enabled
- [ ] Database password changed from default
- [ ] API rate limiting configured
- [ ] CORS properly restricted
- [ ] Health checks passing
- [ ] Load testing completed
- [ ] Disaster recovery plan documented

## Advanced Topics

### Scaling

For high-traffic scenarios:

1. **Multiple API instances** behind load balancer
2. **Database replication** for read-heavy workloads
3. **Caching layer** (Redis) for frequently accessed data

### CI/CD Integration

GitHub Actions workflow automatically:
- Runs tests
- Builds Docker image
- Pushes to registry
- Deploys to staging/production

See `.github/workflows/tests.yml`

### Custom Configuration

Extend `docker-compose.yml` for your needs:

```bash
# Use multiple compose files
docker-compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.custom.yml up -d
```

## Support & Issues

- GitHub Issues: https://github.com/your-org/geohealth-pipeline/issues
- Documentation: https://geohealth-pipeline.readthedocs.io
- Email: support@example.com
