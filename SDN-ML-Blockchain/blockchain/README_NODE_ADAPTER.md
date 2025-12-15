# Node Gateway Adapter (Express)

This small microservice exposes a simple REST API for the SDN controller to interact with Hyperledger Fabric using the official Node SDK (`fabric-network`).

Endpoints
- POST /api/v1/events
  - Body: JSON object representing the event (same shape used by chaincode RecordEvent)
  - Returns: { success: true, txId }
- GET /api/v1/trust/:deviceId
  - Returns the QueryTrustLog result for the device

Configuration (env vars)
- CONNECTION_PROFILE: path to connection profile JSON (defaults to fabric-samples test-network connection-org1.json)
- WALLET_PATH: path to wallet dir (default: `blockchain/wallet`)
- IDENTITY_LABEL: identity in wallet (default: `User1@org1.example.com`)
- CHANNEL_NAME: channel (default: `sdnchannel`)
- CHAINCODE_NAME: chaincode (default: `trustlog`)
- PORT: HTTP port (default: 3001)

Usage
1. Install deps:
```bash
cd blockchain
npm install
```
2. Ensure wallet contains identity and connection profile exists (see docs/FABRIC_SETUP_NOTE.md)
3. Start service:
```bash
npm start
```

Then call endpoints from the Ryu controller or curl.
