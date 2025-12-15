#!/bin/bash
###############################################################################
# Script khắc phục lỗi thường gặp
###############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Auto-detect project root (parent directory of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo -e "${YELLOW}=========================================${NC}"
echo -e "${YELLOW}  Auto-fix Common Issues${NC}"
echo -e "${YELLOW}=========================================${NC}"

# 1. Fix Permission Denied on CSV files
echo -e "\n${YELLOW}[1] Fixing file permissions...${NC}"
if [ -d "${PROJECT_ROOT}/data" ]; then
    sudo chown -R $USER:$USER "${PROJECT_ROOT}/data" 2>/dev/null || true
    chmod -R 664 "${PROJECT_ROOT}/data"/*.csv 2>/dev/null || true
    chmod 775 "${PROJECT_ROOT}/data" 2>/dev/null || true
    echo -e "  ${GREEN}✓ Fixed data directory permissions${NC}"
fi

if [ -d "${PROJECT_ROOT}/blockchain/wallet" ]; then
    chmod -R 755 "${PROJECT_ROOT}/blockchain/wallet" 2>/dev/null || true
    echo -e "  ${GREEN}✓ Fixed wallet permissions${NC}"
fi

# 2. Re-import Blockchain Identity
echo -e "\n${YELLOW}[2] Re-importing blockchain identity...${NC}"
cd "${PROJECT_ROOT}/blockchain"
if node import_identity.js 2>&1 | grep -q "Imported identity"; then
    echo -e "  ${GREEN}✓ Identity imported successfully${NC}"
else
    echo -e "  ${RED}✗ Failed to import identity${NC}"
    echo "  Check if Fabric network is running"
fi

# 3. Clear port conflicts
echo -e "\n${YELLOW}[3] Clearing port conflicts...${NC}"
PORTS=(6633 3001)
for port in "${PORTS[@]}"; do
    PID=$(lsof -ti:${port} 2>/dev/null)
    if [ ! -z "$PID" ]; then
        kill -9 $PID 2>/dev/null || sudo kill -9 $PID 2>/dev/null
        echo -e "  ${GREEN}✓ Freed port ${port} (killed PID: ${PID})${NC}"
    else
        echo -e "  ${GREEN}✓ Port ${port} is free${NC}"
    fi
done

# 4. Clean up stale Mininet processes
echo -e "\n${YELLOW}[4] Cleaning up Mininet...${NC}"
sudo mn -c 2>/dev/null
sudo killall -9 ovs-testcontroller 2>/dev/null || true
sudo killall -9 controller 2>/dev/null || true
echo -e "  ${GREEN}✓ Mininet cleaned${NC}"

# 5. Restart Docker if needed
echo -e "\n${YELLOW}[5] Checking Docker...${NC}"
if ! docker ps &> /dev/null; then
    echo "  Docker not responding, attempting restart..."
    sudo systemctl restart docker
    sleep 3
    if docker ps &> /dev/null; then
        echo -e "  ${GREEN}✓ Docker restarted${NC}"
    else
        echo -e "  ${RED}✗ Docker failed to start${NC}"
    fi
else
    echo -e "  ${GREEN}✓ Docker running${NC}"
fi

# 6. Clean Docker networks
echo -e "\n${YELLOW}[6] Cleaning Docker resources...${NC}"
docker network prune -f > /dev/null 2>&1
docker volume prune -f > /dev/null 2>&1
echo -e "  ${GREEN}✓ Docker cleanup complete${NC}"

# 7. Install missing npm packages
echo -e "\n${YELLOW}[7] Checking npm packages...${NC}"
cd "${PROJECT_ROOT}/blockchain"
if [ ! -d "node_modules" ]; then
    echo "  Installing npm packages..."
    npm install --silent
    echo -e "  ${GREEN}✓ npm packages installed${NC}"
else
    echo -e "  ${GREEN}✓ npm packages present${NC}"
fi

# 8. Check Python dependencies
echo -e "\n${YELLOW}[8] Checking Python dependencies...${NC}"
cd "${PROJECT_ROOT}"
MISSING_DEPS=()

python3 -c "import sklearn" 2>/dev/null || MISSING_DEPS+=("scikit-learn")
python3 -c "import pandas" 2>/dev/null || MISSING_DEPS+=("pandas")
python3 -c "import requests" 2>/dev/null || MISSING_DEPS+=("requests")

if [ ${#MISSING_DEPS[@]} -eq 0 ]; then
    echo -e "  ${GREEN}✓ All Python dependencies present${NC}"
else
    echo -e "  ${YELLOW}Missing packages: ${MISSING_DEPS[@]}${NC}"
    echo "  Installing..."
    pip3 install -q ${MISSING_DEPS[@]}
    echo -e "  ${GREEN}✓ Installed missing packages${NC}"
fi

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}  Auto-fix completed!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Now you can run:"
echo "  bash scripts/start_system.sh"
echo ""
