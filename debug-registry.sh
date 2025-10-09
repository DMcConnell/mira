#!/bin/bash

# Script to debug Docker registry connectivity

REGISTRY="${1:-registry.mesgexchange.io}"

echo "=== Docker Registry Debug Tool ==="
echo "Testing registry: $REGISTRY"
echo ""

# 1. Check DNS resolution
echo "1. Checking DNS resolution..."
if host "$REGISTRY" > /dev/null 2>&1; then
    echo "✓ DNS resolves"
    host "$REGISTRY"
else
    echo "✗ DNS resolution failed"
fi
echo ""

# 2. Check network connectivity
echo "2. Checking network connectivity..."
if ping -c 3 "$REGISTRY" > /dev/null 2>&1; then
    echo "✓ Host is reachable"
else
    echo "✗ Host unreachable (may be blocked or not exist)"
fi
echo ""

# 3. Check HTTPS connectivity
echo "3. Checking HTTPS connectivity..."
if curl -m 10 -s "https://$REGISTRY/v2/" > /dev/null 2>&1; then
    echo "✓ HTTPS endpoint accessible"
else
    echo "✗ HTTPS endpoint not accessible"
fi
echo ""

# 4. Check Docker login status
echo "4. Checking Docker authentication..."
if docker login "$REGISTRY" --get-login > /dev/null 2>&1; then
    echo "✓ Authenticated to registry"
else
    echo "✗ Not authenticated - run: docker login $REGISTRY"
fi
echo ""

# 5. List available registries in Docker config
echo "5. Available registries in Docker config:"
if [ -f ~/.docker/config.json ]; then
    cat ~/.docker/config.json | grep -A 5 "auths"
else
    echo "No Docker config found"
fi
echo ""

echo "=== Common Solutions ==="
echo "1. Use Docker Hub instead: ./build.sh --publish v1.0.0 --registry docker.io/<your-username> frontend"
echo "2. Use GitHub Container Registry: ./build.sh --publish v1.0.0 --registry ghcr.io/<your-username> frontend"
echo "3. Use a local registry: docker run -d -p 5000:5000 --name registry registry:2"
echo "   Then: ./build.sh --publish v1.0.0 --registry localhost:5000 frontend"
echo "4. Skip publishing for local dev: ./build.sh frontend"

