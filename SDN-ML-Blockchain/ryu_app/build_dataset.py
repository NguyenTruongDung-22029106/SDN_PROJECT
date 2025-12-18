#!/usr/bin/env python3
"""
Filter and copy data/result.csv into dataset/result.csv.
Kết hợp chức năng:
1. Lọc theo reason='collect' (thu thập gốc, không dùng nhãn do ML tự gán)
2. Xử lý giá trị âm (chuyển thành trị tuyệt đối)
3. (Tùy chọn) Lọc để giảm overlap giữa normal và attack

Usage:
  # Chỉ cần chạy (mặc định: data/result.csv -> dataset/result.csv, reason=collect)
  python3 ryu_app/build_dataset.py
  
  # Hoặc chỉ định rõ đường dẫn
  python3 ryu_app/build_dataset.py --src data/result.csv --out dataset/result.csv
  
  # Kết hợp với filter để giảm overlap
  python3 ryu_app/build_dataset.py --filter \
      --min_attack_sfe 10 --min_attack_ssip 10 \
      --out dataset/result_filtered.csv
"""

import argparse
import os
import pandas as pd


def main():
    # Auto-detect project root (parent directory of ryu_app/)
    RYU_APP_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(RYU_APP_DIR)
    
    parser = argparse.ArgumentParser(description="Filter result.csv và lưu vào dataset/ (kết hợp build + filter)")
    parser.add_argument('--src', default=os.path.join(PROJECT_ROOT, 'data', 'result.csv'), 
                       help='Nguồn dữ liệu (append runtime)')
    parser.add_argument('--out', default=os.path.join(PROJECT_ROOT, 'dataset', 'result.csv'), 
                       help='Đích lưu dataset đã lọc')
    parser.add_argument('--reason', default='collect', help="Giá trị reason cần giữ (vd: collect)")
    
    # Thêm các tham số filter (từ filter_dataset.py)
    parser.add_argument('--filter', action='store_true',
                       help='Bật chức năng lọc để giảm overlap giữa normal và attack')
    parser.add_argument('--min_attack_sfe', type=float, default=10.0,
                       help='Bỏ attack nếu SFE < giá trị này (0 = không dùng ngưỡng, chỉ dùng khi --filter)')
    parser.add_argument('--min_attack_ssip', type=float, default=10.0,
                       help='Bỏ attack nếu SSIP < giá trị này (0 = không dùng ngưỡng, chỉ dùng khi --filter)')
    parser.add_argument('--max_normal_sfe', type=float, default=0.0,
                       help='Bỏ normal nếu SFE > giá trị này (0 = không lọc normal theo SFE, chỉ dùng khi --filter)')
    parser.add_argument('--max_normal_ssip', type=float, default=0.0,
                       help='Bỏ normal nếu SSIP > giá trị này (0 = không lọc normal theo SSIP, chỉ dùng khi --filter)')
    
    args = parser.parse_args()

    if not os.path.exists(args.src):
        raise FileNotFoundError(f"File not found: {args.src}")

    # Đọc CSV với xử lý lỗi: bỏ qua các dòng bị lỗi format
    # Dòng có thể bị dính nhau do lỗi ghi file, pandas sẽ tự động xử lý
    try:
        # Pandas 2.0+ dùng on_bad_lines
        df = pd.read_csv(args.src, on_bad_lines='skip', engine='python', quoting=1)
    except TypeError:
        # Pandas cũ dùng error_bad_lines
        try:
            df = pd.read_csv(args.src, error_bad_lines=False, warn_bad_lines=True, engine='python')
        except Exception:
            # Fallback: đọc thủ công và xử lý
            print("Warning: Using manual CSV parsing due to format issues")
            import csv
            rows = []
            with open(args.src, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                for row in reader:
                    if len(row) == 8:  # Chỉ lấy dòng có đúng 8 cột
                        rows.append(row)
            df = pd.DataFrame(rows, columns=header)

    # Chuẩn hóa tên cột nếu khác
    rename_map = {}
    cols = list(df.columns)
    # Expect time,sfe,ssip,rfip,label,reason,confidence,dpid
    if len(cols) >= 4:
        rename_map[cols[0]] = 'time'
        rename_map[cols[1]] = 'sfe'
        rename_map[cols[2]] = 'ssip'
        rename_map[cols[3]] = 'rfip'
    if 'label' not in cols and len(cols) > 4:
        rename_map[cols[4]] = 'label'
    df = df.rename(columns=rename_map)

    # Chỉ lấy các cột cần thiết
    keep_cols = ['time', 'sfe', 'ssip', 'rfip', 'label', 'reason']
    df = df[[c for c in keep_cols if c in df.columns]].copy()

    # Lọc theo reason nếu có cột reason
    if 'reason' in df.columns:
        before = len(df)
        df = df[df['reason'] == args.reason]
        print(f"Filtered reason={args.reason}: kept {len(df)}/{before}")
    else:
        print("No 'reason' column found; keeping all rows.")

    # Ép numeric cho features/label, drop NaN
    for c in ['sfe', 'ssip', 'rfip', 'label']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    before = len(df)
    df = df.dropna(subset=['sfe', 'ssip', 'rfip', 'label'])
    print(f"Dropped NaN rows: {before - len(df)}")

    # Dùng trị tuyệt đối cho SFE, SSIP để bỏ dấu âm (giống style tác giả, chỉ quan tâm độ lớn)
    df['sfe'] = df['sfe'].abs()
    df['ssip'] = df['ssip'].abs()
    
    # Ép label về int
    df['label'] = df['label'].astype(int)

    # (Tùy chọn) Lọc để giảm overlap giữa normal và attack
    if args.filter:
        total_before = len(df)
        normal = df[df['label'] == 0].copy()
        attack = df[df['label'] == 1].copy()
        
        # Lọc attack: giữ attack "mạnh" (SFE/SSIP đủ lớn)
        if args.min_attack_sfe > 0:
            before_attack = len(attack)
            attack = attack[attack['sfe'] >= args.min_attack_sfe]
            if len(attack) < before_attack:
                print(f"Filtered attack (SFE < {args.min_attack_sfe}): kept {len(attack)}/{before_attack}")
        if args.min_attack_ssip > 0:
            before_attack = len(attack)
            attack = attack[attack['ssip'] >= args.min_attack_ssip]
            if len(attack) < before_attack:
                print(f"Filtered attack (SSIP < {args.min_attack_ssip}): kept {len(attack)}/{before_attack}")
        
        # (Tùy chọn) Lọc normal có SFE/SSIP quá lớn
        if args.max_normal_sfe > 0:
            before_normal = len(normal)
            normal = normal[normal['sfe'] <= args.max_normal_sfe]
            if len(normal) < before_normal:
                print(f"Filtered normal (SFE > {args.max_normal_sfe}): kept {len(normal)}/{before_normal}")
        if args.max_normal_ssip > 0:
            before_normal = len(normal)
            normal = normal[normal['ssip'] <= args.max_normal_ssip]
            if len(normal) < before_normal:
                print(f"Filtered normal (SSIP > {args.max_normal_ssip}): kept {len(normal)}/{before_normal}")
        
        df = pd.concat([normal, attack], ignore_index=True)
        print(f"After overlap filtering: {len(df)}/{total_before} samples kept")

    # Chỉ xuất 4 cột cần cho training
    df_out = df[['sfe', 'ssip', 'rfip', 'label']].copy()

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    df_out.to_csv(args.out, index=False)

    print(f"\n✓ Saved dataset: {args.out}")
    print(f"Total samples: {len(df_out)}")
    print("Label distribution:")
    print(df_out['label'].value_counts())
    
    # Thống kê thêm
    if len(df_out) > 0:
        print(f"\nFeature statistics:")
        print(f"  SFE: min={df_out['sfe'].min():.2f}, max={df_out['sfe'].max():.2f}, mean={df_out['sfe'].mean():.2f}")
        print(f"  SSIP: min={df_out['ssip'].min():.2f}, max={df_out['ssip'].max():.2f}, mean={df_out['ssip'].mean():.2f}")
        print(f"  RFIP: min={df_out['rfip'].min():.2f}, max={df_out['rfip'].max():.2f}, mean={df_out['rfip'].mean():.2f}")
        
        # Đếm mẫu "hậu attack" (label=0, SFE>20 hoặc SSIP>10)
        post_attack = df_out[(df_out['label'] == 0) & ((df_out['sfe'] > 20) | (df_out['ssip'] > 10))]
        if len(post_attack) > 0:
            print(f"\n  Post-attack samples (label=0, SFE>20 or SSIP>10): {len(post_attack)}")


if __name__ == '__main__':
    main()

