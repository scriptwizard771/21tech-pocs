#!/bin/bash
# Script to test and deploy the Docker fixes

echo "=== Docker Build Test Script ==="
echo "Testing different Dockerfile approaches..."

# Test 1: Minimal approach (no libmagic dependencies)
echo "1. Testing minimal Dockerfile..."
docker build -t test-minimal -f resources/dockerfile.prod.minimal . --no-cache
if [ $? -eq 0 ]; then
    echo "✅ Minimal build SUCCESSFUL"
    WORKING_DOCKERFILE="dockerfile.prod.minimal"
else
    echo "❌ Minimal build FAILED"
fi

# Test 2: Alpine approach
echo "2. Testing Alpine Dockerfile..."
docker build -t test-alpine -f resources/dockerfile.prod.alpine . --no-cache
if [ $? -eq 0 ]; then
    echo "✅ Alpine build SUCCESSFUL"
    WORKING_DOCKERFILE="dockerfile.prod.alpine"
else
    echo "❌ Alpine build FAILED"
fi

# Test 3: Main production Dockerfile
echo "3. Testing main production Dockerfile..."
docker build -t test-main -f resources/dockerfile.prod . --no-cache
if [ $? -eq 0 ]; then
    echo "✅ Main production build SUCCESSFUL"
    WORKING_DOCKERFILE="dockerfile.prod"
else
    echo "❌ Main production build FAILED"
fi

echo "=== Results ==="
if [ -n "$WORKING_DOCKERFILE" ]; then
    echo "✅ Working Dockerfile found: $WORKING_DOCKERFILE"
    echo "Updating GitHub Actions to use this Dockerfile..."
    
    # Update GitHub Actions workflow
    sed -i "s/dockerfile.prod.minimal/$WORKING_DOCKERFILE/g" .github/workflows/main.yml
    
    echo "Ready to commit and push changes!"
    echo "Run: git add . && git commit -m 'Fix Docker build issues' && git push origin dev"
else
    echo "❌ No working Dockerfile found. Check the errors above."
fi

# Clean up test images
docker rmi test-minimal test-alpine test-main 2>/dev/null || true