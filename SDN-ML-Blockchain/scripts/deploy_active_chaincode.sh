#!/bin/bash
# Script để deploy chaincode đã nâng cấp với Active Mode features

echo "=========================================="
echo "🚀 Deploying Active Mode Chaincode"
echo "=========================================="
echo ""

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

# Check if fabric network is running
if ! docker ps | grep -q "peer0.org1.example.com"; then
    echo "❌ Fabric network is not running!"
    echo "Please start it first:"
    echo "  cd fabric-samples/test-network"
    echo "  ./network.sh up createChannel"
    exit 1
fi

echo "✓ Fabric network is running"
echo ""

# Package chaincode
echo "📦 Packaging chaincode..."
cd blockchain/chaincode
GO111MODULE=on go mod tidy
GO111MODULE=on go mod vendor

cd ../../fabric-samples/test-network

# Set environment for peer CLI
export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=$PWD/../config/
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051

# Package
echo "📦 Creating chaincode package..."
CHAINCODE_PATH="${PROJECT_ROOT}/blockchain/chaincode"
peer lifecycle chaincode package trustlog.tar.gz \
  --path "${CHAINCODE_PATH}" \
  --lang golang \
  --label trustlog_2.0

if [ $? -ne 0 ]; then
    echo "❌ Failed to package chaincode"
    exit 1
fi

echo "✓ Chaincode packaged"
echo ""

# Install on Org1
echo "📥 Installing on Org1 peer..."
peer lifecycle chaincode install trustlog.tar.gz

if [ $? -ne 0 ]; then
    echo "❌ Failed to install on Org1"
    exit 1
fi

echo "✓ Installed on Org1"
echo ""

# Install on Org2
echo "📥 Installing on Org2 peer..."
export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_ADDRESS=localhost:9051

peer lifecycle chaincode install trustlog.tar.gz

if [ $? -ne 0 ]; then
    echo "❌ Failed to install on Org2"
    exit 1
fi

echo "✓ Installed on Org2"
echo ""

# Get package ID
echo "🔍 Getting package ID..."
PACKAGE_ID=$(peer lifecycle chaincode queryinstalled | grep trustlog_2.0 | awk '{print $3}' | sed 's/,$//')

if [ -z "$PACKAGE_ID" ]; then
    echo "❌ Failed to get package ID"
    exit 1
fi

echo "✓ Package ID: $PACKAGE_ID"
echo ""

# Approve for Org2
echo "✅ Approving chaincode for Org2..."
peer lifecycle chaincode approveformyorg \
  -o localhost:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --channelID sdnchannel \
  --name trustlog \
  --version 2.0 \
  --package-id $PACKAGE_ID \
  --sequence 2 \
  --tls \
  --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

if [ $? -ne 0 ]; then
    echo "❌ Failed to approve for Org2"
    exit 1
fi

echo "✓ Approved for Org2"
echo ""

# Approve for Org1
echo "✅ Approving chaincode for Org1..."
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051

peer lifecycle chaincode approveformyorg \
  -o localhost:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --channelID sdnchannel \
  --name trustlog \
  --version 2.0 \
  --package-id $PACKAGE_ID \
  --sequence 2 \
  --tls \
  --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

if [ $? -ne 0 ]; then
    echo "❌ Failed to approve for Org1"
    exit 1
fi

echo "✓ Approved for Org1"
echo ""

# Check commit readiness
echo "🔍 Checking commit readiness..."
peer lifecycle chaincode checkcommitreadiness \
  --channelID sdnchannel \
  --name trustlog \
  --version 2.0 \
  --sequence 2 \
  --tls \
  --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
  --output json

echo ""

# Commit chaincode
echo "🚀 Committing chaincode to channel..."
peer lifecycle chaincode commit \
  -o localhost:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --channelID sdnchannel \
  --name trustlog \
  --version 2.0 \
  --sequence 2 \
  --tls \
  --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
  --peerAddresses localhost:7051 \
  --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
  --peerAddresses localhost:9051 \
  --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt

if [ $? -ne 0 ]; then
    echo "❌ Failed to commit chaincode"
    exit 1
fi

echo ""
echo "✓ Chaincode committed successfully!"
echo ""

# Query committed chaincode
echo "🔍 Verifying deployment..."
peer lifecycle chaincode querycommitted --channelID sdnchannel --name trustlog

echo ""
echo "=========================================="
echo "✅ Chaincode Active Mode Deployed!"
echo "=========================================="
echo ""
echo "New functions available:"
echo "  - GetRecentAttacks(timeWindow)"
echo "  - GetMitigationAction(switchID, confidence)"
echo "  - CheckCoordinatedAttack(timeWindow, threshold)"
echo "  - SetMitigationPolicy(policyJSON)"
echo "  - GetMitigationPolicy(policyID)"
echo ""
echo "Next steps:"
echo "  1. Restart gateway: docker restart sdn-blockchain-gateway"
echo "  2. Test new APIs: curl http://localhost:3001/api/v1/attacks/recent"
echo "  3. Run controller with active mode enabled"
echo ""
