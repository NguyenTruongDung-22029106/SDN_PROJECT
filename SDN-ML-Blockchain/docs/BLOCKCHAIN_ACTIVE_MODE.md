# Blockchain Active Mode - Tác Động Vào Hệ Thống

## Tổng Quan

Trước đây, blockchain chỉ **ghi nhận (logging)** các sự kiện. Bây giờ blockchain đã được nâng cấp để **tác động trực tiếp** vào quyết định của hệ thống.

---

## Các Tính Năng Mới

### 1⃣ **Trust-Based Blocking** (Chặn dựa trên Trust Score)

**Nguyên lý:**
- Mỗi switch có `trust_score` (0.0 - 1.0) được lưu trên blockchain
- Trust score giảm khi có attack, tăng khi traffic bình thường
- Switch có trust < 0.3 → Tự động bị block

**Luồng hoạt động:**
```
PacketIn → Query trust_score từ blockchain
              ↓
      trust_score < 0.3?
       /              \
     YES               NO
      ↓                ↓
  Block port      Process normally
  immediately
```

**Code (sử dụng `switch_id` dạng số, ví dụ `"1"`):**
```python
trust_log = blockchain_client.query_trust_log(str(dpid))
if trust_log['current_trust'] < 0.3:
    block_port(datapath, in_port, reason="Low Trust Score")
    return
```

**Ví dụ thực tế:**
```
Switch 1 bị tấn công DDoS → Trust giảm từ 1.0 → 0.2
Lần sau PacketIn → Blockchain trả về trust=0.2
Controller: " Switch 1 has low trust score (0.20), blocking port 1"
```

---

### 2⃣ **Blockchain-Guided Mitigation** (Quyết định mitigation từ blockchain)

**Nguyên lý:**
- Chaincode function `GetMitigationAction()` phân tích:
  - ML confidence
  - Trust history
  - Event count
- Trả về: `block_immediately`, `standard_mitigation`, hoặc `warn_only`

**Logic trong Chaincode:**
```go
if confidence > 0.95 {
    return "block_immediately"
}

if confidence > 0.7 {
    if trust_score < 0.5 {
        return "block_immediately"  // Low trust + medium confidence
    } else if trust_score > 0.8 {
        return "warn_only"           // High trust + medium confidence
    }
    return "standard_mitigation"
}

return "warn_only"
```

**Ví dụ:**
```
Case 1: ML confidence=0.96, trust=0.8
  → Blockchain: "block_immediately" (rất chắc chắn)

Case 2: ML confidence=0.75, trust=0.9
  → Blockchain: "warn_only" (switch có lịch sử tốt)

Case 3: ML confidence=0.75, trust=0.3
  → Blockchain: "block_immediately" (switch có lịch sử xấu)
```

---

### 3⃣ **Coordinated Attack Detection** (Phát hiện tấn công phối hợp)

**Nguyên lý:**
- Query blockchain: "Có bao nhiêu switch bị tấn công trong 5 phút?"
- Nếu ≥ 3 switches → DDoS phân tán (coordinated)
- Kích hoạt mitigation mạnh hơn trên toàn mạng

**Luồng:**
```
Switch 1 phát hiện attack
         ↓
Query blockchain: GetRecentAttacks(300s)
         ↓
Kết quả: Switch 1, 2, 4 đều bị tấn công
         ↓
CheckCoordinatedAttack(threshold=3)
         ↓
is_coordinated = TRUE
         ↓
 COORDINATED ATTACK!
         ↓
Tất cả switches → Aggressive mitigation mode
```

**Code:**
```python
is_coordinated, affected = blockchain_client.check_coordinated_attack(300, 3)
if is_coordinated:
    logger.critical(f" COORDINATED ATTACK! Switches: {affected}")
    mitigation = 2  # Aggressive mode
```

---

### 4⃣ **Mitigation Policy on Blockchain** (Chính sách trên blockchain)

**Tính năng:**
- Lưu mitigation policies trên blockchain
- Admin có thể update policy mà không cần restart controller
- Policy được audit trail minh bạch

**Cấu trúc Policy:**
```json
{
  "policy_id": "high_security",
  "name": "High Security Mode",
  "min_confidence": 0.8,
  "min_trust_score": 0.5,
  "action": "block_immediately",
  "block_duration": 300,
  "description": "Aggressive blocking for production"
}
```

**API:**
```bash
# Set policy
curl -X POST http://localhost:3001/api/v1/policy \
  -H "Content-Type: application/json" \
  -d @policy.json

# Get policy
curl http://localhost:3001/api/v1/policy/high_security
```

---

## So Sánh: Passive vs Active Mode

| Tính Năng | Passive Mode (Trước) | Active Mode (Bây giờ) |
|-----------|---------------------|----------------------|
| **Vai trò blockchain** |  Chỉ ghi log |  Tham gia quyết định |
| **Trust score** |  Chỉ để xem |  Quyết định block |
| **Quyết định mitigation** |  Hardcode trong code |  Query từ chaincode |
| **Cross-switch info** |  Không chia sẻ |  Phát hiện coordinated attack |
| **Policy management** |  Sửa code + restart |  Update on-chain, no restart |
| **Latency** |  Cực nhanh |  +50-100ms (query blockchain) |

---

## Mitigation Levels

### Level 0: Warn Only
```python
mitigation = 0
```
- Chỉ log warning
- Không block port
- Dùng khi: High trust + low confidence

### Level 1: Standard Mitigation
```python
mitigation = 1
```
- Phát hiện IP spoofing → Block port 120s
- Dùng khi: Medium confidence attack

### Level 2: Aggressive Mitigation
```python
mitigation = 2
```
- Block ngay khi thấy traffic bất thường
- Dùng khi: Coordinated attack hoặc confidence > 0.95

---

## Luồng Hoạt Động Hoàn Chỉnh

### Trường hợp 1: Attack lần đầu (Trust cao)

```
1. ML phát hiện: confidence=0.85, switch_1
2. Query blockchain: trust_score=1.0 (chưa có lịch sử)
3. GetMitigationAction() → "standard_mitigation"
4. mitigation = 1 (chế độ bình thường)
5. IP spoofing detected → Block port
6. Ghi log vào blockchain → trust_score giảm xuống 0.7
```

### Trường hợp 2: Attack lặp lại (Trust thấp)

```
1. ML phát hiện: confidence=0.80, switch_1
2. Query blockchain: trust_score=0.3 (lịch sử xấu)
3. GetMitigationAction() → "block_immediately"
4. mitigation = 2 (aggressive mode)
5. PacketIn tiếp theo → Block ngay lập tức
6. Ghi log → trust_score giảm xuống 0.15
```

### Trường hợp 3: Coordinated DDoS

```
1. Switch 1: ML phát hiện attack
2. Switch 2: ML phát hiện attack (cách 30s)
3. Switch 4: ML phát hiện attack (cách 60s)
4. CheckCoordinatedAttack(300s, threshold=3)
   → is_coordinated=true, affected=[1,2,4]
5. Tất cả controllers: mitigation = 2
6. Log "coordinated_attack_detected" vào blockchain
```

---

## API Endpoints Mới

### 1. Get Recent Attacks
```bash
GET /api/v1/attacks/recent?timeWindow=300
```
Response:
```json
{
  "success": true,
  "attacks": [
    {"switch_id": "1", "timestamp": 1732435200, "confidence": 0.95},
    {"switch_id": "2", "timestamp": 1732435230, "confidence": 0.88}
  ],
  "count": 2
}
```

### 2. Get Mitigation Action
```bash
POST /api/v1/mitigation/action
Content-Type: application/json

{
  "switch_id": "1",
  "confidence": 0.85
}
```
Response:
```json
{
  "success": true,
  "switch_id": "1",
  "confidence": 0.85,
  "action": "standard_mitigation"
}
```

### 3. Check Coordinated Attack
```bash
GET /api/v1/attacks/coordinated?timeWindow=300&threshold=3
```
Response:
```json
{
  "success": true,
  "is_coordinated": true,
  "affected_switches": ["1", "2", "4"]
}
```

### 4. Set Policy
```bash
POST /api/v1/policy
Content-Type: application/json

{
  "policy_id": "default",
  "name": "Default Policy",
  "min_confidence": 0.7,
  "min_trust_score": 0.5,
  "action": "standard_mitigation",
  "block_duration": 120
}
```

### 5. Get Policy
```bash
GET /api/v1/policy/default
```

---

## Performance Impact

### Latency Analysis:

| Operation | Passive Mode | Active Mode | Overhead |
|-----------|--------------|-------------|----------|
| PacketIn processing | 1-2ms | 50-100ms | +48-98ms |
| Attack detection | 10ms | 60-150ms | +50-140ms |
| Block port | 5ms | 5ms | 0ms |

**Giải thích overhead (với backend thực tế):**
- Query trust_log: ~30-50ms (gRPC + LevelDB/CouchDB query)
- Get mitigation action: ~30-50ms
- Check coordinated: ~50-100ms (scan nhiều events)

### Optimization:

1. **Cache trust score** (TTL 10s):
```python
trust_cache = {}
def get_trust_cached(dpid):
    if dpid in trust_cache and time.time() - trust_cache[dpid]['time'] < 10:
        return trust_cache[dpid]['trust']
    
    trust = blockchain_client.query_trust_log(dpid)
    trust_cache[dpid] = {'trust': trust, 'time': time.time()}
    return trust
```

2. **Async blockchain calls**:
```python
# Non-blocking
threading.Thread(target=blockchain_client.record_event, args=(event,)).start()
```

3. **Fast path for high confidence**:
```python
if confidence > 0.98:
    # Skip blockchain query, block immediately
    self.block_port(datapath, in_port)
```

---

## Configuration

### Environment Variables:

```bash
# Enable blockchain active mode
BLOCKCHAIN_ACTIVE_MODE=true

# Trust score threshold for auto-block
TRUST_BLOCK_THRESHOLD=0.3

# Coordinated attack threshold
COORDINATED_THRESHOLD=3
COORDINATED_TIME_WINDOW=300

# Cache trust score TTL
TRUST_CACHE_TTL=10
```

### Docker Compose:
```yaml
services:
  ryu:
    environment:
      - BLOCKCHAIN_ACTIVE_MODE=true
      - TRUST_BLOCK_THRESHOLD=0.3
      - COORDINATED_THRESHOLD=3
```

---

## Testing

### Test 1: Low Trust Blocking
```bash
# Tạo nhiều attacks để giảm trust
for i in {1..5}; do
  curl -X POST http://localhost:3001/api/v1/events \
    -d '{"event_type":"attack_detected","switch_id":"1","timestamp":'$(date +%s)',"confidence":0.95,"trust_score":0.0}'
  sleep 2
done

# Check trust score
curl http://localhost:3001/api/v1/trust/1
# Output: {"current_trust": 0.2, "status": "blocked"}

# Tiếp tục traffic → Port sẽ bị block ngay
```

### Test 2: Coordinated Attack
```bash
# Terminal 1: Attack switch 1
mininet> h1 hping3 -S --flood -p 80 10.0.2.1 &

# Terminal 2: Attack switch 2  
mininet> h5 hping3 -S --flood -p 80 10.0.3.1 &

# Terminal 3: Attack switch 4
mininet> h9 hping3 -S --flood -p 80 10.0.1.1 &

# Check log → Sẽ thấy:
# COORDINATED ATTACK DETECTED! Affected switches: ['1', '2', '4']
```

### Test 3: High Trust - Warn Only
```bash
# Tạo nhiều normal traffic
curl -X POST http://localhost:3001/api/v1/events \
  -d '{"event_type":"normal_traffic","switch_id":"2","timestamp":'$(date +%s)',"trust_score":1.0}'

# Attack với low confidence
# → Blockchain sẽ recommend "warn_only"
```

---

## Tài Liệu Liên Quan

- [Chaincode Functions](../blockchain/chaincode/trustlog.go)
- [Gateway API](../blockchain/gateway_node_server.js)
- [Controller Logic](../ryu_app/controller_blockchain.py)
- [ML Algorithms](./ML_ALGORITHMS.md)

---

## Checklist Deployment

- [ ] Deploy chaincode mới với `GetMitigationAction`, `CheckCoordinatedAttack`
- [ ] Restart gateway để load API endpoints mới
- [ ] Update controller với blockchain active logic
- [ ] Test trust-based blocking
- [ ] Test coordinated attack detection
- [ ] Monitor performance overhead
- [ ] Setup trust score cache nếu latency cao
- [ ] Configure thresholds phù hợp với môi trường

---

## Kết Luận

**Blockchain giờ đây không chỉ là "audit log"**, mà là **bộ não phân tích** giúp:
- Quyết định thông minh hơn dựa trên lịch sử
- Phát hiện tấn công phối hợp cross-switch
- Quản lý policy tập trung, minh bạch
- Trust-based security với reputation system

**Trade-off:**
- Tăng latency ~50-100ms
- Phụ thuộc vào blockchain availability
- Cần optimize với cache và async calls
