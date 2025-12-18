# Quick Test Guide - 3 Chế Độ Mitigation

## 🚀 Khởi Động Nhanh

```bash
# Terminal 1: Start system
bash scripts/start_system.sh

# Terminal 2: Start Mininet
sudo python3 topology/custom_topo.py

# Terminal 3: Watch logs
tail -f logs/ryu_controller.log
```

---

## 📋 Test Case 1: WARN_ONLY (Chỉ cảnh báo)

### ⚠️ Điều kiện để trigger `warn_only`:
Theo logic blockchain, `warn_only` chỉ xảy ra khi:
- **Option 1:** Confidence ≤ 0.7 (traffic nhẹ) → `warn_only`
- **Option 2:** Confidence 0.7-0.95 VÀ Trust Score > 0.8 → `warn_only`
- **Lưu ý:** Nếu confidence > 0.95 → luôn `block_immediately` (không bao giờ `warn_only`)

### 🔧 Chuẩn bị (Reset trust score):
```bash
# Kiểm tra trust score hiện tại
curl http://localhost:3001/api/v1/trust/2

# Nếu trust < 0.8, cần reset hoặc đợi trust tăng lại
# (Trust tự động tăng khi không có attack trong 5 phút)
```

### Trong Mininet CLI (Traffic nhẹ để confidence < 0.7):
```bash
# Tạo traffic nhẹ (interval lớn, ít packet)
mininet> h1 ping -c 10 10.0.0.3 &
mininet> h1 hping3 --rand-source -1 -i u100000 -c 20 10.0.0.3 &
```

**HOẶC** (Nếu trust score cao > 0.8):
```bash
# Traffic vừa phải (confidence 0.7-0.95) + trust cao
mininet> h1 hping3 --rand-source -1 -i u50000 -c 30 10.0.0.3 &
```

### Kỳ vọng trong log:
```
✓ Normal / Low-risk Traffic - Confidence: XX% (XX < 70%)
⛓️ Blockchain recommends: warn_only
ℹ️ High trust score - monitoring only, no blocking
```

**HOẶC** (nếu confidence 0.7-0.95 và trust > 0.8):
```
🚨 ATTACK DETECTED! Confidence: XX% (70% < XX < 95%)
⛓️ Blockchain recommends: warn_only
ℹ️ High trust score - monitoring only, no blocking
```

### Kiểm tra:
```bash
# Không có flow block
sudo ovs-ofctl dump-flows s2 | grep priority=100
# → Không có kết quả

# Traffic vẫn hoạt động
mininet> h1 ping -c 3 10.0.0.3
# → Ping thành công
```

---

## 📋 Test Case 2: STANDARD_MITIGATION (Block theo FLOW)

### Trong Mininet CLI:
```bash
mininet> xterm h2
# Trong xterm h2:
hping3 --rand-source -1 -i u20000 -c 100 10.0.0.3
```

### Kỳ vọng trong log:
```
⛓️ Blockchain recommends: standard_mitigation
⚠️ IP Spoofing detected from port 2, IP: 10.0.0.X
🚫 Standard mode: Blocking FLOW 10.0.0.X → 10.0.0.3 on port 2
```

### Kiểm tra:
```bash
# Có flow block theo cặp (IP nguồn, IP đích)
sudo ovs-ofctl dump-flows s2 | grep priority=100
# → priority=100, in_port=2, ipv4_src=10.0.0.X, ipv4_dst=10.0.0.3, actions=drop

# Flow 10.0.0.X → 10.0.0.3 bị block (ping h2→h3 fail)
mininet> h2 ping -c 3 10.0.0.3
# → Ping fail

# Nhưng 10.0.0.X ping host khác vẫn OK (nếu có route)
# Và host khác (ví dụ h1) ping 10.0.0.3 vẫn OK
mininet> h1 ping -c 3 10.0.0.3
```

---

## 📋 Test Case 3: BLOCK_IMMEDIATELY (Block theo IP nguồn)

### Trong Mininet CLI:
```bash
mininet> xterm h2
# Trong xterm h2, tạo flood mạnh:
hping3 --rand-source -1 -i u5000 -c 500 10.0.0.3 &
hping3 --rand-source -S -p 80 -i u5000 -c 500 10.0.0.3 &
```

### Kỳ vọng trong log:
```
🚨 ATTACK DETECTED! Confidence: XX%
⛓️ Blockchain recommends: block_immediately
⚠️ Aggressive mitigation mode activated
⚠️ IP Spoofing detected from port 2, IP: 10.0.0.X
🚫 Aggressive mode: Blocking ALL FLOWS from 10.0.0.X on port 2
```

### Kiểm tra:
```bash
# Có flow block theo IP nguồn (KHÔNG cần ipv4_dst)
sudo ovs-ofctl dump-flows s2 | grep priority=100
# → priority=100, in_port=2, ipv4_src=10.0.0.X, eth_type=0x0800, actions=drop

# Tất cả traffic từ 10.0.0.X bị block
mininet> h2 ping -c 3 10.0.0.3
# → Ping fail

# Host khác vẫn hoạt động bình thường
mininet> h1 ping -c 3 10.0.0.3
# → Ping OK
```

---

## 🔍 Công Cụ Kiểm Tra Nhanh

```bash
# Xem log real-time
tail -f logs/ryu_controller.log | grep -E "(BLOCKING|mitigation|ATTACK)"

# Xem toàn bộ flow trên switch (ví dụ s2)
sudo ovs-ofctl dump-flows s2

# Chỉ xem các flow block (priority=100)
sudo ovs-ofctl dump-flows s2 | grep "priority=100"

# Xem flow block chi tiết (OpenFlow13)
sudo ovs-ofctl -O OpenFlow13 dump-flows s2 | grep "priority=100"

# Gỡ toàn bộ flow block (priority=100) trên s2 (reset nhanh)
sudo ovs-ofctl --strict del-flows s2 "priority=100"

# Gỡ block theo đúng port (ví dụ in_port=2 trên s2)
sudo ovs-ofctl --strict del-flows s2 "priority=100,in_port=2"

# Xem recent attacks từ blockchain
curl http://localhost:3001/api/v1/attacks/recent
```

---

## 📊 So Sánh Nhanh

| Chế Độ | Flow Rule (chính) | Traffic |
|--------|-------------------|---------|
| **warn_only** | Không có | ✅ Tất cả hoạt động |
| **standard_mitigation** | `in_port=X, ipv4_src=Y, ipv4_dst=Z, eth_type=0x0800` | ❌ Chỉ flow Y→Z bị block |
| **block_immediately** | `in_port=X, ipv4_src=Y, eth_type=0x0800` | ❌ Mọi flow từ IP Y bị block |

---

## ⚠️ Lưu Ý

- Flow block tự động hết hạn sau **120 giây**
- Cần đợi **2-4 giây** để ML phát hiện attack
- Trust score thay đổi dần dần, không tức thì
- **Port 1 (Uplink) Protection**: Port 1 trên leaf switches được bảo vệ, không thể block trực tiếp. Khi phát hiện attack từ port 1, hệ thống block source IP trên port host (2-5) thay thế
- **Blocking Rules Limit**: Tối đa 50 rules per switch. Hệ thống tự động kiểm tra và dừng khi đạt giới hạn

## 📖 Logic Blockchain Mitigation

Blockchain quyết định mitigation action dựa trên:

| Confidence | Trust Score | Mitigation Action |
|------------|-------------|-------------------|
| > 0.95 | Bất kỳ | `block_immediately` |
| 0.7 - 0.95 | > 0.8 | `warn_only` |
| 0.7 - 0.95 | 0.5 - 0.8 | `standard_mitigation` |
| 0.7 - 0.95 | < 0.5 | `block_immediately` |
| ≤ 0.7 | ≥ 0.3 | `warn_only` |
| ≤ 0.7 | < 0.3 | `standard_mitigation` |

**Lưu ý:** Nếu có **coordinated attack** (nhiều switch bị tấn công cùng lúc) → luôn `block_immediately`

