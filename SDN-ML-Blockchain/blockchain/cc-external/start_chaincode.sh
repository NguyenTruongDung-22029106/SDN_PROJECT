#!/bin/sh
set -e

echo "[trustlog-external] starting entrypoint"

# Basic checks for required cert/key files
if [ "$CHAINCODE_TLS_DISABLED" = "true" ]; then
  echo "TLS disabled, skipping certificate checks."
elif [ ! -f /etc/hyperledger/fabric/client_pem.crt ] || [ ! -f /etc/hyperledger/fabric/client_pem.key ] ; then
  echo "ERROR: TLS cert/key not found under /etc/hyperledger/fabric"
  echo "Place client_pem.crt and client_pem.key (and cacerts/) into that path and restart."
  exit 1
fi

echo "Found TLS files (listing):"
ls -la /etc/hyperledger/fabric || true

# Example: run the chaincode server binary. Adapt flags as needed by your chaincode server.
# The binary should start a TLS-enabled gRPC chaincode server listening on port 9999.

exec /app/trustlog_server "$@"
