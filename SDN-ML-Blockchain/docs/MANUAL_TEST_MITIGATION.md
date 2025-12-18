# Hướng Dẫn Test Thủ Công 3 Chế Độ Mitigation trên Mininet

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

## Test Case 1: WARN_ONLY Mode (Chỉ cảnh báo, không block)

### Mục tiêu:
- Test khi trust score cao (>0.8) và confidence trung bình
- Kỳ vọng: Chỉ log warning, KHÔNG block traffic

### Các bước:

#### Bước 1: Kiểm tra trust score hiện tại
```bash
# Trong Terminal 1 (hoặc terminal mới)
curl http://localhost:3001/api/v1/trust/1
# Nếu trust_score > 0.8 → OK, nếu không cần reset (xem phần Reset Trust Score)
```

#### Bước 2: Tạo traffic tấn công nhẹ (trong Mininet CLI)
```bash
# Trong Mininet CLI (Terminal 2)
mininet> h1 ping -c 5 10.0.0.3
mininet> h1 hping3 -1 --rand-source -i u50000 -c 50 10.0.0.3 &
```

#### Bước 3: Quan sát log (Terminal 3)
```bash
# Tìm các dòng:
# - "ℹ️ High trust score - monitoring only, no blocking"
# - "⛓️ Blockchain recommends: warn_only"
# - KHÔNG có dòng "🚫 BLOCKING"
```

#### Bước 4: Kiểm tra flow table (không có rule block)
```bash
# Terminal mới
sudo ovs-ofctl dump-flows s2 | grep priority=100
# Kỳ vọng: KHÔNG có flow rule với priority=100 (không có block rule)
```

#### Bước 5: Test connectivity (traffic vẫn hoạt động)
```bash
# Trong Mininet CLI
mininet> h1 ping -c 3 10.0.0.3
# Kỳ vọng: Ping thành công (traffic không bị block)
```

---

## Test Case 2: STANDARD_MITIGATION Mode (Block theo FLOW)

### Mục tiêu:
- Test khi trust score trung bình (0.3-0.8) và confidence trung bình
- Kỳ vọng: Block flow cụ thể (IP nguồn → IP đích) đang tấn công (block_mode="flow_specific")

### Các bước:

#### Bước 1: Đảm bảo trust score trung bình
```bash
# Nếu trust quá cao, có thể tạo một vài attack event trước:
# (Trong Mininet CLI)
mininet> h2 hping3 --rand-source -S -p 80 -i u10000 -c 100 10.0.0.3 &
# Đợi 10-15 giây để ML phát hiện và trust score giảm xuống
```

#### Bước 2: Tạo traffic với IP spoofing (trong Mininet CLI)
```bash
# Trong Mininet CLI
mininet> xterm h2
# Trong xterm của h2:
hping3 --rand-source -1 -i u20000 -c 100 10.0.0.3
# Hoặc:
hping3 --rand-source -S -p 80 -i u20000 -c 100 10.0.0.3
```

#### Bước 3: Quan sát log (Terminal 3)
```bash
# Tìm các dòng:
# - "⛓️ Blockchain recommends: standard_mitigation"
# - "⚠️ IP Spoofing detected from port X, IP: Y"
# - "🚫 Standard mode: Blocking FLOW Y → 10.0.0.3 on port X"
```

#### Bước 4: Kiểm tra flow table (có rule block theo FLOW)
```bash
# Terminal mới
sudo ovs-ofctl dump-flows s2 | grep priority=100
# Kỳ vọng: Có flow rule như:
#   priority=100, in_port=2, ipv4_src=10.0.0.X, ipv4_dst=10.0.0.3, eth_type=0x0800, actions=drop
#   (Chỉ block flow Y→10.0.0.3, không block toàn bộ traffic từ Y)
```

#### Bước 5: Test connectivity
```bash
# Trong Mininet CLI
# Test từ IP bị block tới đúng đích (sẽ fail):
mininet> h2 ping -c 3 10.0.0.3
# Kỳ vọng: Ping fail hoặc timeout (flow h2→h3 bị block)

# Nếu có route, test h2 ping sang host khác (không phải 10.0.0.3) có thể vẫn OK

# Test từ host khác trên cùng port (nếu có) hoặc host khác:
mininet> h1 ping -c 3 10.0.0.3
# Kỳ vọng: Ping thành công (IP khác không bị block)
```

---

## Test Case 3: BLOCK_IMMEDIATELY Mode (Block theo IP nguồn)

### Mục tiêu:
- Test khi confidence rất cao (>0.95) hoặc coordinated attack
- Kỳ vọng: Block tất cả flows từ 1 IP nguồn (block_mode="source_ip"),
  trong khi các host/IP khác vẫn hoạt động bình thường.

### Cách 1: Tạo attack với confidence cao

#### Bước 1: Tạo traffic tấn công mạnh (trong Mininet CLI)
```bash
# Trong Mininet CLI
mininet> xterm h2
# Trong xterm của h2, tạo flood mạnh:
hping3 --rand-source -1 -i u5000 -c 500 10.0.0.3 &
hping3 --rand-source -S -p 80 -i u5000 -c 500 10.0.0.3 &
hping3 --rand-source -S -p 443 -i u5000 -c 500 10.0.0.3 &
```

#### Bước 2: Quan sát log (Terminal 3)
```bash
# Tìm các dòng:
# - "🚨 ATTACK DETECTED! Confidence: XX%"
# - "⛓️ Blockchain recommends: block_immediately"
# - "⚠️ Aggressive mitigation mode activated"
# - "⚠️ IP Spoofing detected from port X, IP: Y"
# - "🚫 Aggressive mode: Blocking ALL FLOWS from Y on port X"
```

#### Bước 3: Kiểm tra flow table (block theo IP nguồn)
```bash
# Terminal mới
sudo ovs-ofctl dump-flows s2 | grep priority=100
# Kỳ vọng: Có flow rule như:
#   priority=100, in_port=2, ipv4_src=10.0.0.X, eth_type=0x0800, actions=drop
#   (KHÔNG có ipv4_dst, nghĩa là block TẤT CẢ flows từ IP Y trên port X)
```

#### Bước 4: Test connectivity
```bash
# Trong Mininet CLI
mininet> h2 ping -c 3 10.0.0.3
# Kỳ vọng: Ping fail hoặc timeout (tất cả traffic từ IP h2 bị block)

# Host khác vẫn ping được:
mininet> h1 ping -c 3 10.0.0.3
```

### Cách 2: Tạo coordinated attack (nhiều switch cùng bị tấn công)

#### Bước 1: Tạo attack từ nhiều switch
```bash
# Trong Mininet CLI
mininet> xterm h2 h5 h9
# Trong xterm h2 (switch s2):
hping3 --rand-source -1 -i u10000 -c 200 10.0.0.3 &

# Trong xterm h5 (switch s3):
hping3 --rand-source -1 -i u10000 -c 200 10.0.0.3 &

# Trong xterm h9 (switch s4):
hping3 --rand-source -1 -i u10000 -c 200 10.0.0.3 &
```

#### Bước 2: Quan sát log (Terminal 3)
```bash
# Tìm các dòng:
# - "🚨 COORDINATED ATTACK DETECTED! Affected switches: [...]"
# - "⚠️ Aggressive mitigation mode activated"
# - "🚫 Aggressive mode: Blocking ALL FLOWS from Y" (từ nhiều switch)
```

---

## Công Cụ Kiểm Tra

### 1. Xem log Ryu Controller
```bash
tail -f logs/ryu_controller.log | grep -E "(BLOCKING|mitigation|ATTACK|IP Spoofing)"
```

### 2. Xem flow table của switch
```bash
# Switch s2
sudo ovs-ofctl dump-flows s2

# Chỉ xem flow block (priority=100)
sudo ovs-ofctl dump-flows s2 | grep priority=100

# Xem flow block với thông tin chi tiết
sudo ovs-ofctl dump-flows s2 -O OpenFlow13 | grep priority=100
```

### 3. Kiểm tra trust score từ blockchain
```bash
# Query trust score của switch 1
curl http://localhost:3001/api/v1/trust/1

# Query trust score của switch 2
curl http://localhost:3001/api/v1/trust/2
```

### 4. Xem recent attacks
```bash
curl http://localhost:3001/api/v1/attacks/recent?timeWindow=300
```

### 5. Kiểm tra coordinated attack
```bash
curl "http://localhost:3001/api/v1/attacks/coordinated?timeWindow=300&threshold=3"
```

---

## Reset Trust Score (Nếu Cần)

Nếu muốn reset trust score để test lại từ đầu:

### Cách 1: Xóa và tạo lại Fabric network
```bash
cd fabric-samples/test-network
./network.sh down
./network.sh up createChannel
./network.sh deployCC -ccn trustlog -ccp ../../blockchain/chaincode -ccl go -c sdnchannel
```

### Cách 2: Tạo nhiều normal traffic để tăng trust
```bash
# Trong Mininet CLI
mininet> h1 ping -c 100 10.0.0.3
mininet> h2 ping -c 100 10.0.0.4
# Đợi vài phút để trust score tăng dần
```

---

## So Sánh Kết Quả

| Chế Độ | Log Message | Flow Rule | Traffic Status |
|--------|-------------|-----------|---------------|
| **warn_only** | "monitoring only, no blocking" | Không có priority=100 | ✅ Vẫn hoạt động |
| **standard_mitigation** | "Blocking FLOW Y → Z" | `in_port=X, ipv4_src=Y, ipv4_dst=Z, eth_type=0x0800` | ❌ Chỉ flow Y→Z bị block |
| **block_immediately** | "Blocking ALL FLOWS from Y" | `in_port=X, ipv4_src=Y, eth_type=0x0800` | ❌ Mọi flow từ IP Y bị block |

---

## Lưu Ý

1. **Thời gian block**: Flow rule block có `hardtime=120` (120 giây), sau đó tự động unblock
2. **ML Confidence**: Cần đợi ML phát hiện attack (khoảng 2-4 giây sau khi có traffic)
3. **Trust Score**: Thay đổi dần dần, không tức thì
4. **IP Spoofing**: Chỉ phát hiện khi IP không khớp với ARP table đã học
5. **Port 1 (Uplink) Protection**: 
   - Port 1 trên leaf switches (s2, s3, s4) không thể bị block trực tiếp
   - Khi phát hiện IP spoofing từ port 1, hệ thống tự động block source IP trên các port host (2-5)
   - Đảm bảo routing giữa các switch không bị ảnh hưởng
6. **Blocking Rules Limit**: 
   - Tối đa 50 blocking rules per switch
   - Hệ thống tự động kiểm tra và dừng khi đạt giới hạn
   - Chỉ log/blockchain khi có rule được tạo thành công

---

## Troubleshooting

### Không thấy log "BLOCKING"
- Kiểm tra ML có phát hiện attack không: `grep "ATTACK DETECTED" logs/ryu_controller.log`
- Kiểm tra blockchain gateway có hoạt động: `curl http://localhost:3001/health`
- Kiểm tra confidence threshold: `grep ML_CONF_THRESHOLD ryu_app/controller_blockchain.py`

### Flow rule không xuất hiện
- Kiểm tra switch có kết nối controller: `sudo ovs-vsctl show`
- Kiểm tra flow table: `sudo ovs-ofctl dump-flows s2`

### Trust score không thay đổi
- Kiểm tra blockchain có ghi event: `curl http://localhost:3001/api/v1/attacks/recent`
- Kiểm tra chaincode có hoạt động: `docker logs peer0.org1.example.com --tail 50`

