# Hướng dẫn sử dụng các thuật toán Machine Learning

## Danh sách thuật toán được hỗ trợ

### 1. **Decision Tree** (Cây quyết định) -  MẶC ĐỊNH
- **Model**: `sklearn.tree.DecisionTreeClassifier()`
- **Tốc độ**:  (Rất nhanh)
- **Độ chính xác**:  (Trung bình)
- **Phù hợp**: Real-time detection, dữ liệu đơn giản
- **Nhược điểm**: Dễ overfit, nhạy cảm với noise

### 2. **Random Forest** (Rừng ngẫu nhiên) -  KHUYẾN KHÍCH
- **Model**: `sklearn.ensemble.RandomForestClassifier(n_estimators=100)`
- **Tốc độ**:  (Khá nhanh)
- **Độ chính xác**:  (Rất cao)
- **Phù hợp**: Production environment, cần độ chính xác cao
- **Ưu điểm**: Chống overfit tốt, robust với noise

### 3. **SVM** (Support Vector Machine)
- **Model**: `sklearn.svm.SVC(probability=True)`
- **Tốc độ**:  (Chậm)
- **Độ chính xác**:  (Cao)
- **Phù hợp**: Dataset nhỏ, phân tách phi tuyến
- **Nhược điểm**: Chậm với dataset lớn, nhạy cảm với hyperparameters

### 4. **Naive Bayes** (Bayes ngây thơ)
- **Model**: `sklearn.naive_bayes.GaussianNB()`
- **Tốc độ**:  (Cực nhanh)
- **Độ chính xác**:  (Thấp)
- **Phù hợp**: Baseline model, tài nguyên hạn chế
- **Nhược điểm**: Giả định features độc lập (không thực tế với network traffic)

---

## Cách đổi thuật toán

### **Phương pháp 1: Dùng biến môi trường** ( KHUYẾN KHÍCH)

#### Linux/macOS:
```bash
# Random Forest (độ chính xác cao)
export ML_MODEL_TYPE=random_forest
ryu-manager ryu_app/controller_blockchain.py

# SVM
export ML_MODEL_TYPE=svm
ryu-manager ryu_app/controller_blockchain.py

# Naive Bayes (cực nhanh)
export ML_MODEL_TYPE=naive_bayes
ryu-manager ryu_app/controller_blockchain.py

# Decision Tree (mặc định)
export ML_MODEL_TYPE=decision_tree
ryu-manager ryu_app/controller_blockchain.py
```

#### Docker:
```bash
# Trong docker-compose.yml
services:
  ryu:
    environment:
      - ML_MODEL_TYPE=random_forest
```

### **Phương pháp 2: Sửa code trực tiếp**

Mở file `ryu_app/controller_blockchain.py`, tìm dòng:

```python
ML_MODEL_TYPE = os.environ.get('ML_MODEL_TYPE', 'decision_tree')
```

Sửa thành:

```python
ML_MODEL_TYPE = os.environ.get('ML_MODEL_TYPE', 'random_forest')  # Đổi default
```

---

## So sánh hiệu năng

| Thuật toán | Training Time | Prediction Time | Accuracy | Memory Usage |
|-----------|--------------|----------------|----------|--------------|
| Decision Tree | 0.1s | 0.001s | 85-90% | Thấp |
| Random Forest | 1.0s | 0.01s | 92-97% | Trung bình |
| SVM | 5.0s | 0.1s | 88-93% | Cao |
| Naive Bayes | 0.05s | 0.0005s | 75-82% | Rất thấp |

*Dựa trên dataset 10,000 samples, 3 features*

---

## Test và so sánh các thuật toán

### Script test tất cả thuật toán:

```bash
#!/bin/bash
# test_all_models.sh

echo "Testing all ML algorithms..."

for model in decision_tree random_forest svm naive_bayes; do
    echo ""
    echo "=========================================="
    echo "Testing $model"
    echo "=========================================="
    
    export ML_MODEL_TYPE=$model
    
    # Train model
    python3 -c "
from ryu_app.ml_detector import MLDetector
detector = MLDetector(model_type='$model', model_path='dataset/result.csv')
print(f' {model} trained successfully')
"
    
    # Test model
    python3 -c "
from ryu_app.ml_detector import MLDetector
import time

detector = MLDetector(model_type='$model')

# Test cases
test_cases = [
    ([10, 5, 15], 'Normal traffic'),
    ([80, 40, 120], 'DDoS attack'),
    ([25, 12, 35], 'Suspicious'),
]

print(f'\nTesting {model}:')
for features, label in test_cases:
    start = time.time()
    prediction, confidence = detector.classify(features)
    duration = time.time() - start
    
    result = 'Attack' if prediction == 1 else 'Normal'
    print(f'  {label:20} -> {result:10} ({confidence:.2%}) [{duration*1000:.2f}ms]')
"
done
```

Chạy script:

```bash
chmod +x scripts/test_all_models.sh
./scripts/test_all_models.sh
```

---

## Khuyến nghị cho production

### Môi trường khác nhau:

1. **Development/Testing**: `decision_tree`
   - Nhanh, dễ debug, phù hợp với iterate nhanh

2. **Production (Real-time)**: `random_forest`
   - Cân bằng tốt giữa accuracy và speed
   - Robust với noise và outliers

3. **Production (High accuracy)**: `random_forest` hoặc `svm`
   - Khi cần độ chính xác cao nhất
   - Chấp nhận tốc độ chậm hơn

4. **Embedded/IoT**: `naive_bayes` hoặc `decision_tree`
   - Tài nguyên hạn chế
   - Ưu tiên tốc độ

---

## Fine-tuning hyperparameters

### Random Forest:
```python
# Trong ml_detector.py, sửa dòng:
self.model = RandomForestClassifier(
    n_estimators=100,      # Số lượng cây (tăng = chính xác hơn nhưng chậm hơn)
    max_depth=10,          # Độ sâu tối đa của mỗi cây
    min_samples_split=5,   # Số sample tối thiểu để split
    random_state=42        # Reproducibility
)
```

### SVM:
```python
self.model = svm.SVC(
    kernel='rbf',          # 'linear', 'poly', 'rbf', 'sigmoid'
    C=1.0,                 # Regularization parameter
    gamma='scale',         # Kernel coefficient
    probability=True
)
```

### Decision Tree:
```python
self.model = tree.DecisionTreeClassifier(
    max_depth=10,          # Giới hạn độ sâu để tránh overfit
    min_samples_split=5,
    criterion='gini'       # 'gini' hoặc 'entropy'
)
```

---

## Debug và monitoring

### Xem model đang sử dụng:
```bash
grep "ML Detector initialized" /tmp/ryu_controller.log
```

Output:
```
 ML Detector initialized with RANDOM_FOREST algorithm
```

### Kiểm tra model files:
```bash
ls -lh ryu_app/ml_model_*.pkl
```

### Xem feature importance (Random Forest/Decision Tree):
```python
from ryu_app.ml_detector import MLDetector

detector = MLDetector(model_type='random_forest')
importance = detector.get_feature_importance()
print(importance)
# Output: {'SFE': 0.45, 'SSIP': 0.35, 'RFIP': 0.20}
```

---

## Tài liệu tham khảo

- **Scikit-learn Documentation**: https://scikit-learn.org/stable/
- **Random Forest**: https://scikit-learn.org/stable/modules/ensemble.html#forest
- **SVM**: https://scikit-learn.org/stable/modules/svm.html
- **Decision Trees**: https://scikit-learn.org/stable/modules/tree.html
- **Naive Bayes**: https://scikit-learn.org/stable/modules/naive_bayes.html

---

## FAQ

**Q: Thuật toán nào tốt nhất cho DDoS detection?**  
A: `random_forest` - Cân bằng tốt giữa accuracy (92-97%) và tốc độ

**Q: Có thể thêm thuật toán khác không?**  
A: Có! Edit `ml_detector.py`, thêm vào `_create_default_model()` method

**Q: Training data ở đâu?**
A: `dataset/result.csv` - Committed training dataset. Format used for training: `sfe,ssip,rfip,label`.

Note: Runtime CSVs produced by the running controller are stored under `data/` (for example `data/switch_1_data.csv` and `data/result.csv`) and include an extended schema used for logging/detection: `time,sfe,ssip,rfip,label,reason,confidence,dpid`.

**Q: Làm sao re-train model?**  
A: 
1. Xóa file `ryu_app/ml_model_*.pkl`
2. Hoặc chạy: `python3 ryu_app/ml_detector.py --all`
3. Controller sẽ tự động train lại khi khởi động nếu không tìm thấy .pkl file

**Q: Model lưu ở đâu?**  
A: `ryu_app/ml_model_{model_type}.pkl` (dùng joblib). Controller ưu tiên load file .pkl này khi khởi động (không train lại mỗi lần).

**Q: Confidence threshold được tính như thế nào?**
A: 
- Base threshold: `ML_CONF_THRESHOLD` (mặc định 0.8)
- Dynamic adjustment dựa trên model threshold (từ .pkl):
  - Nếu model threshold < 0.6 → effective = max(ML_CONF_THRESHOLD, 0.75)
  - Nếu model threshold > 0.7 → effective = max(ML_CONF_THRESHOLD, model_threshold - 0.1)
  - Ngược lại → effective = ML_CONF_THRESHOLD
- Mục đích: Giảm false positives, tăng độ chính xác detection
