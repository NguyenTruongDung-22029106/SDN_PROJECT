# SDN-ML-Blockchain Security System

Hệ thống phát hiện và giảm thiểu tấn công DDoS trong mạng SDN sử dụng Machine Learning và Blockchain.

## Mô Tả Dự Án

Dự án tích hợp 3 công nghệ chính:
- **SDN (Software-Defined Networking)**: Điều khiển mạng linh hoạt với Ryu Controller
- **Machine Learning**: Phát hiện tấn công DDoS bằng SVM, Decision Tree, Random Forest
- **Blockchain (Hyperledger Fabric)**: Lưu trữ bất biến các sự kiện bảo mật

## Quick Start (3 Bước Đơn Giản)

### Bước 1: Fix lỗi thường gặp
```bash
cd <project-root>
bash scripts/fix_common_issues.sh
```

### Bước 2: Khởi động toàn bộ hệ thống
```bash
bash scripts/start_system.sh
```
**Thời gian:** 2-3 phút. Script sẽ tự động khởi động Fabric, Gateway, và Ryu Controller.

### Bước 3: Kiểm tra trạng thái
```bash
bash scripts/check_status.sh
```

**Xong!** Hệ thống đã sẵn sàng. Xem [QUICK_START.md](docs/QUICK_START.md) để biết thêm chi tiết.

## Cấu Trúc Dự Án

> ** Chi tiết:** Xem [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) để biết cấu trúc đầy đủ

```
SDN-ML-Blockchain/
 blockchain/          # Hyperledger Fabric integration
    chaincode/      # Smart contract (Go)
    gateway_node_server.js  # REST API Gateway
    wallet/         # Identity certificates
 ryu_app/            # SDN Controller + ML Detection
    controller_blockchain.py  # Main controller
    ml_detector.py           # ML detection module
 scripts/            # Automation scripts 
    start_system.sh          # Start entire system
    stop_system.sh           # Stop system
    fix_common_issues.sh     # Auto-fix common errors
    check_status.sh          # Check system status
 logs/               # System logs (NEW!)
    gateway.log
    ryu_controller.log
 data/               # Runtime data (CSV files)
 topology/           # Mininet network topology
 docs/               # Documentation (9 files)
    QUICK_START.md  # Quick start guide
    MANUAL_SETUP.md # Manual setup guide
    ARCHITECTURE.md # System architecture
 configs/            # Docker compose configs
    docker-compose.yml
 tests/              # Unit tests
 tools/              # Utility tools
```

## Kiểm Tra Hoạt Động

### Test Blockchain Gateway
```bash
# Gửi event test
curl -X POST http://localhost:3001/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "switch_id": "s1",
    "event_type": "attack_detected",
    "timestamp": 1234567890,
    "trust_score": 0.3,
    "action": "block_port",
    "details": {}
  }'

# Query trust score
curl http://localhost:3001/api/v1/trust/s1
```

### Xem Blockchain Logs
```bash
# Peer logs
docker logs peer0.org1.example.com --tail 50

# Gateway logs
docker logs sdn-blockchain-gateway

# Orderer logs
docker logs orderer.example.com --tail 50
```

## Tài Liệu Chi Tiết

- [QUICK_START.md](docs/QUICK_START.md) - Hướng dẫn nhanh
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Kiến trúc hệ thống
- [MANUAL_SETUP.md](docs/MANUAL_SETUP.md) - Chạy từng component riêng lẻ
- [HUONG_DAN_CHAY_DU_AN.md](docs/HUONG_DAN_CHAY_DU_AN.md) - Hướng dẫn tiếng Việt
- [FABRIC_SETUP_NOTE.md](docs/FABRIC_SETUP_NOTE.md) - Cấu hình Fabric

## Troubleshooting

### Lỗi "creator org unknown"
```bash
docker exec -it sdn-blockchain-gateway node import_identity.js
docker restart sdn-blockchain-gateway
```

### Peer không chạy
```bash
docker start peer0.org1.example.com peer0.org2.example.com orderer.example.com
```

### Reset toàn bộ hệ thống
```bash
cd fabric-samples/test-network
./network.sh down
cd ../..
bash scripts/setup_fabric.sh
```

## Development

### Sửa Chaincode
```bash
# 1. Edit chaincode
vim blockchain/chaincode/trustlog.go

# 2. Redeploy
cd fabric-samples/test-network
./network.sh deployCC -ccn trustlog -ccp ../../blockchain/chaincode -ccl go -c sdnchannel
```

### Chạy Tests
```bash
# Python tests
cd tests
python3 -m pytest test_fabric_client.py

# System verification
bash scripts/verify_system.sh
```

## Performance Metrics

Hệ thống có thể:
- Xử lý **1000+ flows/second** trên SDN controller
- Phát hiện tấn công với độ chính xác **95%+**
- Ghi log vào blockchain trong **< 3 seconds**

## Contributing

1. Fork repository
2. Tạo branch mới: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Tạo Pull Request

## License

MIT License - xem file [LICENSE](LICENSE)

## Authors

- Nguyen Truong Dung (@NguyenTruongDung-22029106)

## Acknowledgments

- Shehryar Kamran's MS Thesis - ML algorithms reference
- vishalsingh45/SDN-DDOS-Detection - Base SDN controller
- Hyperledger Fabric - Blockchain framework

## Contact

- GitHub: [@NguyenTruongDung-22029106](https://github.com/NguyenTruongDung-22029106)
- Repository: [SDN-PROJECT-SEC](https://github.com/NguyenTruongDung-22029106/SDN-PROJECT-SEC)

---

**Note**: Dự án này được phát triển cho mục đích nghiên cứu và giáo dục.
