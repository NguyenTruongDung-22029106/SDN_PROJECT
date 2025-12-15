# Triệt để: Chạy `trustlog` như external chaincode (CCaaS)

Mục tiêu
 - Chạy chaincode `trustlog` như một service Docker lâu dài (external chaincode) và mount TLS cert/key cố định vào container để fingerprint ổn định. Điều này tránh lỗi "certificate hash not found in registry" do fingerprint thay đổi khi dev-peer ephemeral container được tái tạo.

Nội dung thư mục
 - `Dockerfile` : template để build binary chaincode server.
 - `start_chaincode.sh` : entrypoint kiểm tra cert rồi chạy binary.
 - `docker-compose.trustlog-external.yml` : snippet service để thêm vào mạng của test-network.
 - `enroll_chaincode_tls.sh` : helper để chuẩn bị thư mục `certs/trustlog` (bạn cần copy hoặc enroll chứng chỉ từ CA).
 - `connection.json.template` : metadata template để chỉ endpoint & đường dẫn TLS (tham khảo).

Các bước triển khai (tóm tắt)
1) Chuẩn bị certs
   - Chạy `blockchain/cc-external/enroll_chaincode_tls.sh` và đặt file:
     - `certs/trustlog/client_pem.crt` (signcert cho chaincode service)
     - `certs/trustlog/client_pem.key` (private key)
     - `certs/trustlog/cacerts/ca-cert.pem` (CA root mà peer tin tưởng)

2) Build và chạy service
   - Từ `blockchain/cc-external` build image và chạy compose:

```bash
cd blockchain/cc-external
docker compose -f docker-compose.trustlog-external.yml build
docker compose -f docker-compose.trustlog-external.yml up -d
```

   - Lưu ý: network `byfn` trong snippet giả định bạn đang dùng test-network compose (mạng mặc định của test-network). Nếu tên mạng khác, sửa `networks` trong file.

3) Package & deploy external chaincode metadata
   - Bạn cần gói chaincode metadata so peer biết chaincode là external; dưới đây là ví dụ lệnh (adapt theo đường dẫn/peers của bạn):

```bash
# Example: package a minimal external chaincode package - this is illustrative
peer lifecycle chaincode package trustlog-external.tar.gz --path ../chaincode --lang golang --label trustlog_2.2

# Install on peers
peer lifecycle chaincode install trustlog-external.tar.gz

# Approve & commit using the standard lifecycle commands (set sequence, endorsement policy, etc.)
```

   - Thay vì package truyền thống, bạn sẽ cần đảm bảo chaincode definition cho biết endpoint external; tham khảo docs Fabric về "external chaincode" và "external builder / CCaaS" để có metadata chính xác (có thể cần thêm `connection.json` trong package metadata).

4) Kiểm tra
   - Kiểm tra peer logs (docker logs peer0.org1.example.com) để thấy peer thực hiện đăng ký chaincode thành công (no certificate-hash errors).
   - Gửi một giao dịch thử (POST qua adapter) và theo dõi commit.

Ghi chú & lưu ý
- Cert TLS phải được CA ký mà peer tin cậy.
- Đảm bảo container chaincode có hostname/endpoint mà peer có thể kết nối (dùng docker compose cùng network hoặc network alias).
- Nếu cần, tôi có thể giúp bạn thực hiện các lệnh lifecycle chính xác với tham số dựa trên cấu hình test-network của bạn (tên channel, org MSP, peer addresses). Yêu cầu: cho tôi quyền chạy một vài lệnh `peer` trong môi trường hoặc cung cấp các biến môi trường CLI cần thiết.

Tham khảo
- Hyperledger Fabric docs: test-network, chaincode lifecycle, external chaincode / CCaaS.
