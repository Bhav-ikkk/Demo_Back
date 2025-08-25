# 🚀 AI Product Council Backend - Deployment Guide

This guide covers deploying your AI Product Council Backend for both local development and production environments.

## 📋 Prerequisites

### Required
- **Google API Key**: For Gemini AI integration
- **Python 3.11+**: For local development
- **Docker Desktop**: For production deployment

### Optional
- **PostgreSQL**: For production database (SQLite used locally)
- **Redis**: For caching and rate limiting
- **Domain & SSL**: For production HTTPS

## 🏠 Local Development Deployment

### Quick Start (Recommended)

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Set up environment**:
   ```bash
   # Copy environment template
   Copy-Item env.example .env
   
   # Edit .env with your Google API key
   notepad .env
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the server**:
   ```bash
   python run_local.py
   ```

### Manual Setup

1. **Set environment variables**:
   ```powershell
   $env:GOOGLE_API_KEY="your_actual_api_key_here"
   ```

2. **Start with uvicorn**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Local Development Features

- ✅ **Auto-reload**: Code changes restart server automatically
- ✅ **SQLite Database**: No external database setup required
- ✅ **Local Redis**: Optional (falls back to memory if not available)
- ✅ **CORS**: Configured for localhost frontend development
- ✅ **Hot Reload**: Fast development iteration

## 🐳 Production Deployment with Docker

### Quick Deployment

1. **Set up production environment**:
   ```bash
   # Copy production environment template
   Copy-Item env.prod.example .env.prod
   
   # Edit with your production values
   notepad .env.prod
   ```

2. **Deploy with PowerShell script**:
   ```powershell
   .\deploy.ps1
   ```

3. **Or deploy manually**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

### Production Features

- ✅ **Multi-container**: API, PostgreSQL, Redis, Nginx
- ✅ **Health checks**: Automatic service monitoring
- ✅ **Load balancing**: Nginx reverse proxy
- ✅ **Persistent data**: Database and cache persistence
- ✅ **Auto-restart**: Services restart on failure
- ✅ **Logging**: Centralized logging system

## 🌐 Frontend Integration

### Update Frontend Configuration

Once your backend is deployed, update your frontend to use the correct backend URL:

#### For Local Development
```javascript
// In your frontend API configuration
const API_BASE_URL = 'http://localhost:8000';
```

#### For Production
```javascript
// In your frontend API configuration
const API_BASE_URL = 'https://yourdomain.com'; // or your server IP
```

### CORS Configuration

The backend is configured to accept requests from common frontend development ports. Update `CORS_ORIGINS` in your environment file if needed:

```bash
# For local development
CORS_ORIGINS=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"]

# For production
CORS_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GOOGLE_API_KEY` | Google Gemini AI API key | - | ✅ |
| `DATABASE_URL` | Database connection string | SQLite local | ❌ |
| `REDIS_URL` | Redis connection string | localhost:6379 | ❌ |
| `SECRET_KEY` | Application secret key | auto-generated | ❌ |
| `CORS_ORIGINS` | Allowed frontend origins | localhost | ❌ |
| `LOG_LEVEL` | Logging verbosity | INFO | ❌ |

### Database Options

#### SQLite (Development)
```bash
DATABASE_URL=sqlite:///./ai_council.db
```

#### PostgreSQL (Production)
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_council
```

### Redis Options

#### Local Redis
```bash
REDIS_URL=redis://localhost:6379
```

#### Redis with Password
```bash
REDIS_URL=redis://:password@localhost:6379
```

## 📊 Monitoring & Health Checks

### Health Endpoints

- **API Health**: `GET /health`
- **Database Status**: Included in `/health`
- **Redis Status**: Included in `/health`

### Logs

#### View Docker Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f api
```

#### Log Locations
- **Application logs**: `logs/` directory
- **Nginx logs**: `logs/nginx/` directory
- **Database logs**: Docker container logs

## 🚨 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <PID> /F
```

#### 2. Docker Not Running
```bash
# Start Docker Desktop
# Or check Docker service
docker info
```

#### 3. Environment Variables Not Loaded
```bash
# Check if .env file exists
Get-ChildItem .env*

# Verify environment variables
echo $env:GOOGLE_API_KEY
```

#### 4. Database Connection Failed
```bash
# Check database container status
docker-compose -f docker-compose.prod.yml ps db

# Check database logs
docker-compose -f docker-compose.prod.yml logs db
```

#### 5. CORS Errors in Frontend
- Verify `CORS_ORIGINS` includes your frontend URL
- Check browser console for CORS error details
- Ensure backend is accessible from frontend

### Performance Issues

#### High Memory Usage
```bash
# Check container resource usage
docker stats

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

#### Slow Response Times
- Check database connection pool settings
- Verify Redis is working properly
- Monitor API response times in logs

## 🔒 Security Considerations

### Production Security

1. **Change Default Passwords**:
   - Update `POSTGRES_PASSWORD` and `REDIS_PASSWORD`
   - Use strong, unique passwords

2. **Secure Secret Key**:
   ```bash
   # Generate secure secret key
   openssl rand -hex 32
   ```

3. **Configure Firewall**:
   - Only expose necessary ports (80, 443, 8000)
   - Restrict access to database ports (5432, 6379)

4. **SSL/TLS**:
   - Obtain SSL certificates for your domain
   - Configure Nginx for HTTPS
   - Redirect HTTP to HTTPS

5. **Rate Limiting**:
   - Adjust `RATE_LIMIT_REQUESTS` based on your needs
   - Monitor for abuse patterns

## 📈 Scaling Considerations

### Horizontal Scaling

1. **Load Balancer**: Use Nginx or cloud load balancer
2. **Multiple API Instances**: Scale API containers
3. **Database Clustering**: PostgreSQL read replicas
4. **Redis Cluster**: For high availability

### Vertical Scaling

1. **Resource Limits**: Adjust Docker memory/CPU limits
2. **Database Tuning**: Optimize PostgreSQL settings
3. **Connection Pooling**: Adjust database pool size

## 🆘 Getting Help

### Debug Mode

Enable debug logging:
```bash
LOG_LEVEL=DEBUG
```

### Support Commands

```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# View real-time logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Complete reset
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d --build
```

### Health Check

Test your deployment:
```bash
# API health
curl http://localhost:8000/health

# API documentation
curl http://localhost:8000/docs

# Test endpoint
curl -X POST "http://localhost:8000/refine/sync" \
  -H "Content-Type: application/json" \
  -d '{"idea": "Test product idea"}'
```

---

**🎉 Your backend is now ready to power your AI Product Council frontend!**

For additional support, check the logs and use the health endpoints to diagnose any issues.
