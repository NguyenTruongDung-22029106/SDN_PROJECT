#!/usr/bin/env python3
"""
So sánh Training Data vs Runtime Data để tìm nguyên nhân False Positives
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def _get_output_dir():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load training data
    train_path = os.path.abspath(os.path.join(base_dir, "..", "dataset", "result.csv"))
    runtime_path = os.path.abspath(os.path.join(base_dir, "..", "data", "result.csv"))
    
    print("=" * 70)
    print("SO SÁNH TRAINING DATA vs RUNTIME DATA")
    print("=" * 70)
    
    # Load data
    train_df = pd.read_csv(train_path, on_bad_lines='skip')
    runtime_df = pd.read_csv(runtime_path, on_bad_lines='skip')
    
    # Chỉ lấy ML predictions từ runtime
    runtime_ml = runtime_df[runtime_df['reason'] == 'ml'].copy() if 'reason' in runtime_df.columns else runtime_df.copy()
    
    print(f"\n📊 Training Data (dataset/result.csv):")
    print(f"   Tổng: {len(train_df)} samples")
    print(f"   Normal: {(train_df['label'] == 0).sum()} ({(train_df['label'] == 0).sum()/len(train_df)*100:.1f}%)")
    print(f"   Attack: {(train_df['label'] == 1).sum()} ({(train_df['label'] == 1).sum()/len(train_df)*100:.1f}%)")
    
    print(f"\n📊 Runtime Data - ML Predictions (data/result.csv, reason='ml'):")
    print(f"   Tổng: {len(runtime_ml)} samples")
    print(f"   Normal: {(runtime_ml['label'] == 0).sum()} ({(runtime_ml['label'] == 0).sum()/len(runtime_ml)*100:.1f}%)")
    print(f"   Attack: {(runtime_ml['label'] == 1).sum()} ({(runtime_ml['label'] == 1).sum()/len(runtime_ml)*100:.1f}%)")
    
    # So sánh feature distributions
    print(f"\n📈 So sánh Feature Distributions:")
    
    features = ['sfe', 'ssip', 'rfip']
    for feat in features:
        train_normal = train_df[train_df['label'] == 0][feat].abs() if feat in ['sfe', 'ssip'] else train_df[train_df['label'] == 0][feat]
        train_attack = train_df[train_df['label'] == 1][feat].abs() if feat in ['sfe', 'ssip'] else train_df[train_df['label'] == 1][feat]
        runtime_normal = runtime_ml[runtime_ml['label'] == 0][feat].abs() if feat in ['sfe', 'ssip'] else runtime_ml[runtime_ml['label'] == 0][feat]
        runtime_attack = runtime_ml[runtime_ml['label'] == 1][feat].abs() if feat in ['sfe', 'ssip'] else runtime_ml[runtime_ml['label'] == 1][feat]
        
        print(f"\n   {feat.upper()}:")
        print(f"     Training - Normal:  min={train_normal.min():.1f}, max={train_normal.max():.1f}, mean={train_normal.mean():.1f}")
        print(f"     Training - Attack:  min={train_attack.min():.1f}, max={train_attack.max():.1f}, mean={train_attack.mean():.1f}")
        print(f"     Runtime - Normal:   min={runtime_normal.min():.1f}, max={runtime_normal.max():.1f}, mean={runtime_normal.mean():.1f}")
        print(f"     Runtime - Attack:   min={runtime_attack.min():.1f}, max={runtime_attack.max():.1f}, mean={runtime_attack.mean():.1f}")
        
        # Kiểm tra overlap
        if runtime_normal.max() > train_normal.max() * 1.5:
            print(f"     ⚠️  Runtime Normal có giá trị cao hơn Training Normal nhiều!")
        if runtime_normal.mean() > train_normal.mean() * 2:
            print(f"     ⚠️  Runtime Normal có mean cao hơn Training Normal gấp 2 lần!")
    
    # Vẽ biểu đồ so sánh
    output_dir = _get_output_dir()
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    for idx, feat in enumerate(features):
        ax = axes[idx]
        
        # Training data
        train_normal = train_df[train_df['label'] == 0][feat].abs() if feat in ['sfe', 'ssip'] else train_df[train_df['label'] == 0][feat]
        train_attack = train_df[train_df['label'] == 1][feat].abs() if feat in ['sfe', 'ssip'] else train_df[train_df['label'] == 1][feat]
        
        # Runtime data
        runtime_normal = runtime_ml[runtime_ml['label'] == 0][feat].abs() if feat in ['sfe', 'ssip'] else runtime_ml[runtime_ml['label'] == 0][feat]
        runtime_attack = runtime_ml[runtime_ml['label'] == 1][feat].abs() if feat in ['sfe', 'ssip'] else runtime_ml[runtime_ml['label'] == 1][feat]
        
        # Histogram
        max_val = max(
            train_df[feat].abs().max() if feat in ['sfe', 'ssip'] else train_df[feat].max(),
            runtime_ml[feat].abs().max() if feat in ['sfe', 'ssip'] else runtime_ml[feat].max()
        )
        bins = np.linspace(0, max_val, 50)
        
        ax.hist(train_normal, bins=bins, alpha=0.5, label='Train Normal', color='blue', density=True)
        ax.hist(train_attack, bins=bins, alpha=0.5, label='Train Attack', color='red', density=True)
        ax.hist(runtime_normal, bins=bins, alpha=0.3, label='Runtime Normal', color='cyan', density=True, histtype='step', linewidth=2)
        ax.hist(runtime_attack, bins=bins, alpha=0.3, label='Runtime Attack', color='orange', density=True, histtype='step', linewidth=2)
        
        ax.set_xlabel(feat.upper())
        ax.set_ylabel('Density')
        ax.set_title(f'{feat.upper()} Distribution Comparison')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    out_path = os.path.join(output_dir, 'training_vs_runtime_comparison.png')
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"\n✅ Đã lưu biểu đồ: {out_path}")
    
    # Phân tích vấn đề
    print(f"\n{'='*70}")
    print("PHÂN TÍCH VẤN ĐỀ")
    print(f"{'='*70}")
    
    # Kiểm tra nếu runtime normal có features giống attack
    train_normal_sfe = train_df[train_df['label'] == 0]['sfe'].abs()
    train_attack_sfe = train_df[train_df['label'] == 1]['sfe'].abs()
    runtime_normal_sfe = runtime_ml[runtime_ml['label'] == 0]['sfe'].abs()
    
    runtime_normal_high_sfe = runtime_normal_sfe[runtime_normal_sfe > train_attack_sfe.mean()]
    if len(runtime_normal_high_sfe) > 0:
        print(f"\n⚠️  VẤN ĐỀ PHÁT HIỆN:")
        print(f"   {len(runtime_normal_high_sfe)} Normal samples trong runtime có SFE > mean của Attack trong training")
        print(f"   Chiếm: {len(runtime_normal_high_sfe)/len(runtime_normal_sfe)*100:.1f}% tổng Normal samples")
        print(f"   → Model có thể phân loại những samples này thành Attack (False Positive)")
        print(f"\n💡 GIẢI PHÁP:")
        print(f"   1. Thu thập thêm Normal data với SFE/SSIP cao hơn để train model")
        print(f"   2. Điều chỉnh confidence threshold cao hơn")
        print(f"   3. Sử dụng model có FAR thấp hơn (Decision Tree hoặc Random Forest)")

if __name__ == "__main__":
    main()

