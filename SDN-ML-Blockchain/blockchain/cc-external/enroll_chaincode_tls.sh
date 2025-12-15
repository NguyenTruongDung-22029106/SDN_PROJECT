#!/bin/bash
set -euo pipefail

# enroll_chaincode_tls.sh
# Example helper to create the certs layout for the chaincode external service.
# This script assumes you already have access to the org CA (fabric-ca) or the signed cert/key.
#
# Two modes:
# 1) Copy an existing signed cert/key into ./certs/trustlog
# 2) Use fabric-ca-client to enroll with a CA (uncomment and adapt the enroll steps below)

OUT_DIR="$(pwd)/certs/trustlog"
mkdir -p "$OUT_DIR"/cacerts

echo "Place your chaincode TLS cert and key into: $OUT_DIR"
echo "Required files (example names):"
echo "  client_pem.crt   -> $OUT_DIR/client_pem.crt"
echo "  client_pem.key   -> $OUT_DIR/client_pem.key"
echo "  cacerts/ca-cert.pem -> $OUT_DIR/cacerts/ca-cert.pem"

cat > "$OUT_DIR/README.txt" <<'EOF'
Step: produce or copy TLS cert/key for the chaincode service.

1) If you have a Fabric CA:
   - Register an identity for the chaincode service (e.g. 'chaincode-trustlog') with the CA.
   - Use fabric-ca-client to enroll that identity and get the cert+key.
   - Copy signcert and key to client_pem.crt / client_pem.key and the CA cert into cacerts/.

2) If you already have cert/key (signed by the same CA the peers trust), copy them here.

Important: the TLS cert must be signed by the CA that the peer trusts (or be in the peer's cacerts).
EOF

echo "Wrote helper README to $OUT_DIR/README.txt"

# Example (commented) fabric-ca-client flow - adapt CA server URL, MSP, enrollment ID/secret:
# export FABRIC_CA_CLIENT_HOME="$OUT_DIR/fabric-ca-client"
# fabric-ca-client enroll -u https://chaincode-trustlog:secret@ca.org1.example.com:7054 --tls.certfiles /path/to/ca-cert.pem
# cp $FABRIC_CA_CLIENT_HOME/msp/signcerts/cert.pem $OUT_DIR/client_pem.crt
# cp $FABRIC_CA_CLIENT_HOME/msp/keystore/*_sk $OUT_DIR/client_pem.key
# cp /path/to/ca-cert.pem $OUT_DIR/cacerts/ca-cert.pem

echo "Done. Customize the certs and then use docker-compose.trustlog-external.yml to run the service."
