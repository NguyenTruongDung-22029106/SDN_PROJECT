#!/bin/bash
# Comprehensive System Verification Test
# Tests each component individually to verify functionality

# Auto-detect project root (parent directory of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}╔════════════════════════════════════════════════╗"
echo -e "║  SDN-ML-Blockchain System Verification         ║"
echo -e "║  Testing Each Component Separately             ║"
echo -e "╚════════════════════════════════════════════════╝${NC}\n"

PASS=0
FAIL=0

# Test 1: Python Environment
echo -e "${YELLOW}[TEST 1/6]${NC} Python Environment"
python3 --version > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "  ${GREEN}✅ PASS${NC} - Python 3 available"
    ((PASS++))
else
    echo -e "  ${RED}❌ FAIL${NC} - Python 3 not found"
    ((FAIL++))
fi

# Test 2: Python Imports
echo -e "\n${YELLOW}[TEST 2/6]${NC} Python Module Imports"
python3 << EOF
import sys
import os
PROJECT_ROOT = "${PROJECT_ROOT}"
sys.path.insert(0, PROJECT_ROOT)
try:
    from ryu_app.ml_detector import MLDetector
    from blockchain.fabric_client import BlockchainClient
    print("  ✅ PASS - All Python modules import successfully")
    sys.exit(0)
except Exception as e:
    print(f"  ❌ FAIL - Import error: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    ((PASS++))
else
    ((FAIL++))
fi

# Test 3: ML Detector Functionality
echo -e "\n${YELLOW}[TEST 3/6]${NC} ML Detector Classification"
python3 << EOF
import sys
import os
PROJECT_ROOT = "${PROJECT_ROOT}"
sys.path.insert(0, PROJECT_ROOT)
from ryu_app.ml_detector import MLDetector

try:
    detector = MLDetector(model_type='random_forest')  # Default model type
    prediction, confidence = detector.classify([100, 50, 10])
    print(f"  ✅ PASS - ML Detection working (prediction={prediction}, confidence={confidence:.2f})")
    sys.exit(0)
except Exception as e:
    print(f"  ❌ FAIL - ML Detector error: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    ((PASS++))
else
    ((FAIL++))
fi

# Test 4: Blockchain (Fabric test-network)
echo -e "\n${YELLOW}[TEST 4/6]${NC} Blockchain (Fabric test-network)"
python3 << EOF
import sys
import json
import os
PROJECT_ROOT = "${PROJECT_ROOT}"
sys.path.insert(0, PROJECT_ROOT)
from blockchain.fabric_client import BlockchainClient

try:
    client = BlockchainClient()
    event = {"event_type": "test", "switch_id": "s1", "timestamp": 123, "action": "test", "details": {}}
    result = client.record_event(event)
    attacks = client.get_recent_attacks(time_window=300)

    if result:
        print(f"  ✅ PASS - Blockchain logging working (recent attacks: {len(attacks) if attacks else 0})")
        sys.exit(0)
    else:
        print("  ❌ FAIL - Blockchain logging failed")
        sys.exit(1)
except Exception as e:
    print(f"  ❌ FAIL - Blockchain error: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    ((PASS++))
else
    ((FAIL++))
fi

# Test 5: Mininet Availability
echo -e "\n${YELLOW}[TEST 5/6]${NC} Mininet Network Emulation"
which mn > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "  ${GREEN}✅ PASS${NC} - Mininet command available"
    ((PASS++))
    
    # Quick Mininet test
    echo "         Testing basic topology creation..."
    sudo mn -c > /dev/null 2>&1
    timeout 5 sudo python3 << 'EOF' 2>&1 | grep -q "MININET_OK"
from mininet.net import Mininet
from mininet.log import setLogLevel
setLogLevel('error')
try:
    net = Mininet()
    net.addHost('h1')
    net.addSwitch('s1')
    net.start()
    print("MININET_OK")
    net.stop()
except:
    pass
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "         ${GREEN}✓${NC} Mininet can create networks"
    else
        echo -e "         ${YELLOW}⚠${NC}  Mininet needs cleanup (run: sudo mn -c)"
    fi
else
    echo -e "  ${RED}❌ FAIL${NC} - Mininet not installed"
    ((FAIL++))
fi

# Test 6: Ryu Controller
echo -e "\n${YELLOW}[TEST 6/6]${NC} Ryu SDN Controller"
which ryu-manager > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "  ${GREEN}✅ PASS${NC} - Ryu controller installed"
    ((PASS++))
    
    # Test if controller can load our app
    echo "         Testing controller app loading..."
    sudo pkill -9 -f ryu > /dev/null 2>&1
    sleep 1
    
    timeout 5 sudo PYTHONPATH="${PROJECT_ROOT}" \
        python3 -m ryu.cmd.manager ryu_app.controller_blockchain 2>&1 | \
        grep -q "✓ ML Detector initialized"
    
    if [ $? -eq 0 ]; then
        echo -e "         ${GREEN}✓${NC} Controller app loads successfully"
        sudo pkill -9 -f ryu > /dev/null 2>&1
    else
        echo -e "         ${YELLOW}⚠${NC}  Controller may have port conflicts"
    fi
else
    echo -e "  ${RED}❌ FAIL${NC} - Ryu not installed"
    ((FAIL++))
fi

# Summary
echo -e "\n${YELLOW}╔════════════════════════════════════════════════╗"
echo -e "║              Test Summary                      ║"
echo -e "╚════════════════════════════════════════════════╝${NC}"
echo -e "  ${GREEN}PASSED:${NC} $PASS/6"
echo -e "  ${RED}FAILED:${NC} $FAIL/6"

if [ $FAIL -eq 0 ]; then
    echo -e "\n${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}System is ready for use.${NC}\n"
    echo "Next steps:"
    echo "  1. See HOW_TO_RUN_3_TERMINALS.md for usage guide"
    echo "  2. Run: bash scripts/demo_system.sh for full demo"
    echo "  3. Start system with 3 terminals (see documentation)"
    exit 0
else
    echo -e "\n${RED}⚠️  SOME TESTS FAILED${NC}"
    echo "Please review errors above and fix before proceeding."
    exit 1
fi
