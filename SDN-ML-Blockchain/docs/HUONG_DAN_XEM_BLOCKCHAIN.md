# Hướng Dẫn Xem Events Trên Blockchain

## Tổng Quan

Khi SDN Controller phát hiện events (attack, switch connected, etc.), nó sẽ ghi vào **Hyperledger Fabric Blockchain**. Blockchain lưu trữ:
- **Security Events**: Các sự kiện bảo mật (attack, port blocked, switch connected)
- **Trust Logs**: Điểm tin cậy của từng switch/device

---

## Cách 1: Xem Qua REST API Gateway (Dễ Nhất)

### 1.1. Xem Trust Score của Switch

**Trust Score** là điểm tin cậy của switch (0.0 = không tin cậy, 1.0 = rất tin cậy).

> **Lưu ý quan trọng:**  
> Trong chaincode `trustlog.go`, `device_id` được lưu là **DPID dạng số** (ví dụ `"1"`, `"2"`, `"3"`, `"4"`), tương ứng với `dpid` của switch trong Ryu, **không** phải chuỗi `"s1"`, `"s2"`.  
> Vì vậy, khi query trust log phải dùng `"1"`, `"2"`... chứ không dùng `"s1"`.

```bash
# Xem trust score của switch có dpid = 1
curl http://localhost:3001/api/v1/trust/1

# Format đẹp hơn (cần cài jq: sudo apt install jq)
curl -s http://localhost:3001/api/v1/trust/1 | jq .
```

**Kết quả mẫu:**
```json
{
  "success": true,
  "trust_log": {
    "device_id": "1",
    "current_trust": 0.8,
    "event_count": 15,
    "last_update": 1732750000,
    "status": "trusted"
  }
}
```

**Giải thích:**
- `device_id`: ID của switch (1, 2, 3, 4 - trùng với dpid trong Mininet/Ryu)
- `current_trust`: Điểm tin cậy hiện tại (0.0 - 1.0)
- `event_count`: Số lượng events đã ghi
- `last_update`: Timestamp của lần cập nhật cuối
- `status`: Trạng thái (`trusted`, `suspicious`, `blocked`)

---

### 1.2. Xem Recent Attacks

Xem các cuộc tấn công gần đây trong khoảng thời gian (mặc định 300 giây = 5 phút):

```bash
# Xem attacks trong 5 phút qua
curl http://localhost:3001/api/v1/attacks/recent?timeWindow=300

# Format đẹp
curl -s http://localhost:3001/api/v1/attacks/recent?timeWindow=300 | jq .
```

**Kết quả mẫu:**
```json
{
  "success": true,
  "attacks": [
    {
      "event_id": "EVT-s1-abc123",
      "event_type": "attack_detected",
      "switch_id": "s1",
      "timestamp": 1732750000,
      "action": "port_blocked",
      "details": {
        "sfe": 80.0,
        "ssip": 40.0,
        "rfip": 0.5
      }
    }
  ],
  "count": 1
}
```

---

### 1.3. Xem Coordinated Attack

Kiểm tra xem có nhiều switch bị tấn công cùng lúc không (coordinated attack):

```bash
# Kiểm tra coordinated attack trong 5 phút, threshold = 3 switches
curl "http://localhost:3001/api/v1/attacks/coordinated?timeWindow=300&threshold=3"

# Format đẹp
curl -s "http://localhost:3001/api/v1/attacks/coordinated?timeWindow=300&threshold=3" | jq .
```

**Kết quả mẫu:**
```json
{
  "success": true,
  "is_coordinated": true,
  "affected_switches": ["s1", "s2", "s4"],
  "attack_count": 5
}
```

---

## Cách 2: Xem Qua Peer CLI (Chi Tiết Hơn)

### 2.1. Setup Environment

```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/fabric-samples/test-network

# Set environment variables
export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=$PWD/../config/

export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051
```

### 2.2. Query Trust Log

```bash
# Query trust log của switch có dpid = 1
peer chaincode query \
  -C sdnchannel \
  -n trustlog \
  -c '{"function":"QueryTrustLog","Args":["1"]}'
```

**Kết quả:**
```json
{"device_id":"s1","current_trust":0.8,"event_count":15,"last_update":1732750000,"status":"trusted"}
```

### 2.3. Query Events Theo Type

```bash
# ⚠️ Lưu ý: Network hiện tại dùng LevelDB nên **không hỗ trợ rich query** `QueryEventsByType/QueryEventsBySwitch`.
# Nếu bạn chạy các hàm này sẽ gặp lỗi:
#   ExecuteQuery not supported for leveldb
#
# Thay vào đó, hãy dùng các hàm được tối ưu cho LevelDB:

# Xem tất cả events (cẩn thận nếu có nhiều data)
peer chaincode query \
  -C sdnchannel \
  -n trustlog \
  -c '{"Args":["GetAllEvents"]}'

# Xem các attack events gần đây trong N giây (vd: 300 giây)
peer chaincode query \
  -C sdnchannel \
  -n trustlog \
  -c '{"Args":["GetRecentAttacks","300"]}'
```

### 2.4. Query Events Theo Switch

```bash
# Với LevelDB, không dùng được trực tiếp QueryEventsBySwitch.
# Cách khuyến nghị:
#   1) Query tất cả events hoặc recent attacks bằng peer CLI (GetAllEvents/GetRecentAttacks)
#   2) Lọc theo trường "switch_id" ở phía client (jq/Python,...)

# Ví dụ: lấy recent attacks rồi lọc switch_id bằng jq (qua REST dễ hơn):
curl -s "http://localhost:3001/api/v1/attacks/recent?timeWindow=300" | jq '.attacks[] | select(.switch_id=="1")'
```

### 2.5. Query Tất Cả Events

```bash
# Xem tất cả events (cẩn thận nếu có nhiều data)
peer chaincode query \
  -C sdnchannel \
  -n trustlog \
  -c '{"function":"GetAllEvents","Args":[]}'
```

---

## Cách 3: Xem Logs Trực Tiếp

### 3.1. Xem Gateway Logs

Gateway log sẽ hiển thị mỗi khi có event được ghi:

```bash
# Xem log real-time
tail -f /home/obito/SDN_Project/SDN-ML-Blockchain/logs/gateway.log

# Hoặc
tail -f /home/obito/SDN_Project/SDN-ML-Blockchain/blockchain/gateway.log
```

**Log mẫu:**
```
POST /api/v1/events 200 - Event recorded: EVT-s1-abc123 - attack_detected
```

### 3.2. Xem Ryu Controller Logs

Ryu controller log sẽ hiển thị khi ghi event vào blockchain:

```bash
# Xem log real-time
tail -f /home/obito/SDN_Project/SDN-ML-Blockchain/logs/ryu_controller.log
```

**Log mẫu:**
```
 Switch 1 connection logged to blockchain
 Attack event logged to blockchain
```

### 3.3. Xem Peer Logs

Xem logs của Fabric peer để thấy transactions:

```bash
# Xem logs của peer0.org1
docker logs peer0.org1.example.com --tail 50

# Xem logs real-time
docker logs -f peer0.org1.example.com
```

---

## Test Thực Tế

### Bước 1: Ghi Event Test

```bash
# Ghi một event test vào blockchain (cho switch có dpid = 1)
curl -X POST http://localhost:3001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "switch_id": "1",
    "event_type": "test_event",
    "timestamp": 1732750000,
    "action": "logged",
    "details": {"test": true}
  }'
```

**Kết quả:**
```json
{
  "success": true,
  "txId": "abc123def456...",
  "result": "",
  "attempts": 1
}
```

### Bước 2: Query Để Xác Nhận

```bash
# Xem trust log
curl -s http://localhost:3001/api/v1/trust/1 | jq .

# Kết quả sẽ có event_count tăng lên
```

---

## Giải Thích Cấu Trúc Data

### Security Event Structure

Mỗi event trong blockchain có cấu trúc:

```json
{
  "event_id": "EVT-1-abc123",            // ID duy nhất của event (EVT-{dpid}-{txId})
  "event_type": "attack_detected",       // Loại event
  "switch_id": "1",                      // ID của switch (dpid dạng số)
  "timestamp": 1732750000,                // Unix timestamp
  "action": "port_blocked",               // Hành động đã thực hiện
  "details": {                            // Chi tiết bổ sung (features)
    "sfe": 80.0,
    "ssip": 40.0,
    "rfip": 0.5
  },
  "recorded_by": "User1@org1.example.com", // Người ghi
  "recorded_time": 1732750000             // Thời gian ghi
}
```

### Trust Log Structure

Trust log tổng hợp thông tin của một switch:

```json
{
  "device_id": "1",                       // ID của switch (dpid dạng số)
  "current_trust": 0.8,                  // Điểm tin cậy trung bình
  "event_count": 15,                      // Tổng số events
  "last_update": 1732750000,              // Lần cập nhật cuối
  "status": "trusted"                     // Trạng thái
}
```

**Note:** Trust score management has been removed. Detection is now handled purely by ML model.

---

## Tóm Tắt Các Cách Xem

| Cách | Ưu điểm | Nhược điểm | Khi nào dùng |
|------|---------|------------|--------------|
| **REST API** | Dễ dùng, nhanh | Không thấy chi tiết transaction | Xem nhanh, test |
| **Peer CLI** | Chi tiết, đầy đủ | Phức tạp hơn, cần setup env | Debug, kiểm tra kỹ |
| **Logs** | Xem real-time | Chỉ thấy events mới | Monitor, debug |

---

## FAQ

### Q: Làm sao biết event đã được ghi thành công?

**A:** Kiểm tra response của API:
```bash
curl -X POST http://localhost:3001/api/v1/events ... | jq .
```

Nếu thấy `"success": true` và có `txId` → đã ghi thành công.

### Q: Event được lưu ở đâu trong blockchain?

**A:** Event được lưu trong **ledger** của channel `sdnchannel` với key là `EVT-{switch_id}-{txId}`.

### Q: Có thể xóa event không?

**A:** Không. Blockchain là **immutable** (không thể thay đổi). Một khi đã ghi, không thể xóa.

### Q: Làm sao biết có bao nhiêu events đã ghi?

**A:** Query trust log:
```bash
curl -s http://localhost:3001/api/v1/trust/s1 | jq .trust_log.event_count
```

### Q: Event nào được ghi tự động?

**A:** 
- `switch_connected`: Khi switch kết nối với controller
- `attack_detected`: Khi ML phát hiện attack
- `port_blocked`: Khi controller block port

---

## Xem Thêm

- [MANUAL_SETUP.md](./MANUAL_SETUP.md) - Hướng dẫn setup
- [BLOCKCHAIN_ACTIVE_MODE.md](./BLOCKCHAIN_ACTIVE_MODE.md) - Chế độ blockchain active

