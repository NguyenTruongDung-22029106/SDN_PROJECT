# SDN-ML-Blockchain System Diagrams Index

---

## 1. System Overview Architecture

**Mô tả**: Kiến trúc tổng thể hệ thống bao gồm Application Layer, Control Plane, Data Plane, và Blockchain Layer.

**File**: [`diagrams/01_system_overview.mmd`](diagrams/01_system_overview.mmd)

```mermaid
graph TB
    subgraph "Application Layer"
        REST[REST Gateway<br/>Port 3001]
        CLI[CLI Tools]
        MONITOR[Monitoring Dashboard]
    end
    
    subgraph "Control Plane - Ryu SDN Controller"
        FLOW[Flow Monitor<br/>INTERVAL=2s]
        FEATURE[Feature Extraction<br/>SFE, SSIP, RFIP]
        ML[ML Detector<br/>Decision Tree/RF/SVM/NB]
        MITIGATION[Attack Mitigation<br/>Block Port]
        BCLOG[Blockchain Logger]
        SPOOFING[IP Spoofing Detection<br/>Optional]
    end
    
    subgraph "Data Plane"
        SWITCH1[Switch 1]
        SWITCH2[Switch 2]
        SWITCH3[Switch 3]
        HOST1[Hosts 1-3]
        HOST2[Hosts 4-6]
        HOST3[Hosts 7-10]
    end
    
    subgraph "Blockchain Layer - Hyperledger Fabric"
        CHAINCODE[Smart Contract<br/>trustlog.go]
        PEER1[Peer 0 Org1]
        PEER2[Peer 1 Org1]
        ORDERER[Orderer]
        LEDGER[(Distributed Ledger)]
    end
    
    HOST1 --> SWITCH1
    HOST2 --> SWITCH2
    HOST3 --> SWITCH3
    
    SWITCH1 -.OpenFlow.-> FLOW
    SWITCH2 -.OpenFlow.-> FLOW
    SWITCH3 -.OpenFlow.-> FLOW
    
    FLOW --> FEATURE
    FEATURE --> ML
    ML -->|Attack Detected| MITIGATION
    ML -->|Normal Traffic| BCLOG
    MITIGATION --> BCLOG
    MITIGATION -.Drop Rules.-> SWITCH1
    MITIGATION -.Drop Rules.-> SWITCH2
    MITIGATION -.Drop Rules.-> SWITCH3
    
    SPOOFING -.Optional.-> MITIGATION
    
    BCLOG --> REST
    REST --> CHAINCODE
    CLI --> CHAINCODE
    
    CHAINCODE --> PEER1
    CHAINCODE --> PEER2
    PEER1 --> LEDGER
    PEER2 --> LEDGER
    ORDERER --> LEDGER
    
    LEDGER -.Query.-> MONITOR
    
    style ML fill:#ff9999
    style MITIGATION fill:#ffcc99
    style CHAINCODE fill:#99ccff
    style LEDGER fill:#99ff99
```

---

## 2. Attack Detection Flow

**Mô tả**: Luồng phát hiện và xử lý tấn công DDoS từ khi phát hiện đến khi ghi log vào Blockchain.

**File**: [`diagrams/02_attack_detection_flow.mmd`](diagrams/02_attack_detection_flow.mmd)

```mermaid
sequenceDiagram
    participant Attacker
    participant Switch
    participant Controller
    participant Feature
    participant ML
    participant Mitigation
    participant Blockchain
    
    Attacker->>Switch: Malicious Traffic
    Switch->>Controller: Packet-In Event
    
    Note over Controller: Flow Monitor (every 2s)
    Controller->>Switch: Request Flow Stats
    Switch-->>Controller: Flow Statistics
    
    Controller->>Feature: Extract Features
    Note over Feature: SFE = len(flows) / INTERVAL<br/>SSIP = new_ips / INTERVAL<br/>RFIP = pairs / total_flows
    Feature-->>Controller: [sfe, ssip, rfip]
    
    Controller->>ML: classify([sfe, ssip, rfip])
    Note over ML: model.predict()<br/>NO confidence<br/>NO threshold
    ML-->>Controller: ['1'] (Attack)
    
    alt Attack Detected (if '1' in result)
        Controller->>Mitigation: Block Port
        Note over Mitigation: Install Drop Rule<br/>hard_timeout=60s<br/>in_port=X, actions=drop
        Mitigation->>Switch: Install Flow Rule
        Switch-->>Mitigation: Rule Installed
        
        Controller->>Blockchain: Log Attack Event
        Note over Blockchain: event_type: attack_detected<br/>action: port_blocked<br/>features: {sfe, ssip, rfip}
        Blockchain-->>Controller: Event Recorded
    else Normal Traffic (if '0' in result)
        Controller->>Blockchain: Log Normal (every 30s)
        Note over Blockchain: event_type: normal_traffic_logged
    end
```

---

## 3. ML Detection Pipeline

**Mô tả**: Pipeline chi tiết của quá trình phát hiện tấn công bằng Machine Learning.

**File**: [`diagrams/03_ml_detection_pipeline.mmd`](diagrams/03_ml_detection_pipeline.mmd)

```mermaid
flowchart TD
    START([Flow Statistics]) --> EXTRACT[Extract Features]
    
    EXTRACT --> SFE[SFE = len flows / INTERVAL]
    EXTRACT --> SSIP[SSIP = new_ips / INTERVAL]
    EXTRACT --> RFIP[RFIP = pairs / total_flows]
    
    SFE --> COMBINE[Combine Features]
    SSIP --> COMBINE
    RFIP --> COMBINE
    
    COMBINE --> ARRAY["[sfe, ssip, rfip]"]
    
    ARRAY --> LOAD{Model Loaded?}
    
    LOAD -->|Yes| PREDICT[model.predict]
    LOAD -->|No| TRAIN[Train from dataset/result.csv]
    TRAIN --> PREDICT
    
    PREDICT --> RESULT{Result?}
    
    RESULT -->|'1' in result| ATTACK[🚨 ATTACK DETECTED]
    RESULT -->|'0' in result| NORMAL[✓ Normal Traffic]
    
    ATTACK --> LOG1[Log to Blockchain<br/>event_type: attack_detected]
    ATTACK --> BLOCK{PREVENTION=1?}
    BLOCK -->|Yes| MITIGATION[Block Port<br/>hard_timeout=60s]
    BLOCK -->|No| NOMITIGATE[No Action]
    
    NORMAL --> LOG2[Log to Blockchain<br/>every 30s]
    
    LOG1 --> WRITE1[Write to data/result.csv<br/>if APP_TYPE=1]
    LOG2 --> WRITE2[Write to dataset/result.csv<br/>if APP_TYPE=0]
    
    MITIGATION --> END([End])
    NOMITIGATE --> END
    WRITE1 --> END
    WRITE2 --> END
    
    style ATTACK fill:#ff6666
    style NORMAL fill:#66ff66
    style PREDICT fill:#6699ff
    style MITIGATION fill:#ff9966
```

---

## 4. Blockchain Layer Architecture

**Mô tả**: Kiến trúc chi tiết của lớp Blockchain sử dụng Hyperledger Fabric.

**File**: [`diagrams/04_blockchain_layer.mmd`](diagrams/04_blockchain_layer.mmd)

```mermaid
graph TB
    subgraph "Controller Layer"
        CTRL[Ryu Controller]
        FABRIC_CLIENT[Fabric Client Python]
    end
    
    subgraph "Gateway Layer"
        REST_API[REST Gateway<br/>Node.js Express<br/>Port 3001]
    end
    
    subgraph "Fabric Network"
        subgraph "Chaincode"
            RECORD[RecordEvent]
            QUERY[QueryEvent]
            QUERY_SWITCH[QueryEventsBySwitch]
            QUERY_TYPE[QueryEventsByType]
            QUERY_TIME[QueryEventsByTimeRange]
        end
        
        subgraph "Peers"
            PEER0[Peer0 Org1]
            PEER1[Peer1 Org1]
        end
        
        ORDERER[Orderer]
        
        subgraph "Storage"
            LEDGER[(Immutable Ledger)]
            STATE[(State Database)]
        end
    end
    
    CTRL --> FABRIC_CLIENT
    FABRIC_CLIENT -->|Option 1: Direct CLI| RECORD
    FABRIC_CLIENT -->|Option 2: REST API| REST_API
    
    REST_API --> RECORD
    REST_API --> QUERY
    REST_API --> QUERY_SWITCH
    REST_API --> QUERY_TYPE
    REST_API --> QUERY_TIME
    
    RECORD --> PEER0
    RECORD --> PEER1
    QUERY --> PEER0
    QUERY_SWITCH --> PEER0
    QUERY_TYPE --> PEER0
    QUERY_TIME --> PEER0
    
    PEER0 --> ORDERER
    PEER1 --> ORDERER
    
    ORDERER --> LEDGER
    PEER0 --> STATE
    PEER1 --> STATE
    
    style RECORD fill:#ff9999
    style LEDGER fill:#99ff99
    style REST_API fill:#9999ff
```

---

## 5. SecurityEvent Data Structure

**Mô tả**: Cấu trúc dữ liệu SecurityEvent được lưu trữ trong Blockchain.

**File**: [`diagrams/05_data_structure.mmd`](diagrams/05_data_structure.mmd)

```mermaid
classDiagram
    class SecurityEvent {
        +string EventID
        +string EventType
        +string SwitchID
        +int64 Timestamp
        +string Action
        +map Details
        +string RecordedBy
        +int64 RecordedTime
        +RecordEvent()
        +QueryEvent()
        +QueryEventsBySwitch()
        +QueryEventsByType()
        +QueryEventsByTimeRange()
    }
    
    class Details {
        +string host_id
        +string src_ip
        +int src_port
        +string dst_ip
        +int dst_port
        +string protocol
        +string reason
        +float sfe
        +float ssip
        +float rfip
        +string ml_model
        +string prediction
    }
    
    class EventTypes {
        <<enumeration>>
        attack_detected
        port_blocked
        switch_connected
        switch_disconnected
        normal_traffic_logged
        mitigation_action
    }
    
    class Actions {
        <<enumeration>>
        port_blocked
        flow_dropped
        traffic_allowed
        alert_generated
        none
    }
    
    SecurityEvent --> Details : contains
    SecurityEvent --> EventTypes : uses
    SecurityEvent --> Actions : uses
    
    note for SecurityEvent "NO TrustScore field\n(removed in latest version)\n\nPassive logging only\nNO decision making"
    
    note for Details "Features (sfe, ssip, rfip)\nonly in attack_detected events\n\nml_model and prediction\nonly when ML detection used"
```

---

## 6. Data Collection and Training Workflow

**Mô tả**: Quy trình thu thập dữ liệu và huấn luyện ML model.

**File**: [`diagrams/06_data_collection_training.mmd`](diagrams/06_data_collection_training.mmd)

```mermaid
flowchart LR
    subgraph "Collection Mode APP_TYPE=0"
        START1[Start System<br/>APP_TYPE=0<br/>TEST_TYPE=0/1]
        RUN1[Run Topology<br/>normal/attack]
        COLLECT1[Controller Collects<br/>Features + Label]
        WRITE1[Write to<br/>dataset/result.csv]
    end
    
    subgraph "Training Phase"
        TRAIN[Train ML Models<br/>python3 ml_detector.py]
        LOAD[Load dataset/result.csv]
        SPLIT[NO train/test split<br/>Use all data]
        FIT[model.fit X, y]
        SAVE[Save model.pkl<br/>decision_tree.pkl<br/>random_forest.pkl<br/>svm.pkl<br/>naive_bayes.pkl]
    end
    
    subgraph "Detection Mode APP_TYPE=1"
        START2[Start System<br/>APP_TYPE=1<br/>PREVENTION=1]
        RUN2[Run Topology<br/>attack traffic]
        DETECT[ML Detects<br/>model.predict]
        BLOCK[Block if '1' in result]
        WRITE2[Write to<br/>data/result.csv]
    end
    
    START1 --> RUN1
    RUN1 --> COLLECT1
    COLLECT1 --> WRITE1
    
    WRITE1 -.Manual.-> TRAIN
    TRAIN --> LOAD
    LOAD --> SPLIT
    SPLIT --> FIT
    FIT --> SAVE
    
    SAVE -.Model Ready.-> START2
    START2 --> RUN2
    RUN2 --> DETECT
    DETECT --> BLOCK
    BLOCK --> WRITE2
    
    style WRITE1 fill:#99ccff
    style SAVE fill:#ff9999
    style BLOCK fill:#ffcc99
```

---

## 7. Production Deployment Architecture

**Mô tả**: Kiến trúc triển khai hệ thống trong môi trường Production.

**File**: [`diagrams/07_production_deployment.mmd`](diagrams/07_production_deployment.mmd)

```mermaid
graph TB
    subgraph "Network Layer"
        INTERNET[Internet]
        FIREWALL[Firewall]
        ROUTER[Router]
    end
    
    subgraph "SDN Infrastructure"
        CTRL_CLUSTER[Controller Cluster<br/>Active-Standby]
        CTRL1[Ryu Controller 1<br/>Port 6653]
        CTRL2[Ryu Controller 2<br/>Port 6653]
        
        SWITCH_FABRIC[OpenFlow Switch Fabric]
        SW1[Switch 1]
        SW2[Switch 2]
        SW3[Switch 3]
        SW4[Switch 4]
    end
    
    subgraph "Blockchain Infrastructure"
        ORG1[Organization 1]
        PEER0_1[Peer0 Org1]
        PEER1_1[Peer1 Org1]
        
        ORG2[Organization 2]
        PEER0_2[Peer0 Org2]
        
        ORDERER_CLUSTER[Orderer Cluster<br/>Raft Consensus]
        ORD1[Orderer 1]
        ORD2[Orderer 2]
        ORD3[Orderer 3]
    end
    
    subgraph "Application Layer"
        GATEWAY[REST Gateway<br/>Load Balanced<br/>Port 3001]
        MONITOR[Monitoring<br/>Grafana + Prometheus]
        ADMIN[Admin Dashboard]
    end
    
    subgraph "Storage Layer"
        DB1[(CouchDB<br/>Peer0 Org1)]
        DB2[(CouchDB<br/>Peer1 Org1)]
        DB3[(CouchDB<br/>Peer0 Org2)]
    end
    
    INTERNET --> FIREWALL
    FIREWALL --> ROUTER
    ROUTER --> SW1
    ROUTER --> SW2
    
    SW1 --> SW3
    SW2 --> SW4
    
    SW1 -.OpenFlow.-> CTRL1
    SW2 -.OpenFlow.-> CTRL1
    SW3 -.OpenFlow.-> CTRL2
    SW4 -.OpenFlow.-> CTRL2
    
    CTRL1 --> GATEWAY
    CTRL2 --> GATEWAY
    
    GATEWAY --> PEER0_1
    GATEWAY --> PEER1_1
    GATEWAY --> PEER0_2
    
    PEER0_1 --> DB1
    PEER1_1 --> DB2
    PEER0_2 --> DB3
    
    PEER0_1 --> ORD1
    PEER1_1 --> ORD2
    PEER0_2 --> ORD3
    
    ORD1 --> ORD2
    ORD2 --> ORD3
    
    GATEWAY --> MONITOR
    PEER0_1 --> MONITOR
    PEER1_1 --> MONITOR
    
    ADMIN --> GATEWAY
    
    style CTRL1 fill:#ff9999
    style GATEWAY fill:#99ccff
    style ORD1 fill:#99ff99
```

---

## 8. IP Spoofing Detection vs ML Detection

**Mô tả**: So sánh và phân biệt giữa cơ chế phát hiện IP Spoofing và ML Detection.

**File**: [`diagrams/08_ip_spoofing_vs_ml.mmd`](diagrams/08_ip_spoofing_vs_ml.mmd)

```mermaid
flowchart TD
    START([Packet-In Event]) --> CHECK_SPOOF{ENABLE_IP_SPOOFING_DETECTION=1?}
    
    CHECK_SPOOF -->|Yes| SPOOF_CHECK[Check ARP Table]
    CHECK_SPOOF -->|No| FLOW_MON[Wait for Flow Monitor]
    
    SPOOF_CHECK --> IS_SPOOFED{IP in ARP table?}
    
    IS_SPOOFED -->|No - Spoofed| VERIFY[Verify MAC-IP mapping]
    IS_SPOOFED -->|Yes - Legitimate| FLOW_MON
    
    VERIFY --> KNOWN{Known host IP?}
    KNOWN -->|Yes| FLOW_MON
    KNOWN -->|No| BLOCK_SPOOF[🚫 Block Port<br/>Reason: IP Spoofing]
    
    BLOCK_SPOOF --> LOG_SPOOF[Log to Blockchain<br/>event_type: port_blocked]
    LOG_SPOOF --> END1([End - Blocked by IP Spoofing Detection])
    
    FLOW_MON --> EXTRACT[Extract Features<br/>SFE, SSIP, RFIP]
    EXTRACT --> ML[ML Classification<br/>model.predict]
    
    ML --> RESULT{Result?}
    
    RESULT -->|'1' - Attack| BLOCK_ML[🚫 Block Port<br/>Reason: DDoS Attack]
    RESULT -->|'0' - Normal| NORMAL[✓ Normal Traffic]
    
    BLOCK_ML --> LOG_ML[Log to Blockchain<br/>event_type: attack_detected]
    LOG_ML --> END2([End - Blocked by ML])
    
    NORMAL --> LOG_NORMAL[Log to Blockchain<br/>every 30s]
    LOG_NORMAL --> END3([End - Allowed])
    
    style BLOCK_SPOOF fill:#ff6666
    style BLOCK_ML fill:#ff9966
    style NORMAL fill:#66ff66
    style CHECK_SPOOF fill:#ffcc99
```

---

## 9. Component Interaction Diagram

**Mô tả**: Sơ đồ tương tác chi tiết giữa tất cả các thành phần trong hệ thống.

**File**: [`diagrams/09_component_interaction.mmd`](diagrams/09_component_interaction.mmd)

```mermaid
sequenceDiagram
    participant Host
    participant Switch
    participant Controller
    participant FlowMonitor
    participant FeatureExtractor
    participant MLDetector
    participant Mitigation
    participant Blockchain
    participant Gateway
    
    Host->>Switch: Send Packet
    Switch->>Controller: Packet-In (no matching flow)
    Controller->>Switch: Install Default Flow
    
    loop Every 2 seconds
        FlowMonitor->>Switch: Request Flow Stats
        Switch-->>FlowMonitor: Flow Statistics
        FlowMonitor->>FeatureExtractor: Process Stats
        FeatureExtractor-->>FlowMonitor: [sfe, ssip, rfip]
        
        FlowMonitor->>MLDetector: classify([sfe, ssip, rfip])
        
        alt Model exists
            MLDetector-->>FlowMonitor: ['0'] or ['1']
        else No model
            MLDetector->>MLDetector: Train from dataset
            MLDetector-->>FlowMonitor: ['0'] or ['1']
        end
        
        alt Attack Detected ('1' in result)
            FlowMonitor->>Mitigation: Block Attack
            Mitigation->>Switch: Install Drop Rule
            Switch-->>Mitigation: Rule Installed
            
            Mitigation->>Blockchain: Log Attack
            Blockchain->>Gateway: POST /api/v1/events
            Gateway-->>Blockchain: Event Recorded
        else Normal Traffic ('0' in result)
            FlowMonitor->>Blockchain: Log Normal (every 30s)
            Blockchain->>Gateway: POST /api/v1/events
            Gateway-->>Blockchain: Event Recorded
        end
    end
```

---

## 10. Feature Extraction Process

**Mô tả**: Quy trình chi tiết trích xuất các đặc trưng SFE, SSIP, RFIP.

**File**: [`diagrams/10_feature_extraction.mmd`](diagrams/10_feature_extraction.mmd)

```mermaid
flowchart TD
    START([Flow Statistics from Switch]) --> PARSE[Parse Flow Stats]
    
    PARSE --> COUNT_FLOWS[Count Total Flows]
    PARSE --> EXTRACT_IPS[Extract Source IPs]
    PARSE --> EXTRACT_PAIRS[Extract Flow Pairs]
    
    subgraph "SFE Calculation"
        COUNT_FLOWS --> LOOP1[Loop through flows]
        LOOP1 --> INCREMENT1[Increment counter]
        INCREMENT1 --> SFE_CALC[SFE = count / INTERVAL]
    end
    
    subgraph "SSIP Calculation"
        EXTRACT_IPS --> COMPARE[Compare with old_ssip_len]
        COMPARE --> NEW_IPS[Count new IPs]
        NEW_IPS --> SSIP_CALC[SSIP = new_ips / INTERVAL]
        SSIP_CALC --> UPDATE_OLD[Update old_ssip_len]
    end
    
    subgraph "RFIP Calculation"
        EXTRACT_PAIRS --> COUNT_PAIRS[Count unique pairs]
        COUNT_PAIRS --> TOTAL_FLOWS[Get total flows]
        TOTAL_FLOWS --> RFIP_CALC[RFIP = pairs / total_flows]
        RFIP_CALC --> HANDLE_ZERO{total_flows == 0?}
        HANDLE_ZERO -->|Yes| SET_ZERO[RFIP = 0]
        HANDLE_ZERO -->|No| KEEP_RFIP[Keep calculated RFIP]
    end
    
    SFE_CALC --> COMBINE[Combine Features]
    UPDATE_OLD --> COMBINE
    SET_ZERO --> COMBINE
    KEEP_RFIP --> COMBINE
    
    COMBINE --> ARRAY["[sfe, ssip, rfip]"]
    ARRAY --> WRITE_CSV{APP_TYPE?}
    
    WRITE_CSV -->|0 - Collection| WRITE_DATASET[Write to dataset/result.csv<br/>with TEST_TYPE as label]
    WRITE_CSV -->|1 - Detection| WRITE_DATA[Write to data/result.csv<br/>with ML prediction as label]
    
    ARRAY --> ML[Send to ML Detector]
    
    style SFE_CALC fill:#99ccff
    style SSIP_CALC fill:#99ff99
    style RFIP_CALC fill:#ffcc99
    style ARRAY fill:#ff9999
```

---

## 11. System Operation Modes

**Mô tả**: State machine mô tả các chế độ hoạt động của hệ thống.

**File**: [`diagrams/11_system_modes.mmd`](diagrams/11_system_modes.mmd)

```mermaid
stateDiagram-v2
    [*] --> CheckMode: Start System
    
    CheckMode --> CollectionMode: APP_TYPE=0
    CheckMode --> DetectionMode: APP_TYPE=1
    
    state CollectionMode {
        [*] --> CollectNormal: TEST_TYPE=0
        [*] --> CollectAttack: TEST_TYPE=1
        
        CollectNormal --> ExtractFeatures: Monitor Traffic
        CollectAttack --> ExtractFeatures: Monitor Traffic
        
        ExtractFeatures --> WriteDataset: [sfe, ssip, rfip, label]
        WriteDataset --> dataset/result.csv
        
        dataset/result.csv --> [*]: Continue Collection
    }
    
    state DetectionMode {
        [*] --> LoadModel: Check for .pkl file
        
        LoadModel --> UseModel: Model exists
        LoadModel --> TrainModel: No model
        
        TrainModel --> UseModel: Training complete
        
        UseModel --> MonitorTraffic: Ready
        MonitorTraffic --> ExtractFeaturesRT: Every 2s
        ExtractFeaturesRT --> Classify: [sfe, ssip, rfip]
        
        Classify --> Normal: ['0']
        Classify --> Attack: ['1']
        
        Normal --> LogNormal: Every 30s
        Attack --> CheckPrevention: Immediate
        
        CheckPrevention --> Block: PREVENTION=1
        CheckPrevention --> LogOnly: PREVENTION=0
        
        Block --> LogAttack
        LogOnly --> LogAttack
        
        LogNormal --> WriteData
        LogAttack --> WriteData
        
        WriteData --> data/result.csv
        data/result.csv --> MonitorTraffic: Continue
    }
    
    CollectionMode --> TrainManual: Manual Training
    TrainManual --> DetectionMode: Models Ready
    
    DetectionMode --> [*]: Stop System
    CollectionMode --> [*]: Stop System
    
    note right of CollectionMode
        Purpose: Collect labeled data
        Output: dataset/result.csv
        Label: TEST_TYPE (0 or 1)
    end note
    
    note right of DetectionMode
        Purpose: Real-time detection
        Output: data/result.csv
        Label: ML prediction (0 or 1)
    end note
```

---

## 12. ML Model Comparison

**Mô tả**: So sánh các thuật toán Machine Learning được sử dụng trong hệ thống.

**File**: [`diagrams/12_ml_model_comparison.mmd`](diagrams/12_ml_model_comparison.mmd)

```mermaid
graph TD
    subgraph "Input"
        FEATURES["Features: [sfe, ssip, rfip]"]
    end
    
    subgraph "ML Models"
        DT[Decision Tree<br/>✓ Default Model<br/>✓ Fast<br/>✓ Interpretable<br/>✓ No scaling needed]
        RF[Random Forest<br/>✓ Ensemble method<br/>✓ High accuracy<br/>✓ Robust to overfitting<br/>✓ No scaling needed]
        SVM[Support Vector Machine<br/>✓ Good for small datasets<br/>✓ Kernel: RBF<br/>✓ Gamma: scale<br/>⚠ Slower training]
        NB[Naive Bayes<br/>✓ Very fast<br/>✓ Probabilistic<br/>✓ Good for real-time<br/>⚠ Assumes independence]
    end
    
    subgraph "Training Process"
        LOAD[Load dataset/result.csv]
        PARSE[Parse: numpy.loadtxt<br/>dtype='str', skiprows=1]
        SPLIT_XY[Split X features, y labels]
        FIT[model.fit X, y]
        SAVE[Save to .pkl file]
    end
    
    subgraph "Prediction Process"
        LOAD_MODEL[Load .pkl file]
        PREDICT[model.predict features]
        RESULT["Result: ['0'] or ['1']"]
    end
    
    subgraph "Output"
        DECISION{if '1' in result}
        DECISION -->|Yes| ATTACK_OUT[🚨 Attack Detected]
        DECISION -->|No| NORMAL_OUT[✓ Normal Traffic]
    end
    
    FEATURES --> DT
    FEATURES --> RF
    FEATURES --> SVM
    FEATURES --> NB
    
    DT --> LOAD
    RF --> LOAD
    SVM --> LOAD
    NB --> LOAD
    
    LOAD --> PARSE
    PARSE --> SPLIT_XY
    SPLIT_XY --> FIT
    FIT --> SAVE
    
    SAVE -.Model Ready.-> LOAD_MODEL
    LOAD_MODEL --> PREDICT
    PREDICT --> RESULT
    RESULT --> DECISION
    
    style DT fill:#99ff99
    style RF fill:#99ccff
    style SVM fill:#ffcc99
    style NB fill:#ff9999
    style ATTACK_OUT fill:#ff6666
    style NORMAL_OUT fill:#66ff66
```

---


