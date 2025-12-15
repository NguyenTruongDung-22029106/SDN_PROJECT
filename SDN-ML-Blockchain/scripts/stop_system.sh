#!/bin/bash
###############################################################################
# Script dừng toàn bộ hệ thống SDN-ML-Blockchain
###############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Auto-detect project root (parent directory of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FABRIC_ROOT="${PROJECT_ROOT}/fabric-samples/test-network"

echo -e "${YELLOW}Stopping SDN-ML-Blockchain System...${NC}"

# Stop Ryu Controller
if [ -f /tmp/sdn_ryu.pid ]; then
    RYU_PID=$(cat /tmp/sdn_ryu.pid)
    if ps -p $RYU_PID > /dev/null 2>&1; then
        kill $RYU_PID 2>/dev/null
        echo "  ✓ Stopped Ryu Controller (PID: ${RYU_PID})"
    fi
    rm /tmp/sdn_ryu.pid
else
    pkill -f "ryu-manager" 2>/dev/null && echo "  ✓ Stopped Ryu Controllers"
fi

# Stop Gateway
if [ -f /tmp/sdn_gateway.pid ]; then
    GATEWAY_PID=$(cat /tmp/sdn_gateway.pid)
    if ps -p $GATEWAY_PID > /dev/null 2>&1; then
        kill $GATEWAY_PID 2>/dev/null
        echo "  ✓ Stopped Gateway (PID: ${GATEWAY_PID})"
    fi
    rm /tmp/sdn_gateway.pid
else
    pkill -f "gateway_node_server.js" 2>/dev/null && echo "  ✓ Stopped Gateway servers"
fi

# Stop Mininet
sudo mn -c 2>/dev/null && echo "  ✓ Cleaned up Mininet"

# Stop Fabric Network
cd "${FABRIC_ROOT}"
./network.sh down
echo "  ✓ Stopped Fabric network"

echo -e "${GREEN}System stopped successfully!${NC}"
