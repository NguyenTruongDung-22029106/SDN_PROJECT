#!/usr/bin/env python3
"""
Train ML models for DDoS detection
Tests multiple algorithms and saves the best one
"""

import sys
import os

# Auto-detect project root (parent directory of scripts/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from ryu_app.ml_detector import MLDetector
import time

print("=" * 70)
print("Training ML Models for DDoS Detection")
print("=" * 70)

# Load dataset
print("\n1. Loading training data...")
data_file = os.path.join(PROJECT_ROOT, 'dataset', 'result.csv')
df = pd.read_csv(data_file)

print(f"   Loaded {len(df)} samples")
print(f"   Features: {list(df.columns[:-1])}")
print(f"   Classes: {df['label'].unique()}")

# Prepare data
X = df[['sfe', 'ssip', 'rfip']].values
y = df['label'].values

# Split train/test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

print(f"\n2. Data split:")
print(f"   Training: {len(X_train)} samples")
print(f"   Testing: {len(X_test)} samples")
print(f"   Train distribution: {np.bincount(y_train)}")
print(f"   Test distribution: {np.bincount(y_test)}")

# Train different models
algorithms = ['svm', 'decision_tree', 'random_forest', 'naive_bayes']
results = []

print("\n3. Training models...")
print("-" * 70)

for algo in algorithms:
    print(f"\n   Training {algo.upper()}...")
    start_time = time.time()
    
    # Create and train detector
    detector = MLDetector(model_type=algo, model_path=data_file)
    
    # Evaluate on test set
    predictions = []
    confidences = []
    
    for features in X_test:
        pred, conf = detector.classify(features.tolist())
        predictions.append(pred)
        confidences.append(conf)
    
    predictions = np.array(predictions)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(y_test, predictions)
    recall = recall_score(y_test, predictions)
    f1 = f1_score(y_test, predictions)
    
    training_time = time.time() - start_time
    
    results.append({
        'algorithm': algo,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'avg_confidence': np.mean(confidences),
        'training_time': training_time
    })
    
    print(f"      Accuracy:  {accuracy*100:.2f}%")
    print(f"      Precision: {precision*100:.2f}%")
    print(f"      Recall:    {recall*100:.2f}%")
    print(f"      F1-Score:  {f1*100:.2f}%")
    print(f"      Avg Conf:  {np.mean(confidences):.3f}")
    print(f"      Time:      {training_time:.2f}s")

# Find best model
print("\n" + "=" * 70)
print("4. Model Comparison")
print("=" * 70)

results_df = pd.DataFrame(results)
results_df = results_df.sort_values('f1_score', ascending=False)

print("\nRanked by F1-Score:")
print(results_df.to_string(index=False))

best_model = results_df.iloc[0]
print(f"\n🏆 Best Model: {best_model['algorithm'].upper()}")
print(f"   F1-Score: {best_model['f1_score']*100:.2f}%")
print(f"   Accuracy: {best_model['accuracy']*100:.2f}%")

# Test with specific examples
print("\n" + "=" * 70)
print("5. Testing with Real-World Examples")
print("=" * 70)

detector = MLDetector(model_type=best_model['algorithm'], model_path=data_file)

test_cases = [
    {
        'name': 'Normal Web Browsing',
        'features': [10, 5, 8],
        'expected': 'NORMAL'
    },
    {
        'name': 'Normal File Transfer',
        'features': [25, 3, 2],
        'expected': 'NORMAL'
    },
    {
        'name': 'Suspicious Traffic',
        'features': [75, 40, 15],
        'expected': 'BORDERLINE'
    },
    {
        'name': 'Clear DDoS Attack',
        'features': [250, 150, 5],
        'expected': 'ATTACK'
    },
    {
        'name': 'Massive DDoS',
        'features': [500, 200, 2],
        'expected': 'ATTACK'
    }
]

for test in test_cases:
    pred, conf = detector.classify(test['features'])
    result = 'ATTACK' if pred == 1 else 'NORMAL'
    status = '✅' if (result == test['expected'] or test['expected'] == 'BORDERLINE') else '❌'
    
    print(f"\n{status} {test['name']}")
    print(f"   Features: sfe={test['features'][0]}, ssip={test['features'][1]}, rfip={test['features'][2]}")
    print(f"   Prediction: {result} (confidence: {conf:.2%})")
    print(f"   Expected: {test['expected']}")

# Save best model
print("\n" + "=" * 70)
print("6. Saving Best Model")
print("=" * 70)

model_path = os.path.join(PROJECT_ROOT, 'dataset', f'trained_model_{best_model["algorithm"]}.pkl')
detector.save_model(model_path)
print(f"✅ Model saved to: {model_path}")

print("\n" + "=" * 70)
print("✅ TRAINING COMPLETE!")
print("=" * 70)
print(f"\nBest performing model: {best_model['algorithm'].upper()}")
print(f"Performance: {best_model['f1_score']*100:.2f}% F1-Score")
print(f"\nThe ML detector is now ready for real-time DDoS detection!")
print("\nTo use in controller:")
print(f"  detector = MLDetector(model_type='{best_model['algorithm']}', model_path='{data_file}')")
