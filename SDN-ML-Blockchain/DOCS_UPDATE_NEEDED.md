# DANH SÁCH FILES CẦN CẬP NHẬT

## 🎯 Các thay đổi cần áp dụng

### 1. Xóa references đến `build_dataset.py`
**Lý do:** File này đã DEPRECATED, không còn sử dụng

**Files cần sửa:**
- DATA_COLLECTION_GUIDE.md ✅ (đang sửa)
- HUONG_DAN_THU_THAP_DU_LIEU.md
- Các file khác có mention build_dataset

**Thay thế bằng:**
```bash
# Trực tiếp train từ dataset/result.csv
python3 ryu_app/ml_detector.py --all --data dataset/result.csv
```

### 2. Xóa/Cập nhật confidence threshold logic
**Lý do:** Đã đơn giản hóa, không còn dùng confidence threshold

**Files cần sửa:**
- ML_ALGORITHMS.md (9 occurrences)
- QUICK_START.md ✅ (đã sửa CSV schema)
- Các file giải thích ML logic

**Thay đổi:**
- Trước: `if prediction==1 and confidence >= threshold`
- Sau: `if '1' in result`

### 3. Cập nhật CSV schema
**Lý do:** Không còn cột "confidence"

**Trước:** `time,sfe,ssip,rfip,label,reason,confidence,dpid`
**Sau:** `time,sfe,ssip,rfip,label,reason,dpid`

### 4. Cập nhật ML workflow
**Lý do:** Đơn giản hóa train/predict process

**Workflow mới:**
1. Thu thập: `APP_TYPE=0 TEST_TYPE=0/1`
2. Train: `python3 ryu_app/ml_detector.py --all`
3. Detect: `APP_TYPE=1 ryu-manager ...`

## 📊 Tiến độ

| File | Status | Notes |
|------|--------|-------|
| QUICK_START.md | ✅ | Đã xóa confidence trong CSV |
| DATA_COLLECTION_GUIDE.md | ⏳ | Đang cập nhật |
| ML_ALGORITHMS.md | ⏳ | Cần xóa Q&A về threshold |
| build_dataset.py | ✅ | Đã đánh dấu DEPRECATED |
| Các file khác | ⏳ | Chưa bắt đầu |

## 🔍 Cách tìm files cần sửa

```bash
# Tìm files có build_dataset
grep -l "build_dataset" docs/*.md

# Tìm files có confidence threshold
grep -l "confidence.*threshold\|ML_CONF_THRESHOLD" docs/*.md

# Tìm files có CSV schema cũ
grep -l "confidence,dpid" docs/*.md
```

