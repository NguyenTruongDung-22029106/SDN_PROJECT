#!/bin/bash
###############################################################################
# Script khởi động toàn bộ hệ thống SDN-ML-Blockchain
# Đảm bảo mọi thứ chạy đúng thứ tự và kiểm tra lỗi
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Auto-detect project root (parent directory of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FABRIC_ROOT="${PROJECT_ROOT}/fabric-samples/test-network"
BLOCKCHAIN_DIR="${PROJECT_ROOT}/blockchain"
RYU_DIR="${PROJECT_ROOT}/ryu_app"

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  SDN-ML-Blockchain System Startup${NC}"
echo -e "${BLUE}=========================================${NC}"

###############################################################################
# 1. Pre-flight Checks
###############################################################################
echo -e "\n${YELLOW}[1/6] Pre-flight checks...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${NC}"
    exit 1
fi

# Check Docker daemon
if ! docker ps &> /dev/null; then
    echo -e "${RED}✗ Docker daemon not running${NC}"
    echo "Start with: sudo systemctl start docker"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js not found${NC}"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python3 not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites OK${NC}"

###############################################################################
# 2. Cleanup old processes and networks
###############################################################################
echo -e "\n${YELLOW}[2/6] Cleaning up old processes...${NC}"

# Kill old Ryu processes
pkill -f "ryu-manager" 2>/dev/null || true
echo "  ✓ Stopped old Ryu controllers"

# Kill old Gateway processes
pkill -f "gateway_node_server.js" 2>/dev/null || true
echo "  ✓ Stopped old Gateway servers"

# Cleanup Mininet
sudo mn -c 2>/dev/null || true
echo "  ✓ Cleaned up Mininet"

# Stop old Fabric network
cd "${FABRIC_ROOT}"
./network.sh down 2>/dev/null || true
echo "  ✓ Stopped old Fabric network"

sleep 2

###############################################################################
# 3. Fix File Permissions
###############################################################################
echo -e "\n${YELLOW}[3/6] Fixing file permissions...${NC}"

# Fix data directory permissions
if [ -d "${PROJECT_ROOT}/data" ]; then
    sudo chown -R $USER:$USER "${PROJECT_ROOT}/data" 2>/dev/null || true
    chmod -R 664 "${PROJECT_ROOT}/data"/*.csv 2>/dev/null || true
    echo "  ✓ Fixed data directory permissions"
fi

# Fix blockchain wallet permissions
if [ -d "${BLOCKCHAIN_DIR}/wallet" ]; then
    chmod -R 755 "${BLOCKCHAIN_DIR}/wallet" 2>/dev/null || true
    echo "  ✓ Fixed wallet permissions"
fi

###############################################################################
# 4. Start Hyperledger Fabric Network
###############################################################################
echo -e "\n${YELLOW}[4/6] Starting Hyperledger Fabric network...${NC}"

cd "${FABRIC_ROOT}"

# Start network with CA
echo "  → Starting Fabric network..."
./network.sh up createChannel -c sdnchannel -ca

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to start Fabric network${NC}"
    exit 1
fi

# Deploy chaincode
echo "  → Deploying trustlog chaincode..."
./network.sh deployCC -ccn trustlog -ccp ../../blockchain/chaincode -ccl go -c sdnchannel

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to deploy chaincode${NC}"
    exit 1
fi

# Verify containers
PEER1_RUNNING=$(docker ps --filter "name=peer0.org1.example.com" --format "{{.Names}}" | grep -c "peer0.org1.example.com" || true)
PEER2_RUNNING=$(docker ps --filter "name=peer0.org2.example.com" --format "{{.Names}}" | grep -c "peer0.org2.example.com" || true)
ORDERER_RUNNING=$(docker ps --filter "name=orderer.example.com" --format "{{.Names}}" | grep -c "orderer.example.com" || true)

if [ "$PEER1_RUNNING" -eq 0 ] || [ "$PEER2_RUNNING" -eq 0 ] || [ "$ORDERER_RUNNING" -eq 0 ]; then
    echo -e "${RED}✗ Some containers failed to start${NC}"
    docker ps -a | grep hyperledger
    exit 1
fi

echo -e "${GREEN}✓ Fabric network is running${NC}"

###############################################################################
# 5. Setup and Start Gateway
###############################################################################
echo -e "\n${YELLOW}[5/6] Setting up Blockchain Gateway...${NC}"

cd "${BLOCKCHAIN_DIR}"

# Re-import identity to ensure it's fresh
echo "  → Importing fresh identity..."
node import_identity.js

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to import identity${NC}"
    exit 1
fi

# Check if npm packages are installed
if [ ! -d "node_modules" ]; then
    echo "  → Installing npm packages..."
    npm install --silent
fi

# Start Gateway in background
echo "  → Starting Gateway on port 3001..."
mkdir -p "${PROJECT_ROOT}/logs"
nohup node gateway_node_server.js > "${PROJECT_ROOT}/logs/gateway.log" 2>&1 &
GATEWAY_PID=$!

# Wait for Gateway to start
sleep 3

# Verify Gateway is running
if ! curl -s http://localhost:3001/health > /dev/null 2>&1; then
    echo -e "${RED}✗ Gateway failed to start${NC}"
    echo "Check logs: cat ${PROJECT_ROOT}/logs/gateway.log"
    exit 1
fi

echo -e "${GREEN}✓ Gateway running on port 3001 (PID: ${GATEWAY_PID})${NC}"

###############################################################################
# 6. Start Ryu Controller
###############################################################################
echo -e "\n${YELLOW}[6/6] Starting Ryu SDN Controller...${NC}"

cd "${RYU_DIR}"

# Check if ML models exist
if ! ls ml_model_*.pkl 1> /dev/null 2>&1; then
    echo -e "${RED}✗ ML model files not found${NC}"
    echo "Run: python3 -c 'from ml_detector import MLDetector; d=MLDetector(); d.train(\"../dataset/result.csv\"); d.save_model()'"
    exit 1
fi

# Start Ryu Controller in background
echo "  → Starting Ryu Controller..."
mkdir -p "${PROJECT_ROOT}/logs"
nohup ryu-manager --observe-links controller_blockchain.py > "${PROJECT_ROOT}/logs/ryu_controller.log" 2>&1 &
RYU_PID=$!

# Wait for controller to initialize
sleep 3

# Check if Ryu is running
if ! ps -p $RYU_PID > /dev/null 2>&1; then
    echo -e "${RED}✗ Ryu Controller failed to start${NC}"
    echo "Check logs: cat ${PROJECT_ROOT}/logs/ryu_controller.log"
    exit 1
fi

echo -e "${GREEN}✓ Ryu Controller running (PID: ${RYU_PID})${NC}"

###############################################################################
# Summary
###############################################################################
echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}  System Started Successfully! ✓${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Running Services:"
echo "  • Fabric Network: ✓"
echo "    - peer0.org1.example.com (port 7051)"
echo "    - peer0.org2.example.com (port 9051)"
echo "    - orderer.example.com (port 7050)"
echo ""
echo "  • Gateway API: ✓ (http://localhost:3001)"
echo "    - PID: ${GATEWAY_PID}"
echo "    - Test: curl http://localhost:3001/health"
echo ""
echo "  • Ryu Controller: ✓ (port 6633)"
echo "    - PID: ${RYU_PID}"
echo "    - ML Model: Decision Tree"
echo ""
echo "Next Steps:"
echo "  1. Test Gateway API:"
echo "     ${BLOCKCHAIN_DIR}/test_gateway_api.sh"
echo ""
echo "  2. Start Mininet (in new terminal):"
echo "     cd ${PROJECT_ROOT}/topology"
echo "     sudo python3 custom_topo.py"
echo ""
echo "  3. Generate traffic (in Mininet CLI):"
echo "     mininet> h1 ping -c 10 h10"
echo "     mininet> h2 bash ../scripts/attack_traffic.sh &"
echo ""
echo "Logs:"
echo "  • Gateway: ${PROJECT_ROOT}/logs/gateway.log"
echo "  • Ryu: ${PROJECT_ROOT}/logs/ryu_controller.log"
echo "  • Fabric: docker logs peer0.org1.example.com"
echo ""
echo -e "${BLUE}=========================================${NC}"

# Save PIDs for later
echo "${GATEWAY_PID}" > /tmp/sdn_gateway.pid
echo "${RYU_PID}" > /tmp/sdn_ryu.pid

exit 0
