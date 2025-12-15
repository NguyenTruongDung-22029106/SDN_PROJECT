# Hướng Dẫn Chạy Từng Component Riêng Lẻ

> **Manual Setup Guide** - Chạy từng bước để hiểu rõ từng thành phần

---

## Checklist Trước Khi Bắt Đầu

```bash
# 1. Kiểm tra Docker
docker --version
docker ps

# 2. Kiểm tra Node.js
node --version
npm --version

# 3. Kiểm tra Python
python3 --version
pip3 --version

# 4. Kiểm tra quyền file
ls -la /home/obito/SDN_Project/SDN-ML-Blockchain/data/
```

---

## Bước 0: Chuẩn Bị (Chỉ Lần Đầu)

### Fix quyền truy cập file
```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain

# Fix data directory
sudo chown -R $USER:$USER data/
chmod -R 664 data/*.csv
chmod 775 data/

# Fix wallet directory
chmod -R 755 blockchain/wallet/
```

### Cài đặt npm packages (nếu chưa có)
```bash
cd blockchain
npm install
```

### Kiểm tra ML models
```bash
ls -la ryu_app/ml_model_*.pkl

# Nếu không có, train models:
cd ryu_app
python3 << 'EOF'
from ml_detector import MLDetector

# Train Decision Tree
detector = MLDetector(model_type='decision_tree')
detector.train('../dataset/result.csv')
detector.save_model('ml_model_decision_tree.pkl')

# Train Random Forest
detector = MLDetector(model_type='random_forest')
detector.train('../dataset/result.csv')
detector.save_model('ml_model_random_forest.pkl')

# Train SVM
detector = MLDetector(model_type='svm')
detector.train('../dataset/result.csv')
detector.save_model('ml_model_svm.pkl')

# Train Naive Bayes
detector = MLDetector(model_type='naive_bayes')
detector.train('../dataset/result.csv')
detector.save_model('ml_model_naive_bayes.pkl')

print("All models trained successfully!")
EOF
```

---

## COMPONENT 1: Hyperledger Fabric Network

### Terminal 1: Start Fabric Network

```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/fabric-samples/test-network

# Dọn dẹp network cũ (nếu có)
./network.sh down

# Khởi động network với CA
./network.sh up createChannel -c sdnchannel -ca
```

**Đợi 30-60 giây để network khởi động hoàn toàn**

**Kiểm tra containers:**
```bash
docker ps | grep hyperledger

# Phải thấy:
# - peer0.org1.example.com
# - peer0.org2.example.com
# - orderer.example.com
# - ca_org1, ca_org2, ca_orderer
```

### Deploy Chaincode

```bash
# Vẫn trong terminal 1
./network.sh deployCC -ccn trustlog -ccp ../../blockchain/chaincode -ccl go -c sdnchannel
```

**Đợi 2-3 phút cho chaincode build & deploy**

**Verify chaincode đã deploy:**
```bash
# QUAN TRỌNG: Phải set đầy đủ biến môi trường trước khi chạy peer command
# Vẫn trong terminal 1, thư mục fabric-samples/test-network

# Set environment (BẮT BUỘC)
export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=$PWD/../config/

export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051

# Query chaincode (sau khi đã set environment)
peer lifecycle chaincode querycommitted -C sdnchannel -n trustlog

# Phải thấy:
# Committed chaincode definition for chaincode 'trustlog' on channel 'sdnchannel':
# Version: 1.0, Sequence: 1, Endorsement Plugin: escc, Validation Plugin: vscc, Approvals: [Org1MSP: true, Org2MSP: true]
```

** Fabric network OK!** Giữ terminal này mở.

---

## COMPONENT 2: Blockchain Gateway

### Terminal 2: Start Gateway API

```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/blockchain

# Import identity (mỗi lần start network mới)
node import_identity.js

# Phải thấy: "Imported identity User1@org1.example.com into wallet"
```

**Start Gateway:**
```bash
# Option 1: Chạy foreground (xem log trực tiếp)
node gateway_node_server.js

# Option 2: Chạy background
nohup node gateway_node_server.js > gateway.log 2>&1 &

# Xem log (nếu dùng option 2)
tail -f gateway.log
```

** Nếu gặp lỗi `EADDRINUSE` (port 3001 đã được sử dụng):**
```bash
# Dừng gateway cũ
pkill -f "gateway_node_server.js"

# Hoặc kill process trên port 3001
lsof -ti:3001 | xargs kill -9

# Sau đó chạy lại gateway
nohup node gateway_node_server.js > gateway.log 2>&1 &
```

**Đợi 3-5 giây, kiểm tra Gateway:**
```bash
# Trong terminal mới
curl http://localhost:3001/health

# Phải trả về: {"status":"ok"}

# Test POST event
curl -X POST http://localhost:3001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "switch_id": "s1",
    "event_type": "test_event",
    "timestamp": 1732750000,
    "trust_score": 0.8,
    "action": "logged",
    "details": {"test": true}
  }'

# Phải trả về: {"success":true,"txId":"..."}

# Query trust log
curl http://localhost:3001/api/v1/trust/s1

# Phải trả về trust log data
```

** Gateway OK!** Giữ terminal này mở.

---

## COMPONENT 3: Ryu SDN Controller

### Terminal 3: Start Ryu Controller

```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/ryu_app

# Kiểm tra ML models
ls -la ml_model_*.pkl

# Phải có ít nhất: ml_model_decision_tree.pkl
```

**Start Ryu Controller:**
```bash
# Option 1: Chạy foreground (xem log trực tiếp)
ryu-manager --observe-links controller_blockchain.py

# Option 2: Chạy background
nohup ryu-manager --observe-links controller_blockchain.py > ryu_controller.log 2>&1 &

# Xem log (nếu dùng option 2)
tail -f ../logs/ryu_controller.log
```

**Phải thấy log:**
```
 Blockchain client initialized successfully
 ML Detector initialized with DECISION_TREE algorithm
```

**Kiểm tra Ryu đang lắng nghe:**
```bash
# Trong terminal mới
netstat -tln | grep 6633

# Phải thấy: tcp ... 0.0.0.0:6633 ... LISTEN
```

** Ryu Controller OK!** Giữ terminal này mở.

---

## COMPONENT 4: Mininet Network

### Terminal 4: Start Mininet

```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/topology

# Cleanup trước (nếu có Mininet cũ)
sudo mn -c

# Start Mininet với topology
sudo python3 custom_topo.py
```

**Đợi 5-10 giây, Mininet CLI sẽ xuất hiện:**
```
mininet>
```

**Test trong Mininet CLI:**
```bash
# Test connectivity
mininet> pingall

# Test ping giữa 2 hosts
mininet> h1 ping -c 5 h10

# Xem topology
mininet> net

# Xem switches
mininet> nodes
```

** Mininet OK!**

---

## COMPONENT 5: Generate Traffic

### Trong Mininet CLI (Terminal 4)

#### **Normal Traffic**
```bash
# Ping bình thường
mininet> h1 ping -c 10 h10

# HTTP traffic
mininet> h10 python3 -m http.server 8000 &
mininet> h1 curl http://10.0.0.10:8000

# iPerf bandwidth test
mininet> iperf h1 h10
```

#### **Attack Traffic**
```bash
# Single host attack
mininet> h2 bash ../scripts/attack_traffic.sh &

# Multi-host DDoS
mininet> h2 bash ../scripts/attack_traffic.sh &
mininet> h3 bash ../scripts/attack_traffic.sh &
mininet> h9 bash ../scripts/attack_traffic.sh &

# Botnet attack (multi-vector)
mininet> h9 bash ../scripts/botnet_attack.sh &
```

** Dừng Attack Traffic:**
```bash
# Trong Mininet CLI - Dừng tất cả attack
mininet> h2 killall hping3
mininet> h3 killall hping3
mininet> h9 killall hping3
mininet> h9 killall bash

# Hoặc kill tất cả process của host
mininet> h9 killall -9 hping3 bash

# Kiểm tra xem còn process nào không
mininet> h9 ps aux | grep -E "hping3|botnet|attack"
```

**Quan sát:**
- **Terminal 3 (Ryu)**: Sẽ thấy log phát hiện attack
- **Terminal 2 (Gateway)**: Sẽ thấy log ghi event vào blockchain

---

## Dừng Attack Traffic

### Trong Mininet CLI (Khuyến nghị)
```bash
# Dừng attack trên từng host
mininet> h2 killall hping3
mininet> h3 killall hping3
mininet> h9 killall hping3
mininet> h9 killall bash

# Hoặc kill tất cả process
mininet> h9 killall -9 hping3 bash

# Kiểm tra xem còn process nào không
mininet> h9 ps aux | grep -E "hping3|botnet|attack"
```

### Từ Terminal Hệ Thống
```bash
# Kill tất cả hping3 (cần sudo vì chạy trong namespace)
sudo pkill -9 hping3

# Kill tất cả botnet attack scripts
sudo pkill -9 -f botnet_attack
sudo pkill -9 -f attack_traffic

# Kiểm tra
ps aux | grep -E "hping3|botnet|attack" | grep -v grep
```

**Lưu ý:** Script `botnet_attack.sh` mặc định chạy 180 giây (3 phút) rồi tự dừng. Nếu muốn dừng sớm, dùng các lệnh trên.

---

## Monitoring & Debugging

### Xem Flow Tables
```bash
# Trong Mininet CLI
mininet> sh ovs-ofctl dump-flows s1
mininet> sh ovs-ofctl dump-flows s2
```

### Xem Port Status
```bash
mininet> sh ovs-ofctl show s1
mininet> sh ovs-ofctl dump-ports s1
```

### Xem Blockchain Logs
```bash
# Trong terminal mới
docker logs -f peer0.org1.example.com

# Hoặc
docker logs -f orderer.example.com
```

### Xem Gateway Logs
```bash
# Nếu chạy background
tail -f /home/obito/SDN_Project/SDN-ML-Blockchain/blockchain/gateway.log

# Hoặc xem container logs
docker logs -f sdn-blockchain-gateway 2>&1
```

### Xem Ryu Logs
```bash
# Nếu chạy background
tail -f /home/obito/SDN_Project/SDN-ML-Blockchain/ryu_app/ryu_controller.log
```

### Test Gateway API
```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/blockchain
./test_gateway_api.sh
```

---

## Query Blockchain Data

### Setup Environment (Terminal mới)
```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/fabric-samples/test-network

export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=$PWD/../config/

export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051
```

### Query Commands
```bash
# Query trust log của switch s1
peer chaincode query \
    -C sdnchannel \
    -n trustlog \
    -c '{"function":"QueryTrustLog","Args":["s1"]}'

# Query recent attacks
peer chaincode query \
    -C sdnchannel \
    -n trustlog \
    -c '{"function":"GetRecentAttacks","Args":["300"]}'

# Query events by type
peer chaincode query \
    -C sdnchannel \
    -n trustlog \
    -c '{"function":"QueryEventsByType","Args":["attack_detected"]}'
```

---

## Dừng Từng Component

### Stop Mininet (Terminal 4)
```bash
# Trong Mininet CLI
mininet> exit

# Cleanup
sudo mn -c
```

### Stop Ryu Controller (Terminal 3)
```bash
# Nếu chạy foreground: Ctrl+C

# Nếu chạy background:
pkill -f "ryu-manager"
```

### Stop Gateway (Terminal 2)
```bash
# Nếu chạy foreground: Ctrl+C

# Nếu chạy background:
pkill -f "gateway_node_server.js"
```

### Stop Fabric Network (Terminal 1)
```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/fabric-samples/test-network
./network.sh down
```

---

## Restart Một Component

### Restart Gateway
```bash
pkill -f "gateway_node_server.js"
cd /home/obito/SDN_Project/SDN-ML-Blockchain/blockchain
node import_identity.js
node gateway_node_server.js
```

### Restart Ryu
```bash
pkill -f "ryu-manager"
cd /home/obito/SDN_Project/SDN-ML-Blockchain/ryu_app
ryu-manager --observe-links controller_blockchain.py
```

### Restart Mininet
```bash
sudo mn -c
cd /home/obito/SDN_Project/SDN-ML-Blockchain/topology
sudo python3 custom_topo.py
```

---

## Checklist Đầy Đủ

- [ ] **Terminal 1**: Fabric network running (6 containers)
- [ ] **Terminal 2**: Gateway API responding on port 3001
- [ ] **Terminal 3**: Ryu Controller listening on port 6633
- [ ] **Terminal 4**: Mininet CLI active
- [ ] **Files**: CSV files writable (obito:obito)
- [ ] **Models**: ML model files exist (4 .pkl files)
- [ ] **Identity**: Wallet contains User1@org1.example.com

---

## Troubleshooting Từng Component

### Fabric Network Issues
```bash
# Kiểm tra containers
docker ps -a | grep hyperledger

# Restart specific container
docker restart peer0.org1.example.com

# Xem logs
docker logs peer0.org1.example.com 2>&1 | tail -50

# Full reset
./network.sh down
docker system prune -f
./network.sh up createChannel -c sdnchannel -ca
```

### Gateway Issues
```bash
# Check port
lsof -i :3001

# Re-import identity
cd blockchain
node import_identity.js

# Check connection profile
ls -la ../fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/

# Manual test
curl http://localhost:3001/health
```

### Ryu Controller Issues
```bash
# Check port
lsof -i :6633

# Check ML models
ls -la ryu_app/ml_model_*.pkl

# Check permissions
ls -la data/*.csv

# Manual permission fix
sudo chown -R $USER:$USER data/
chmod 664 data/*.csv
```

### Mininet Issues
```bash
# Full cleanup
sudo mn -c
sudo killall -9 controller
sudo killall -9 ovs-testcontroller

# Check OVS
sudo ovs-vsctl show

# Restart OVS (nếu cần)
sudo systemctl restart openvswitch-switch
```

---

## Tips

1. **Luôn chạy theo thứ tự**: Fabric → Gateway → Ryu → Mininet
2. **Đợi mỗi component khởi động xong** trước khi chạy component tiếp theo
3. **Kiểm tra logs** để đảm bảo không có lỗi
4. **Test từng bước** bằng curl/ping để verify
5. **Dùng multiple terminals** để dễ theo dõi

---

## Quick Commands Reference

```bash
# Check all ports
sudo netstat -tlnp | grep -E "6633|3001|7051|9051|7050"

# Check all processes
ps aux | grep -E "ryu-manager|gateway_node_server|mininet"

# Check Docker
docker ps | grep hyperledger

# Test connectivity
curl http://localhost:3001/health
```

---

**Với hướng dẫn này, bạn có thể chạy từng component riêng lẻ và hiểu rõ từng bước!**
