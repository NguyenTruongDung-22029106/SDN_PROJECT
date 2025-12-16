# PHÂN TÍCH CÁC BIỂU ĐỒ DECISION BOUNDARY

## 📊 TÓM TẮT NHẬN XÉT

### ✅ **ĐIỂM ĐÚNG:**
1. **Các mô hình đều học được ranh giới phân loại** - không có lỗi training
2. **SFE là feature quan trọng nhất** - phù hợp với lý thuyết DDoS detection
3. **Phân loại rõ ràng giữa Normal và Attack** dựa trên SFE

### ⚠️ **VẤN ĐỀ PHÁT HIỆN:**

#### 1. **RFIP của Normal không có biến thiên**
- **Normal**: RFIP = 1.0 (cố định, 100% samples)
- **Attack**: RFIP = 0.0-1.0 (đa dạng)
- **Hệ quả**: RFIP không hữu ích để phân loại Normal

#### 2. **Dữ liệu Normal quá đơn điệu**
- Normal chỉ có SFE thấp (0-12), SSIP thấp (0-8)
- Thiếu các samples Normal với SFE/SSIP trung bình (20-100)
- **Hệ quả**: Ranh giới quá đơn giản, không phản ánh đúng thực tế

#### 3. **Ranh giới quyết định quá đơn giản**
- Hầu hết các mô hình chỉ dùng ngưỡng SFE để phân loại
- Thiếu tính phức tạp như biểu đồ của tác giả gốc

---

## 🔍 CHI TIẾT TỪNG BIỂU ĐỒ

### **Decision Tree (SFE vs RFIP)**
- ✅ Ranh giới thẳng đứng ở SFE ≈ 0
- ⚠️ RFIP không được sử dụng (do Normal có RFIP=1.0 cố định)
- ⚠️ Quá đơn giản, chỉ phân loại dựa trên SFE

### **Decision Tree (SFE vs SSIP)**
- ✅ Ranh giới ngang ở SSIP ≈ 0
- ⚠️ Chỉ phân loại dựa trên SSIP, bỏ qua SFE trong một số trường hợp
- ⚠️ Quá đơn giản

### **SVM (SFE vs RFIP)**
- ✅ Ranh giới thẳng đứng ở SFE ≈ 50
- ✅ Phân loại tốt hơn Decision Tree
- ⚠️ Vẫn quá đơn giản, RFIP không được sử dụng hiệu quả

### **SVM (SFE vs SSIP)**
- ✅ Ranh giới đường chéo - tốt nhất trong các biểu đồ
- ✅ Sử dụng cả SFE và SSIP
- ⚠️ Vẫn đơn giản hơn so với tác giả gốc

### **Random Forest (SFE vs RFIP) & (SFE vs SSIP)**
- ⚠️ Hầu hết không gian được phân loại là Attack (class 1)
- ⚠️ Ranh giới không rõ ràng
- ⚠️ Có thể do dữ liệu mất cân bằng hoặc thiếu đa dạng

### **Naive Bayes (SFE vs RFIP) & (SFE vs SSIP)**
- ⚠️ Hầu hết không gian là Attack
- ⚠️ Ranh giới không rõ ràng
- ⚠️ Model không học được ranh giới tốt với dữ liệu hiện tại

---

## 💡 ĐỀ XUẤT CẢI THIỆN

### 1. **Thu thập thêm dữ liệu Normal đa dạng hơn**
```bash
# Cần thu thập Normal với:
- SFE: 0-500 (không chỉ 0-12)
- SSIP: 0-500 (không chỉ 0-8)
- RFIP: 0.0-1.0 (không chỉ 1.0)
```

### 2. **Tạo dữ liệu Normal với RFIP đa dạng**
- Chạy nhiều loại traffic normal khác nhau
- Đảm bảo RFIP có giá trị từ 0.0 đến 1.0

### 3. **Cân bằng dữ liệu**
- Tăng số lượng Attack samples để cân bằng với Normal
- Hoặc giảm Normal nhưng đảm bảo đa dạng

### 4. **Kiểm tra lại cách tính RFIP**
- Xem lại công thức tính RFIP trong controller
- Đảm bảo RFIP có biến thiên cho cả Normal và Attack

---

## 📈 KẾT LUẬN

**Các biểu đồ hiện tại PHẢN ÁNH ĐÚNG dữ liệu của bạn**, nhưng:
- Dữ liệu quá đơn điệu → Ranh giới quá đơn giản
- RFIP của Normal không có biến thiên → Feature không hữu ích
- Thiếu dữ liệu Normal đa dạng → Không thể học ranh giới phức tạp

**Để có biểu đồ như tác giả gốc**, bạn cần:
1. ✅ Thu thập Normal với SFE/SSIP đa dạng hơn
2. ✅ Đảm bảo RFIP có biến thiên cho Normal
3. ✅ Cân bằng và đa dạng hóa dữ liệu

