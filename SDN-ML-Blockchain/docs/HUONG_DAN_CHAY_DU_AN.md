# Hướng Dẫn Chạy Dự Án SDN-ML-Blockchain

> **Tài liệu hướng dẫn chi tiết cách khởi động, giám sát và quản lý hệ thống phát hiện DDoS sử dụng SDN, Machine Learning và Blockchain**

---

## Mục Lục

1. [Yêu Cầu Hệ Thống](#yêu-cầu-hệ-thống)
2. [Cài Đặt Ban Đầu](#cài-đặt-ban-đầu)
3. [Khởi Động Hệ Thống](#khởi-động-hệ-thống)
4. [Xem Log & Monitoring](#xem-log--monitoring)
5. [Query Dữ Liệu Blockchain](#query-dữ-liệu-blockchain)
6. [Sử Dụng REST API](#sử-dụng-rest-api)
7. [Kiểm Tra Mạng](#kiểm-tra-mạng)
8. [Dừng Hệ Thống](#dừng-hệ-thống)
9. [Troubleshooting](#troubleshooting)

---

## Yêu Cầu Hệ Thống

### Hardware
- **RAM**: Tối thiểu 8GB (khuyến nghị 16GB)
- **CPU**: 4 cores trở lên
- **Disk**: 50GB trống

### Software
- **OS**: Ubuntu 20.04/22.04 LTS
- **Docker**: 20.10+ (chỉ dùng cho Hyperledger Fabric test-network, không cần hiểu Docker sâu)
- **Docker Compose**: 1.29+ (tùy chọn, chỉ cần nếu bạn muốn tự chạy `configs/docker-compose.yml`)
- **Python**: 3.8+
- **Node.js**: 18+
- **Go**: 1.21+

### Kiểm tra các dependency
```bash
# Kiểm tra Docker
docker --version
docker-compose --version

# Kiểm tra Python
python3 --version
pip3 --version

# Kiểm tra Node.js
node --version
npm --version

# Kiểm tra Go
go version

# Kiểm tra Mininet
sudo mn --version

# Kiểm tra Ryu
ryu --version
```

---

---

## Cài Đặt Ban Đầu

### Bước 1: Clone Repository
```bash
cd /home/obito/SDN_Project
git clone <repository-url> SDN-ML-Blockchain
cd SDN-ML-Blockchain
```

### Bước 2: Cài Đặt Python Dependencies
```bash
pip3 install -r requirements.txt
```

### Bước 3: Cài Đặt Blockchain Components
```bash
# Tải Hyperledger Fabric binaries
cd fabric-samples
curl -sSL https://bit.ly/2ysbOFE | bash -s -- 2.5.0 1.5.5

# Thêm vào PATH (thêm vào ~/.bashrc)
export PATH=$PATH:$(pwd)/bin
```

### Bước 4: Cài Đặt Node.js Dependencies (cho Gateway)
```bash
cd blockchain
npm install
cd ..
```

---

## Khởi Động Hệ Thống

### **Phương Án 1: Khởi động đầy đủ (4 Terminals)**

#### **Terminal 1: Blockchain Network**
```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/fabric-samples/test-network

# Dọn dẹp network cũ (nếu có)
./network.sh down

# Khởi động Fabric network + tạo channel
./network.sh up createChannel -c sdnchannel -ca

# Deploy smart contract (chaincode)
./network.sh deployCC -ccn trustlog -ccp ../../blockchain/chaincode -ccl go -c sdnchannel

# Thành công khi thấy:
# "Chaincode definition committed on channel 'sdnchannel'"
```

**Xác nhận Blockchain đã chạy:**
```bash
# Kiểm tra containers
docker ps | grep hyperledger

# Nên thấy:
# - peer0.org1.example.com
# - peer0.org2.example.com
# - orderer.example.com
# - ca_org1, ca_org2
```

#### **Terminal 2: Blockchain Gateway (Optional)**
```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/blockchain

# Chạy Node.js Gateway Server
node gateway_node_server.js

# Gateway sẽ lắng nghe trên: http://localhost:3001

# Thành công khi thấy:
# "Fabric Node Gateway adapter listening on port 3001"
# "Available endpoints:"
```

**Hoặc chạy Python Gateway:**
```bash
python3 gateway_server.py
```

#### **Terminal 3: Ryu SDN Controller**
```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/ryu_app

# Khởi động controller với blockchain integration
ryu-manager --observe-links controller_blockchain.py

# Controller sẽ lắng nghe trên port 6633

# Thành công khi thấy trên console:
# "connected socket"
# "ML Detector initialized with model: decision_tree"
# "Blockchain client initialized"
```

**Cấu hình controller (qua biến môi trường):**

Trong file `controller_blockchain.py`, các tham số chính được đọc từ biến môi trường:

- `APP_TYPE`:
  - `0`: **Data collection** (ghi label theo `TEST_TYPE` vào CSV để huấn luyện)
  - `1`: **Detection mode** (dùng ML model để phát hiện tấn công, ghi kết quả vào CSV)
- `TEST_TYPE` (chỉ dùng khi `APP_TYPE=0`):
  - `0`: normal traffic
  - `1`: attack traffic

Ví dụ:
```bash
# Thu thập data normal
export APP_TYPE=0
export TEST_TYPE=0

# Thu thập data attack
export APP_TYPE=0
export TEST_TYPE=1

# Chế độ phát hiện tấn công
export APP_TYPE=1
unset TEST_TYPE  # không cần dùng trong detection
```

Các tham số khác (như `PREVENTION`, `BLOCKCHAIN_LOG`, `INTERVAL`) vẫn có thể chỉnh trực tiếp trong code nếu cần, nhưng luồng chính **APP_TYPE/TEST_TYPE** nên cấu hình qua biến môi trường như trên.

#### **Terminal 4: Mininet Network**
```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/topology

# Khởi động topology (cần sudo)
sudo python3 custom_topo.py

# Thành công khi thấy Mininet CLI:
# mininet>
```

**Trong Mininet CLI, test kết nối:**
```bash
# Test ping
mininet> h1 ping -c 3 h10

# Test connectivity toàn bộ
mininet> pingall

# Xem topology
mininet> net

# Xem nodes
mininet> nodes

# Xem links
mininet> links
```

---

### **Phương Án 2: Khởi động tự động (Script)**

```bash
# Sử dụng script tự động
cd /home/obito/SDN_Project/SDN-ML-Blockchain
bash scripts/run.sh
```

---

## Generate Traffic

### **Traffic Bình Thường**
```bash
# Trong Mininet CLI
mininet> h1 ping -c 10 h10
mininet> h1 iperf h10

# Hoặc chạy script
mininet> h1 bash ../scripts/normal_traffic.sh &
```

### **Traffic Tấn Công**
```bash
# Attack từ single host
mininet> h2 bash ../scripts/attack_traffic.sh &

# Attack từ nhiều hosts (DDoS distributed)
mininet> h2 bash ../scripts/attack_traffic.sh &
mininet> h3 bash ../scripts/attack_traffic.sh &
mininet> h9 bash ../scripts/attack_traffic.sh &

# Botnet attack (multi-vector)
mininet> h9 bash ../scripts/botnet_attack.sh &
```

### **Mixed Traffic (Normal + Attack)**
```bash
# Terminal 1 trong Mininet
mininet> h1 bash ../scripts/normal_traffic.sh &

# Terminal 2 trong Mininet
mininet> h2 bash ../scripts/attack_traffic.sh &
```

---

## Xem Log & Monitoring

### **1. Log Ryu Controller**

**Xem log trên console:**
```bash
# Log sẽ hiển thị trực tiếp ở terminal chạy ryu-manager
# Bao gồm:
# - Packet-in events
# - ML detection results
# - Attack mitigation actions
# - Blockchain logging status
```

**Xem log file (chuẩn hiện tại):**
```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain

# Real-time monitoring
tail -f logs/ryu_controller.log

# Xem 100 dòng cuối
tail -n 100 logs/ryu_controller.log

# Search cho attack events
grep "ATTACK" logs/ryu_controller.log

# Search cho blockchain events
grep -i "blockchain" logs/ryu_controller.log
```

**Log quan trọng cần chú ý (ví dụ):**
```
 "✓ Normal Traffic (Switch 1)"
 "🚨 ATTACK DETECTED! (Switch 1, SFE=80.0, SSIP=40.0, RFIP=0.50)"
 "Port blocked: 1:2"
 "Event logged to blockchain: attack_detected"
```

---

### **2. Log Blockchain**

#### **Peer Logs (Org1)**
```bash
# Xem log peer0 của Org1
docker logs peer0.org1.example.com

# Real-time monitoring (50 dòng cuối)
docker logs -f peer0.org1.example.com --tail 50

# Search chaincode invocations
docker logs peer0.org1.example.com 2>&1 | grep "trustlog"

# Search errors
docker logs peer0.org1.example.com 2>&1 | grep "ERROR"
```

#### **Peer Logs (Org2)**
```bash
docker logs peer0.org2.example.com --tail 50
docker logs -f peer0.org2.example.com
```

#### **Orderer Logs**
```bash
# Xem log orderer
docker logs orderer.example.com --tail 50

# Real-time
docker logs -f orderer.example.com

# Search block creation
docker logs orderer.example.com 2>&1 | grep "Created block"
```

#### **Gateway Logs**
```bash
# Xem log gateway container
docker logs sdn-blockchain-gateway

# Real-time monitoring
docker logs -f sdn-blockchain-gateway --tail 100

# Search API calls
docker logs sdn-blockchain-gateway 2>&1 | grep "POST /api"
```

#### **CA (Certificate Authority) Logs**
```bash
# CA Org1
docker logs ca_org1

# CA Org2
docker logs ca_org2
```

---

### **3. System Monitoring**

#### **Docker Containers Status**
```bash
# Liệt kê containers đang chạy
docker ps

# Format đẹp hơn
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Xem tất cả containers (kể cả stopped)
docker ps -a
```

#### **Resource Usage**
```bash
# CPU, Memory, Network usage
docker stats

# Không stream (chỉ xem 1 lần)
docker stats --no-stream

# Chỉ xem specific containers
docker stats peer0.org1.example.com orderer.example.com
```

#### **Disk Usage**
```bash
# Xem Docker disk usage
docker system df

# Chi tiết
docker system df -v
```

#### **Network Inspection**
```bash
# Xem Docker networks
docker network ls

# Inspect Fabric network
docker network inspect fabric_test
```

---

## Query Dữ Liệu Blockchain

### **Setup Environment (Chạy 1 lần/session)**

```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/fabric-samples/test-network

# Set environment variables cho Org1
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051
export ORDERER_CA=${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

**Tip:** Lưu vào script `setup_env.sh`:
```bash
#!/bin/bash
# File: setup_env.sh
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051
export ORDERER_CA=${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

Sau đó:
```bash
source setup_env.sh
```

---

### **Các Query Phổ Biến (LevelDB backend)**

> **Lưu ý:** Test-network hiện tại dùng **LevelDB**, nên các hàm rich query như  
> `QueryEventsByType`, `QueryEventsBySwitch`, `QueryEventsByTimeRange`, `QueryAllEvents`  
> **sẽ lỗi** với thông báo:  
> `ExecuteQuery not supported for leveldb`.
>
> Thay vào đó, hãy dùng các hàm đã được thiết kế cho LevelDB (`QueryTrustLog`, `GetAllEvents`, `GetRecentAttacks`)
> hoặc sử dụng REST API Gateway để lọc thêm ở phía client.

#### **1. Query Trust Log của Switch**
```bash
# Query trust log của switch có dpid = 1 (dùng ID số, không phải "s1")
peer chaincode query \
    -C sdnchannel \
    -n trustlog \
  -c '{"Args":["QueryTrustLog","1"]}'

# Output mẫu:
# {
#   "device_id": "1",
#   "current_trust": 1,
#   "event_count": 1,
#   "last_update": 1765818005,
#   "status": "trusted"
# }
```

#### **2. Lấy danh sách events (LevelDB friendly)**
```bash
# Lấy tất cả events (cẩn thận nếu data lớn)
peer chaincode query \
    -C sdnchannel \
    -n trustlog \
  -c '{"Args":["GetAllEvents"]}'

# Lấy các attack events gần đây trong 300 giây
peer chaincode query \
    -C sdnchannel \
    -n trustlog \
  -c '{"Args":["GetRecentAttacks","300"]}'
```

#### **3. Lọc events theo switch ở phía client (gợi ý)**

Thay vì query trực tiếp theo switch (không hỗ trợ trên LevelDB), bạn có thể:

1. Lấy recent attacks qua REST:
```bash
   curl -s "http://localhost:3001/api/v1/attacks/recent?timeWindow=300" | jq .
```
2. Hoặc lọc theo `switch_id`:
```bash
   curl -s "http://localhost:3001/api/v1/attacks/recent?timeWindow=300" \
     | jq '.attacks[] | select(.switch_id=="1")'
```

---

### **Format Query Results (với jq)**

```bash
# Cài jq nếu chưa có
sudo apt install jq

# Query và format JSON đẹp
peer chaincode query \
    -C sdnchannel \
    -n trustlog \
  -c '{"Args":["QueryTrustLog","1"]}' | jq .

# Extract specific field
peer chaincode query \
    -C sdnchannel \
    -n trustlog \
  -c '{"Args":["QueryTrustLog","1"]}' | jq '.current_trust'

# Đếm số attack events gần đây (vd: 300 giây)
peer chaincode query \
    -C sdnchannel \
    -n trustlog \
  -c '{"Args":["GetRecentAttacks","300"]}' | jq '. | length'
```

---

### **Invoke Chaincode (Write Operations)**

```bash
# Record event thủ công
peer chaincode invoke \
    -o localhost:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    --tls --cafile $ORDERER_CA \
    -C sdnchannel \
    -n trustlog \
    --peerAddresses localhost:7051 \
    --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
    --peerAddresses localhost:9051 \
    --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt \
    -c '{"Args":[
        "RecordEvent",
        "test_event_123",
        "manual_test",
        "1",
        "1732723456",
        "0.5",
        "manual_logged",
        "{\"test\":true}"
    ]}'

# Thành công khi thấy:
# "Chaincode invoke successful. result: status:200"
```

---

## Sử Dụng REST API

### **Gateway API Endpoints**

#### **1. Health Check**
```bash
# Kiểm tra gateway đang chạy
curl http://localhost:3001/health

# Output: {"status":"ok"}
```

#### **2. API Info**
```bash
# Xem thông tin API
curl http://localhost:3001/api/v1/info

# Pretty print
curl -s http://localhost:3001/api/v1/info | jq .
```

---

### **Record Event via REST API**

```bash
# POST event mới
curl -X POST http://localhost:3001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "switch_id": "s1",
    "event_type": "attack_detected",
    "timestamp": 1732723456,
    "action": "block_port",
    "details": {
      "src_ip": "10.0.0.2",
      "dst_ip": "10.0.0.10",
      "port": 80,
      "protocol": "TCP"
    }
  }'

# Output mẫu:
# {
# "success": true,
# "event_id": "event_1732723456_s1_attack",
# "message": "Event recorded successfully"
# }
```

**Test với nhiều events:**
```bash
# Attack event
curl -X POST http://localhost:3001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "switch_id": "s2",
    "event_type": "attack_detected",
    "timestamp": 1732723500,
    "action": "port_blocked",
    "details": {"attacker_ip": "10.0.0.5"}
  }'

# Normal event
curl -X POST http://localhost:3001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "switch_id": "s1",
    "event_type": "normal_traffic",
    "timestamp": 1732723600,
    "action": "allowed",
    "details": {}
  }'
```

---

### **Query via REST API**

#### **Query Trust Score**
```bash
# Query trust của switch s1
curl http://localhost:3001/api/v1/trust/s1

# Pretty print
curl -s http://localhost:3001/api/v1/trust/s1 | jq .

# Output mẫu:
# {
# "device_id": "s1",
# "current_trust": 0.75,
# "event_count": 20,
# "last_update": 1732723456,
# "status": "active"
# }
```

#### **Query Events**
```bash
# Query by type
curl http://localhost:3001/api/v1/events?type=attack_detected

# Query by switch
curl http://localhost:3001/api/v1/events?switch=s1

# Query by time range
curl "http://localhost:3001/api/v1/events?start=1732700000&end=1732800000"

# Combined filters
curl "http://localhost:3001/api/v1/events?switch=s1&type=attack_detected"
```

#### **Statistics**
```bash
# Get statistics
curl http://localhost:3001/api/v1/stats

# Pretty print
curl -s http://localhost:3001/api/v1/stats | jq .

# Output mẫu:
# {
# "total_events": 150,
# "attack_events": 25,
# "normal_events": 125,
# "switches": 4
# }
```

---

### **Test Script cho API**

Tạo file `test_api.sh`:
```bash
#!/bin/bash
# File: test_api.sh

BASE_URL="http://localhost:3001/api/v1"

echo "=== Testing Gateway API ==="

# 1. Health check
echo -e "\n1. Health Check:"
curl -s http://localhost:3001/health | jq .

# 2. Record attack event
echo -e "\n2. Recording attack event:"
curl -s -X POST $BASE_URL/events \
  -H "Content-Type: application/json" \
  -d '{
    "switch_id": "s1",
    "event_type": "attack_detected",
    "timestamp": '$(date +%s)',
    "action": "blocked",
    "details": {"test": true}
  }' | jq .

# 3. Query trust
echo -e "\n3. Querying trust for s1:"
curl -s $BASE_URL/trust/s1 | jq .

# 4. Query events
echo -e "\n4. Querying attack events:"
curl -s "$BASE_URL/events?type=attack_detected" | jq '. | length'

echo -e "\n=== Test Complete ==="
```

Chạy:
```bash
chmod +x test_api.sh
./test_api.sh
```

---

## Kiểm Tra Mạng

### **OpenFlow Commands (trong Mininet CLI)**

#### **Xem Flow Tables**
```bash
# Xem flow rules của switch 1
mininet> sh ovs-ofctl dump-flows s1

# Xem flow rules của tất cả switches
mininet> sh ovs-ofctl dump-flows s1
mininet> sh ovs-ofctl dump-flows s2
mininet> sh ovs-ofctl dump-flows s3
mininet> sh ovs-ofctl dump-flows s4

# Format đẹp hơn
mininet> sh ovs-ofctl dump-flows s1 --protocols=OpenFlow13
```

**Ý nghĩa các trường trong flow:**
```
cookie=0x0, duration=10.5s, table=0, n_packets=5, n_bytes=490,
priority=1,in_port=1 actions=output:2

# cookie: ID của flow
# duration: Thời gian flow tồn tại
# n_packets: Số packets match
# n_bytes: Tổng bytes
# priority: Độ ưu tiên
# in_port: Port đầu vào
# actions: Hành động (forward, drop, etc.)
```

#### **Xem Port Status**
```bash
# Port info
mininet> sh ovs-ofctl show s1

# Output sẽ hiển thị:
# - Port numbers
# - MAC addresses
# - Link status (UP/DOWN)
# - Speed, duplex
```

#### **Xem Port Statistics**
```bash
# Port statistics
mininet> sh ovs-ofctl dump-ports s1

# Chi tiết hơn
mininet> sh ovs-ofctl dump-ports-desc s1
```

#### **Xem Group Tables**
```bash
mininet> sh ovs-ofctl dump-groups s1
```

#### **Delete Flow Rules (nếu cần)**
```bash
# Xóa tất cả flows của switch
mininet> sh ovs-ofctl del-flows s1

# Xóa flow cụ thể theo port
mininet> sh ovs-ofctl del-flows s1 in_port=1
```

---

### **Network Testing**

#### **Connectivity Tests**
```bash
# Ping giữa 2 hosts
mininet> h1 ping -c 5 h10

# Ping tất cả hosts
mininet> pingall

# Ping với kích thước packet khác
mininet> h1 ping -c 3 -s 1000 h10
```

#### **Bandwidth Tests**
```bash
# iPerf test
mininet> iperf h1 h10

# iPerf với thời gian cụ thể
mininet> h1 iperf -c 10.0.0.10 -t 10

# UDP test
mininet> h1 iperf -c 10.0.0.10 -u -b 10M
```

#### **Traceroute**
```bash
mininet> h1 traceroute h10
```

#### **Network Information**
```bash
# Xem topology
mininet> net

# Xem nodes
mininet> nodes

# Xem links
mininet> links

# Xem dump info
mininet> dump
```

---

### **Packet Capture**

#### **Capture trên Switch Interface**
```bash
# Trong terminal riêng (không phải Mininet CLI)
sudo tcpdump -i s1-eth1 -w capture.pcap

# Với filter
sudo tcpdump -i s1-eth1 'tcp port 80' -w http_capture.pcap

# Xem real-time
sudo tcpdump -i s1-eth1 -n
```

#### **Capture trên Host Interface**
```bash
# Trong Mininet CLI
mininet> h1 tcpdump -i h1-eth0 -w h1_capture.pcap &

# Stop capture
mininet> h1 pkill tcpdump
```

#### **Analyze Capture với tshark**
```bash
# Đọc capture file
tshark -r capture.pcap

# Filter HTTP
tshark -r capture.pcap -Y "http"

# Statistics
tshark -r capture.pcap -q -z io,stat,1
```

---

### **Host Commands (trong Mininet CLI)**

#### **Execute Command trên Host**
```bash
# Chạy command trên h1
mininet> h1 ifconfig

# Xem routing table
mininet> h1 route -n

# Xem ARP table
mininet> h1 arp -n

# Xem IP address
mininet> h1 ip addr show
```

#### **Open Shell trên Host**
```bash
# Mở xterm window
mininet> xterm h1

# Trong xterm window có thể chạy các lệnh bình thường
```

#### **Background Processes**
```bash
# Chạy HTTP server
mininet> h10 python3 -m http.server 80 &

# Test với curl
mininet> h1 curl http://10.0.0.10
```

---

## Dừng Hệ Thống

### **Dừng từng Component**

#### **1. Dừng Mininet**
```bash
# Trong Mininet CLI
mininet> exit

# Cleanup Mininet
sudo mn -c

# Kill tất cả processes liên quan
sudo killall -9 controller mn
```

#### **2. Dừng Ryu Controller**
```bash
# Trong terminal chạy Ryu: Ctrl+C

# Hoặc kill process
pkill -f "ryu-manager"

# Xác nhận đã stop
ps aux | grep ryu
```

#### **3. Dừng Gateway**
```bash
# Trong terminal chạy Gateway: Ctrl+C

# Hoặc stop container
docker stop sdn-blockchain-gateway

# Hoặc kill Node.js process
pkill -f "node gateway"
```

#### **4. Dừng Blockchain Network**
```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/fabric-samples/test-network

# Dừng network
./network.sh down

# Xác nhận containers đã stop
docker ps | grep hyperledger
# Không nên thấy container nào
```

---

### **Restart Toàn Bộ Hệ Thống**

```bash
#!/bin/bash
# File: restart_all.sh

echo "=== Stopping all components ==="

# Stop Fabric
cd /home/obito/SDN_Project/SDN-ML-Blockchain/fabric-samples/test-network
./network.sh down

# Cleanup Mininet
sudo mn -c

# Kill processes
sudo killall -9 ryu-manager node python3

echo "=== Starting Fabric network ==="
./network.sh up createChannel -c sdnchannel -ca
./network.sh deployCC -ccn trustlog -ccp ../../blockchain/chaincode -ccl go -c sdnchannel

echo "=== Fabric network ready ==="
echo "Now start Ryu controller and Mininet manually"
```

Chạy:
```bash
chmod +x restart_all.sh
./restart_all.sh
```

---

### **Clean Up (Full Reset)**

```bash
#!/bin/bash
# File: full_cleanup.sh

echo "=== Full system cleanup ==="

# Stop everything
cd /home/obito/SDN_Project/SDN-ML-Blockchain/fabric-samples/test-network
./network.sh down

# Clean Mininet
sudo mn -c

# Remove Docker volumes (cẩn thận!)
docker volume prune -f

# Remove unused containers
docker container prune -f

# Remove unused images
docker image prune -a -f

# Clean logs
cd /home/obito/SDN_Project/SDN-ML-Blockchain/ryu_app
rm -f *.log

echo "=== Cleanup complete ==="
```

** Warning:** Script này sẽ xóa tất cả data trên blockchain!

---

## Troubleshooting

### **Lỗi: "creator org unknown"**

**Nguyên nhân:** Gateway chưa có identity certificate

**Giải pháp:**
```bash
# Import identity vào gateway
docker exec -it sdn-blockchain-gateway node import_identity.js

# Restart gateway
docker restart sdn-blockchain-gateway

# Xác nhận
docker logs sdn-blockchain-gateway | grep "Connected"
```

---

### **Lỗi: "port already in use"**

**Nguyên nhân:** Port 6633 (Ryu) hoặc 3001 (Gateway) đã bị dùng

**Giải pháp:**
```bash
# Tìm process đang dùng port 6633
sudo lsof -i :6633

# Kill process
sudo fuser -k 6633/tcp

# Tương tự cho port 3001
sudo fuser -k 3001/tcp

# Hoặc kill all
sudo killall -9 ryu-manager node
```

---

### **Lỗi: "peer0.org1.example.com không chạy"**

**Kiểm tra:**
```bash
# Xem containers
docker ps -a | grep peer0.org1

# Nếu container Exited, xem logs
docker logs peer0.org1.example.com

# Start lại peer
docker start peer0.org1.example.com

# Hoặc restart toàn bộ network
cd fabric-samples/test-network
./network.sh down
./network.sh up createChannel -c sdnchannel -ca
```

---

### **Lỗi: "chaincode not found"**

**Nguyên nhân:** Chaincode chưa được deploy hoặc deploy sai

**Giải pháp:**
```bash
# Verify chaincode
peer lifecycle chaincode queryinstalled

# Nếu không thấy, deploy lại
cd fabric-samples/test-network
./network.sh deployCC -ccn trustlog -ccp ../../blockchain/chaincode -ccl go -c sdnchannel

# Verify committed
peer lifecycle chaincode querycommitted -C sdnchannel
```

---

### **Lỗi: "Mininet cannot connect to controller"**

**Nguyên nhân:** Ryu controller chưa chạy hoặc port sai

**Giải pháp:**
```bash
# Kiểm tra Ryu đang chạy
ps aux | grep ryu-manager

# Kiểm tra port
sudo netstat -tlnp | grep 6633

# Trong Mininet, test controller
mininet> sh ovs-vsctl show

# Nếu không kết nối, set controller thủ công
mininet> sh ovs-vsctl set-controller s1 tcp:127.0.0.1:6633
```

---

### **Lỗi: "ML model file not found"**

**Nguyên nhân:** File model chưa được train hoặc path sai

**Giải pháp:**
```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/ryu_app

# Kiểm tra file model
ls -la *.pkl

# Nếu không có, train model
python3 -c "
from ml_detector import MLDetector
detector = MLDetector(model_type='decision_tree')
detector.train('../dataset/result.csv')
detector.save_model('ml_model_decision_tree.pkl')
"

# Verify
ls -la ml_model_decision_tree.pkl
```

---

### **Lỗi: "Permission denied" khi chạy Mininet**

**Giải pháp:**
```bash
# Phải dùng sudo
sudo python3 topology/custom_topo.py

# Hoặc add user vào group
sudo usermod -aG sudo $USER

# Logout và login lại
```

---

### **Lỗi: "Docker daemon not running"**

**Giải pháp:**
```bash
# Start Docker service
sudo systemctl start docker

# Enable auto-start
sudo systemctl enable docker

# Verify
sudo systemctl status docker

# Add user to docker group (để không cần sudo)
sudo usermod -aG docker $USER

# Logout và login lại
```

---

### **Diagnostic Commands**

#### **Check System Status**
```bash
#!/bin/bash
# File: check_status.sh

echo "=== System Status Check ==="

echo -e "\n1. Docker Status:"
sudo systemctl status docker | grep Active

echo -e "\n2. Docker Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}"

echo -e "\n3. Ports in Use:"
sudo netstat -tlnp | grep -E ':(6633|3001|7051|7050)'

echo -e "\n4. Ryu Process:"
ps aux | grep ryu-manager | grep -v grep

echo -e "\n5. Mininet Status:"
sudo mn -c 2>&1 | head -5

echo -e "\n=== Check Complete ==="
```

#### **Network Diagnostics**
```bash
# Test connectivity to Fabric
curl -k https://localhost:7051
curl -k https://localhost:9051

# Test gateway
curl http://localhost:3001/health

# Check DNS
nslookup localhost
```

---

## **Checklist Khởi Động**

Trước khi chạy hệ thống, đảm bảo:

- [ ] Docker đang chạy: `sudo systemctl status docker`
- [ ] Không có containers cũ: `docker ps -a`
- [ ] Port 6633 trống: `sudo lsof -i :6633`
- [ ] Port 3001 trống: `sudo lsof -i :3001`
- [ ] Mininet đã cleanup: `sudo mn -c`
- [ ] Python dependencies đã cài: `pip3 list | grep scikit-learn`
- [ ] ML model file tồn tại: `ls ryu_app/*.pkl`

---

## **Support & Contact**

Nếu gặp vấn đề:

1. Kiểm tra logs theo hướng dẫn trên
2. Xem phần Troubleshooting
3. Chạy `check_status.sh` để chẩn đoán
4. Reset hệ thống với `restart_all.sh`

---

## **Tài Liệu Tham Khảo**

- [ARCHITECTURE.md](ARCHITECTURE.md) - Kiến trúc chi tiết
- [QUICK_START.md](QUICK_START.md) - Hướng dẫn nhanh
- [README.md](../README.md) - Tổng quan dự án
- [Hyperledger Fabric Docs](https://hyperledger-fabric.readthedocs.io/)
- [Ryu Documentation](https://ryu.readthedocs.io/)
- [Mininet Walkthrough](http://mininet.org/walkthrough/)

---

**Cập nhật lần cuối:** November 27, 2025

**Version:** 1.0.0

---

 **Tài liệu này cung cấp đầy đủ các lệnh cần thiết để vận hành hệ thống SDN-ML-Blockchain**
