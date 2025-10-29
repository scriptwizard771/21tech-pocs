#!/bin/bash

# Production Deployment Script for Django + Nginx + Docker

echo "🚀 Starting production deployment..."

# Navigate to project directory
cd "$(dirname "$0")"

# Generate SSL certificates if they don't exist
if [ ! -f "../twenty_one_tech_pocs/cert.pem" ] || [ ! -f "../twenty_one_tech_pocs/key.pem" ]; then
    echo "📜 Generating SSL certificates..."
    cd ../twenty_one_tech_pocs
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
        -subj "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=54.219.76.120"
    cd ../resources
    echo "✅ SSL certificates generated"
else
    echo "✅ SSL certificates already exist"
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Remove old images (optional - uncomment if you want fresh builds)
# echo "🗑️ Removing old images..."
# docker-compose -f docker-compose.prod.yml down --rmi all

# Build and start production containers
echo "🔨 Building and starting production containers..."
docker-compose -f docker-compose.prod.yml up --build -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
docker-compose -f docker-compose.prod.yml ps

# Test HTTPS endpoint
echo "🧪 Testing HTTPS endpoint..."
if curl -k -s -o /dev/null -w "%{http_code}" https://54.219.76.120:8001/ | grep -q "200\|301\|302"; then
    echo "✅ HTTPS endpoint is responding!"
else
    echo "❌ HTTPS endpoint is not responding. Check logs with: docker-compose -f docker-compose.prod.yml logs"
fi

echo ""
echo "🎉 Deployment complete!"
echo "📱 Your API is available at: https://54.219.76.120:8001/"
echo "📊 View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "🛑 Stop services: docker-compose -f docker-compose.prod.yml down"
echo ""
echo "🔧 Production Features Enabled:"
echo "   ✅ Gunicorn WSGI server"
echo "   ✅ Nginx reverse proxy"
echo "   ✅ SSL/TLS encryption"
echo "   ✅ Auto HTTP to HTTPS redirect"
echo "   ✅ Static/media file serving"
echo "   ✅ Security headers"
echo "   ✅ Container restart policies" 