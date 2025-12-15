# Scripts Directory

Automation scripts for SDN-ML-Blockchain system management.

---

## Core System Scripts

### `start_system.sh` 
**Main system startup script** - Khởi động toàn bộ hệ thống tự động
```bash
bash scripts/start_system.sh
```
**What it does:**
1. Pre-flight checks (Docker, Node.js, Python)
2. Cleanup old processes
3. Fix file permissions
4. Start Fabric network + deploy chaincode
5. Start Gateway API (port 3001)
6. Start Ryu Controller (port 6633)

**Time:** ~2-3 minutes

---

### `stop_system.sh`
**System shutdown script** - Dừng toàn bộ hệ thống an toàn
```bash
bash scripts/stop_system.sh
```
**What it does:**
- Stop Ryu Controller
- Stop Gateway API
- Stop Mininet (sudo mn -c)
- Stop Fabric network

---

### `fix_common_issues.sh`
**Auto-fix common errors** - Sửa các lỗi thường gặp tự động
```bash
bash scripts/fix_common_issues.sh
```
**Fixes:**
1. File permissions (CSV files)
2. Blockchain identity re-import
3. Port conflicts (6633, 3001)
4. Mininet cleanup
5. Docker restart if needed
6. npm/pip packages check

**Use when:** Gặp lỗi Permission Denied, Port in use, Identity errors

---

### `check_status.sh`
**System health check** - Kiểm tra trạng thái hệ thống
```bash
bash scripts/check_status.sh
```
**Checks:**
- Docker daemon status
- Fabric containers (3)
- Gateway API (port 3001)
- Ryu Controller (port 6633)
- ML models (4 .pkl files)
- File permissions

**Output:** "All core services running (X/5)"

---

### `install.sh`
**Initial installation** - Cài đặt dependencies (chỉ lần đầu)
```bash
bash scripts/install.sh
```
**Installs:**
- Mininet
- Ryu Controller
- Python packages
- Docker & Docker Compose
- Hyperledger Fabric binaries
- Attack tools (hping3)

**Run once:** After cloning repository

---

### `setup_fabric.sh`
**Fabric network setup** - Thiết lập Hyperledger Fabric network
```bash
bash scripts/setup_fabric.sh
```
**What it does:**
1. Start Fabric test-network
2. Create channel "sdnchannel"
3. Deploy "trustlog" chaincode
4. Test connection

**Note:** `start_system.sh` already includes this

---

## Testing & Verification Scripts

### `test_system.sh`
**Quick system check** - Kiểm tra dependencies nhanh
```bash
bash scripts/test_system.sh
```
**Tests:**
- Python, pip, Docker availability
- Python modules (scikit-learn, ryu, etc.)
- Mininet installation
- Project structure

---

### `verify_system.sh`
**Comprehensive verification** - Kiểm tra chi tiết từng component
```bash
bash scripts/verify_system.sh
```
**Tests:**
1. Python environment
2. Module imports
3. ML models existence
4. Blockchain connectivity (if Fabric running)
5. Network connectivity
6. File permissions

**Output:** PASS/FAIL for each test + summary

---

### `test_ml_models.sh`
**ML algorithms comparison** - So sánh hiệu năng các thuật toán ML
```bash
bash scripts/test_ml_models.sh
```
**Tests:**
- Decision Tree
- Random Forest
- SVM
- Naive Bayes

**Test cases:**
1. Normal traffic: [10, 5, 15]
2. Suspicious: [25, 12, 35]
3. DDoS attack: [80, 40, 120]
4. Heavy DDoS: [150, 80, 250]

---

## Traffic Generation Scripts

### `attack_traffic.sh`
**DDoS attack simulation** - Tạo attack traffic
```bash
# In Mininet CLI:
mininet> h1 bash ../scripts/attack_traffic.sh &
```
**Generates:**
- SYN flood (hping3)
- High packet rate
- Random source IPs
- Multiple targets

---

### `normal_traffic.sh`
**Normal traffic simulation** - Tạo normal traffic
```bash
mininet> h3 bash ../scripts/normal_traffic.sh &
```
**Generates:**
- Regular ping
- HTTP requests
- Normal packet rate

---

### `botnet_attack.sh`
**Botnet simulation** - Mô phỏng botnet attack phức tạp
```bash
mininet> h9 bash ../scripts/botnet_attack.sh &
```
**Phases:**
1. Ping sweep (reconnaissance)
2. SYN flood
3. ACK flood
4. UDP amplification
5. Slow HTTP

**Duration:** ~5 minutes with jitter

---

## Utility Scripts

### `clean_data.sh`
**Clean runtime data** - Xóa CSV files runtime
```bash
bash scripts/clean_data.sh
```
**What it does:**
- Lists all CSV files in data/
- Asks confirmation
- Deletes all switch_*.csv files

**Use when:** Want to start fresh data collection

---

### `demo_system.sh`
**Full system demo** - Demo hệ thống đầy đủ (educational)
```bash
bash scripts/demo_system.sh
```
**Demonstrates:**
1. System components overview
2. ML detection examples
3. Blockchain logging simulation
4. Attack scenarios

**Good for:** Presentations, learning, understanding workflow

---

### `deploy_active_chaincode.sh`
**Deploy active mode chaincode** - Deploy chaincode version nâng cao
```bash
bash scripts/deploy_active_chaincode.sh
```
**Features:**
- Active monitoring mode
- Enhanced trust calculation
- Additional chaincode functions

**Use when:** Need advanced blockchain features

---

## ML/Data Scripts (Python)

### `generate_training_data.py`
**Generate ML training data** - Thu thập dữ liệu huấn luyện
```bash
python3 scripts/generate_training_data.py
```
**What it does:**
- Collect flow statistics
- Extract features (SFE, SSIP, RFIP)
- Label data (normal/attack)
- Save to dataset/result.csv

---

### `train_model.py`
**Train ML models** - Huấn luyện các ML models
```bash
python3 scripts/train_model.py
```
**Trains:**
1. Decision Tree
2. Random Forest
3. SVM
4. Naive Bayes

**Saves models to:** `ryu_app/ml_model_*.pkl`

---

## Usage Examples

### Complete Workflow:
```bash
# 1. First time setup
bash scripts/install.sh

# 2. Start system
bash scripts/start_system.sh

# 3. Check status
bash scripts/check_status.sh

# 4. In another terminal, start Mininet
cd topology
sudo python3 custom_topo.py

# 5. Generate traffic (in Mininet CLI)
mininet> h1 ping -c 10 h10
mininet> h2 bash ../scripts/attack_traffic.sh &

# 6. Stop system
bash scripts/stop_system.sh
```

### Troubleshooting:
```bash
# Fix errors
bash scripts/fix_common_issues.sh

# Verify everything works
bash scripts/verify_system.sh

# Test ML models
bash scripts/test_ml_models.sh
```

---

## Quick Reference

| Task | Command |
|------|---------|
| **Start everything** | `bash scripts/start_system.sh` |
| **Check status** | `bash scripts/check_status.sh` |
| **Fix errors** | `bash scripts/fix_common_issues.sh` |
| **Stop everything** | `bash scripts/stop_system.sh` |
| **Test system** | `bash scripts/test_system.sh` |
| **Generate attack** | In Mininet: `h1 bash ../scripts/attack_traffic.sh &` |

---

## Important Notes

1. **Run from project root:** All scripts assume you're in project root
2. **Mininet needs sudo:** Traffic generation scripts need to be run in Mininet CLI
3. **Check status first:** Always run `check_status.sh` before debugging
4. **Logs location:** All logs are in `logs/` directory

---

## Need Help?

- **Quick Start:** See `docs/QUICK_START.md`
- **Manual Setup:** See `docs/MANUAL_SETUP.md`
- **Vietnamese Guide:** See `docs/HUONG_DAN_CHAY_DU_AN.md`
- **Project Structure:** See `PROJECT_STRUCTURE.md`

---

**Total scripts: 17** (after cleanup)
- Core: 6 scripts
- Testing: 3 scripts
- Traffic: 3 scripts
- Utility: 3 scripts
- ML/Data: 2 Python scripts
