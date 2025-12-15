#!/usr/bin/env python3
"""
Filter and copy data/result.csv into dataset/result.csv.
Mặc định chỉ giữ các dòng reason='collect' (thu thập gốc, không dùng nhãn do ML tự gán).

Usage:
  python3 build_dataset.py --src data/result.csv --out dataset/result.csv --reason collect
"""

import argparse
import os
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description="Filter result.csv và lưu vào dataset/")
    parser.add_argument('--src', default='/home/obito/SDN_Project/SDN-ML-Blockchain/data/result.csv', help='Nguồn dữ liệu (append runtime)')
    parser.add_argument('--out', default='/home/obito/SDN_Project/SDN-ML-Blockchain/dataset/result.csv', help='Đích lưu dataset đã lọc')
    parser.add_argument('--reason', default='collect', help="Giá trị reason cần giữ (vd: collect)")
    args = parser.parse_args()

    if not os.path.exists(args.src):
        raise FileNotFoundError(f"File not found: {args.src}")

    df = pd.read_csv(args.src)

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

    # Chỉ xuất 4 cột cần cho training
    df_out = df[['sfe', 'ssip', 'rfip', 'label']].copy()

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    df_out.to_csv(args.out, index=False)

    print("Saved dataset:", args.out)
    print(df_out['label'].value_counts())


if __name__ == '__main__':
    main()