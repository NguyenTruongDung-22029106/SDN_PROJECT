# Hyperledger Fabric Setup Notes

## Current Status

 **All tools installed successfully:**
- Docker 28.1.1
- docker-compose v2.24.0
- Go 1.21.0
- Node.js 18.20.8
- fabric-samples downloaded
- Fabric binaries (v2.5.0) installed

## Known Issue with Docker Compose

The fabric-samples test-network has docker-compose format compatibility issues with docker-compose v2.24.0.

**Error:** `expected a map, got 'slice'` for networks, ports, volumes fields

**Root Cause:** 
- fabric-samples main branch uses newer compose format (`compose/*.yaml`)
- But network.sh also references older format files (`compose/docker/*.yaml`)
- docker-compose v2 is stricter about YAML format

## Workarounds

### Use Real Hyperledger Fabric (Recommended)

This project is intended to run against a real Hyperledger Fabric test network (the `fabric-samples/test-network`). Running against a real Fabric instance provides persistent storage, realistic performance characteristics, and proper certificate handling. The setup scripts in `scripts/setup_fabric.sh` automate bringing up the `test-network` and deploying the `trustlog` chaincode.

If you can't run Fabric on your machine, you may still inspect and run unit tests for individual components, but production and integration testing require the Fabric network.

### Option 2: Fix Docker Permissions

User added to docker group but needs logout/login:

```bash
# Method 1: Logout and login again
# Method 2: Use newgrp (temporary)
newgrp docker

# Method 3: Use sudo for fabric commands
sudo -E ./network.sh up createChannel -c sdnchannel -ca
```

### Option 3: Downgrade to fabric-samples v2.5.0 tag

```bash
cd fabric-samples
git checkout v2.5.0
cd test-network
./network.sh up createChannel -c sdnchannel -ca
```

### Option 4: Fix docker-compose files manually

The compose files need format conversion from:
```yaml
volumes:
  - ./path:/container/path
```
To:
```yaml
volumes:
  - type: bind
    source: ./path
    target: /container/path
```

## Recommended Approach for This Project

Use the real Hyperledger Fabric test-network for integration and verification. The in-project mock client has been removed and integration tests/scripts now expect a running Fabric `test-network`.

Why run Fabric?
- Persistent ledger and realistic performance
- Proper certificate and TLS handling
- Realistic multi-organization behavior

To start the Fabric test-network quickly, run:
```bash
bash scripts/setup_fabric.sh
```
or follow the manual steps in the "Quick Start (Real Fabric)" section below.

## Quick Start (Real Fabric)

```bash
# Terminal 1: Start Fabric test network (in project root)
bash scripts/setup_fabric.sh

# Terminal 2: Start SDN controller
sudo python3 -m ryu_app.controller_blockchain

# Terminal 3: Start network topology
sudo python3 topology/custom_topo.py

# Terminal 4: Generate attack traffic
bash scripts/attack_traffic.sh
```

## Production Deployment

For production, you MUST setup real Hyperledger Fabric network for:
- Persistent storage
- Immutable audit trail
- Multi-organization consensus
- Byzantine fault tolerance

See `PRODUCTION_DEPLOYMENT.md` for details.

## Summary

 **Development-ready:** Use the Fabric test-network for integration and demo runs (mock client removed)
⏳ **Production-ready:** Fabric setup pending docker-compose format fix or Docker permissions
 **Recommended:** Start testing with the Fabric test-network. The project now requires a running Hyperledger Fabric test-network for integration tests and demos.

The system is fully functional for development and testing purposes.
