#!/bin/bash
set -euo pipefail

# deploy_external_chaincode.sh
# Template script to package/install/approve/commit an external chaincode
# Adapt the environment variables below to match your test-network setup.

CHANNEL=${CHANNEL:-sdnchannel}
CC_LABEL=${CC_LABEL:-trustlog_2.2}
PACKAGE=${PACKAGE:-trustlog-external.tar.gz}
CHAINCODE_NAME=${CHAINCODE_NAME:-trustlog}
SEQUENCE=${SEQUENCE:-1}
INIT_REQUIRED=${INIT_REQUIRED:-false}

echo "Using CHANNEL=${CHANNEL}, CC_LABEL=${CC_LABEL}, PACKAGE=${PACKAGE}, CHAINCODE_NAME=${CHAINCODE_NAME}"

echo "1) Package chaincode (note: external chaincode packaging may be minimal; adjust path)"
peer lifecycle chaincode package ${PACKAGE} --path ../chaincode --lang golang --label ${CC_LABEL}

echo "2) Install package on local peer"
peer lifecycle chaincode install ${PACKAGE}

echo "3) Query installed to get package-id (you must export CORE_PEER_* env vars for target peer)"
peer lifecycle chaincode queryinstalled

echo "4) Approve chaincode definition for my org (adjust endorsement policy & init requirement as needed)"
# Example: peer lifecycle chaincode approveformyorg --channelID $CHANNEL --name ${CHAINCODE_NAME} --version 2.2 --package-id <PACKAGE_ID> --sequence ${SEQUENCE} --init-required ${INIT_REQUIRED}
echo "  Replace <PACKAGE_ID> after running 'queryinstalled' and then run the approve command (example above)."

echo "5) Commit chaincode definition (after approvals from required orgs)"
# Example commit command (adjust peer addresses and orderer endpoint):
# peer lifecycle chaincode commit -o localhost:7050 --channelID $CHANNEL --name ${CHAINCODE_NAME} --version 2.2 --sequence ${SEQUENCE} --init-required ${INIT_REQUIRED} --peerAddresses localhost:7051 --tlsRootCertFiles /path/to/peer/tlsca.pem

echo "NOTE: For external chaincode you may need to include connection metadata (connection.json) in the package or use external builder metadata. Check Fabric docs for exact metadata format for your Fabric version."

echo "After commit, ensure the external chaincode service is running and reachable at the endpoint configured in your metadata/connection.json (e.g., trustlog-external:9999)."
