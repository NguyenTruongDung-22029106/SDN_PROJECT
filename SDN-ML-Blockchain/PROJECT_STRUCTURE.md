# Cấu Trúc Dự Án SDN-ML-Blockchain

> **Cập nhật:** 28/11/2025 - Dự án đã được sắp xếp và loại bỏ các file thừa thải

---

## Cấu Trúc Thư Mục Chính

```
SDN-ML-Blockchain/

  README.md                    # Tài liệu chính (tiếng Anh)
  LICENSE                      # Giấy phép Apache 2.0
  requirements.txt             # Python dependencies
  .gitignore                   # Git ignore rules

  blockchain/                  #  Blockchain Components
    chaincode/                  # Smart contract (Go)
       trustlog.go            # TrustLog chaincode
    fabric_client.py           # Python Fabric client
    gateway_client.py          # Gateway client implementation
    gateway_node_server.js     # Node.js REST gateway (ĐANG DÙNG)
    import_identity.js         # Import user identity
    enrollUser.js              # Enroll user script
    test_gateway_api.sh        # API testing script
    package.json               # Node.js dependencies
    docker-compose.yml         # Docker setup
    wallet/                    # User identities (gitignored)

  ryu_app/                     #  SDN Controller
    controller_blockchain.py   # Main controller (WITH BLOCKCHAIN)
    ml_detector.py             # ML detection module
    ml_model_decision_tree.pkl # Trained model - Decision Tree
    ml_model_random_forest.pkl # Trained model - Random Forest
    ml_model_svm.pkl           # Trained model - SVM
    ml_model_naive_bayes.pkl   # Trained model - Naive Bayes
    requirements.txt           # Python dependencies
    Dockerfile                 # Docker build file

  scripts/                     #  Utility Scripts
    start_system.sh            #  Khởi động toàn bộ hệ thống
    stop_system.sh             #  Dừng hệ thống
    fix_common_issues.sh       #  Sửa các lỗi thường gặp
    check_status.sh            #  Kiểm tra trạng thái hệ thống
    install.sh                 # Cài đặt dependencies
    setup_fabric.sh            # Setup Fabric network
    attack_traffic.sh          # Generate attack traffic
    normal_traffic.sh          # Generate normal traffic
    botnet_attack.sh           # Botnet simulation
    test_system.sh             # System testing

  topology/                    #  Network Topologies
    custom_topo.py             # Mininet custom topology

  data/                        #  Runtime Data Files
    switch_1_data.csv          # Switch 1 monitoring data
    switch_1_flowcount.csv     # Switch 1 flow counts
    README.md                  # Data directory info

  dataset/                     #  ML Training Data
    result.csv                 # Training dataset

  logs/                        #  System Logs (NEW!)
    gateway.log                # Gateway API logs
    ryu_controller.log         # Ryu Controller logs
    .gitkeep                   # Keep directory in git

  docs/                        #  Documentation
    HUONG_DAN_CHAY_DU_AN.md   #  Hướng dẫn chạy dự án (Vietnamese)
    MANUAL_SETUP.md            #  Hướng dẫn chạy từng component
    QUICK_START.md             # Quick start guide
    ARCHITECTURE.md            # System architecture
    BLOCKCHAIN_ACTIVE_MODE.md  # Blockchain integration guide
    PROJECT_REVIEW_REPORT.md   #  Báo cáo kiểm tra dự án (NEW!)
    FABRIC_SETUP_NOTE.md       # Fabric setup details
    ML_ALGORITHMS.md           # ML algorithms explained
    PRODUCTION_DEPLOYMENT.md   # Production deployment
    CHANGELOG.md               # Project changelog

  tests/                       #  Test Files
  tools/                       #  Additional Tools
  configs/                     #  Configuration Files
     config.ini                 # Main config
     docker-compose.yml         # Docker compose

```

---

## Files Đã Loại Bỏ (Redundant/Outdated)

### Đã Xóa:
1. **`PROJECT_STRUCTURE.txt`** - Outdated, replaced by this file
2. **`docs/QUICKSTART.md`** - Duplicate of `QUICK_START.md`
3. **`docs/HOW_TO_RUN_3_TERMINALS.md`** - Outdated, replaced by `MANUAL_SETUP.md`
4. **`docs/HUONG_DAN_TIENG_VIET.md`** - Old version, replaced by `HUONG_DAN_CHAY_DU_AN.md`
5. **`docs/README.md`** - Duplicate, using root `README.md`

### Đã Di Chuyển:
1. **CSV files** từ `ryu_app/` → `data/` (14 files)
2. **Log files** từ `blockchain/` và `ryu_app/` → `logs/`

---

## Hướng Dẫn Sử Dụng File Documentation

### Cho Người Mới:
1. **Bắt đầu:** `docs/QUICK_START.md`
2. **Chạy dự án (tiếng Việt):** `docs/HUONG_DAN_CHAY_DU_AN.md` 
3. **Architecture:** `docs/ARCHITECTURE.md`

### Cho Advanced Users:
1. **Chạy từng component riêng:** `docs/MANUAL_SETUP.md` 
2. **Blockchain integration:** `docs/BLOCKCHAIN_ACTIVE_MODE.md`
3. **Production deployment:** `docs/PRODUCTION_DEPLOYMENT.md`

### Technical Reference:
1. **Fabric setup:** `docs/FABRIC_SETUP_NOTE.md`
2. **ML algorithms:** `docs/ML_ALGORITHMS.md`
3. **Changelog:** `docs/CHANGELOG.md`

---

## Quick Commands

### Khởi động hệ thống (Automated):
```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain
bash scripts/start_system.sh
```

### Kiểm tra trạng thái:
```bash
bash scripts/check_status.sh
```

### Xem logs:
```bash
# Gateway
tail -f logs/gateway.log

# Ryu Controller
tail -f logs/ryu_controller.log

# Fabric
docker logs -f peer0.org1.example.com
```

### Dừng hệ thống:
```bash
bash scripts/stop_system.sh
```

---

## File Priorities (Theo mức độ quan trọng)

### Critical (Không được xóa):
- `README.md`
- `requirements.txt`
- `blockchain/gateway_node_server.js`
- `blockchain/chaincode/trustlog.go`
- `ryu_app/controller_blockchain.py`
- `ryu_app/ml_detector.py`
- `scripts/start_system.sh`
- `scripts/stop_system.sh`
- `topology/custom_topo.py`

### Important (Cần cho production):
- `scripts/fix_common_issues.sh`
- `scripts/check_status.sh`
- `blockchain/fabric_client.py`
- `ryu_app/ml_model_*.pkl` (4 files)
- `docs/HUONG_DAN_CHAY_DU_AN.md`
- `docs/MANUAL_SETUP.md`

### Optional (Có thể tạo lại nếu cần):
- `dataset/result.csv` (training data)
- `data/*.csv` (runtime data)
- `logs/*.log` (logs)
- Other documentation files

---

## Dependencies

### Core:
- Python 3.8+
- Node.js 18+
- Docker 20.10+
- Go 1.21+

### Python Packages:
```bash
pip3 install -r requirements.txt
```

### Node.js Packages:
```bash
cd blockchain
npm install
```

### System Packages:
```bash
sudo apt install mininet openvswitch-switch hping3 iperf3
```

---

## Gitignore Strategy

File `.gitignore` được cấu hình để:
- Ignore logs (runtime generated)
- Ignore runtime CSV data
- Ignore ML models (large, retrain locally)
- Ignore blockchain wallet (private keys)
- Ignore node_modules
- Ignore Fabric binaries (too large)
- Keep directory structure (với .gitkeep)

---

## Disk Space Usage (Estimated)

```
Total Project: ~500MB (without Fabric binaries)

Breakdown:
  blockchain/          ~150MB (chaincode + node_modules)
  ryu_app/             ~50MB  (ML models + code)
  scripts/             ~1MB   (shell scripts)
  docs/                ~1MB   (documentation)
  data/                ~1MB   (CSV files)
  logs/                ~10MB  (log files)
  dataset/             ~100MB (training data)
  fabric-samples/      ~5GB   (if included - gitignored)
  fabric binaries/     ~300MB (if included - gitignored)
```

**Recommendation:** Clone fresh, download Fabric separately

---

## Maintenance Notes

### Regular Cleanup:
```bash
# Clean old logs (older than 7 days)
find logs/ -name "*.log" -mtime +7 -delete

# Clean runtime data
rm -f data/switch_*_*.csv

# Clean Docker resources
docker system prune -f
```

### Update ML Models:
```bash
cd ryu_app
python3 -c "
from ml_detector import MLDetector
detector = MLDetector(model_type='decision_tree')
detector.train('../dataset/result.csv')
detector.save_model('ml_model_decision_tree.pkl')
"
```

---

## Support

- **Documentation:** `docs/` folder
- **Issues:** GitHub Issues
- **Quick Help:** Read `QUICK_START.md` first

---

** Project is now clean and well-organized!**
