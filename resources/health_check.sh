#!/bin/bash

# Health Check Script for Django Production Deployment
echo "🏥 Starting comprehensive health check..."
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Navigate to project directory
cd "$(dirname "$0")"

echo "1. 🐳 Checking Docker containers..."
docker-compose -f docker-compose.prod.yml ps
echo ""

echo "2. 🔍 Checking container health..."
# Check if all required containers are running
DJANGO_STATUS=$(docker-compose -f docker-compose.prod.yml ps -q django_app | wc -l)
NGINX_STATUS=$(docker-compose -f docker-compose.prod.yml ps -q nginx_proxy | wc -l)
ELASTICSEARCH_STATUS=$(docker-compose -f docker-compose.prod.yml ps -q elasticsearch | wc -l)

print_status $((DJANGO_STATUS > 0 ? 0 : 1)) "Django container"
print_status $((NGINX_STATUS > 0 ? 0 : 1)) "Nginx container"
print_status $((ELASTICSEARCH_STATUS > 0 ? 0 : 1)) "Elasticsearch container"
echo ""

echo "3. 🌐 Testing HTTPS connectivity..."
HTTP_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" https://54.219.76.120:8001/ 2>/dev/null)
if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 500 ]; then
    print_status 0 "HTTPS endpoint responding (HTTP $HTTP_CODE)"
else
    print_status 1 "HTTPS endpoint not responding (HTTP $HTTP_CODE)"
fi
echo ""

echo "4. 🧪 Testing API endpoints..."

# Test Equipment Entries API
echo "Testing Equipment Entries API..."
EQUIPMENT_API_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" \
  -X POST https://54.219.76.120:8001/api/equipment-entries/generate/test/ \
  -H "Content-Type: application/json" \
  -d '{"attribute": "category", "accepted_values": {}, "expected_values": []}' 2>/dev/null)

if [ "$EQUIPMENT_API_CODE" -ge 200 ] && [ "$EQUIPMENT_API_CODE" -lt 500 ]; then
    print_status 0 "Equipment Entries API (HTTP $EQUIPMENT_API_CODE)"
else
    print_status 1 "Equipment Entries API (HTTP $EQUIPMENT_API_CODE)"
fi

# Test Maintenance API
echo "Testing Maintenance API..."
MAINTENANCE_API_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" \
  -X POST https://54.219.76.120:8001/api/maintenance/process-document/ \
  -H "Content-Type: application/json" \
  -d '{"document_code": "HEALTH_CHECK", "create_in_eam": false}' 2>/dev/null)

if [ "$MAINTENANCE_API_CODE" -ge 200 ] && [ "$MAINTENANCE_API_CODE" -lt 500 ]; then
    print_status 0 "Maintenance API (HTTP $MAINTENANCE_API_CODE)"
else
    print_status 1 "Maintenance API (HTTP $MAINTENANCE_API_CODE)"
fi
echo ""

echo "5. 🔍 Testing Elasticsearch..."
ES_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://54.219.76.120:9201/_cluster/health 2>/dev/null)
print_status $((ES_STATUS == 200 ? 0 : 1)) "Elasticsearch health (HTTP $ES_STATUS)"
echo ""

echo "6. 📊 Checking system resources..."
echo "Memory usage:"
free -h
echo ""
echo "Disk usage:"
df -h | grep -E "(Filesystem|/dev/)"
echo ""

echo "7. 🔗 SSL Certificate info..."
echo | openssl s_client -connect 54.219.76.120:8001 -servername 54.219.76.120 2>/dev/null | openssl x509 -noout -dates 2>/dev/null
echo ""

echo "========================================"
echo "🏥 Health check complete!"
echo ""
echo "📱 Your API endpoints:"
echo "   • Main API: https://54.219.76.120:8001/"
echo "   • Equipment: https://54.219.76.120:8001/api/equipment-entries/"
echo "   • Maintenance: https://54.219.76.120:8001/api/maintenance/"
echo "   • Service Manuals: https://54.219.76.120:8001/api/service-manuals/"
echo "   • Safety Procedures: https://54.219.76.120:8001/api/safety-procedures/"
echo "   • Training Manuals: https://54.219.76.120:8001/api/training-manuals/"
echo ""
echo "📋 Useful commands:"
echo "   • View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "   • Restart: docker-compose -f docker-compose.prod.yml restart"
echo "   • Stop: docker-compose -f docker-compose.prod.yml down" 