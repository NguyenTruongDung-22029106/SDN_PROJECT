#!/usr/bin/env python3
"""
Phân tích chi tiết False Positives - Normal bị phân loại thành Attack
"""

import os
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report

def analyze_model(model_name, model_path, X_test, y_test):
    """Phân tích chi tiết một model"""
    if not os.path.exists(model_path):
        print(f"\n{model_name}: Model file not found")
        return None
    
    clf = joblib.load(model_path)
    if isinstance(clf, dict) and "model" in clf:
        clf = clf["model"]
    
    preds = clf.predict(X_test)
    
    # Confusion Matrix
    tn, fp, fn, tp = confusion_matrix(y_test, preds).ravel()
    
    # False Positives: Normal (label=0) bị phân loại thành Attack (pred=1)
    false_positives = X_test[(y_test == 0) & (preds == 1)]
    false_negatives = X_test[(y_test == 1) & (preds == 0)]
    
    print(f"\n{'='*70}")
    print(f"{model_name.upper()}")
    print(f"{'='*70}")
    print(f"\n📊 Confusion Matrix:")
    print(f"                    Predicted")
    print(f"                  Normal  Attack")
    print(f"Actual Normal      {tn:4d}    {fp:4d}")
    print(f"       Attack      {fn:4d}    {tp:4d}")
    
    print(f"\n📈 Metrics:")
    accuracy = (tp + tn) / (tp + tn + fp + fn) * 100
    precision = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"  Accuracy:  {accuracy:.2f}%")
    print(f"  Precision: {precision:.2f}% (Attack predicted correctly)")
    print(f"  Recall:    {recall:.2f}% (Attack detected)")
    print(f"  F1-Score:  {f1:.2f}%")
    
    # False Positive Rate
    far = fp / (fp + tn) * 100 if (fp + tn) > 0 else 0
    print(f"\n⚠️  False Positive Rate (FAR): {far:.2f}%")
    print(f"   → {fp} Normal samples bị phân loại SAI thành Attack")
    print(f"   → {tn} Normal samples được phân loại ĐÚNG")
    
    # False Negative Rate
    fnr = fn / (fn + tp) * 100 if (fn + tp) > 0 else 0
    print(f"\n⚠️  False Negative Rate (FNR): {fnr:.2f}%")
    print(f"   → {fn} Attack samples bị bỏ sót (phân loại thành Normal)")
    print(f"   → {tp} Attack samples được phát hiện ĐÚNG")
    
    # Phân tích False Positives
    if len(false_positives) > 0:
        print(f"\n🔍 PHÂN TÍCH FALSE POSITIVES (Normal → Attack):")
        print(f"   Số lượng: {len(false_positives)} samples")
        print(f"   Chiếm: {len(false_positives) / len(X_test[y_test == 0]) * 100:.2f}% tổng Normal samples")
        
        fp_df = pd.DataFrame(false_positives, columns=['sfe', 'ssip', 'rfip'])
        print(f"\n   Thống kê features của False Positives:")
        print(f"     SFE:  min={fp_df['sfe'].min():.1f}, max={fp_df['sfe'].max():.1f}, mean={fp_df['sfe'].mean():.1f}")
        print(f"     SSIP: min={fp_df['ssip'].min():.1f}, max={fp_df['ssip'].max():.1f}, mean={fp_df['ssip'].mean():.1f}")
        print(f"     RFIP: min={fp_df['rfip'].min():.2f}, max={fp_df['rfip'].max():.2f}, mean={fp_df['rfip'].mean():.2f}")
        
        # So sánh với Normal samples thực tế
        normal_samples = X_test[y_test == 0]
        normal_df = pd.DataFrame(normal_samples, columns=['sfe', 'ssip', 'rfip'])
        print(f"\n   So sánh với Normal samples thực tế:")
        print(f"     SFE:  min={normal_df['sfe'].min():.1f}, max={normal_df['sfe'].max():.1f}, mean={normal_df['sfe'].mean():.1f}")
        print(f"     SSIP: min={normal_df['ssip'].min():.1f}, max={normal_df['ssip'].max():.1f}, mean={normal_df['ssip'].mean():.1f}")
        print(f"     RFIP: min={normal_df['rfip'].min():.2f}, max={normal_df['rfip'].max():.2f}, mean={normal_df['rfip'].mean():.2f}")
        
        # Tìm pattern
        print(f"\n   💡 Pattern False Positives:")
        if fp_df['sfe'].mean() > normal_df['sfe'].mean():
            print(f"     → SFE trung bình cao hơn Normal ({fp_df['sfe'].mean():.1f} vs {normal_df['sfe'].mean():.1f})")
        if fp_df['ssip'].mean() > normal_df['ssip'].mean():
            print(f"     → SSIP trung bình cao hơn Normal ({fp_df['ssip'].mean():.1f} vs {normal_df['ssip'].mean():.1f})")
        if fp_df['rfip'].mean() < normal_df['rfip'].mean():
            print(f"     → RFIP trung bình thấp hơn Normal ({fp_df['rfip'].mean():.2f} vs {normal_df['rfip'].mean():.2f})")
    
    # Phân tích False Negatives
    if len(false_negatives) > 0:
        print(f"\n🔍 PHÂN TÍCH FALSE NEGATIVES (Attack → Normal):")
        print(f"   Số lượng: {len(false_negatives)} samples")
        print(f"   Chiếm: {len(false_negatives) / len(X_test[y_test == 1]) * 100:.2f}% tổng Attack samples")
        
        fn_df = pd.DataFrame(false_negatives, columns=['sfe', 'ssip', 'rfip'])
        print(f"\n   Thống kê features của False Negatives:")
        print(f"     SFE:  min={fn_df['sfe'].min():.1f}, max={fn_df['sfe'].max():.1f}, mean={fn_df['sfe'].mean():.1f}")
        print(f"     SSIP: min={fn_df['ssip'].min():.1f}, max={fn_df['ssip'].max():.1f}, mean={fn_df['ssip'].mean():.1f}")
        print(f"     RFIP: min={fn_df['rfip'].min():.2f}, max={fn_df['rfip'].max():.2f}, mean={fn_df['rfip'].mean():.2f}")
    
    return {
        'model': model_name,
        'fp': fp,
        'fn': fn,
        'tn': tn,
        'tp': tp,
        'far': far,
        'fnr': fnr,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.abspath(os.path.join(base_dir, "..", "dataset", "result.csv"))
    
    if not os.path.exists(data_path):
        print(f"❌ Dataset not found: {data_path}")
        return
    
    print("=" * 70)
    print("PHÂN TÍCH FALSE POSITIVES - NORMAL BỊ PHÂN LOẠI THÀNH ATTACK")
    print("=" * 70)
    
    # Load data
    df = pd.read_csv(data_path, on_bad_lines='skip')
    X = df[['sfe', 'ssip', 'rfip']].values
    y = df['label'].values
    
    print(f"\n📊 Dataset:")
    print(f"   Tổng samples: {len(df)}")
    print(f"   Normal (0): {(y == 0).sum()} ({(y == 0).sum()/len(y)*100:.1f}%)")
    print(f"   Attack (1): {(y == 1).sum()} ({(y == 1).sum()/len(y)*100:.1f}%)")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    print(f"\n   Test set: {len(X_test)} samples")
    print(f"     Normal: {(y_test == 0).sum()}")
    print(f"     Attack: {(y_test == 1).sum()}")
    
    # Analyze models
    model_dir = os.path.abspath(os.path.join(base_dir, "..", "ryu_app"))
    models = {
        "decision_tree": os.path.join(model_dir, "ml_model_decision_tree.pkl"),
        "random_forest": os.path.join(model_dir, "ml_model_random_forest.pkl"),
        "svm": os.path.join(model_dir, "ml_model_svm.pkl"),
        "naive_bayes": os.path.join(model_dir, "ml_model_naive_bayes.pkl"),
    }
    
    results = []
    for name, path in models.items():
        result = analyze_model(name, path, X_test, y_test)
        if result:
            results.append(result)
    
    # Summary
    if results:
        print(f"\n{'='*70}")
        print("TÓM TẮT - SO SÁNH CÁC MODELS")
        print(f"{'='*70}")
        print(f"\n{'Model':<15} {'FAR (%)':<10} {'FNR (%)':<10} {'Accuracy (%)':<12} {'F1 (%)':<10}")
        print("-" * 70)
        for r in results:
            print(f"{r['model']:<15} {r['far']:<10.2f} {r['fnr']:<10.2f} {r['accuracy']:<12.2f} {r['f1']:<10.2f}")
        
        # Tìm model tốt nhất (FAR thấp nhất)
        best_far = min(results, key=lambda x: x['far'])
        print(f"\n✅ Model có FAR thấp nhất: {best_far['model']} (FAR = {best_far['far']:.2f}%)")
        
        # Tìm model cân bằng nhất (F1 cao nhất)
        best_f1 = max(results, key=lambda x: x['f1'])
        print(f"✅ Model có F1 cao nhất: {best_f1['model']} (F1 = {best_f1['f1']:.2f}%)")


if __name__ == "__main__":
    main()

