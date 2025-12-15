# SDN-ML-Blockchain Architecture Overview

## System Architecture

```

                    Application Layer                             
        
   REST Gateway      CLI Tool       Monitoring Dashboard  
        

                            
                            

                   Control Plane (Ryu SDN Controller)            
      |
    Flow Monitor → ML Detector → Attack Mitigation             |
                                                            |
                                     → Block Port         |
                                                             |
                      → Blockchain Logger                  |
                                                             |
         → Feature Extraction                              |
              (SFE, SSIP, RFIP)                               |
      |

                            
                    OpenFlow Protocol
                            
                            

                      Data Plane                                  
               
   Switch 1  Switch 2  Switch 3  Switch 4     
               
                                                             
                                  
    Hosts       Hosts       Hosts       Hosts         
                                  

                            
                  Security Event Stream
                            
                            

              Blockchain Layer (Hyperledger Fabric)               
    
                      Smart Contract                           
            
     RecordEvent  QueryTrustLog   QueryEventsByType    
            
    
    
                    Distributed Ledger                         
             
      Peer 0      Peer 1      Peer 2      Peer N     
      (Org1)      (Org1)      (Org2)      (OrgN)     
             
    

```

## Data Flow

### 1. Normal Traffic Flow
```
Host → Switch → Controller (Flow Request)
       ↓
Controller: ML Analysis (Normal) → Install Flow Rule
       ↓
Switch: Forward Packet to Destination
       ↓
(Optional) Log to Blockchain: "normal_traffic_logged"
```

### 2. Attack Detection Flow
```
Attacker → Switch → Controller (Flow Request)
           ↓
Controller: Extract Features (SFE, SSIP, RFIP)
           ↓
ML Detector: Classify (Attack Detected!)
           ↓
Mitigation Module: Block Port
           ↓
Blockchain Logger: Record Attack Event
           ↓
           → event_type: "attack_detected"
           → switch_id: "s1"
           → trust_score: 0.2
           → action: "port_blocked"
           → timestamp: 1234567890
```

### 3. Blockchain Logging Flow
```
Event Data (JSON)
    ↓
Fabric Client (Python)
    ↓
    → Option 1: Direct CLI Invoke
       → peer chaincode invoke ...
    
    → Option 2: REST Gateway (Port 3001)
        → HTTP POST http://localhost:3001/api/v1/events
            ↓
        Gateway Server (Node.js)
            ↓
        Fabric SDK (Node.js)
            ↓
Chaincode (Go)
    ↓
    → RecordEvent()
       → Store in Ledger
    
    → UpdateTrustLog()
        → Calculate & Update Trust Score
```

## Component Details

### Ryu Controller Components

```python
controller_blockchain.py
 FlowMonitor Thread (every 2s)
    Request flow stats
    Extract features
    Trigger ML detection

 MLDetector
    Load trained model
    Classify traffic
    Return (prediction, confidence)

 MitigationEngine
    Block malicious ports
    Install drop rules
    Update ARP spoofing detection

 BlockchainLogger
     Connect to Fabric
     Format event data
     Invoke RecordEvent()
```

### ML Detection Pipeline

```
Flow Statistics
    ↓
Feature Extraction
    → SFE (Speed of Flow Entries)
    → SSIP (Speed of Source IPs)
    → RFIP (Ratio of Flow Pairs)
    ↓
Normalization (if needed)
    ↓
ML Model (Decision Tree / SVM / RF / NB)
    ↓
Classification
    → 0 (Normal Traffic)
    → 1 (Attack Traffic)
    ↓
Confidence Score
    ↓
Decision: Trigger Mitigation?
```

### Blockchain Smart Contract Structure

```go
trustlog.go
 Data Structures
    SecurityEvent
       EventID
       EventType
       SwitchID
       Timestamp
       TrustScore
       Action
       Details
   
    TrustLog
        DeviceID
        CurrentTrust
        EventCount
        LastUpdate
        Status

 Functions
    RecordEvent()
    QueryEvent()
    QueryTrustLog()
    QueryEventsBySwitch()
    QueryEventsByType()
    QueryEventsByTimeRange()

 Internal Functions
     updateTrustLog()
```

## Integration Points

### 1. Controller ↔ ML Detector
- **Interface**: Python function calls
- **Data**: [sfe, ssip, rfip] array
- **Return**: (prediction, confidence) tuple

### 2. Controller ↔ Blockchain
- **Interface**: 
  - Direct: Subprocess calls to `peer` CLI
  - Gateway: HTTP POST to REST API (port 3001)
- **Data**: JSON event structure
- **Return**: Success/failure boolean
- **Gateway URL**: `http://localhost:3001`

### 3. Blockchain ↔ Applications
- **Interface**: 
  - Fabric SDK (Python/Node.js/Go)
  - REST Gateway API (port 3001)
- **Operations**: 
  - Invoke chaincode functions
  - Query ledger data
- **REST Gateway Endpoints**:
  - `POST /api/v1/events` - Record security event
  - `GET /api/v1/trust/:deviceId` - Query trust log
  - `GET /api/v1/attacks/recent` - Get recent attacks
  - `POST /api/v1/mitigation/action` - Get mitigation recommendation
  - `GET /api/v1/attacks/coordinated` - Check coordinated attack
  - `POST /api/v1/policy` - Set mitigation policy
  - `GET /api/v1/policy/:policyId` - Get mitigation policy
  - `GET /health` - Health check

## Security Considerations

### 1. Authentication
- Fabric uses MSP (Membership Service Provider)
- TLS for secure communication
- Certificate-based identity

### 2. Access Control
- Chaincode ACLs
- Channel-based isolation
- Organization-based permissions

### 3. Data Integrity
- Cryptographic hashing
- Immutable ledger
- Consensus mechanisms (Raft/Kafka)

## Scalability

### Horizontal Scaling
```
Multiple Controllers (Multi-domain)
    ↓
Shared Blockchain Network
    ↓
Consistent Security View Across Domains
```

### Performance Optimization
- Batch blockchain transactions
- Async logging (non-blocking)
- Local cache for frequent queries
- Connection pooling

## Deployment Scenarios

### Scenario 1: Single Node (Development)
```
One Machine:
 Ryu Controller (port 6633)
 Mininet
 Fabric Network (Multi-org, 2 Peers + Orderer)
 REST Gateway (port 3001)
```

### Scenario 2: Distributed (Production)
```
Machine 1: SDN Controller Cluster (port 6633)
Machine 2: Mininet/Physical Switches
Machine 3-5: Fabric Network (Multi-org, Peers + Orderers)
Machine 6: REST Gateway (port 3001) & Monitoring
```

## Monitoring Points

### 1. Controller Metrics
- Flow table size
- Packet-in rate
- Flow installation latency
- Detection accuracy

### 2. Blockchain Metrics
- Transaction throughput (TPS)
- Transaction latency
- Query latency
- Ledger size

### 3. Network Metrics
- Bandwidth utilization
- Packet loss
- Latency
- Jitter

## Future Enhancements

1. **Multi-domain Federation**
   - Cross-domain trust sharing
   - Distributed attack detection

2. **Advanced ML**
   - Deep Learning models
   - Online learning
   - Anomaly detection

3. **Smart Mitigation**
   - Adaptive rate limiting
   - Traffic rerouting
   - Collaborative filtering

4. **Enhanced Blockchain**
   - Private data collections
   - State-based queries
   - Event subscriptions
