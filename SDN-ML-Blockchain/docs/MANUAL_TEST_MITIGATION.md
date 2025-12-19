# Hướng Dẫn Test Thủ Công trên Mininet

## Chuẩn Bị

### 1. Khởi động hệ thống
```bash
# Terminal 1: Khởi động hệ thống
cd /home/obito/SDN_Project/SDN-ML-Blockchain
bash scripts/start_system.sh

# Đợi 2-3 phút để Fabric, Gateway, và Ryu khởi động xong
```

### 2. Khởi động Mininet
```bash
# Terminal 2: Khởi động Mininet
cd /home/obito/SDN_Project/SDN-ML-Blockchain
sudo python3 topology/custom_topo.py
```

### 3. Mở terminal để xem log
```bash
# Terminal 3: Xem log Ryu Controller
tail -f logs/ryu_controller.log
```

---

## Test Case: Attack Detection và Blocking

### Mục tiêu:
- Test khi ML phát hiện attack và hệ thống block port
- Kỳ vọng: Phát hiện attack → Block port ngay

### Các bước:

#### Bước 1: Tạo attack traffic (trong Mininet CLI)
```bash
# Trong Mininet CLI (Terminal 2)
mininet> h2 hping3 --rand-source -1 -i u10000 -c 500 10.0.0.3 &
```

#### Bước 2: Kiểm tra log (Terminal 3)
```bash
tail -f logs/ryu_controller.log | grep -E "(ATTACK|BLOCKING|IP Spoofing)"
```

### Kỳ vọng trong log:
```
🚨 ATTACK DETECTED! (Switch 2, SFE=XX, SSIP=XX, RFIP=XX)
⛓️ Attack event logged to blockchain
🛡️ Prevention Enabled
⚠️ IP Spoofing detected from port 2, IP: XXX.XXX.XXX.XXX
🚫 BLOCKING PORT 2 on switch 2 for 60s (reason: IP Spoofing Attack)
⛓️ Port blocking logged to blockchain (mode: port_only)
```

#### Bước 3: Kiểm tra flow table
```bash
# Xem blocking rules
sudo ovs-ofctl dump-flows s2 | grep priority=100
```

**Kỳ vọng:**
```
priority=100, in_port=2, actions=drop
```

#### Bước 4: Test connectivity
```bash
# Trong Mininet CLI
mininet> h2 ping -c 3 10.0.0.3
# → Ping fail (port bị block)

# Host khác vẫn ping được
mininet> h1 ping -c 3 10.0.0.3
# → Ping thành công (host khác không bị block)
```

---

## Test Case: Normal Traffic

### Mục tiêu:
- Test khi có traffic bình thường
- Kỳ vọng: Không block, chỉ log

### Các bước:

#### Bước 1: Tạo normal traffic
```bash
# Trong Mininet CLI
mininet> h2 ping -c 10 10.0.0.3
```

#### Bước 2: Kiểm tra log
```bash
tail -f logs/ryu_controller.log | grep "Normal"
```

### Kỳ vọng:
```
✓ Normal Traffic (Switch 2)
⛓️ Normal traffic logged to blockchain (switch 2)
```

---

## Lưu Ý

1. **Thời gian block**: Flow rule block có `hardtime=60` (60 giây), sau đó tự động unblock
2. **ML Detection**: Cần đợi ML phát hiện attack (khoảng 2-4 giây sau khi có traffic)
3. **IP Spoofing**: Chỉ phát hiện khi IP không khớp với ARP table đã học
4. **Blocking Mechanism**: 
   - **Chỉ block port number** (giống repo tham khảo)
   - Block port = block tất cả traffic từ port đó (không phân biệt IP)
   - Flow rule: `in_port=X, actions=drop`

---

## Troubleshooting

### Không thấy attack được phát hiện:
- **Nguyên nhân:** Traffic chưa đủ mạnh hoặc chưa có IP spoofing
- **Giải pháp:** Tăng số lượng packets, dùng `--rand-source` để tạo IP spoofing

### Không thấy blocking:
- **Nguyên nhân:** Chưa phát hiện IP spoofing hoặc IP là IP thật của host
- **Giải pháp:** Đảm bảo có IP spoofing (dùng `--rand-source`)

### Port bị block quá lâu:
- **Nguyên nhân:** Hard timeout là 60 giây
- **Giải pháp:** Đợi 60 giây hoặc xóa flow rule thủ công:
  ```bash
  sudo ovs-ofctl del-flows s2 priority=100
  ```
