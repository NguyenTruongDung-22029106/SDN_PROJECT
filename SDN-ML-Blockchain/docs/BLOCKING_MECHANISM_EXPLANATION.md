# Giải Thích Cơ Chế Blocking Mới (Port-Only Blocking)


## 1. Cơ Chế 


### Cơ Chế (Port-Only):
- **port_only**: Block tất cả traffic từ port
  - Flow rule: `in_port=X, actions=drop`
  - Block **TẤT CẢ** traffic từ port X (không phân biệt IP)
  - Đơn giản, hiệu quả

## 3. Cách Hoạt Động

### Khi Phát Hiện Attack:

1. **ML Model phát hiện attack** → Prediction = ['1']
2. **Blockchain logging**:
   - Ghi log attack vào blockchain
   - Không quyết định hành động
3. **IP Spoofing Detection**:
   - Phát hiện IP không khớp với ARP table
   - Block port ngay
4. **Block Port**:
   - Tạo flow rule: `in_port=X, actions=drop`
   - Hard timeout: 60 giây (tự động unblock sau 60s)
   - Log vào blockchain

### Ví Dụ Cụ Thể:

**Scenario**: h2 (port 2 trên switch s2) tấn công h3

1. h2 gửi traffic attack → Switch s2 nhận trên port 2
2. ML model phát hiện: Prediction = ['1'] (Attack)
3. Phát hiện IP spoofing → Block port ngay
4. Hệ thống tạo flow rule:
   ```
   priority=100, in_port=2, actions=drop
   ```
5. **Kết quả**: 
   - Tất cả traffic từ port 2 bị block (không phân biệt IP)
   - h2 không thể gửi bất kỳ traffic nào
   - Các host khác (h1, h3, h4) vẫn hoạt động bình thường

## 4. Ưu Điểm

### Đơn Giản:
- Chỉ cần 1 flow rule: `in_port=X, actions=drop`
- Không cần phân biệt IP, không cần match src/dst
- Dễ debug, dễ kiểm tra

### Hiệu Quả:
- Block ngay lập tức tất cả traffic từ port
- Không cần tạo nhiều rules cho nhiều IP
- Tiết kiệm flow table space

### Phù Hợp với DDoS:
- DDoS thường từ 1 port (1 host)
- Block port = block toàn bộ host
- Ngăn chặn hiệu quả

### Giống Repo Tham Khảo:
- Dễ so sánh, dễ hiểu
- Phù hợp với nghiên cứu

## 5. Nhược Điểm

### ⚠️ Block Toàn Bộ Host:
- Block port = block tất cả traffic từ host đó
- Không thể block chỉ 1 IP cụ thể
- Có thể block nhầm traffic hợp pháp

### ⚠️ Không Linh Hoạt:
- Không thể block chỉ flow cụ thể
- Không thể block chỉ IP spoofed (phải block cả IP thật)

## 6. Flow Rule Format

### Cơ Chế Mới:
```
priority=100, in_port=2, actions=drop
```

### So Sánh với Cơ Chế Cũ:
```
# flow_specific (đã loại bỏ):
priority=100, in_port=2, ipv4_src=10.0.0.2, ipv4_dst=10.0.0.3, eth_type=0x0800, actions=drop

# source_ip (đã loại bỏ):
priority=100, in_port=2, ipv4_src=10.0.0.2, eth_type=0x0800, actions=drop

# port_only (mới):
priority=100, in_port=2, actions=drop
```

## 7. Khi Nào Block?

### Điều Kiện Block:
1. **IP Spoofing Detection**:
   - IP không khớp với ARP table
   - Port đã có IP được học (để tránh block nhầm IP thật)

2. **Port hợp lệ**:
   - Bất kỳ port nào đều có thể block

## 8. Tự Động Unblock

### Hard Timeout:
- Flow rule có `hardtime=60` (60 giây)
- Sau 60 giây, flow rule tự động bị xóa
- Port tự động được unblock

### Lý Do:
- Cho phép host có cơ hội phục hồi
- Tránh block vĩnh viễn
- Tự động cleanup

### Code:
```python
self.add_flow(datapath, 100, match, actions, flow_serial_no, hardtime=120)
```

## 9. Logging & Blockchain

### Log Messages:
```
🚫 BLOCKING PORT 2 on switch 2 for 60s (reason: DDoS Attack Detected)
⛓️ Port blocking logged to blockchain (mode: port_only)
```

### Blockchain Event:
```json
{
  "event_type": "port_blocked",
  "switch_id": "2",
  "port": 2,
  "timestamp": 1234567890,
  "reason": "DDoS Attack Detected",
  "action": "port_blocked_for_60s",
  "block_mode": "port_only"
}
```

## 10. Code Implementation

### Function `block_port()`:

```python
def block_port(self, datapath, portnumber, src_ip=None, dst_ip=None, 
               reason="DDoS Attack", block_mode="port_only"):
    """
    Block traffic from specific port (giống repo tham khảo)
    Chỉ block port number, không block theo IP
    """
    dpid = datapath.id
    
    # Bảo vệ port 1 (uplink)
    if portnumber == 1 and dpid != 1:
        self.logger.warning("Cannot block port 1 (uplink port)")
        return
    
    # Kiểm tra giới hạn
    if self.blocking_rules_count[dpid] >= 50:
        self.logger.warning("Reached maximum blocking rules")
        return
    
    # Tạo flow rule: chỉ match in_port
    match_args = {'in_port': portnumber}
    match = parser.OFPMatch(**match_args)
    actions = []
    
    # Install flow với hardtime=60s
    self.add_flow(datapath, 100, match, actions, flow_serial_no, hardtime=60)
    
    # Log và ghi blockchain
    self.logger.warning(f"🚫 BLOCKING PORT {portnumber} on switch {dpid} for 60s")
    # ... blockchain logging ...
```


### Hệ Thống Hiện Tại:
- ✅ Sử dụng ML (Random Forest, SVM, Decision Tree, Naive Bayes)
- ✅ Block port number (giống repo)
- ✅ Có blockchain logging
- ✅ Có trust-based mitigation
- ✅ Bảo vệ port 1 (uplink)

## 12. Kết Luận

Cơ chế blocking mới **đơn giản, hiệu quả, và phù hợp với DDoS mitigation**:

- ✅ Chỉ block port number
- ✅ Block tất cả traffic từ port đó
- ✅ Đơn giản, dễ hiểu
- ✅ Giống repo tham khảo
- ✅ Tự động unblock sau 60s
- ✅ Logging và blockchain integration

### Trade-offs:
- ⚠️ Block toàn bộ host (không linh hoạt)
- ⚠️ Có thể block nhầm traffic hợp pháp
- ✅ Nhưng đơn giản và hiệu quả cho DDoS mitigation

