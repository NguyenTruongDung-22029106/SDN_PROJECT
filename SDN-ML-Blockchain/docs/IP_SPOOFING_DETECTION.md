# IP Spoofing Detection Configuration

## 📋 Tổng quan

Hệ thống có **2 cơ chế phát hiện attack**:

1. **IP Spoofing Detection**: Phát hiện IP giả mạo dựa trên ARP table
2. **ML Detection**: Phát hiện DDoS dựa trên Machine Learning (SFE, SSIP, RFIP)

## 🎯 Vấn đề

Khi **cả 2 cơ chế đều bật**, IP Spoofing Detection sẽ **block traffic trước** khi ML có cơ hội phân loại, dẫn đến:
- ML không thể phát hiện attack
- Không có `label=1` trong `data/result.csv`
- Logs chỉ hiện "IP Spoofing detected" thay vì "Attack Traffic detected"

## ⚙️ Cấu hình

### Biến môi trường `ENABLE_IP_SPOOFING_DETECTION`

| Giá trị | Mô tả | Khi nào dùng |
|---------|-------|--------------|
| **0** (mặc định) | **TẮT** IP Spoofing Detection | Muốn dùng **CHÍNH ML** để phát hiện attack |
| **1** | **BẬT** IP Spoofing Detection | Muốn có **2 lớp bảo vệ** (IP Spoofing + ML) |

## 📊 So sánh các chế độ

### 🔹 Chế độ 1: Chỉ dùng ML Detection (Khuyến nghị)

```bash
# Mặc định: IP Spoofing Detection = 0 (tắt)
./scripts/start_system.sh
```

**Kết quả:**
- ✅ ML phát hiện attack dựa trên SFE, SSIP, RFIP
- ✅ Ghi `label=1` vào `data/result.csv`
- ✅ Logs: "🚨 ATTACK DETECTED!"
- ✅ Block attack (nếu `PREVENTION=1`)

---

### 🔹 Chế độ 2: Dùng cả IP Spoofing + ML Detection

```bash
# Bật IP Spoofing Detection
ENABLE_IP_SPOOFING_DETECTION=1 ./scripts/start_system.sh
```

**Kết quả:**
- ✅ IP Spoofing Detection block **ngay lập tức** khi phát hiện IP giả
- ❌ ML **không có cơ hội** phát hiện (traffic đã bị block)
- ❌ Không ghi `label=1` (vì ML chưa chạy)
- ✅ Logs: "⚠️ IP Spoofing detected"

---

### 🔹 Chế độ 3: Chỉ phát hiện, không block (Test ML)

```bash
# Tắt blocking để test ML
PREVENTION=0 ./scripts/start_system.sh
```

**Kết quả:**
- ✅ ML phát hiện attack
- ✅ Ghi `label=1` vào `data/result.csv`
- ✅ Logs: "🚨 ATTACK DETECTED!"
- ❌ **Không block** (chỉ cảnh báo)

---

## 🚀 Hướng dẫn sử dụng

### Scenario 1: Test xem ML có phát hiện được không?

```bash
# Tắt IP Spoofing Detection, tắt blocking
ENABLE_IP_SPOOFING_DETECTION=0 PREVENTION=0 ./scripts/start_system.sh
```

**Mục đích:** Xem ML có phát hiện attack hay không (không block)

---

### Scenario 2: Triển khai thực tế (ML Detection + Blocking)

```bash
# Tắt IP Spoofing Detection, bật blocking
ENABLE_IP_SPOOFING_DETECTION=0 PREVENTION=1 ./scripts/start_system.sh
```

**Mục đích:** Dùng ML để phát hiện và block attack

---

### Scenario 3: Bảo vệ 2 lớp (IP Spoofing + ML)

```bash
# Bật cả 2 cơ chế
ENABLE_IP_SPOOFING_DETECTION=1 PREVENTION=1 ./scripts/start_system.sh
```

**Mục đích:** 
- IP Spoofing Detection block IP giả **ngay lập tức**
- ML phát hiện các attack khác (không dùng IP giả)

---

## 📝 Logs

### Khi IP Spoofing Detection **TẮT** (ENABLE_IP_SPOOFING_DETECTION=0)

```
✓ IP Spoofing Detection: DISABLED (ML will handle all detection)
🚨 ATTACK DETECTED! (Switch 1, SFE=150, SSIP=45, RFIP=0.8500)
Mitigation Started
```

### Khi IP Spoofing Detection **BẬT** (ENABLE_IP_SPOOFING_DETECTION=1)

```
✓ IP Spoofing Detection: ENABLED
⚠️ IP Spoofing detected from port 3, IP: 10.0.0.5
```

---

## 🎓 Khuyến nghị

### Cho mục đích học tập / nghiên cứu ML:
```bash
ENABLE_IP_SPOOFING_DETECTION=0 ./scripts/start_system.sh
```
→ Để ML có cơ hội học và phát hiện attack

### Cho triển khai thực tế:
```bash
ENABLE_IP_SPOOFING_DETECTION=1 ./scripts/start_system.sh
```
→ Bảo vệ 2 lớp: IP Spoofing + ML

---

## 🔍 Kiểm tra cấu hình

Sau khi start system, kiểm tra logs:

```bash
tail -50 logs/ryu_controller.log | grep "IP Spoofing Detection"
```

Kết quả mong đợi:
- Nếu `ENABLE_IP_SPOOFING_DETECTION=0`: `✓ IP Spoofing Detection: DISABLED`
- Nếu `ENABLE_IP_SPOOFING_DETECTION=1`: `✓ IP Spoofing Detection: ENABLED`

---

## 📊 File output

### `data/result.csv` (Detection Mode)

**Khi IP Spoofing Detection TẮT:**
```csv
sfe,ssip,rfip,label
150,45,0.85,1    # ML detected attack
120,38,0.75,1    # ML detected attack
10,5,0.95,0      # ML detected normal
```

**Khi IP Spoofing Detection BẬT:**
```csv
sfe,ssip,rfip,label
10,5,0.95,0      # Only normal traffic (attacks blocked before ML)
8,4,0.92,0
```

---

## ❓ FAQ

### Q1: Tại sao mặc định `ENABLE_IP_SPOOFING_DETECTION=0`?

**A:** Để ML có cơ hội phát hiện attack. Nếu bật IP Spoofing Detection, ML sẽ không bao giờ thấy attack traffic.

### Q2: Có thể dùng cả 2 cơ chế không?

**A:** Có, nhưng IP Spoofing Detection sẽ block trước, ML chỉ phát hiện được các attack không dùng IP giả.

### Q3: Làm sao biết ML đang hoạt động?

**A:** Kiểm tra logs:
```bash
grep "Attack Traffic detected" logs/ryu_controller.log
```

Nếu có kết quả → ML đang hoạt động ✓

### Q4: Tôi muốn ML phát hiện nhưng không block?

**A:** Dùng `PREVENTION=0`:
```bash
PREVENTION=0 ./scripts/start_system.sh
```

---

## 📚 Tham khảo

- **Controller Code**: `ryu_app/controller_blockchain.py` (dòng 79-82, 626-657)
- **Start Script**: `scripts/start_system.sh` (dòng 200-210)
- **ML Detector**: `ryu_app/ml_detector.py`

---

**Tác giả:** SDN-ML-Blockchain Project  
**Ngày cập nhật:** 2025-12-19

