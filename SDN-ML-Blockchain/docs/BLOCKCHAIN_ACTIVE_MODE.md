# Blockchain Logging Mode

## Tổng Quan

Blockchain được sử dụng để **ghi nhận (logging)** các sự kiện trong hệ thống. Blockchain không quyết định hành động blocking, chỉ lưu trữ thông tin.

---

## Tính Năng

### **Blockchain Logging** (Ghi nhận sự kiện)

**Nguyên lý:**
- Blockchain lưu trữ tất cả events: attacks, blocking actions, normal traffic
- Blockchain KHÔNG quyết định có block hay không
- Blockchain KHÔNG quyết định mức độ mitigation

**Luồng hoạt động:**
```
ML phát hiện attack → Log vào blockchain
Phát hiện IP spoofing → Block port ngay
Block port → Log vào blockchain
```

**Blocking Mechanism:**
- Khi phát hiện IP spoofing: block **PORT NUMBER** (giống repo tham khảo)  
  `in_port=X, actions=drop`
- Block port = block tất cả traffic từ port đó (không phân biệt IP)
- Hard timeout: 60 giây (tự động unblock)

---

## Events Được Log

### 1. Attack Detected
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

**Lưu ý**: ❌ KHÔNG có `confidence` (đã bỏ)

### 2. Port Blocked
```json
{
  "event_type": "port_blocked",
  "switch_id": "2",
  "port": 2,
  "timestamp": 1234567890,
  "reason": "IP Spoofing Attack",
  "action": "port_blocked_for_60s",
  "block_mode": "port_only"
}
```

### 3. Normal Traffic
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

**Lưu ý**: ❌ KHÔNG có `confidence` (đã bỏ)

### 4. Switch Connected
```json
{
  "event_type": "switch_connected",
  "switch_id": "2",
  "timestamp": 1234567890
}
```

---

## Luồng Hoạt Động

### Trường hợp: Phát hiện Attack

```
1. ML phát hiện attack (if '1' in result)
2. Log vào blockchain: "attack_detected"
3. Nếu ENABLE_IP_SPOOFING_DETECTION=1:
   - Phát hiện IP spoofing trong packet_in_handler
   - Block port ngay (KHÔNG hỏi blockchain)
   - Log vào blockchain: "port_blocked"
4. Nếu ENABLE_IP_SPOOFING_DETECTION=0:
   - Chỉ ML detection hoạt động
   - Block dựa trên ML prediction (nếu PREVENTION=1)
```

### Trường hợp: Normal Traffic

```
1. ML phát hiện normal traffic (prediction = ['0'])
2. Log vào blockchain: "normal_traffic" (mỗi 30 giây)
3. KHÔNG block gì cả
```

---

## API Endpoints

### 1. Record Event
```bash
POST /api/v1/events
Content-Type: application/json

{
  "event_type": "attack_detected",
  "switch_id": "1",
  "timestamp": 1234567890,
  "features": {
    "sfe": 80.0,
    "ssip": 40.0,
    "rfip": 0.5
  }
}
```

### 2. Get Recent Attacks
```bash
GET /api/v1/attacks/recent?timeWindow=300
```
Response:
```json
{
  "success": true,
  "attacks": [
    {"switch_id": "1", "timestamp": 1732435200, "sfe": 80.0, "ssip": 40.0},
    {"switch_id": "2", "timestamp": 1732435230, "sfe": 75.0, "ssip": 35.0}
  ],
  "count": 2
}
```

---

## BlockchainClient Methods

- `record_event(event)` - Ghi log events
- `get_recent_attacks(time_window)` - Lấy danh sách attacks


---

## So Sánh: Trước vs Bây Giờ

| Tính Năng | Trước (Active Mode) | Bây Giờ (Logging Mode) |
|-----------|-------------------|------------------------|
| **Vai trò blockchain** | Quyết định mitigation | Chỉ ghi log |
| **Trust score** | Quyết định block | Không dùng |
| **Quyết định mitigation** | Query từ chaincode | Không có (block ngay) |
| **Blocking** | Phụ thuộc blockchain | Độc lập, block ngay |
| **Latency** | +50-100ms (query) | 0ms (không query) |

---

## Configuration

### Environment Variables:

```bash
# Enable blockchain logging
BLOCKCHAIN_LOG=true

# Blockchain gateway URL
BLOCKCHAIN_ADAPTER_URL=http://localhost:3001
```

---

## Testing

### Test 1: Attack Detection và Blocking
```bash
# Tạo attack traffic
mininet> h2 hping3 --rand-source -1 -i u10000 -c 500 10.0.0.3 &

# Kiểm tra log
tail -f logs/ryu_controller.log | grep -E "(ATTACK|BLOCKING)"

# Kỳ vọng:
# 🚨 ATTACK DETECTED! → Log vào blockchain
# ⚠️ IP Spoofing detected → Block port ngay
# 🚫 BLOCKING PORT 2 → Log vào blockchain
```

### Test 2: Normal Traffic
```bash
# Tạo normal traffic
mininet> h2 ping -c 10 10.0.0.3

# Kiểm tra log
tail -f logs/ryu_controller.log | grep "Normal traffic"

# Kỳ vọng:
# ✓ Normal / Low-risk Traffic → Log vào blockchain (mỗi 30s)
```

---

## Tài Liệu Liên Quan

- [Blocking Mechanism](./BLOCKING_MECHANISM_EXPLANATION.md)
- [Architecture](./ARCHITECTURE.md)
- [Controller Logic](../ryu_app/controller_blockchain.py)

---

## Kết Luận

**Blockchain giờ đây chỉ là "audit log"**:
- Lưu trữ tất cả events
- Không quyết định hành động
- Không ảnh hưởng đến performance
- Đơn giản, dễ maintain

**Blocking hoàn toàn độc lập:**
- Phát hiện IP spoofing → Block ngay
- Không cần query blockchain
- Nhanh, hiệu quả
