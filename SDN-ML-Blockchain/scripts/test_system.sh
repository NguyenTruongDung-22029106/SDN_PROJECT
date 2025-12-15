#!/bin/bash
# Quick test script to verify system components

echo "=========================================="
echo "SDN-ML-Blockchain System Check"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 installed"
        return 0
    else
        echo -e "${RED}✗${NC} $1 not found"
        return 1
    fi
}

echo ""
echo "1. Checking Basic Dependencies..."
echo "------------------------------------------"
check_command python3
check_command pip3
check_command git
check_command docker
check_command docker-compose
check_command go
check_command node

echo ""
echo "2. Checking SDN Components..."
echo "------------------------------------------"
check_command mn
check_command ovs-vsctl
check_command ryu-manager

echo ""
echo "3. Checking Attack Tools..."
echo "------------------------------------------"
check_command hping3
check_command iperf3

echo ""
echo "4. Checking Python Packages..."
echo "------------------------------------------"
python3 -c "import numpy; print('✓ numpy')" 2>/dev/null || echo "✗ numpy"
python3 -c "import pandas; print('✓ pandas')" 2>/dev/null || echo "✗ pandas"
python3 -c "import sklearn; print('✓ scikit-learn')" 2>/dev/null || echo "✗ scikit-learn"
python3 -c "import flask; print('✓ flask')" 2>/dev/null || echo "✗ flask"
python3 -c "import ryu; print('✓ ryu')" 2>/dev/null || echo "✗ ryu"

echo ""
echo "5. Checking Fabric Installation..."
echo "------------------------------------------"
if [ -d "fabric-samples" ]; then
    echo -e "${GREEN}✓${NC} fabric-samples directory exists"
    
    if [ -f "fabric-samples/bin/peer" ]; then
        echo -e "${GREEN}✓${NC} Fabric binaries installed"
        fabric-samples/bin/peer version 2>/dev/null | head -n 1
    else
        echo -e "${RED}✗${NC} Fabric binaries not found"
    fi
else
    echo -e "${RED}✗${NC} fabric-samples not found"
fi

echo ""
echo "6. Checking Docker Status..."
echo "------------------------------------------"
if systemctl is-active --quiet docker; then
    echo -e "${GREEN}✓${NC} Docker service running"
else
    echo -e "${YELLOW}!${NC} Docker service not running"
    echo "  Run: sudo systemctl start docker"
fi

echo ""
echo "7. Checking Project Structure..."
echo "------------------------------------------"
[ -d "ryu_app" ] && echo -e "${GREEN}✓${NC} ryu_app/" || echo -e "${RED}✗${NC} ryu_app/"
[ -d "blockchain" ] && echo -e "${GREEN}✓${NC} blockchain/" || echo -e "${RED}✗${NC} blockchain/"
[ -d "topology" ] && echo -e "${GREEN}✓${NC} topology/" || echo -e "${RED}✗${NC} topology/"
[ -d "scripts" ] && echo -e "${GREEN}✓${NC} scripts/" || echo -e "${RED}✗${NC} scripts/"
[ -d "dataset" ] && echo -e "${GREEN}✓${NC} dataset/" || echo -e "${RED}✗${NC} dataset/"
[ -d "analysis" ] && echo -e "${GREEN}✓${NC} analysis/" || echo -e "${RED}✗${NC} analysis/"

echo ""
echo "8. Checking Key Files..."
echo "------------------------------------------"
[ -f "ryu_app/controller_blockchain.py" ] && echo -e "${GREEN}✓${NC} controller_blockchain.py" || echo -e "${RED}✗${NC} controller_blockchain.py"
[ -f "ryu_app/ml_detector.py" ] && echo -e "${GREEN}✓${NC} ml_detector.py" || echo -e "${RED}✗${NC} ml_detector.py"
[ -f "blockchain/fabric_client.py" ] && echo -e "${GREEN}✓${NC} fabric_client.py" || echo -e "${RED}✗${NC} fabric_client.py"
[ -f "blockchain/chaincode/trustlog.go" ] && echo -e "${GREEN}✓${NC} trustlog.go" || echo -e "${RED}✗${NC} trustlog.go"
[ -f "topology/custom_topo.py" ] && echo -e "${GREEN}✓${NC} custom_topo.py" || echo -e "${RED}✗${NC} custom_topo.py"

echo ""
echo "9. Testing Python Imports..."
echo "------------------------------------------"
python3 << 'EOF'
import sys
try:
    sys.path.append('ryu_app')
    from ml_detector import MLDetector
    print('✓ ml_detector import successful')
except Exception as e:
    print(f'✗ ml_detector import failed: {e}')

try:
    sys.path.append('blockchain')
    from fabric_client import BlockchainClient
    print('✓ fabric_client import successful')
except Exception as e:
    print(f'✗ fabric_client import failed: {e}')
EOF

echo ""
echo "10. Port Availability Check..."
echo "------------------------------------------"
check_port() {
    if lsof -i:$1 &> /dev/null; then
        echo -e "${YELLOW}!${NC} Port $1 in use"
    else
        echo -e "${GREEN}✓${NC} Port $1 available"
    fi
}

check_port 6633  # Ryu controller
check_port 8080  # Ryu REST
check_port 3001  # Gateway
check_port 7050  # Fabric Orderer
check_port 7051  # Fabric Peer

echo ""
echo "=========================================="
echo "System Check Complete"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. If any components are missing, run: bash scripts/install.sh"
echo "2. To setup Fabric network, run: bash scripts/setup_fabric.sh"
echo "3. To start the system, run: sudo bash scripts/run.sh"
echo ""
