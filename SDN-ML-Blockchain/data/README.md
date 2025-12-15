# Data Directory

Thư mục này chứa các file CSV được tạo tự động khi chạy hệ thống.

## Cấu Trúc File

### 1. Switch Data Files
**Format:** `switch_<dpid>_data.csv`

**Ví dụ:** 
- `switch_1_data.csv` - Data từ switch có DPID = 1
- `switch_2_data.csv` - Data từ switch có DPID = 2
- `switch_3_data.csv` - Data từ switch có DPID = 3

**Nội dung (current runtime schema):**
```csv
time,sfe,ssip,rfip,label,reason,confidence,dpid
2025-12-14T12:00:00Z,10,5,0.5,0,"",0.0,1
2025-12-14T12:00:05Z,12,6,0.6,1,"ml",0.92,1
```

**Các cột:**
- `time`: ISO timestamp or Unix epoch when the sample was recorded
- `sfe`: Speed of Flow Entries (tốc độ tạo flow entries)
- `ssip`: Speed of Source IP (tốc độ xuất hiện source IP mới)
- `rfip`: Ratio of Flow Pairs (tỷ lệ flow pairs)
- `label`: Detection label (0=normal, 1=attack). For training datasets in `dataset/result.csv` this field exists; for runtime rows the controller may populate it when detection/logging is enabled.
- `reason`: Optional short string describing label source (e.g., `ml`, `heuristic`, or empty)
- `confidence`: Float in [0.0,1.0] indicating detection confidence
- `dpid`: Datapath ID of the switch that emitted the row

### 2. Flow Count Files
**Format:** `switch_<dpid>_flowcount.csv`

**Nội dung:**
```csv
time,flowcount
1234567890,25
1234567891,30
```

**Các cột:**
- `time`: Timestamp
- `flowcount`: Số lượng flow entries hiện tại

### 3. Result File
**File:** `result.csv`

Tổng hợp kết quả từ tất cả switches, dùng để training ML model.

## Khi Nào File Được Tạo?

File CSV cho mỗi switch được tạo **tự động** khi:
1. Switch kết nối đến controller lần đầu
2. Controller gọi hàm `init_portcsv(dpid)` và `init_flowcountcsv(dpid)`

## Làm Sạch Data

Để xóa tất cả file CSV cũ:

```bash
# Xóa tất cả CSV trong data/
rm -f data/*.csv

# Giữ lại .gitkeep
touch data/.gitkeep
```

Hoặc dùng script:
```bash
bash scripts/clean_data.sh
```

## Ví Dụ Topology và Files

Nếu bạn chạy topology với 3 switches (s1, s2, s3), sẽ có các file:

```
data/
 .gitkeep
 switch_1_data.csv
 switch_1_flowcount.csv
 switch_2_data.csv
 switch_2_flowcount.csv
 switch_3_data.csv
 switch_3_flowcount.csv
 result.csv
```

## Monitoring Real-time

Để xem data real-time:

```bash
# Theo dõi switch 1
tail -f data/switch_1_data.csv

# Xem tất cả switches
watch -n 1 'ls -lh data/*.csv'

# Đếm số dòng (số lượng samples)
wc -l data/switch_*.csv
```

## Note

- Files này **không được commit** vào Git (đã có trong `.gitignore`)
- File `result.csv` trong `dataset/` là data training (được commit)
- File CSV trong `data/` là runtime data (không commit)
