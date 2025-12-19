# BÁO CÁO CHI TIẾT DỰ ÁN SDN-ML-BLOCKCHAIN
## Hệ Thống Phát Hiện và Giảm Thiểu DDoS Sử Dụng Machine Learning và Blockchain

---

## 1. TỔNG QUAN DỰ ÁN

### 1.1. Mục Tiêu
Xây dựng hệ thống phát hiện và giảm thiểu tấn công DDoS trong mạng SDN bằng cách:
- Sử dụng Machine Learning để phát hiện tấn công tự động
- Sử dụng Blockchain (Hyperledger Fabric) để ghi log sự kiện bảo mật
- Tích hợp với SDN Controller (Ryu) để thực thi blocking tự động

### 1.2. Kiến Trúc Tổng Thể
```
┌─────────────────────────────────────────────────────────┐
│              APPLICATION LAYER                           │
│  REST Gateway | CLI Tools | Monitoring Dashboard        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│         CONTROL PLANE (Ryu SDN Controller)              │
│  Flow Monitor → ML Detector → Mitigation Engine        │
│         ↓              ↓              ↓                 │
│   Feature Ext.    Classification    Block Port          │
│   (SFE,SSIP,RFIP)   (ML Models)    (Port-Only)         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│              DATA PLANE (OpenFlow)                      │
│  Switch 1 | Switch 2 | Switch 3 | Switch 4              │
│     ↓         ↓         ↓         ↓                     │
│  Hosts 1-4  Hosts 5-8  Hosts 9-12                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│      BLOCKCHAIN LAYER (Hyperledger Fabric)             │
│  Smart Contract (Chaincode) → Distributed Ledger       │
│  RecordEvent | QueryEvents | GetRecentAttacks          │
└─────────────────────────────────────────────────────────┘
```

### 1.3. Tính Năng Chính
- ✅ Phát hiện DDoS tự động bằng Machine Learning
- ✅ Giảm thiểu tấn công bằng cách block port
- ✅ Ghi log sự kiện vào blockchain (immutable)
- ✅ Hỗ trợ nhiều ML algorithms (Decision Tree, Random Forest, SVM, Naive Bayes)
- ✅ Phát hiện IP spoofing
- ✅ Tự động unblock sau 60 giây

---

## 2. CÁC CÔNG NGHỆ SỬ DỤNG

### 2.1. SDN (Software-Defined Networking)
- **Framework**: Ryu SDN Controller (v4.34+)
- **Protocol**: OpenFlow v1.3
- **Switch**: Open vSwitch (OVS)
- **Mô phỏng**: Mininet
- **Chức năng**: Tách biệt control plane và data plane, quản lý tập trung

### 2.2. Machine Learning
- **Thư viện**: scikit-learn (v1.0.0+)
- **Algorithms hỗ trợ**:
  - **Decision Tree**: Phân loại dựa trên cây quyết định
  - **Random Forest**: Ensemble của nhiều decision trees
  - **Support Vector Machine (SVM)**: Phân loại với kernel RBF
  - **Naive Bayes**: Phân loại xác suất
- **Features**: SFE, SSIP, RFIP (3 features)
- **Format**: Model được lưu dưới dạng .pkl (pickle)
- **Training**: Tự động train nếu không có pre-trained model

### 2.3. Blockchain
- **Platform**: Hyperledger Fabric
- **Language**: 
  - Go (Chaincode/Smart Contract)
  - Node.js (REST Gateway)
  - Python (Fabric Client)
- **Network**: Multi-org, Multi-peer
- **Consensus**: Raft
- **Storage**: LevelDB/CouchDB
- **Chức năng**: Immutable logging, event query

### 2.4. Ngôn Ngữ Lập Trình
- **Python 3.8+**: Controller, ML, Client
- **Go**: Smart Contract (Chaincode)
- **Node.js**: REST Gateway
- **Bash**: Scripts automation

### 2.5. Thư Viện Chính

#### Python Dependencies:
```
ryu>=4.34                    # SDN Controller
scikit-learn>=1.0.0          # Machine Learning
pandas>=1.3.0                # Data processing
numpy>=1.21.0                # Numerical computing
requests>=2.26.0             # HTTP client
joblib>=1.1.0                # Model serialization
matplotlib>=3.4.0            # Visualization
seaborn>=0.11.0              # Statistical visualization
flask>=2.0.0                 # Web framework
flask-cors>=3.0.0            # CORS support
eventlet==0.30.2             # Async networking
urllib3==1.26.15             # HTTP library
```

#### Node.js Dependencies:
```
fabric-network               # Hyperledger Fabric SDK
express                      # REST API framework
```

#### Go Dependencies:
```
fabric-contract-api-go       # Chaincode API
```

---

## 3. LUỒNG HOẠT ĐỘNG CHI TIẾT

### 3.1. Luồng Phát Hiện và Giảm Thiểu Attack

```
┌─────────────────────────────────────────────────────────┐
│ 1. TRAFFIC FLOW                                         │
│    Host → Switch → Controller (Packet-In)              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. FLOW STATISTICS COLLECTION                           │
│    Controller request flow stats từ switch (mỗi 2 giây) │
│    Switch reply với flow statistics                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. FEATURE EXTRACTION                                   │
│    Controller tính toán:                               │
│    - SFE (Speed of Flow Entries)                        │
│    - SSIP (Speed of Source IPs) - per switch            │
│    - RFIP (Ratio of Flow Pairs)                         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 4. ML CLASSIFICATION (GIỐNG TÁC GIẢ GỐC)               │
│    Input: [SFE, SSIP, RFIP]                            │
│    → ML Model predict: label                            │
│    - label: ['0'] (Normal) hoặc ['1'] (Attack)         │
│    - KHÔNG có confidence, KHÔNG có threshold            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 5. DECISION MAKING (ĐƠN GIẢN)                          │
│    Nếu '1' in result:                                   │
│    → ATTACK DETECTED                                    │
│    → Log vào blockchain: "attack_detected"             │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 6. IP SPOOFING DETECTION                                │
│    Trong packet_in_handler:                            │
│    - Kiểm tra IP có trong ARP table của port không     │
│    - Nếu không → IP Spoofing detected                   │
│    - Kiểm tra MAC-to-IP mapping (bảo vệ IP thật)       │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 7. PORT BLOCKING                                        │
│    Nếu phát hiện IP spoofing:                           │
│    → Tạo flow rule: in_port=X, actions=drop             │
│    → Hard timeout: 60 giây                              │
│    → Log vào blockchain: "port_blocked"                 │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 8. AUTO UNBLOCK                                         │
│    Sau 60 giây, flow rule tự động expire                │
│    → Port được unblock tự động                          │
└─────────────────────────────────────────────────────────┘
```

### 3.2. Luồng Normal Traffic

```
1. TRAFFIC FLOW
   Host → Switch → Controller
   
2. FEATURE EXTRACTION
   Tính SFE, SSIP, RFIP
   
3. ML CLASSIFICATION
   ML Model predict: label=0 (Normal)
   
4. LOGGING (Optional)
   Nếu label=0 (Normal):
   → Log vào blockchain: "normal_traffic" (mỗi 30 giây)
   → Không block gì cả
```

### 3.3. Luồng Blockchain Logging

```
┌─────────────────────────────────────────────────────────┐
│ 1. EVENT CREATION                                       │
│    Controller tạo event data (JSON):                   │
│    {                                                    │
│      "event_type": "attack_detected" | ...             │
│      "switch_id": "2",                                 │
│      "timestamp": 1234567890,                           │
│      "features": {                                      │
│        "sfe": 80.0, "ssip": 40.0, "rfip": 0.5          │
│      }                                                  │
│    }                                                    │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. SEND TO BLOCKCHAIN                                   │
│    Option 1: REST Gateway (HTTP POST)                   │
│    → POST http://localhost:3001/api/v1/events          │
│                                                         │
│    Option 2: Direct CLI                                 │
│    → peer chaincode invoke ...                         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. CHAINCODE PROCESSING                                 │
│    Chaincode (Go) nhận event                            │
│    → RecordEvent() function                             │
│    → Lưu vào ledger với key: "EVT-{timestamp}-{id}"    │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 4. LEDGER STORAGE                                       │
│    Event được lưu vào distributed ledger               │
│    → Immutable, tamper-proof                            │
│    → Có thể query sau này                               │
└─────────────────────────────────────────────────────────┘
```

---

## 4. LOGIC VÀ NGUYÊN LÝ HOẠT ĐỘNG

### 4.1. Feature Extraction (Trích Xuất Đặc Trưng)

#### 4.1.1. SFE (Speed of Flow Entries)
```python
SFE = (Current Flow Count - Previous Flow Count) / Time Interval
```
- **Mục đích**: Đo tốc độ tạo flow entries mới
- **Ý nghĩa**: DDoS thường tạo nhiều flow entries nhanh
- **Tính toán**: Per switch, mỗi 2 giây
- **Đơn vị**: flows/second

**Ví dụ**:
- T0: 100 flows
- T2: 150 flows (sau 2 giây)
- SFE = (150 - 100) / 2 = 25 flows/second

#### 4.1.2. SSIP (Speed of Source IPs)
```python
SSIP = (Current Unique Source IPs - Previous Unique Source IPs) / Time Interval
```
- **Mục đích**: Đo tốc độ xuất hiện source IP mới
- **Ý nghĩa**: IP spoofing tạo nhiều source IP mới
- **Tính toán**: Per switch (không còn global)
- **Lưu ý**: Chỉ đếm IP mới, không đếm lại IP cũ
- **Đơn vị**: IPs/second

**Ví dụ**:
- T0: {10.0.0.1, 10.0.0.2} (2 IPs)
- T2: {10.0.0.1, 10.0.0.2, 10.0.0.3, 10.0.0.4} (4 IPs)
- SSIP = (4 - 2) / 2 = 1 IP/second

#### 4.1.3. RFIP (Ratio of Flow Pairs)
```python
RFIP = (Bidirectional Flows × 2) / Total Flow Count
```
- **Mục đích**: Đo tỷ lệ flow có bidirectional traffic
- **Ý nghĩa**: Normal traffic thường có bidirectional, DDoS thường one-way
- **Giá trị**: 0.0 - 1.0 (1.0 = tất cả flows đều bidirectional)
- **Tính toán**: Per switch

**Ví dụ**:
- Total flows: 100
- Bidirectional flows: 30 (có cả forward và reverse)
- RFIP = (30 × 2) / 100 = 0.6

### 4.2. ML Classification Logic

#### 4.2.1. Model Training (GIỐNG TÁC GIẢ GỐC)
```python
Input: dataset/result.csv (sfe, ssip, rfip, label)
Process:
  1. Load CSV data trực tiếp với numpy.loadtxt():
     - dtype='str': Load as strings
     - skiprows=1: Bỏ qua header
  2. Split features và labels:
     - X = data[:, 0:3]  # sfe, ssip, rfip
     - y = data[:, 3]    # label
  3. Train model với algorithm được chọn:
     - Decision Tree: tree.DecisionTreeClassifier()
     - Random Forest: RandomForestClassifier()
     - SVM: svm.SVC()
     - Naive Bayes: GaussianNB() (cần convert sang numeric)
  4. Save model to .pkl file: ml_model_{type}.pkl
```

**Lưu ý**: 
- ❌ KHÔNG có threshold tuning
- ❌ KHÔNG có train/test split
- ❌ KHÔNG có validation
- ✅ Đơn giản: Load → Train → Save

#### 4.2.2. Model Prediction (GIỐNG TÁC GIẢ GỐC)
```python
Input: [sfe, ssip, rfip]
Process:
  1. Load pre-trained model (.pkl)
     - Ưu tiên: Load từ ml_model_{type}.pkl
     - Fallback: Train từ dataset/result.csv
  2. Predict trực tiếp:
     prediction = model.predict(fparams)
     # Trả về: ['0'] (Normal) hoặc ['1'] (Attack)
  3. Decision:
     - Nếu '1' in prediction:
       → ATTACK
     - Nếu '0' in prediction:
       → NORMAL
```

**Lưu ý**:
- ❌ KHÔNG có confidence
- ❌ KHÔNG có threshold
- ❌ KHÔNG có predict_proba()
- ✅ Chỉ dùng model.predict() - đơn giản nhất

**Ví dụ**:
```python
# Controller code
result = ml_detector.classify([sfe, ssip, rfip])
if '1' in result:
    print("Attack detected!")
    mitigation = 1
if '0' in result:
    print("Normal traffic")
```

### 4.3. IP Spoofing Detection Logic

**Note**: IP Spoofing Detection chỉ chạy khi `ENABLE_IP_SPOOFING_DETECTION=1` và `PREVENTION=1`

```python
1. Packet-In từ switch
   - Extract: src_ip, src_mac, in_port, dpid
   
2. Kiểm tra điều kiện:
   - Nếu PREVENTION=0 hoặc ENABLE_IP_SPOOFING_DETECTION=0:
     → Skip IP Spoofing Detection
   - Ngược lại, tiếp tục kiểm tra
   
3. Kiểm tra ARP table:
   - Nếu src_ip không có trong arp_ip_to_port[dpid][in_port]:
     → is_spoofed = True
   - Ngược lại:
     → is_spoofed = False (IP đã được học từ ARP)
   
4. Bảo vệ IP thật của host:
   - Nếu src_mac trong mac_to_ip:
     - Nếu src_ip trong mac_to_ip[src_mac]:
       → is_spoofed = False (IP thật của host)
       → Không block
   
5. Quyết định block:
   - Nếu is_spoofed VÀ port đã có IP được học:
     → Block port
   - Nếu port chưa có IP được học:
     → Không block (tránh block nhầm IP thật chưa được học)
```

**Ví dụ**:
```
Scenario 1: IP Spoofing
- Port 2 đã học IP: 10.0.0.2 (từ ARP)
- Packet đến với IP: 192.168.1.100
- → IP không khớp → is_spoofed = True
- → Block port 2

Scenario 2: IP Thật
- MAC aa:bb:cc:dd:ee:ff đã có IP: 10.0.0.2
- Packet đến với MAC aa:bb:cc:dd:ee:ff, IP: 10.0.0.2
- → IP khớp với MAC → is_spoofed = False
- → Không block
```

### 4.4. Port Blocking Logic

```python
1. Tạo flow rule:
   match = OFPMatch(in_port=portnumber)
   actions = []  # Drop (empty actions = drop)
   
2. Install flow:
   priority = 100 (cao hơn default flows)
   hard_timeout = 60 (tự động xóa sau 60s)
   cookie = unique_flow_number()
   
3. Logging:
   - Log vào console: "🚫 BLOCKING PORT X on switch Y for 60s"
   - Log vào blockchain: "port_blocked" event
```

**Flow Rule Format**:
```
priority=100, in_port=2, actions=drop
```

---

## 5. CÁC THÀNH PHẦN CHÍNH

### 5.1. SDN Controller (`controller_blockchain.py`)

#### 5.1.1. Class: `BlockchainSDNController`
- **Kế thừa**: `app_manager.RyuApp`
- **OpenFlow Version**: v1.3
- **Chức năng chính**:
  - Quản lý switches và flows
  - Thu thập flow statistics (mỗi 2 giây)
  - Trích xuất features (SFE, SSIP, RFIP)
  - Gọi ML detector để phân loại
  - Thực thi blocking khi phát hiện attack
  - Logging vào blockchain

#### 5.1.2. Các Methods Quan Trọng:

**`_flow_monitor()`**:
- Thread chạy liên tục
- Request flow stats từ tất cả switches mỗi 2 giây
- Trigger feature extraction và ML detection

**`flow_stats_reply_handler()`**:
- Xử lý flow statistics reply từ switches
- Tính toán SFE, SSIP, RFIP
- Gọi ML detector để classify
- Quyết định block nếu phát hiện attack
- Logging vào blockchain

**`_speed_of_flow_entries()`**:
- Tính SFE (Speed of Flow Entries)
- So sánh flow count hiện tại với trước đó

**`_speed_of_source_ip()`**:
- Tính SSIP (Speed of Source IPs) - per switch
- Track unique source IPs per switch
- Chỉ đếm IP mới

**`_ratio_of_flowpair()`**:
- Tính RFIP (Ratio of Flow Pairs)
- Đếm bidirectional flows

**`_packet_in_handler()`**:
- Xử lý packet-in từ switches
- Học MAC-to-IP mapping từ ARP
- Phát hiện IP spoofing
- Trigger blocking nếu cần

**`block_port()`**:
- Block port khi phát hiện attack
- Tạo flow rule với hard timeout 60s
- Logging vào blockchain

### 5.2. ML Detector (`ml_detector.py`)

#### 5.2.1. Class: `MLDetector`
- **Chức năng**: Phát hiện DDoS bằng Machine Learning
- **Algorithms hỗ trợ**: Decision Tree, Random Forest, SVM, Naive Bayes
- **Model Storage**: .pkl files trong ryu_app/

#### 5.2.2. Các Methods:

**`__init__()`**:
- Khởi tạo detector với model type
- Load pre-trained model nếu có (.pkl file)
- Nếu không có, train từ dataset/result.csv
- KHÔNG có threshold (đơn giản)

**`train()`**:
- Train model từ CSV data
- Load trực tiếp với numpy.loadtxt()
- KHÔNG có train/test split, KHÔNG có threshold tuning
- Save model to .pkl file

**`classify()`** :
- Predict traffic (normal/attack)
- Input: [sfe, ssip, rfip]
- Output: prediction array (['0'] hoặc ['1'])
- Chỉ dùng model.predict() - KHÔNG có predict_proba()

**`load_model()`**:
- Load pre-trained model từ .pkl file
- Restore model (KHÔNG có threshold)

**`save_model()`**:
- Save trained model to .pkl file
- KHÔNG lưu threshold (vì không có)

### 5.3. Blockchain Components

#### 5.3.1. Smart Contract (`chaincode/trustlog.go`)

**Data Structures**:
```go
type SecurityEvent struct {
    EventID      string
    EventType    string  // attack_detected, port_blocked, normal_traffic
    SwitchID     string
    Timestamp    int64
    TrustScore   float64  // Deprecated, không dùng nữa
    Action       string
    Details      map[string]interface{}
    RecordedBy   string
    RecordedTime int64
}
```

**Functions**:
- `RecordEvent()`: Ghi event vào ledger
- `QueryEvent()`: Query event cụ thể
- `GetRecentAttacks()`: Lấy danh sách attacks gần đây (bao gồm cả port_blocked)
- `QueryEventsBySwitch()`: Query events theo switch
- `QueryEventsByType()`: Query events theo type
- `QueryEventsByTimeRange()`: Query events trong khoảng thời gian

#### 5.3.2. REST Gateway (`gateway_node_server.js`)

**Endpoints**:
- `POST /api/v1/events`: Record security event
- `GET /api/v1/attacks/recent?timeWindow=300`: Get recent attacks
- `GET /health`: Health check

**Configuration**:
- Port: 3001 (default)
- Connection Profile: từ environment variable
- Wallet Path: từ environment variable

#### 5.3.3. Fabric Client (`fabric_client.py`)

**Class**: `BlockchainClient`

**Methods**:
- `record_event()`: Ghi event vào blockchain
- `get_recent_attacks()`: Lấy recent attacks
- `query_event()`: Query event cụ thể
- `query_events_by_switch()`: Query theo switch
- `query_events_by_type()`: Query theo type

**Modes**:
- Gateway mode: Sử dụng REST API
- CLI mode: Sử dụng peer CLI trực tiếp

### 5.4. Topology (`custom_topo.py`)

#### 5.4.1. Multi-Switch Topology
```
                    s1 (Central Switch)
                     |
    +----------------+----------------+
    |                |                |
   s2               s3               s4
    |                |                |
  h1-h4           h5-h8            h9-h12
```

**Chi tiết**:
- **4 switches**: 
  - s1: Central switch (kết nối với tất cả leaf switches)
  - s2, s3, s4: Leaf switches (kết nối với hosts)
- **12 hosts**: h1-h12
- **Bandwidth**: 10 Mbps giữa switches
- **Link**: TCLink với bandwidth limit

**IP Assignment**:
- h1-h4: 10.0.0.1 - 10.0.0.4 (switch s2)
- h5-h8: 10.0.0.5 - 10.0.0.8 (switch s3)
- h9-h12: 10.0.0.9 - 10.0.0.12 (switch s4)

---

## 6. PHƯƠNG THỨC HOẠT ĐỘNG

### 6.1. Khởi Động Hệ Thống

```bash
# 1. Start Blockchain Network
cd fabric-samples/test-network
./network.sh up createChannel

# 2. Deploy Chaincode
cd ../../blockchain
bash ../scripts/deploy_active_chaincode.sh

# 3. Start REST Gateway
cd blockchain
node gateway_node_server.js
# Hoặc: npm start (nếu có package.json)

# 4. Start SDN Controller
cd ..
export APP_TYPE=1
export ML_MODEL_TYPE=random_forest
ryu-manager ryu_app/controller_blockchain.py

# 5. Start Mininet
sudo python3 topology/custom_topo.py
```

### 6.2. Data Collection Mode

**Mục đích**: Thu thập dữ liệu để train ML model

```bash
# Set environment variables
export APP_TYPE=0  # Data collection mode
export TEST_TYPE=0  # Normal traffic (hoặc 1 cho attack)

# Start controller
ryu-manager ryu_app/controller_blockchain.py

# Generate traffic
# Normal: bash scripts/normal_traffic.sh
# Attack: bash scripts/attack_traffic.sh

# Data được lưu vào: dataset/result.csv (vì APP_TYPE=0)
# Format: sfe,ssip,rfip,label (4 cột - ground truth)
```

**Workflow**:
1. Controller thu thập features mỗi 2 giây
2. Ghi vào CSV với label = TEST_TYPE
3. Không có ML detection, không có blocking
4. Dữ liệu dùng để train model sau này

### 6.3. Detection Mode

**Mục đích**: Phát hiện và giảm thiểu DDoS attacks

```bash
# Set environment variables
export APP_TYPE=1  # Detection mode
export ML_MODEL_TYPE=random_forest  # hoặc decision_tree, svm, naive_bayes

# Start controller
ryu-manager ryu_app/controller_blockchain.py

# Generate attack traffic
bash scripts/attack_traffic.sh
# Hoặc trong Mininet:
# mininet> h2 hping3 --rand-source -1 -i u10000 -c 500 10.0.0.3 &

# Hệ thống sẽ:
# 1. Phát hiện attack (ML classification)
# 2. Phát hiện IP spoofing
# 3. Block port
# 4. Log vào blockchain
```

**Workflow**:
1. Controller thu thập features
2. ML model classify traffic
3. Nếu attack detected → log vào blockchain
4. Nếu IP spoofing detected → block port
5. Log blocking action vào blockchain

### 6.4. Blocking Mechanism

#### 6.4.1. Port-Only Blocking
- **Flow Rule**: `in_port=X, actions=drop`
- **Priority**: 100 (cao hơn default flows)
- **Hard Timeout**: 60 giây
- **Kết quả**: Block tất cả traffic từ port đó (không phân biệt IP)

**Ví dụ**:
```
Switch s2, Port 2 bị block:
priority=100, in_port=2, actions=drop

→ Tất cả traffic từ port 2 bị drop
→ Host h2 (port 2) không thể gửi traffic
→ Các host khác (h1, h3, h4) vẫn hoạt động bình thường
```

#### 6.4.2. Tự Động Unblock
- Sau 60 giây, flow rule tự động expire
- Port được unblock tự động
- Cho phép host có cơ hội phục hồi
- Có thể bị block lại nếu tiếp tục attack

---

## 7. TÍNH NĂNG CHÍNH

### 7.0. Hai Cơ Chế Phát Hiện Attack

Hệ thống hỗ trợ **2 cơ chế phát hiện** có thể hoạt động độc lập hoặc kết hợp:

#### 7.0.1. ML Detection (Machine Learning)
- **Mặc định**: BẬT (luôn hoạt động khi APP_TYPE=1)
- **Phương pháp**: Phân tích features (SFE, SSIP, RFIP)
- **Ưu điểm**: Phát hiện các pattern phức tạp, học từ dữ liệu
- **Khi nào dùng**: Phát hiện DDoS dựa trên hành vi traffic

#### 7.0.2. IP Spoofing Detection
- **Mặc định**: TẮT (`ENABLE_IP_SPOOFING_DETECTION=0`)
- **Phương pháp**: Kiểm tra IP với ARP table
- **Ưu điểm**: Phát hiện nhanh IP giả mạo
- **Khi nào dùng**: Khi muốn bảo vệ 2 lớp (IP Spoofing + ML)

**Cấu hình**:
```bash
# Chỉ dùng ML Detection (khuyến nghị cho học tập/nghiên cứu)
ENABLE_IP_SPOOFING_DETECTION=0 ./scripts/start_system.sh

# Dùng cả 2 cơ chế (bảo vệ 2 lớp)
ENABLE_IP_SPOOFING_DETECTION=1 ./scripts/start_system.sh
```

**Xem thêm**: `docs/IP_SPOOFING_DETECTION.md`

### 7.1. ML-Based Detection
- ✅ Hỗ trợ 4 algorithms: Decision Tree, Random Forest, SVM, Naive Bayes
- ✅ Phân loại đơn giản: model.predict() → ['0'] hoặc ['1']
- ✅ Pre-trained model support (.pkl files)
- ✅ Auto-training nếu không có model
- ✅ Load CSV trực tiếp với numpy.loadtxt()

### 7.2. IP Spoofing Detection
- ✅ Phát hiện IP không khớp với ARP table
- ✅ Bảo vệ IP thật của host (MAC-to-IP mapping)
- ✅ Block port khi phát hiện spoofing
- ✅ Chỉ block nếu port đã có IP được học (tránh false positive)
- ✅ Có thể tắt bằng `ENABLE_IP_SPOOFING_DETECTION=0` (mặc định: tắt)
- ✅ Cho phép ML Detection hoạt động độc lập

### 7.3. Blockchain Logging
- ✅ Ghi log tất cả events: attacks, blocking, normal traffic
- ✅ Immutable ledger (tamper-proof)
- ✅ Query recent attacks (bao gồm cả port_blocked)
- ✅ REST API support (port 3001)
- ✅ Gateway mode và CLI mode

### 7.4. Port Blocking
- ✅ Block port number (giống repo tham khảo)
- ✅ Auto unblock sau 60 giây
- ✅ Logging và monitoring
- ✅ Không block port 1 (uplink) trên leaf switches (đã loại bỏ)

### 7.5. Feature Extraction
- ✅ SFE (Speed of Flow Entries) - per switch
- ✅ SSIP (Speed of Source IPs) - per switch
- ✅ RFIP (Ratio of Flow Pairs) - per switch
- ✅ Tính toán mỗi 2 giây

---

## 8. CẤU TRÚC DỮ LIỆU

### 8.1. Feature Vector
```python
[sfe, ssip, rfip]
- sfe: float (Speed of Flow Entries, flows/second)
- ssip: float (Speed of Source IPs, IPs/second)
- rfip: float (0.0-1.0, Ratio of Flow Pairs)
```

### 8.2. ML Model Output
```python
prediction array: ['0'] hoặc ['1']
- '0': Normal traffic
- '1': Attack traffic
- KHÔNG có confidence
```

### 8.3. Blockchain Event Structure

**Attack Detected Event**:
```json
{
  "event_type": "attack_detected",
  "switch_id": "2",
  "timestamp": 1234567890,
  "features": {
    "sfe": 28.0,
    "ssip": 28.0,
    "rfip": 0.0
  }
}
```

**Lưu ý**: ❌ KHÔNG có `confidence` field

**Port Blocked Event**:
```json
{
  "event_type": "port_blocked",
  "switch_id": "2",
  "port": 2,
  "timestamp": 1234567890,
  "reason": "IP Spoofing Attack",
  "action": "port_blocked_for_60s",
  "block_mode": "port_only",
  "src_ip": "192.168.1.100",
  "dst_ip": "10.0.0.3"
}
```

**Normal Traffic Event**:
```json
{
  "event_type": "normal_traffic",
  "switch_id": "2",
  "timestamp": 1234567890,
  "features": {
    "sfe": 5.0,
    "ssip": 2.0,
    "rfip": 0.5
  }
}
```

**Lưu ý**: ❌ KHÔNG có `confidence` field

### 8.4. CSV Data Format

**Training Data** (`dataset/result.csv`):
```
sfe,ssip,rfip,label
10.5,2.3,0.8,0
28.0,15.0,0.1,1
...
```

**Training Data** (`dataset/result.csv` - từ APP_TYPE=0):
```
sfe,ssip,rfip,label
10.5,2.3,0.8,0
28.0,15.0,0.1,1
...
```

**Detection Results** (`data/result.csv` - từ APP_TYPE=1):
```
sfe,ssip,rfip,label
12.3,5.1,0.9,0
31.2,18.5,0.2,1
...
```

Note: Hệ thống tự động phân chia:
- `dataset/result.csv` ← Ground truth (APP_TYPE=0) để train models
- `data/result.csv` ← ML predictions (APP_TYPE=1) để phân tích

---

## 9. CẤU HÌNH VÀ MÔI TRƯỜNG

### 9.1. Environment Variables

```bash
# Application Mode
APP_TYPE=1                    # 0=data collection, 1=detection
TEST_TYPE=0                   # 0=normal, 1=attack (chỉ khi APP_TYPE=0)

# ML Configuration
ML_MODEL_TYPE=decision_tree   # decision_tree (default), random_forest, svm, naive_bayes

# Blockchain Configuration
BLOCKCHAIN_ADAPTER_URL=http://localhost:3001  # REST Gateway URL
BLOCKCHAIN_LOG=true           # Enable blockchain logging

# Prevention
PREVENTION=1                  # Enable DDoS prevention (0=no blocking, 1=block attacks)
ENABLE_IP_SPOOFING_DETECTION=0  # IP Spoofing Detection (0=disabled, 1=enabled)
INTERVAL=2                    # Flow stats collection interval (seconds)
```

### 9.2. File Paths

```
Project Root: /home/obito/SDN_Project/SDN-ML-Blockchain/
├── ryu_app/
│   ├── controller_blockchain.py    # Main controller
│   ├── ml_detector.py              # ML detector
│   └── ml_model_*.pkl              # Pre-trained models
├── blockchain/
│   ├── chaincode/trustlog.go       # Smart contract
│   ├── gateway_node_server.js      # REST Gateway
│   └── fabric_client.py            # Python client
├── dataset/
│   └── result.csv                  # Training data
├── data/
│   └── result.csv                  # Runtime data
├── logs/
│   └── ryu_controller.log          # Controller logs
└── topology/
    └── custom_topo.py               # Mininet topology
```

---

## 10. SCRIPT VÀ CÔNG CỤ

### 10.1. Attack Scripts

**`attack_traffic.sh`**:
- Generic DDoS traffic generator
- ICMP flood + SYN flood
- IP spoofing với --rand-source
- Duration: 120 giây (default)

**`botnet_attack.sh`**:
- Multi-vector botnet attack
- Phases: reconnaissance, SYN/ACK flood, UDP amplification, Slowloris
- Duration: 180 giây (default)
- Jitter: 1-3 giây random

### 10.2. System Scripts

**`start_system.sh`**:
- Khởi động toàn bộ hệ thống
- Check dependencies
- Start blockchain, gateway, controller

**`stop_system.sh`**:
- Dừng toàn bộ hệ thống
- Cleanup processes

**`verify_system.sh`**:
- Kiểm tra hệ thống hoạt động
- Test blockchain connection
- Test ML model

**`recent_attack.sh`**:
- Query recent attacks từ blockchain
- Hiển thị danh sách attacks gần đây

---

## 11. KẾT LUẬN

### 11.1. Điểm Mạnh
- ✅ Tích hợp ML và Blockchain
- ✅ Tự động phát hiện và giảm thiểu DDoS
- ✅ Immutable logging (blockchain)
- ✅ Hỗ trợ nhiều ML algorithms
- ✅ Dễ mở rộng và tùy chỉnh
- ✅ Port-only blocking (đơn giản, hiệu quả)
- ✅ Auto unblock sau 60 giây
- ✅ IP spoofing detection

### 11.2. Hạn Chế
- ⚠️ Block toàn bộ port (không linh hoạt)
- ⚠️ Phụ thuộc vào ML model accuracy
- ⚠️ Blockchain latency (nếu dùng direct CLI)
- ⚠️ Chỉ hỗ trợ 3 features (SFE, SSIP, RFIP)
- ⚠️ Hard timeout cố định (60 giây)

### 11.3. Hướng Phát Triển
- 🔮 Deep Learning models (LSTM, CNN)
- 🔮 Multi-domain federation
- 🔮 Advanced mitigation strategies (rate limiting, traffic rerouting)
- 🔮 Real-time monitoring dashboard
- 🔮 More features (packet size, protocol distribution)
- 🔮 Adaptive timeout (dựa trên attack severity)
- 🔮 Machine-to-machine communication (M2M)

### 11.4. Ứng Dụng Thực Tế
- **Data Centers**: Bảo vệ servers khỏi DDoS
- **IoT Networks**: Phát hiện và giảm thiểu attacks từ compromised devices
- **Enterprise Networks**: Security monitoring và incident response
- **Research**: Nghiên cứu về SDN security và ML-based detection

---

## 12. TÀI LIỆU THAM KHẢO

### 12.1. Công Nghệ
- **Ryu SDN Framework**: https://ryu-sdn.org/
- **Hyperledger Fabric**: https://www.hyperledger.org/use/fabric
- **scikit-learn**: https://scikit-learn.org/
- **Mininet**: http://mininet.org/
- **OpenFlow**: https://opennetworking.org/

### 12.2. Repo Tham Khảo
- **SDN-DDOS-Detection**: https://github.com/vishalsingh45/SDN-DDOS-Detection-and-Mitigation-using-ML-and-Statistical-methods.git

### 12.3. Tài Liệu Dự Án
- `docs/ARCHITECTURE.md`: Kiến trúc hệ thống
- `docs/BLOCKING_MECHANISM_EXPLANATION.md`: Giải thích cơ chế blocking
- `docs/BLOCKCHAIN_ACTIVE_MODE.md`: Blockchain logging mode
- `docs/QUICK_TEST_GUIDE.md`: Hướng dẫn test nhanh
- `docs/MANUAL_TEST_MITIGATION.md`: Hướng dẫn test thủ công

---

**Ngày tạo**: 2025-12-18  
**Phiên bản**: 1.0  
**Tác giả**: SDN-ML-Blockchain Project Team  
**License**: Xem file LICENSE trong project root

---

## PHỤ LỤC

### A. Các File Quan Trọng

**Controller**:
- `ryu_app/controller_blockchain.py`: Main SDN controller
- `ryu_app/ml_detector.py`: ML detection module

**Blockchain**:
- `blockchain/chaincode/trustlog.go`: Smart contract
- `blockchain/gateway_node_server.js`: REST Gateway
- `blockchain/fabric_client.py`: Python client

**Topology**:
- `topology/custom_topo.py`: Mininet topology

**Scripts**:
- `scripts/start_system.sh`: Start system
- `scripts/attack_traffic.sh`: Attack traffic generator
- `scripts/botnet_attack.sh`: Botnet attack generator

### B. Các Port Sử Dụng

- **Ryu Controller**: 6633 (OpenFlow)
- **REST Gateway**: 3001 (HTTP)
- **Fabric Orderer**: 7050
- **Fabric Peer Org1**: 7051
- **Fabric Peer Org2**: 9051

### C. Các Model Files

- `ryu_app/ml_model_decision_tree.pkl`
- `ryu_app/ml_model_random_forest.pkl`
- `ryu_app/ml_model_svm.pkl`
- `ryu_app/ml_model_naive_bayes.pkl`

---

**Kết thúc báo cáo**

