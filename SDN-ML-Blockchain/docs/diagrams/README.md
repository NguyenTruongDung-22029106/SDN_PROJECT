# SDN-ML-Blockchain System Diagrams

Thư mục này chứa tất cả các sơ đồ kiến trúc hệ thống được vẽ bằng Mermaid.

## 📋 Danh sách Diagrams

### 1. **System Overview** (`01_system_overview.mmd`)
- **Mô tả**: Kiến trúc tổng thể hệ thống
- **Nội dung**: Application Layer, Control Plane, Data Plane, Blockchain Layer
- **Loại**: Graph TB (Top to Bottom)

### 2. **Attack Detection Flow** (`02_attack_detection_flow.mmd`)
- **Mô tả**: Luồng phát hiện và xử lý tấn công DDoS
- **Nội dung**: Sequence diagram từ Attacker → Switch → Controller → ML → Mitigation → Blockchain
- **Loại**: Sequence Diagram

### 3. **ML Detection Pipeline** (`03_ml_detection_pipeline.mmd`)
- **Mô tả**: Pipeline phát hiện tấn công bằng Machine Learning
- **Nội dung**: Feature extraction → ML classification → Decision logic → Mitigation
- **Loại**: Flowchart TD (Top Down)

### 4. **Blockchain Layer** (`04_blockchain_layer.mmd`)
- **Mô tả**: Kiến trúc lớp Blockchain - Hyperledger Fabric
- **Nội dung**: Controller → Gateway → Chaincode → Peers → Ledger
- **Loại**: Graph TB

### 5. **Data Structure** (`05_data_structure.mmd`)
- **Mô tả**: Cấu trúc dữ liệu SecurityEvent trong Blockchain
- **Nội dung**: SecurityEvent class, Details class, EventTypes, Actions
- **Loại**: Class Diagram

### 6. **Data Collection & Training** (`06_data_collection_training.mmd`)
- **Mô tả**: Quy trình thu thập dữ liệu và huấn luyện ML model
- **Nội dung**: Collection Mode → Training Phase → Detection Mode
- **Loại**: Flowchart LR (Left to Right)

### 7. **Production Deployment** (`07_production_deployment.mmd`)
- **Mô tả**: Kiến trúc triển khai Production
- **Nội dung**: Network Layer, SDN Infrastructure, Blockchain Infrastructure, Application Layer
- **Loại**: Graph TB

### 8. **IP Spoofing vs ML** (`08_ip_spoofing_vs_ml.mmd`)
- **Mô tả**: So sánh cơ chế phát hiện IP Spoofing và ML Detection
- **Nội dung**: Decision flow giữa IP Spoofing Detection và ML Detection
- **Loại**: Flowchart TD

### 9. **Component Interaction** (`09_component_interaction.mmd`)
- **Mô tả**: Sơ đồ tương tác giữa các thành phần
- **Nội dung**: Sequence diagram chi tiết của tất cả components
- **Loại**: Sequence Diagram

### 10. **Feature Extraction** (`10_feature_extraction.mmd`)
- **Mô tả**: Quy trình trích xuất đặc trưng (Features)
- **Nội dung**: SFE, SSIP, RFIP calculation process
- **Loại**: Flowchart TD

### 11. **System Modes** (`11_system_modes.mmd`)
- **Mô tả**: Các chế độ hoạt động của hệ thống
- **Nội dung**: Collection Mode vs Detection Mode state machine
- **Loại**: State Diagram

### 12. **ML Model Comparison** (`12_ml_model_comparison.mmd`)
- **Mô tả**: So sánh các thuật toán Machine Learning
- **Nội dung**: Decision Tree, Random Forest, SVM, Naive Bayes
- **Loại**: Graph TD

## 🎨 Cách sử dụng

### 1. Xem trực tiếp trong GitHub/GitLab
File `.mmd` sẽ được render tự động khi xem trên GitHub/GitLab.

### 2. Sử dụng Mermaid Live Editor
- Truy cập: https://mermaid.live/
- Copy nội dung file `.mmd` và paste vào editor
- Export sang PNG/SVG/PDF

### 3. Sử dụng VS Code Extension
- Cài đặt extension: "Markdown Preview Mermaid Support"
- Mở file `.mmd` hoặc embed vào Markdown
- Preview trực tiếp trong VS Code

### 4. Embed vào Markdown
```markdown
```mermaid
# Copy nội dung từ file .mmd vào đây
\```
```

### 5. Export sang ảnh bằng Mermaid CLI
```bash
# Cài đặt Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Export sang PNG
mmdc -i 01_system_overview.mmd -o 01_system_overview.png

# Export sang SVG
mmdc -i 01_system_overview.mmd -o 01_system_overview.svg

# Export tất cả
for file in *.mmd; do
    mmdc -i "$file" -o "${file%.mmd}.png"
done
```

## 📚 Tài liệu tham khảo

- **Mermaid Documentation**: https://mermaid.js.org/
- **Mermaid Live Editor**: https://mermaid.live/
- **Mermaid Syntax**: https://mermaid.js.org/intro/syntax-reference.html

## ✅ Đặc điểm của các Diagrams

Tất cả các diagram đều:
- ✅ Phản ánh chính xác 100% hệ thống hiện tại
- ✅ KHÔNG có `confidence`, `threshold`, `predict_proba`
- ✅ KHÔNG có `TrustScore` trong blockchain
- ✅ Có `ENABLE_IP_SPOOFING_DETECTION` environment variable
- ✅ APP_TYPE=0 → `dataset/result.csv`, APP_TYPE=1 → `data/result.csv`
- ✅ ML chỉ dùng `model.predict()` (không có `predict_proba`)
- ✅ Decision logic đơn giản: `if '1' in result`
- ✅ Default model: `decision_tree`
- ✅ Blockchain chỉ logging (passive mode)

## 🎯 Sử dụng cho

- 📊 **Báo cáo dự án**: Minh họa kiến trúc và workflow
- 🎓 **Thuyết trình**: Giải thích hệ thống cho người khác
- 📖 **Documentation**: Bổ sung vào tài liệu kỹ thuật
- 🔍 **Debugging**: Hiểu rõ luồng xử lý để debug
- 👨‍🏫 **Đào tạo**: Hướng dẫn người mới về hệ thống

## 📝 Lưu ý

- Các file `.mmd` là plain text, có thể edit trực tiếp
- Syntax Mermaid rất đơn giản và dễ học
- Có thể customize màu sắc bằng `style` directive
- Hỗ trợ nhiều loại diagram: flowchart, sequence, class, state, etc.

