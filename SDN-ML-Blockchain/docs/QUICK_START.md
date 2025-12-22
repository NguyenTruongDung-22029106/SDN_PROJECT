# Quick Start Guide - Chạy Dự Án Không Bị Lỗi

## Quy Trình Chạy Chuẩn (3 Bước Đơn Giản)

### Bước 1: Khắc phục lỗi (nếu lần đầu hoặc gặp vấn đề)
```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain
bash scripts/fix_common_issues.sh
```

**Script này sẽ tự động:**
- Fix quyền file (Permission Denied)
- Re-import blockchain identity
- Giải phóng port bị chiếm
- Dọn dẹp Mininet cũ
- Restart Docker nếu cần
- Cài đặt npm/pip packages thiếu

---

### Bước 2: Khởi động toàn bộ hệ thống
```bash
bash scripts/start_system.sh
```

**Script này sẽ:**
1.  Kiểm tra prerequisites (Docker, Node.js, Python)
2.  Dọn dẹp processes cũ
3.  Fix file permissions
4.  Start Fabric network + deploy chaincode
5.  Import identity và start Gateway (port 3001)
6.  Start Ryu Controller (port 6633)

**Thời gian:** ~2-3 phút

**Kết quả khi thành công:**
```
=========================================
  System Started Successfully! 
=========================================

Running Services:
  • Fabric Network: 
  • Gateway API:  (http://localhost:3001)
  • Ryu Controller:  (port 6633)
```

---

### Bước 3: Kiểm tra trạng thái
```bash
bash scripts/check_status.sh
```

**Xem:**
- Status của Fabric containers
- Gateway API health
- Ryu Controller
- Port usage
- ML models
- File permissions

---

## Test Hệ Thống

### Test Gateway API
```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/blockchain
./test_gateway_api.sh
```

### Start Mininet (Terminal riêng)
```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/topology
sudo python3 custom_topo.py
```

### Generate Traffic (trong Mininet CLI)
```bash
# Normal traffic
mininet> h1 ping -c 10 h10

# Attack traffic
mininet> h2 bash ../scripts/attack_traffic.sh &
```

---

## Dừng Hệ Thống

```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain
bash scripts/stop_system.sh
```

---

## Xem Logs

### Gateway logs
```bash
tail -f /home/obito/SDN_Project/SDN-ML-Blockchain/logs/gateway.log
```

### Ryu Controller logs
```bash
tail -f /home/obito/SDN_Project/SDN-ML-Blockchain/logs/ryu_controller.log
```

### CSV files: Data collection and training

**IMPORTANT:** Hệ thống tự động phân chia file theo mode để tách biệt ground truth và predictions.

**File paths theo APP_TYPE:**

- **`dataset/result.csv`** ← Chỉ ghi khi **APP_TYPE=0** (Collection mode)
  - Format: `sfe,ssip,rfip,label` (4 cột)
  - Chứa ground truth data để train ML models
  - Label = `TEST_TYPE` (0=normal, 1=attack)
  - ML Detector đọc từ file này để train

- **`data/result.csv`** ← Chỉ ghi khi **APP_TYPE=1** (Detection mode)
  - Format: `sfe,ssip,rfip,label` (4 cột)
  - Chứa kết quả phân loại của ML models
  - Label = kết quả prediction (0=normal, 1=attack)
  - Dùng để phân tích hiệu suất detection

- **`data/switch_<id>_*.csv`** (Per-switch monitoring - cả 2 modes):
  - `data/switch_<id>_data.csv` (per-switch time series)
  - `data/switch_<id>_flowcount.csv` (flow count tracking)

**Workflow:**
```bash
# 1. Collection: Thu thập training data
APP_TYPE=0 TEST_TYPE=0 ./scripts/start_system.sh  # Normal → dataset/result.csv
APP_TYPE=0 TEST_TYPE=1 ./scripts/start_system.sh  # Attack → dataset/result.csv

# 2. Train models từ dataset/result.csv
python3 ryu_app/ml_detector.py --all

# 3. Detection: Chạy ML detection
APP_TYPE=1 ./scripts/start_system.sh  # Predictions → data/result.csv
```

### Attack scripts and `TARGET_IP`

- When launching attack scripts from Mininet or the scripts directory, you may pass a `TARGET_IP`. If you omit it, the scripts will try to auto-discover a candidate target in the same /24 subnet. This is helpful when running the multi-switch topology.

Examples:
```bash
# Run attack from Mininet host (auto-discover target)
mininet> h2 bash ../scripts/attack_traffic.sh &

# Or specify a target explicitly
mininet> h2 bash ../scripts/attack_traffic.sh 10.0.0.10 &
```

### Fabric peer logs
```bash
docker logs -f peer0.org1.example.com
```

---

## Các Lỗi Thường Gặp & Giải Pháp

### 1. Permission Denied trên CSV files
**Lỗi:**
```
PermissionError: [Errno 13] Permission denied: '.../data/switch_1_data.csv'
```

**Giải pháp:**
```bash
bash scripts/fix_common_issues.sh
```

---

### 2. Gateway: "creator org unknown"
**Lỗi:**
```
access denied: channel [sdnchannel] creator org unknown
```

**Giải pháp:**
```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/blockchain
node import_identity.js
pkill -f gateway_node_server.js
node gateway_node_server.js
```

---

### 3. Port already in use
**Lỗi:**
```
Error: listen EADDRINUSE: address already in use :::3001
```

**Giải pháp:**
```bash
# Gateway port (3001)
sudo fuser -k 3001/tcp

# Ryu port (6633)
sudo fuser -k 6633/tcp
```

---

### 4. Docker daemon not running
**Lỗi:**
```
Cannot connect to the Docker daemon
```

**Giải pháp:**
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

---

### 5. Fabric containers not starting
**Giải pháp:**
```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/fabric-samples/test-network
./network.sh down
docker system prune -f
./network.sh up createChannel -c sdnchannel -ca
```

---

### 6. ML model not found
**Lỗi:**
```
FileNotFoundError: ml_model_decision_tree.pkl
```

**Giải pháp:**
```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/ryu_app
python3 << EOF
from ml_detector import MLDetector
detector = MLDetector(model_type='decision_tree')
detector.train('../dataset/result.csv')
detector.save_model('ml_model_decision_tree.pkl')
EOF
```

---

## Workflow Khuyến Nghị

### Lần đầu chạy:
```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain

# 1. Fix issues
bash scripts/fix_common_issues.sh

# 2. Start system
bash scripts/start_system.sh

# 3. Check status
bash scripts/check_status.sh

# 4. Test API
cd blockchain && ./test_gateway_api.sh
```

### Mỗi lần chạy sau:
```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain

# Start
bash scripts/start_system.sh

# Check
bash scripts/check_status.sh
```

### Khi gặp lỗi:
```bash
# 1. Stop everything
bash scripts/stop_system.sh

# 2. Fix issues
bash scripts/fix_common_issues.sh

# 3. Start again
bash scripts/start_system.sh
```

---

## Checklist Trước Khi Chạy

- [ ] Docker đang chạy: `docker ps`
- [ ] Port 6633 trống: `lsof -i :6633`
- [ ] Port 3001 trống: `lsof -i :3001`
- [ ] Không có Mininet cũ: `sudo mn -c`
- [ ] ML models tồn tại: `ls ryu_app/ml_model_*.pkl`
- [ ] Data directory writable: `ls -la data/`

---

## Debug Commands

### Xem tất cả processes
```bash
ps aux | grep -E "ryu-manager|gateway_node_server|mininet"
```

### Xem ports đang dùng
```bash
sudo netstat -tlnp | grep -E "6633|3001|7051|9051"
```

### Xem Docker containers
```bash
docker ps -a | grep hyperledger
```

### Test Gateway connectivity
```bash
curl http://localhost:3001/health

# Query trust log (dùng ID số, ví dụ switch 1)
curl http://localhost:3001/api/v1/trust/1
```

### Test blockchain query (peer CLI, LevelDB backend)
```bash
cd fabric-samples/test-network
export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=$PWD/../config/
# ... set env vars cho Org1 như trong HUONG_DAN_XEM_BLOCKCHAIN.md ...

# Query trust log cho switch có dpid = 1
peer chaincode query -C sdnchannel -n trustlog -c '{"Args":["QueryTrustLog","1"]}'

# Lấy các attack gần đây trong 300 giây
peer chaincode query -C sdnchannel -n trustlog -c '{"Args":["GetRecentAttacks","300"]}'
```

---

## Cấu hình nâng cao

### IP Spoofing Detection

Hệ thống có 2 cơ chế phát hiện attack:
1. **ML Detection** (mặc định): Dùng Machine Learning
2. **IP Spoofing Detection**: Phát hiện IP giả mạo

**Mặc định:** IP Spoofing Detection = TẮT (để ML xử lý)

**Để bật IP Spoofing Detection:**
```bash
ENABLE_IP_SPOOFING_DETECTION=1 ./scripts/start_system.sh
```

**Để tắt blocking (chỉ phát hiện, không block):**
```bash
PREVENTION=0 ./scripts/start_system.sh
```

**Xem thêm:** `docs/IP_SPOOFING_DETECTION.md`

---

## Tips

1. **Luôn dùng `start_system.sh`** thay vì start thủ công từng component
2. **Check status** trước khi start Mininet: `bash scripts/check_status.sh`
3. **Fix lỗi ngay** khi gặp thay vì cố chạy tiếp
4. **Xem logs** để hiểu nguyên nhân lỗi
5. **Stop đúng cách** bằng `stop_system.sh` trước khi tắt máy
6. **Kiểm tra cấu hình** bằng `scripts/check_config.sh`

---

