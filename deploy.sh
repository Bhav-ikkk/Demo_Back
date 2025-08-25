#!/bin/bash

# AI Product Council Backend Deployment Script
set -e

echo "🚀 Starting AI Product Council Backend Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    print_error ".env.prod file not found!"
    echo "Please copy env.prod.example to .env.prod and fill in your values:"
    echo "cp env.prod.example .env.prod"
    echo "Then edit .env.prod with your actual configuration values."
    exit 1
fi

# Load environment variables
print_status "Loading environment variables..."
source .env.prod

# Validate required environment variables
required_vars=("POSTGRES_PASSWORD" "REDIS_PASSWORD" "GOOGLE_API_KEY" "SECRET_KEY" "CORS_ORIGINS")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        print_error "Required environment variable $var is not set in .env.prod"
        exit 1
    fi
done

print_status "Environment variables validated successfully"

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs/nginx
mkdir -p init-db

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down --remove-orphans || true

# Build and start services
print_status "Building and starting services..."
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."
sleep 30

# Check service health
print_status "Checking service health..."

# Check API health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "✅ API is healthy"
else
    print_warning "⚠️  API health check failed, but continuing..."
fi

# Check database connection
if docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U postgres > /dev/null 2>&1; then
    print_status "✅ Database is healthy"
else
    print_warning "⚠️  Database health check failed, but continuing..."
fi

# Check Redis connection
if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_status "✅ Redis is healthy"
else
    print_warning "⚠️  Redis health check failed, but continuing..."
fi

# Show service status
print_status "Service status:"
docker-compose -f docker-compose.prod.yml ps

# Show logs
print_status "Recent logs:"
docker-compose -f docker-compose.prod.yml logs --tail=20

echo ""
print_status "🎉 Deployment completed successfully!"
echo ""
echo "📡 Your API is now available at:"
echo "   - Local: http://localhost:8000"
echo "   - Network: http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🏥 Health Check: http://localhost:8000/health"
echo ""
echo "🔧 Useful commands:"
echo "   - View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "   - Stop services: docker-compose -f docker-compose.prod.yml down"
echo "   - Restart services: docker-compose -f docker-compose.prod.yml restart"
echo ""
echo "⚠️  Remember to:"
echo "   - Update your frontend to use the correct backend URL"
echo "   - Configure CORS_ORIGINS in .env.prod for your frontend domain"
echo "   - Set up SSL certificates if deploying to production"
echo "   - Configure your firewall to allow traffic on port 8000"
