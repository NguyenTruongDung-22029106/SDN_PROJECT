#!/usr/bin/env python3
"""
ML Model Analysis Tool
Evaluates pre-trained ML models for DDoS detection
Note: Models must be trained first using ml_detector.py --all
"""

import sys
import os

# Auto-detect project root (parent directory of ryu_app/)
RYU_APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(RYU_APP_DIR)
sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import time

print("=" * 70)
print("ML Model Analysis Tool - DDoS Detection")
print("=" * 70)

# Load dataset
print("\n1. Loading test data...")
data_file = os.path.join(PROJECT_ROOT, 'dataset', 'result.csv')
if not os.path.exists(data_file):
    print(f"❌ Error: Dataset not found at {data_file}")
    print("   Please run: python3 ryu_app/build_dataset.py")
    sys.exit(1)

df = pd.read_csv(data_file)
print(f"   Loaded {len(df)} samples")
print(f"   Features: {list(df.columns[:-1])}")
print(f"   Classes: {df['label'].unique()}")

# Prepare data
X = df[['sfe', 'ssip', 'rfip']].values
y = df['label'].values

# Split train/test (use same split for consistency)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

print(f"\n2. Data split:")
print(f"   Training: {len(X_train)} samples")
print(f"   Testing: {len(X_test)} samples")
print(f"   Train distribution: {np.bincount(y_train)}")
print(f"   Test distribution: {np.bincount(y_test)}")

# Check for pre-trained models
print("\n3. Checking for pre-trained models...")
algorithms = ['svm', 'decision_tree', 'random_forest', 'naive_bayes']
model_dir = RYU_APP_DIR  # Models are in ryu_app/
available_models = {}

for algo in algorithms:
    model_file = os.path.join(model_dir, f'ml_model_{algo}.pkl')
    if os.path.exists(model_file):
        available_models[algo] = model_file
        print(f"   ✓ Found: {algo} ({model_file})")
    else:
        print(f"   ✗ Missing: {algo}")

if not available_models:
    print("\n❌ No pre-trained models found!")
    print("   Please train models first:")
    print("   python3 ryu_app/ml_detector.py --all --data dataset/result.csv")
    sys.exit(1)

# Helper function to classify using loaded model
def classify_with_model(model, features):
    """Classify features using loaded model"""
    # Nếu model được lưu dạng dict {model, threshold}, tách ra
    threshold = 0.5
    if isinstance(model, dict) and "model" in model:
        threshold = float(model.get("threshold", 0.5))
        model = model["model"]

    fparams = np.array(features).reshape(1, -1)
    prediction = model.predict(fparams)[0]
    
    # Get confidence if model supports probability
    try:
        probabilities = model.predict_proba(fparams)[0]
        confidence = max(probabilities)
    except Exception:
        confidence = 0.8  # Default confidence
    
    return int(prediction), float(confidence)

# Evaluate models
print("\n4. Evaluating models...")
print("-" * 70)
results = []

for algo, model_file in available_models.items():
    print(f"\n   Evaluating {algo.upper()}...")
    start_time = time.time()
    
    try:
        # Load pre-trained model
        model = joblib.load(model_file)
        
        # Evaluate on test set
        predictions = []
        confidences = []
        
        for features in X_test:
            pred, conf = classify_with_model(model, features)
            predictions.append(pred)
            confidences.append(conf)
        
        predictions = np.array(predictions)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, predictions)
        precision = precision_score(y_test, predictions, zero_division=0)
        recall = recall_score(y_test, predictions, zero_division=0)
        f1 = f1_score(y_test, predictions, zero_division=0)
        
        # Confusion matrix
        cm = confusion_matrix(y_test, predictions)
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
        
        # Detection Rate (TPR) and False Alarm Rate (FPR)
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        
        evaluation_time = time.time() - start_time
        
        results.append({
            'algorithm': algo,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'detection_rate': tpr,
            'false_alarm_rate': fpr,
            'avg_confidence': np.mean(confidences),
            'evaluation_time': evaluation_time,
            'tp': tp,
            'tn': tn,
            'fp': fp,
            'fn': fn
        })
        
        print(f"      Accuracy:       {accuracy*100:.2f}%")
        print(f"      Precision:      {precision*100:.2f}%")
        print(f"      Recall (DR):    {recall*100:.2f}%")
        print(f"      F1-Score:       {f1*100:.2f}%")
        print(f"      Detection Rate: {tpr*100:.2f}%")
        print(f"      False Alarm:    {fpr*100:.2f}%")
        print(f"      Avg Confidence: {np.mean(confidences):.3f}")
        print(f"      Time:           {evaluation_time:.2f}s")
        print(f"      Confusion Matrix:")
        print(f"        TP={tp}, TN={tn}, FP={fp}, FN={fn}")
        
    except Exception as e:
        print(f"      ❌ Error evaluating {algo}: {e}")
        import traceback
        traceback.print_exc()
        continue

if not results:
    print("\n❌ No models could be evaluated!")
    sys.exit(1)

# Model comparison
print("\n" + "=" * 70)
print("5. Model Comparison")
print("=" * 70)

results_df = pd.DataFrame(results)
results_df = results_df.sort_values('f1_score', ascending=False)

print("\nRanked by F1-Score:")
print(results_df[['algorithm', 'accuracy', 'precision', 'recall', 'f1_score', 
                  'detection_rate', 'false_alarm_rate']].to_string(index=False))

best_model = results_df.iloc[0]
print(f"\n🏆 Best Model: {best_model['algorithm'].upper()}")
print(f"   F1-Score:       {best_model['f1_score']*100:.2f}%")
print(f"   Accuracy:       {best_model['accuracy']*100:.2f}%")
print(f"   Detection Rate: {best_model['detection_rate']*100:.2f}%")
print(f"   False Alarm:    {best_model['false_alarm_rate']*100:.2f}%")

# Test with specific examples
print("\n" + "=" * 70)
print("6. Testing with Real-World Examples")
print("=" * 70)

try:
    best_model_file = available_models[best_model['algorithm']]
    best_loaded_model = joblib.load(best_model_file)
    
    test_cases = [
        {
            'name': 'Normal Web Browsing',
            'features': [10, 5, 0.8],
            'expected': 'NORMAL'
        },
        {
            'name': 'Normal File Transfer',
            'features': [25, 3, 0.9],
            'expected': 'NORMAL'
        },
        {
            'name': 'Suspicious Traffic',
            'features': [75, 40, 0.5],
            'expected': 'BORDERLINE'
        },
        {
            'name': 'Clear DDoS Attack',
            'features': [250, 150, 0.2],
            'expected': 'ATTACK'
        },
        {
            'name': 'Massive DDoS',
            'features': [500, 200, 0.1],
            'expected': 'ATTACK'
        }
    ]
    
    for test in test_cases:
        pred, conf = classify_with_model(best_loaded_model, test['features'])
        result = 'ATTACK' if pred == 1 else 'NORMAL'
        status = '✅' if (result == test['expected'] or test['expected'] == 'BORDERLINE') else '❌'
        
        print(f"\n{status} {test['name']}")
        print(f"   Features: sfe={test['features'][0]}, ssip={test['features'][1]}, rfip={test['features'][2]}")
        print(f"   Prediction: {result} (confidence: {conf:.2%})")
        print(f"   Expected: {test['expected']}")
        
except Exception as e:
    print(f"❌ Error testing examples: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 70)
print("✅ ANALYSIS COMPLETE!")
print("=" * 70)
print(f"\nBest performing model: {best_model['algorithm'].upper()}")
print(f"Performance: {best_model['f1_score']*100:.2f}% F1-Score")
print(f"Detection Rate: {best_model['detection_rate']*100:.2f}%")
print(f"False Alarm Rate: {best_model['false_alarm_rate']*100:.2f}%")
print(f"\nTo use in controller:")
print(f"  detector = MLDetector(model_type='{best_model['algorithm']}')")

