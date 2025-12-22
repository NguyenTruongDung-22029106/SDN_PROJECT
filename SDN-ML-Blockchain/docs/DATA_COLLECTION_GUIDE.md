# HƯỚNG DẪN THU THẬP DỮ LIỆU NORMAL & ATTACK (MANUAL)

Mục tiêu: thu thập dữ liệu cân bằng, đa dạng cho huấn luyện 4 mô hình (Decision Tree, Random Forest, SVM, Naive Bayes).

## 1. Chuẩn bị
- Mở 2 terminal: một cho controller, một cho Mininet.
- Đặt biến môi trường để controller ghi dữ liệu thu thập:
  - `APP_TYPE=0` (chế độ thu thập - **QUAN TRỌNG**: Tắt ML detection và trust-based blocking)
  - `TEST_TYPE=0` cho Normal, `TEST_TYPE=1` cho Attack.
- **Lưu ý**: Trong chế độ `APP_TYPE=0`, hệ thống sẽ:
  - Tắt ML detection (không phân loại traffic)
  - Tắt trust-based blocking (cho phép thu thập dữ liệu sạch)
  - Ghi nhãn dữ liệu theo `TEST_TYPE` (0=normal, 1=attack)

## 2. Thu thập Normal (label=0)
1) Chạy controller:
```
APP_TYPE=0 TEST_TYPE=0 ryu-manager ryu_app/controller_blockchain.py
```
2) Chạy Mininet (ví dụ topo single 10 hosts):
```
sudo mn --topo single,10 --controller=remote,ip=127.0.0.1,port=6653 --switch ovsk,protocols=OpenFlow13
```
3) Sinh traffic normal trong CLI Mininet (tùy chọn vài lệnh sau, ưu tiên đa dạng):
```
# Ping all
pingall

# TCP iperf (h1→h2)
h1 iperf -c 10.0.0.2 -t 20

# UDP iperf (h3→h4)
h3 iperf -u -c 10.0.0.4 -b 5M -t 20

# Trong Mininet CLI
mininet> h1 bash -c "for i in {2..12}; do ping -c 10 -i 0.05 10.0.0.$i & done; wait" &
mininet> h2 bash -c "for i in {1,3..12}; do ping -c 10 -i 0.05 10.0.0.$i & done; wait" &
mininet> h3 bash -c "for i in {1,2,4..12}; do ping -c 10 -i 0.05 10.0.0.$i & done; wait" &
mininet> h4 bash -c "for i in {1..3,5..12}; do ping -c 10 -i 0.05 10.0.0.$i & done; wait" &
mininet> h5 bash -c "for i in {1..4,6..12}; do ping -c 10 -i 0.05 10.0.0.$i & done; wait" &
mininet> h6 bash -c "for i in {1..5,7..12}; do ping -c 10 -i 0.05 10.0.0.$i & done; wait" &
mininet> h7 bash -c "for i in {1..6,8..12}; do ping -c 10 -i 0.05 10.0.0.$i & done; wait" &
mininet> h8 bash -c "for i in {1..7,9..12}; do ping -c 10 -i 0.05 10.0.0.$i & done; wait" &

# HTTP tải file nhỏ (nếu có HTTP server nội bộ, chỉnh IP/port phù hợp)
h5 curl -m 5 http://10.0.0.6:8000/
```
4) Dừng Mininet, dừng controller.

## 3. Thu thập Attack (label=1)
1) Chạy controller:
```
APP_TYPE=0 TEST_TYPE=1 ryu-manager ryu_app/controller_blockchain.py
```
2) Chạy Mininet như trên.
3) Sinh traffic attack trong CLI Mininet (chọn một số lệnh sau):
```
# UDP flood nhẹ (h7→h8)
h7 hping3 --udp -i u10000 -d 120 10.0.0.8

# TCP SYN flood nhẹ (h9→h10)
h9 hping3 -S -p 80 -i u15000 10.0.0.10

# ICMP burst (h1→h2)
h1 ping -f -c 200 10.0.0.2
```
4) Dừng Mininet, dừng controller.

## 4. Sau thu thập

Huấn luyện 4 mô hình và xuất .pkl:
```bash
# Train tất cả models và lưu .pkl files
python3 ryu_app/ml_detector.py --all
# Models sẽ được lưu tại: ryu_app/ml_model_{model_type}.pkl
# Controller sẽ tự động load các file .pkl này khi khởi động (không cần train lại)
```

## 5. Lưu ý quan trọng
- **Luôn `APP_TYPE=0` khi thu thập**; `TEST_TYPE=0` cho Normal, `TEST_TYPE=1` cho Attack.
- **Trust-based blocking tự động tắt** trong data collection mode để tránh block traffic khi thu thập.
- Traffic Normal nên đa dạng và đủ thời gian để RFIP/SFE/SSIP có biến thiên, tránh toàn 1.0 cho RFIP.
- Dataset cân bằng giúp SVM/RandomForest học tốt và decision boundary bớt đơn giản.
- Kiểm tra `logs/ryu_controller.log` và `dataset/result.csv` (APP_TYPE=0) hoặc `data/result.csv` (APP_TYPE=1) để xác nhận đang ghi nhận dữ liệu thực (sfe/ssip khác 0).
- **SSIP được tính per-switch** (không còn global), đảm bảo tính chính xác cho mỗi switch.
- Sau khi train, models được lưu tại `ryu_app/ml_model_*.pkl` và sẽ được tự động load khi controller khởi động (không cần train lại mỗi lần).

