#!/bin/bash
# Setup Hyperledger Fabric Network for SDN Security Logging

set -e

echo "=========================================="
echo "Hyperledger Fabric Network Setup"
echo "=========================================="

GREEN='\033[0;32m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[+]${NC} $1"
}

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Navigate to fabric samples
cd $PROJECT_ROOT/fabric-samples/test-network || {
    echo "Error: fabric-samples/test-network not found"
    echo "Please run install.sh first"
    exit 1
}

# Clean up any existing network
print_status "Cleaning up existing network..."
./network.sh down

# Start the network
print_status "Starting Fabric network..."
./network.sh up createChannel -c sdnchannel -ca

# Ensure orderer TLS CA is available under msp/tlscacerts so peer CLI --cafile can find it.
# Some test-network setups only populate tls/tlscacerts; copy the first TLS CA into msp/tlscacerts
# with the expected filename pattern to avoid "unable to load orderer.tls.rootcert.file" errors.
print_status "Ensuring orderer TLS CA certificates are present under msp/tlscacerts..."
for ORDERO in ${PWD}/organizations/ordererOrganizations/*; do
    domain=$(basename "${ORDERO}")
    for ORD in "${ORDERO}/orderers"/*; do
        if [ -d "$ORD" ]; then
            mkdir -p "$ORD/msp/tlscacerts"
            # If msp/tlscacerts is empty, try copy from tls/tlscacerts
            if [ -z "$(ls -A "$ORD/msp/tlscacerts" 2>/dev/null)" ]; then
                src=$(ls "$ORD/tls/tlscacerts"/*.pem 2>/dev/null | head -n1 || true)
                if [ -n "$src" ]; then
                    dst="$ORD/msp/tlscacerts/tlsca.${domain}-cert.pem"
                    cp -f "$src" "$dst" && echo "Copied $src -> $dst"
                fi
            fi
        fi
    done
done


# Deploy chaincode
print_status "Deploying SDN security chaincode..."

# Copy chaincode to fabric-samples
CHAINCODE_SRC="$PROJECT_ROOT/blockchain/chaincode"
CHAINCODE_DEST="$PROJECT_ROOT/fabric-samples/chaincode/trustlog"

if [ -d "$CHAINCODE_SRC" ]; then
    mkdir -p $CHAINCODE_DEST
    cp -r $CHAINCODE_SRC/* $CHAINCODE_DEST/
    
    # Deploy the chaincode
    ./network.sh deployCC -ccn trustlog -ccp $CHAINCODE_DEST -ccl go -c sdnchannel
    
    print_status "Chaincode deployed successfully"
else
    echo "Error: Chaincode source not found at $CHAINCODE_SRC"
    exit 1
fi

# Set environment variables for peer commands
print_status "Setting up environment variables..."
export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=${PWD}/../config/

# For Org1
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051

# Test the chaincode
print_status "Testing chaincode with sample event..."

# Create a test event
TEST_EVENT='{
    "event_type": "test_connection",
    "switch_id": "s0",
    "timestamp": '$(date +%s)',
    "trust_score": 1.0,
    "action": "network_initialized",
    "details": {"message": "Blockchain network setup complete"}
}'

peer chaincode invoke \
    -o localhost:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    --tls \
    --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
    -C sdnchannel \
    -n trustlog \
    --peerAddresses localhost:7051 \
    --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
    -c "{\"function\":\"RecordEvent\",\"Args\":[\"$TEST_EVENT\"]}"

sleep 2

# Query to verify
print_status "Verifying chaincode deployment..."
peer chaincode query \
    -C sdnchannel \
    -n trustlog \
    -c '{"function":"QueryTrustLog","Args":["s0"]}'

echo ""
echo "=========================================="
print_status "Fabric network setup complete!"
echo "=========================================="
echo ""
echo "Network Details:"
echo "  Channel: sdnchannel"
echo "  Chaincode: trustlog"
echo "  Org1 Peer: localhost:7051"
echo "  Orderer: localhost:7050"
echo ""
echo "To interact with the network:"
echo "  1. Use fabric_client.py from Python"
echo "  2. Use gateway_node_server.js REST API (http://localhost:3001)"
echo "  3. Use peer CLI commands"
echo ""
