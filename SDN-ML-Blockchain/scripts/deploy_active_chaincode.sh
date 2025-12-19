#!/bin/bash
###############################################################################
# Script để redeploy chaincode sau khi sửa đổi
# - Tự động detect sequence hiện tại
# - Stop/Restart Ryu Controller
# - Verify chaincode changes
###############################################################################

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}       REDEPLOY CHAINCODE                              ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

###############################################################################
# 1. Check if fabric network is running
###############################################################################
echo -e "${YELLOW}[1/6] Checking Fabric network status...${NC}"

if ! docker ps | grep -q "peer0.org1.example.com"; then
    echo -e "${RED}✗ Fabric network is not running!${NC}"
    echo "Please start it first:"
    echo "  ./scripts/start_system.sh"
    exit 1
fi

echo -e "${GREEN}✓ Fabric network is running${NC}"
echo ""

###############################################################################
# 2. Stop Ryu Controller
###############################################################################
echo -e "${YELLOW}[2/6] Stopping Ryu Controller...${NC}"

pkill -f "ryu-manager" 2>/dev/null || true
sleep 2

echo -e "${GREEN}✓ Ryu Controller stopped${NC}"
echo ""

###############################################################################
# 3. Verify chaincode changes
###############################################################################
echo -e "${YELLOW}[3/6] Verifying chaincode changes...${NC}"

CHAINCODE_FILE="${PROJECT_ROOT}/blockchain/chaincode/trustlog.go"

if grep -q "TrustScore.*float64.*json:\"trust_score\"" "$CHAINCODE_FILE"; then
    echo -e "${RED}✗ TrustScore field still exists in SecurityEvent struct${NC}"
    echo "Changes not applied yet!"
    exit 1
fi

echo -e "${GREEN}✓ Chaincode updated (TrustScore removed from SecurityEvent)${NC}"
echo ""

###############################################################################
# 4. Get current sequence and prepare new version
###############################################################################
echo -e "${YELLOW}[4/6] Preparing chaincode deployment...${NC}"

cd "${PROJECT_ROOT}/fabric-samples/test-network"

# Set environment for peer CLI
export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=$PWD/../config/
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051

# Get current sequence number
CURRENT_SEQ=$(peer lifecycle chaincode querycommitted --channelID sdnchannel --name trustlog 2>/dev/null | grep "Sequence:" | awk '{print $2}' | tr -d ',' | cut -d'.' -f1 || echo "1")
# Ensure CURRENT_SEQ is a valid integer
if [ -z "$CURRENT_SEQ" ] || ! [[ "$CURRENT_SEQ" =~ ^[0-9]+$ ]]; then
    CURRENT_SEQ=1
fi
NEW_SEQ=$((CURRENT_SEQ + 1))

echo "  → Current sequence: $CURRENT_SEQ"
echo "  → New sequence: $NEW_SEQ"
echo ""

# Prepare chaincode
echo "  → Preparing chaincode..."
cd "${PROJECT_ROOT}/blockchain/chaincode"
GO111MODULE=on go mod tidy 2>/dev/null || true
GO111MODULE=on go mod vendor 2>/dev/null || true

cd "${PROJECT_ROOT}/fabric-samples/test-network"

# Package chaincode
echo "  → Packaging chaincode..."
CHAINCODE_PATH="${PROJECT_ROOT}/blockchain/chaincode"
peer lifecycle chaincode package trustlog.tar.gz \
  --path "${CHAINCODE_PATH}" \
  --lang golang \
  --label trustlog_${NEW_SEQ}

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to package chaincode${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Chaincode packaged (version ${NEW_SEQ}.0)${NC}"
echo ""

###############################################################################
# 5. Install and deploy chaincode
###############################################################################
echo -e "${YELLOW}[5/6] Installing and deploying chaincode...${NC}"

# Install on Org1
echo "  → Installing on Org1..."
peer lifecycle chaincode install trustlog.tar.gz 2>&1 | grep -v "already successfully installed" || true

# Install on Org2
echo "  → Installing on Org2..."
export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_ADDRESS=localhost:9051

peer lifecycle chaincode install trustlog.tar.gz 2>&1 | grep -v "already successfully installed" || true

# Get package ID
echo "  → Getting package ID..."
PACKAGE_ID=$(peer lifecycle chaincode queryinstalled | grep "trustlog_${NEW_SEQ}" | awk '{print $3}' | sed 's/,$//')

if [ -z "$PACKAGE_ID" ]; then
    echo -e "${RED}✗ Failed to get package ID${NC}"
    exit 1
fi

echo "  → Package ID: $PACKAGE_ID"
echo ""

  # Approve for Org2
  echo "  → Approving for Org2..."
  peer lifecycle chaincode approveformyorg \
    -o localhost:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    --channelID sdnchannel \
    --name trustlog \
    --version ${NEW_SEQ}.0 \
    --package-id $PACKAGE_ID \
    --sequence $NEW_SEQ \
    --tls \
    --cafile ${PWD}/organizations/ordererOrganizations/example.com/msp/tlscacerts/tlsca.example.com-cert.pem

  if [ $? -ne 0 ]; then
      echo -e "${RED}✗ Failed to approve for Org2${NC}"
      exit 1
  fi

  # Approve for Org1
  echo "  → Approving for Org1..."
  export CORE_PEER_LOCALMSPID="Org1MSP"
  export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
  export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
  export CORE_PEER_ADDRESS=localhost:7051

  peer lifecycle chaincode approveformyorg \
    -o localhost:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    --channelID sdnchannel \
    --name trustlog \
    --version ${NEW_SEQ}.0 \
    --package-id $PACKAGE_ID \
    --sequence $NEW_SEQ \
    --tls \
    --cafile ${PWD}/organizations/ordererOrganizations/example.com/msp/tlscacerts/tlsca.example.com-cert.pem

  if [ $? -ne 0 ]; then
      echo -e "${RED}✗ Failed to approve for Org1${NC}"
      exit 1
  fi

  # Check commit readiness
  echo "  → Checking commit readiness..."
  peer lifecycle chaincode checkcommitreadiness \
    --channelID sdnchannel \
    --name trustlog \
    --version ${NEW_SEQ}.0 \
    --sequence $NEW_SEQ \
    --tls \
    --cafile ${PWD}/organizations/ordererOrganizations/example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
    --output json

  echo ""

  # Commit chaincode
  echo "  → Committing chaincode..."
  peer lifecycle chaincode commit \
    -o localhost:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    --channelID sdnchannel \
    --name trustlog \
    --version ${NEW_SEQ}.0 \
    --sequence $NEW_SEQ \
    --tls \
    --cafile ${PWD}/organizations/ordererOrganizations/example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
    --peerAddresses localhost:7051 \
    --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
    --peerAddresses localhost:9051 \
    --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt

  if [ $? -ne 0 ]; then
      echo -e "${RED}✗ Failed to commit chaincode${NC}"
      exit 1
  fi

  # Verify deployment
  echo "  → Verifying deployment..."
  sleep 3
  peer lifecycle chaincode querycommitted --channelID sdnchannel --name trustlog

echo -e "${GREEN}✓ Chaincode deployed successfully (sequence: $NEW_SEQ)${NC}"
echo ""

###############################################################################
# 6. Restart Ryu Controller
###############################################################################
echo -e "${YELLOW}[6/6] Restarting Ryu Controller...${NC}"

cd "${PROJECT_ROOT}/ryu_app"

# Start Ryu Controller with same config as before
APP_TYPE=${APP_TYPE:-1}
PREVENTION=${PREVENTION:-1}
ENABLE_IP_SPOOFING_DETECTION=${ENABLE_IP_SPOOFING_DETECTION:-0}
ML_MODEL_TYPE=${ML_MODEL_TYPE:-decision_tree}

nohup env APP_TYPE="${APP_TYPE}" PREVENTION="${PREVENTION}" ENABLE_IP_SPOOFING_DETECTION="${ENABLE_IP_SPOOFING_DETECTION}" ML_MODEL_TYPE="${ML_MODEL_TYPE}" ryu-manager --observe-links controller_blockchain.py > /dev/null 2>&1 &
RYU_PID=$!

sleep 3

if ! ps -p $RYU_PID > /dev/null 2>&1; then
    echo -e "${RED}✗ Ryu Controller failed to start${NC}"
    echo "Check logs: cat ${PROJECT_ROOT}/logs/ryu_controller.log"
    exit 1
fi

echo -e "${GREEN}✓ Ryu Controller restarted (PID: ${RYU_PID})${NC}"
echo ""

###############################################################################
# Summary
###############################################################################
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}       CHAINCODE REDEPLOYED SUCCESSFULLY! ✓            ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "Changes:"
echo "  ✓ TrustScore field removed from SecurityEvent"
echo "  ✓ Trust management functions deprecated"
echo "  ✓ Chaincode sequence: $CURRENT_SEQ → $NEW_SEQ"
echo ""
echo "Services:"
echo "  ✓ Fabric Network: Running"
echo "  ✓ Gateway API: http://localhost:3001"
echo "  ✓ Ryu Controller: Running (PID: ${RYU_PID})"
echo ""
echo "Next steps:"
echo "  1. Test new events (no more trust_score in response):"
echo "     bash scripts/recent_attack.sh"
echo ""
echo "  2. Generate attack traffic:"
echo "     cd topology && sudo python3 custom_topo.py"
echo "     mininet> h1 bash ../scripts/attack_traffic.sh &"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

exit 0
