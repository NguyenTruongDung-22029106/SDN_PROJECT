#!/bin/bash
###############################################################################
# Script kiểm tra trạng thái hệ thống
###############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  System Status Check${NC}"
echo -e "${BLUE}=========================================${NC}"

# Check Docker
echo -e "\n${YELLOW}Docker Status:${NC}"
if docker ps &> /dev/null; then
    echo -e "  ${GREEN}✓ Docker daemon running${NC}"
else
    echo -e "  ${RED}✗ Docker daemon not running${NC}"
fi

# Check Fabric Containers
echo -e "\n${YELLOW}Fabric Containers:${NC}"
CONTAINERS=("peer0.org1.example.com" "peer0.org2.example.com" "orderer.example.com")
for container in "${CONTAINERS[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        STATUS=$(docker inspect --format='{{.State.Status}}' ${container})
        echo -e "  ${GREEN}✓ ${container}: ${STATUS}${NC}"
    else
        echo -e "  ${RED}✗ ${container}: not running${NC}"
    fi
done

# Check Gateway
echo -e "\n${YELLOW}Gateway API:${NC}"
if curl -s http://localhost:3001/health > /dev/null 2>&1; then
    HEALTH=$(curl -s http://localhost:3001/health)
    echo -e "  ${GREEN}✓ Gateway running on port 3001${NC}"
    echo "    Response: ${HEALTH}"
    
    # Check if PID file exists
    if [ -f /tmp/sdn_gateway.pid ]; then
        PID=$(cat /tmp/sdn_gateway.pid)
        echo "    PID: ${PID}"
    fi
else
    echo -e "  ${RED}✗ Gateway not responding${NC}"
fi

# Check Ryu Controller
echo -e "\n${YELLOW}Ryu Controller:${NC}"
if pgrep -f "ryu-manager" > /dev/null; then
    RYU_PID=$(pgrep -f "ryu-manager")
    echo -e "  ${GREEN}✓ Ryu Controller running${NC}"
    echo "    PID: ${RYU_PID}"
    
    # Check if listening on port 6633
    if netstat -tln 2>/dev/null | grep -q ":6633"; then
        echo -e "    ${GREEN}✓ Listening on port 6633${NC}"
    fi
else
    echo -e "  ${RED}✗ Ryu Controller not running${NC}"
fi

# Check Mininet
echo -e "\n${YELLOW}Mininet:${NC}"
if pgrep -f "mininet" > /dev/null; then
    echo -e "  ${GREEN}✓ Mininet running${NC}"
else
    echo -e "  ${YELLOW}○ Mininet not started (start manually)${NC}"
fi

# Check Ports
echo -e "\n${YELLOW}Port Status:${NC}"
PORTS=(6633 3001 7051 9051 7050)
for port in "${PORTS[@]}"; do
    if netstat -tln 2>/dev/null | grep -q ":${port}"; then
        echo -e "  ${GREEN}✓ Port ${port} in use${NC}"
    else
        echo -e "  ${YELLOW}○ Port ${port} free${NC}"
    fi
done

# Auto-detect project root (parent directory of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Check ML Models
echo -e "\n${YELLOW}ML Models:${NC}"
RYU_DIR="${PROJECT_ROOT}/ryu_app"
if ls ${RYU_DIR}/ml_model_*.pkl 1> /dev/null 2>&1; then
    MODEL_COUNT=$(ls ${RYU_DIR}/ml_model_*.pkl | wc -l)
    echo -e "  ${GREEN}✓ ${MODEL_COUNT} ML models found${NC}"
    ls ${RYU_DIR}/ml_model_*.pkl | while read model; do
        echo "    - $(basename $model)"
    done
else
    echo -e "  ${RED}✗ No ML models found${NC}"
fi

# Check Data Directory Permissions
echo -e "\n${YELLOW}Data Directory:${NC}"
DATA_DIR="${PROJECT_ROOT}/data"
if [ -d "${DATA_DIR}" ]; then
    OWNER=$(stat -c '%U:%G' ${DATA_DIR})
    echo -e "  ${GREEN}✓ Directory exists${NC}"
    echo "    Owner: ${OWNER}"
    
    # Check CSV files
    if ls ${DATA_DIR}/*.csv 1> /dev/null 2>&1; then
        CSV_COUNT=$(ls ${DATA_DIR}/*.csv | wc -l)
        echo "    CSV files: ${CSV_COUNT}"
        
        # Check if writable
        if [ -w "${DATA_DIR}/switch_1_data.csv" ]; then
            echo -e "    ${GREEN}✓ CSV files writable${NC}"
        else
            echo -e "    ${RED}✗ CSV files not writable${NC}"
            echo "    Fix: sudo chown -R \$USER:\$USER ${DATA_DIR}"
        fi
    fi
else
    echo -e "  ${RED}✗ Data directory not found${NC}"
fi

# Summary
echo -e "\n${BLUE}=========================================${NC}"
RUNNING_COUNT=0
TOTAL_COUNT=5

# Count running services
docker ps --format '{{.Names}}' | grep -q "peer0.org1.example.com" && ((RUNNING_COUNT++))
docker ps --format '{{.Names}}' | grep -q "peer0.org2.example.com" && ((RUNNING_COUNT++))
docker ps --format '{{.Names}}' | grep -q "orderer.example.com" && ((RUNNING_COUNT++))
curl -s http://localhost:3001/health > /dev/null 2>&1 && ((RUNNING_COUNT++))
pgrep -f "ryu-manager" > /dev/null && ((RUNNING_COUNT++))

if [ $RUNNING_COUNT -eq $TOTAL_COUNT ]; then
    echo -e "${GREEN}✓ All core services running (${RUNNING_COUNT}/${TOTAL_COUNT})${NC}"
    echo -e "${GREEN}System is ready!${NC}"
elif [ $RUNNING_COUNT -gt 0 ]; then
    echo -e "${YELLOW}⚠ Partial system running (${RUNNING_COUNT}/${TOTAL_COUNT})${NC}"
    echo "Some services may need to be started"
else
    echo -e "${RED}✗ System not running (0/${TOTAL_COUNT})${NC}"
    echo "Run: bash scripts/start_system.sh"
fi

echo -e "${BLUE}=========================================${NC}"
