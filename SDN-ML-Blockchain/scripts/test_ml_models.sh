#!/bin/bash
# Script test so sánh hiệu năng các thuật toán ML

# Auto-detect project root (parent directory of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=========================================="
echo "🤖 ML Algorithms Performance Test"
echo "=========================================="
echo ""

cd "$PROJECT_ROOT"

# Test cases
echo "📊 Test cases:"
echo "  1. Normal traffic:    [sfe=10, ssip=5, rfip=15]"
echo "  2. Suspicious:        [sfe=25, ssip=12, rfip=35]"
echo "  3. DDoS attack:       [sfe=80, ssip=40, rfip=120]"
echo "  4. Heavy DDoS:        [sfe=150, ssip=80, rfip=250]"
echo ""

# Test all models
for model in decision_tree random_forest svm naive_bayes; do
    echo ""
    echo "=========================================="
    echo "Testing: $model"
    echo "=========================================="
    
    # Test classification
    python3 << EOF
import sys
import os
PROJECT_ROOT = "${PROJECT_ROOT}"
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'ryu_app'))
sys.path.insert(0, PROJECT_ROOT)

from ml_detector import MLDetector
import time

try:
    # Initialize detector
    start_init = time.time()
    detector = MLDetector(model_type='$model')
    init_time = time.time() - start_init
    
    print(f"✓ Model loaded in {init_time*1000:.2f}ms")
    print(f"✓ Trained: {detector.is_trained}")
    print("")
    
    # Test cases
    test_cases = [
        ([10, 5, 15], 'Normal traffic'),
        ([25, 12, 35], 'Suspicious'),
        ([80, 40, 120], 'DDoS attack'),
        ([150, 80, 250], 'Heavy DDoS'),
    ]
    
    total_time = 0
    correct = 0
    
    for features, label in test_cases:
        start = time.time()
        prediction, confidence = detector.classify(features)
        duration = time.time() - start
        total_time += duration
        
        result = 'ATTACK' if prediction == 1 else 'NORMAL'
        
        # Check if prediction matches expected
        expected_attack = label in ['DDoS attack', 'Heavy DDoS']
        is_correct = (prediction == 1) == expected_attack
        if is_correct:
            correct += 1
        
        status = '✓' if is_correct else '✗'
        print(f"{status} {label:20} -> {result:10} ({confidence:6.2%}) [{duration*1000:6.2f}ms]")
    
    print("")
    print(f"📊 Summary:")
    print(f"   Accuracy: {correct}/{len(test_cases)} ({correct/len(test_cases)*100:.0f}%)")
    print(f"   Avg time: {total_time/len(test_cases)*1000:.2f}ms per prediction")
    print(f"   Total:    {total_time*1000:.2f}ms")
    
    # Feature importance (if available)
    importance = detector.get_feature_importance()
    if importance:
        print("")
        print(f"📈 Feature Importance:")
        for feature, value in importance.items():
            print(f"   {feature:5} {value:.3f} {'█' * int(value * 50)}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

EOF

done

echo ""
echo "=========================================="
echo "✅ Test completed!"
echo "=========================================="
echo ""
echo "💡 Khuyến nghị:"
echo "   - Decision Tree: Nhanh nhất, phù hợp development"
echo "   - Random Forest: Chính xác nhất, phù hợp production"
echo "   - SVM: Cân bằng, phù hợp dataset nhỏ"
echo "   - Naive Bayes: Cực nhanh, độ chính xác thấp"
