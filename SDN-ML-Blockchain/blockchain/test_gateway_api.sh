#!/bin/bash
# Test script for Gateway API

BASE_URL="http://localhost:3001/api/v1"
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "========================================="
echo "Gateway API Test Suite"
echo "========================================="

# 1. Health Check
echo -e "\n${GREEN}1. Health Check${NC}"
curl -s http://localhost:3001/health | jq .

# 2. Record Attack Event
echo -e "\n${GREEN}2. Recording Attack Event${NC}"
curl -s -X POST $BASE_URL/events \
  -H "Content-Type: application/json" \
  -d '{
    "switch_id": "s2",
    "event_type": "attack_detected",
    "timestamp": '$(date +%s)',
    "trust_score": 0.2,
    "action": "blocked",
    "details": {"src_ip": "10.0.0.3", "attack_type": "SYN_FLOOD"}
  }' | jq .

# 3. Record Normal Event
echo -e "\n${GREEN}3. Recording Normal Event${NC}"
curl -s -X POST $BASE_URL/events \
  -H "Content-Type: application/json" \
  -d '{
    "switch_id": "s2",
    "event_type": "normal_traffic",
    "timestamp": '$(date +%s)',
    "trust_score": 0.98,
    "action": "allow",
    "details": {"src_ip": "10.0.0.1"}
  }' | jq .

# 4. Query Trust Log
echo -e "\n${GREEN}4. Querying Trust Log for s1${NC}"
curl -s $BASE_URL/trust/s1 | jq .

echo -e "\n${GREEN}5. Querying Trust Log for s2${NC}"
curl -s $BASE_URL/trust/s2 | jq .

# 6. Query Recent Attacks
echo -e "\n${GREEN}6. Querying Recent Attacks${NC}"
curl -s "$BASE_URL/attacks/recent?timeWindow=3600" | jq .

# 7. Check Coordinated Attack
echo -e "\n${GREEN}7. Checking Coordinated Attack${NC}"
curl -s "$BASE_URL/attacks/coordinated?timeWindow=300&threshold=2" | jq .

# 8. Get Mitigation Action
echo -e "\n${GREEN}8. Getting Mitigation Action Recommendation${NC}"
curl -s -X POST $BASE_URL/mitigation/action \
  -H "Content-Type: application/json" \
  -d '{"switch_id": "s2", "confidence": 0.95}' | jq .

echo -e "\n========================================="
echo -e "${GREEN}All Tests Completed!${NC}"
echo "========================================="
