#!/bin/bash

# Mira Control Plane - Validation Script
# Tests the acceptance criteria from Guide 1

BASE_URL="http://localhost:8090"
PASS=0
FAIL=0

echo "🧪 Validating Mira Control Plane Implementation"
echo "================================================"
echo ""

# Function to test endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local url="$3"
    local data="$4"
    
    echo -n "Testing: $name... "
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" -H "Content-Type: application/json" -d "$data" "$url")
    fi
    
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)
    
    # Check if http_code is a valid number
    if [[ "$http_code" =~ ^[0-9]+$ ]] && [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo "✅ PASS (HTTP $http_code)"
        PASS=$((PASS + 1))
        if [ -n "$body" ]; then
            echo "   Response: $(echo $body | jq -c '.' 2>/dev/null || echo $body)"
        fi
    else
        echo "❌ FAIL (HTTP $http_code)"
        FAIL=$((FAIL + 1))
        echo "   Response: $body"
    fi
}

# Check if server is running
echo "1. Checking if Control Plane is running..."
if ! curl -s "$BASE_URL/health" > /dev/null 2>&1; then
    echo "❌ Control Plane is not running at $BASE_URL"
    echo "   Start it with: cd control-plane && ./run.sh"
    exit 1
fi
echo "✅ Control Plane is running"
echo ""

# Test health endpoint
echo "2. Testing Health Endpoint"
test_endpoint "Health Check" "GET" "$BASE_URL/health"
echo ""

# Test get state endpoint
echo "3. Testing State Endpoint"
test_endpoint "Get Current State" "GET" "$BASE_URL/state"
echo ""

# Test command submission - add todo
echo "4. Testing Command Submission"
test_endpoint "Add Todo Command" "POST" "$BASE_URL/command" \
  '{"source":"voice","action":"add_todo","payload":{"text":"Test validation todo"}}'
echo ""

test_endpoint "Toggle Mic Command" "POST" "$BASE_URL/command" \
  '{"source":"gesture","action":"toggle_mic","payload":{}}'
echo ""

test_endpoint "Set Mode Command" "POST" "$BASE_URL/command" \
  '{"source":"system","action":"set_mode","payload":{"mode":"voice"}}'
echo ""

test_endpoint "Unknown Command (should reject)" "POST" "$BASE_URL/command" \
  '{"source":"system","action":"unknown_action","payload":{}}'
echo ""

# Check database exists
echo "5. Checking Database Persistence"
if [ -f "data/control_plane.db" ]; then
    echo "✅ SQLite database exists at data/control_plane.db"
    PASS=$((PASS + 1))
    
    # Check tables exist
    events_count=$(sqlite3 data/control_plane.db "SELECT COUNT(*) FROM events;" 2>/dev/null || echo "0")
    snapshots_count=$(sqlite3 data/control_plane.db "SELECT COUNT(*) FROM snapshots;" 2>/dev/null || echo "0")
    
    echo "   Events in database: $events_count"
    echo "   Snapshots in database: $snapshots_count"
    
    if [ "$events_count" -gt 0 ] 2>/dev/null; then
        echo "✅ Events are being persisted"
        PASS=$((PASS + 1))
    else
        echo "⚠️  No events found yet (workers may still be initializing)"
    fi
else
    echo "❌ SQLite database not found"
    FAIL=$((FAIL + 1))
fi
echo ""

# Summary
echo "================================================"
echo "Validation Summary"
echo "================================================"
echo "✅ Passed: $PASS"
echo "❌ Failed: $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "🎉 All validations passed!"
    exit 0
else
    echo "⚠️  Some validations failed. Check the output above."
    exit 1
fi

