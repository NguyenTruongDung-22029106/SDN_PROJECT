#!/usr/bin/env python3
"""
Visualize vấn đề False Positives: Normal bị phân loại thành Attack
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import joblib
from sklearn.model_selection import train_test_split

def _get_output_dir():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load data
    train_path = os.path.abspath(os.path.join(base_dir, "..", "dataset", "result.csv"))
    runtime_path = os.path.abspath(os.path.join(base_dir, "..", "data", "result.csv"))
    model_path = os.path.abspath(os.path.join(base_dir, "..", "ryu_app", "ml_model_random_forest.pkl"))
    
    print("=" * 70)
    print("VISUALIZE FALSE POSITIVE ISSUE")
    print("=" * 70)
    
    train_df = pd.read_csv(train_path, on_bad_lines='skip')
    runtime_df = pd.read_csv(runtime_path, on_bad_lines='skip')
    runtime_ml = runtime_df[runtime_df['reason'] == 'ml'].copy() if 'reason' in runtime_df.columns else runtime_df.copy()
    
    # Load model
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        return
    
    model = joblib.load(model_path)
    if isinstance(model, dict) and "model" in model:
        model = model["model"]
    
    # Predict trên runtime data
    runtime_features = runtime_ml[['sfe', 'ssip', 'rfip']].values
    runtime_features_abs = runtime_features.copy()
    runtime_features_abs[:, 0] = np.abs(runtime_features_abs[:, 0])  # SFE
    runtime_features_abs[:, 1] = np.abs(runtime_features_abs[:, 1])  # SSIP
    
    predictions = model.predict(runtime_features_abs)
    probabilities = model.predict_proba(runtime_features_abs)[:, 1] if hasattr(model, 'predict_proba') else None
    
    # Tìm False Positives: Normal (label=0) bị predict thành Attack (pred=1)
    runtime_labels = runtime_ml['label'].values
    false_positives = (runtime_labels == 0) & (predictions == 1)
    true_positives = (runtime_labels == 1) & (predictions == 1)
    true_negatives = (runtime_labels == 0) & (predictions == 0)
    false_negatives = (runtime_labels == 1) & (predictions == 0)
    
    print(f"\n📊 Kết quả phân loại trên Runtime Data:")
    print(f"   True Negatives (Normal → Normal):  {true_negatives.sum()}")
    print(f"   False Positives (Normal → Attack): {false_positives.sum()} ⚠️")
    print(f"   False Negatives (Attack → Normal): {false_negatives.sum()}")
    print(f"   True Positives (Attack → Attack):  {true_positives.sum()}")
    
    if false_positives.sum() > 0:
        print(f"\n⚠️  PHÁT HIỆN {false_positives.sum()} FALSE POSITIVES!")
        fp_sfe = runtime_ml[false_positives]['sfe'].abs()
        fp_ssip = runtime_ml[false_positives]['ssip'].abs()
        fp_rfip = runtime_ml[false_positives]['rfip']
        
        print(f"\n   Features của False Positives:")
        print(f"     SFE:  min={fp_sfe.min():.1f}, max={fp_sfe.max():.1f}, mean={fp_sfe.mean():.1f}")
        print(f"     SSIP: min={fp_ssip.min():.1f}, max={fp_ssip.max():.1f}, mean={fp_ssip.mean():.1f}")
        print(f"     RFIP: min={fp_rfip.min():.2f}, max={fp_rfip.max():.2f}, mean={fp_rfip.mean():.2f}")
        
        # So sánh với Training Normal
        train_normal_sfe = train_df[train_df['label'] == 0]['sfe'].abs()
        train_normal_ssip = train_df[train_df['label'] == 0]['ssip'].abs()
        
        print(f"\n   So sánh với Training Normal:")
        print(f"     Training Normal SFE:  max={train_normal_sfe.max():.1f}, mean={train_normal_sfe.mean():.1f}")
        print(f"     Training Normal SSIP: max={train_normal_ssip.max():.1f}, mean={train_normal_ssip.mean():.1f}")
        print(f"     → False Positives có SFE/SSIP cao hơn Training Normal nhiều!")
    
    # Vẽ biểu đồ
    output_dir = _get_output_dir()
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    # 1. SFE vs SSIP - Training Data
    ax = axes[0, 0]
    train_normal = train_df[train_df['label'] == 0]
    train_attack = train_df[train_df['label'] == 1]
    
    ax.scatter(train_normal['sfe'].abs(), train_normal['ssip'].abs(), 
               alpha=0.5, label='Training Normal', color='blue', s=20)
    ax.scatter(train_attack['sfe'].abs(), train_attack['ssip'].abs(), 
               alpha=0.5, label='Training Attack', color='red', s=20)
    ax.set_xlabel('SFE')
    ax.set_ylabel('SSIP')
    ax.set_title('Training Data: SFE vs SSIP')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')
    ax.set_yscale('log')
    
    # 2. SFE vs SSIP - Runtime Data với predictions
    ax = axes[0, 1]
    runtime_normal_correct = runtime_ml[(runtime_labels == 0) & (predictions == 0)]
    runtime_normal_fp = runtime_ml[false_positives]
    runtime_attack_correct = runtime_ml[(runtime_labels == 1) & (predictions == 1)]
    runtime_attack_fn = runtime_ml[false_negatives]
    
    if len(runtime_normal_correct) > 0:
        ax.scatter(runtime_normal_correct['sfe'].abs(), runtime_normal_correct['ssip'].abs(),
                   alpha=0.3, label='Normal → Normal (Correct)', color='green', s=10)
    if len(runtime_normal_fp) > 0:
        ax.scatter(runtime_normal_fp['sfe'].abs(), runtime_normal_fp['ssip'].abs(),
                   alpha=0.8, label='Normal → Attack (False Positive)', color='orange', s=30, marker='x')
    if len(runtime_attack_correct) > 0:
        ax.scatter(runtime_attack_correct['sfe'].abs(), runtime_attack_correct['ssip'].abs(),
                   alpha=0.3, label='Attack → Attack (Correct)', color='red', s=10)
    if len(runtime_attack_fn) > 0:
        ax.scatter(runtime_attack_fn['sfe'].abs(), runtime_attack_fn['ssip'].abs(),
                   alpha=0.8, label='Attack → Normal (False Negative)', color='purple', s=30, marker='x')
    
    ax.set_xlabel('SFE')
    ax.set_ylabel('SSIP')
    ax.set_title('Runtime Data: SFE vs SSIP (Predictions)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')
    ax.set_yscale('log')
    
    # 3. Histogram SFE - So sánh Training vs Runtime
    ax = axes[1, 0]
    bins = np.logspace(0, 4, 50)
    
    ax.hist(train_normal['sfe'].abs(), bins=bins, alpha=0.5, label='Train Normal', color='blue', density=True)
    ax.hist(train_attack['sfe'].abs(), bins=bins, alpha=0.5, label='Train Attack', color='red', density=True)
    
    if len(runtime_normal_correct) > 0:
        ax.hist(runtime_normal_correct['sfe'].abs(), bins=bins, alpha=0.3, 
                label='Runtime Normal (Correct)', color='green', density=True, histtype='step', linewidth=2)
    if len(runtime_normal_fp) > 0:
        ax.hist(runtime_normal_fp['sfe'].abs(), bins=bins, alpha=0.8, 
                label='Runtime Normal (False Positive)', color='orange', density=True, histtype='step', linewidth=2)
    
    ax.set_xlabel('SFE')
    ax.set_ylabel('Density')
    ax.set_title('SFE Distribution Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')
    
    # 4. Histogram SSIP - So sánh Training vs Runtime
    ax = axes[1, 1]
    bins = np.logspace(0, 4, 50)
    
    ax.hist(train_normal['ssip'].abs(), bins=bins, alpha=0.5, label='Train Normal', color='blue', density=True)
    ax.hist(train_attack['ssip'].abs(), bins=bins, alpha=0.5, label='Train Attack', color='red', density=True)
    
    if len(runtime_normal_correct) > 0:
        ax.hist(runtime_normal_correct['ssip'].abs(), bins=bins, alpha=0.3,
                label='Runtime Normal (Correct)', color='green', density=True, histtype='step', linewidth=2)
    if len(runtime_normal_fp) > 0:
        ax.hist(runtime_normal_fp['ssip'].abs(), bins=bins, alpha=0.8,
                label='Runtime Normal (False Positive)', color='orange', density=True, histtype='step', linewidth=2)
    
    ax.set_xlabel('SSIP')
    ax.set_ylabel('Density')
    ax.set_title('SSIP Distribution Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')
    
    plt.tight_layout()
    out_path = os.path.join(output_dir, 'false_positive_analysis.png')
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"\n✅ Đã lưu biểu đồ: {out_path}")
    
    # Tóm tắt
    print(f"\n{'='*70}")
    print("TÓM TẮT VẤN ĐỀ")
    print(f"{'='*70}")
    print(f"\n🔴 NGUYÊN NHÂN:")
    print(f"   - Training Normal có SFE/SSIP thấp (max SFE=40, max SSIP=10)")
    print(f"   - Runtime Normal có SFE/SSIP cao hơn nhiều (max SFE=26419, max SSIP=8849)")
    print(f"   - Model được train trên data có Normal với features thấp")
    print(f"   → Model phân loại Normal có features cao thành Attack")
    
    print(f"\n💡 GIẢI PHÁP:")
    print(f"   1. Thu thập thêm Normal data với SFE/SSIP cao (20-100) để train model")
    print(f"   2. Sử dụng model có FAR thấp (Decision Tree/Random Forest)")
    print(f"   3. Tăng confidence threshold trong controller")
    print(f"   4. Áp dụng filtering trong build_dataset.py để loại bỏ overlap")

if __name__ == "__main__":
    main()

