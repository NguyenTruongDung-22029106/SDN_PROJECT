# Hướng Dẫn Thu Thập Dữ Liệu Thực Tế

## Trạng Thái Hiện Tại
✅ Ryu Controller đang chạy (PID: 14269)
✅ Gateway API đang chạy (PID: 14257)
✅ Controller ở chế độ **Data Collection** (APP_TYPE = 0)

## Các Bước Thu Thập Dữ Liệu

### Bước 1: Chạy Mininet (Terminal mới)

Mở terminal mới và chạy:

```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/topology
sudo python3 custom_topo.py
```

Hoặc nếu muốn tự động generate traffic:

```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/topology
TEST_TYPE=mixed TEST_TIME=60 sudo -E python3 custom_topo.py
```

### Bước 2: Generate Traffic (nếu dùng manual mode)

Trong Mininet CLI, chạy các lệnh sau:

```bash
# Normal traffic
mininet> h1 ping -c 20 h10
mininet> h2 ping -c 20 h10
mininet> h3 ping -c 20 h10

# Attack traffic (high rate)
mininet> h1 ping -f -c 1000 h10 &
mininet> h2 ping -f -c 1000 h10 &
```

Hoặc dùng script có sẵn:
```bash
mininet> h1 bash ../scripts/attack_traffic.sh &
mininet> h2 bash ../scripts/normal_traffic.sh &
```

### Bước 3: Đợi Thu Thập Dữ Liệu

Đợi ít nhất **30-60 giây** để controller thu thập đủ dữ liệu.

Trong terminal khác, bạn có thể theo dõi:
```bash
# Xem dữ liệu real-time
watch -n 1 'wc -l /home/obito/SDN_Project/SDN-ML-Blockchain/data/switch_*_data.csv'

# Hoặc xem log Ryu
tail -f /home/obito/SDN_Project/SDN-ML-Blockchain/logs/ryu_controller.log
```

### Bước 4: Kiểm Tra Dữ Liệu

Sau khi dừng Mininet, kiểm tra:

```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain

# Xem các file CSV đã tạo
ls -lh data/*.csv

# Xem nội dung dữ liệu
head -10 data/switch_1_data.csv
head -10 data/switch_1_flowcount.csv
```

### Bước 5: Vẽ Plots với Dữ Liệu Thực

```bash
cd /home/obito/SDN_Project/SDN-ML-Blockchain/visualization
python3 generate_improved_plots.py
```

## Lưu Ý

1. **Mininet cần sudo**: Phải chạy với quyền root
2. **Controller phải chạy trước**: Ryu controller phải đang chạy trước khi start Mininet
3. **Đợi đủ thời gian**: Controller thu thập dữ liệu mỗi INTERVAL giây (hiện tại là 2 giây)
4. **Kiểm tra kết nối**: Đảm bảo Mininet kết nối được với controller tại 127.0.0.1:6633

## Troubleshooting

Nếu không có dữ liệu:
1. Kiểm tra Ryu log: `tail -f logs/ryu_controller.log`
2. Kiểm tra switch có kết nối: Trong log sẽ thấy "Switch connected"
3. Kiểm tra traffic: Trong Mininet, dùng `pingall` để test connectivity

