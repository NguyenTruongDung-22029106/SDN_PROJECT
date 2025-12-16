#!/usr/bin/env python3
"""
Lọc dataset/result.csv để giảm overlap giữa normal (0) và attack (1).

Ý tưởng đơn giản, giống style tác giả:
- Giữ normal có SFE/SSIP nhỏ
- Giữ attack có SFE/SSIP đủ lớn

Mặc định:
- Bỏ attack nếu sfe < 10 hoặc ssip < 10
- (Tuỳ chọn) bỏ normal nếu sfe > 200 hoặc ssip > 200

Usage:
  python3 ryu_app/filter_dataset.py \
      --src dataset/result.csv \
      --out dataset/result_filtered.csv \
      --min_attack_sfe 10 --min_attack_ssip 10 \
      --max_normal_sfe 0 --max_normal_ssip 0

Nếu không muốn lọc normal theo ngưỡng trên, để max_normal_sfe/max_normal_ssip = 0.
"""

import argparse
import os
import sys

import pandas as pd


RYU_APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(RYU_APP_DIR)
sys.path.insert(0, PROJECT_ROOT)


def main():
    parser = argparse.ArgumentParser(description="Lọc dataset để giảm overlap Normal/Attack")
    parser.add_argument(
        "--src",
        default=os.path.join(PROJECT_ROOT, "dataset", "result.csv"),
        help="File dataset nguồn (sfe,ssip,rfip,label)",
    )
    parser.add_argument(
        "--out",
        default=os.path.join(PROJECT_ROOT, "dataset", "result_filtered.csv"),
        help="File dataset đầu ra sau khi lọc",
    )
    parser.add_argument(
        "--min_attack_sfe",
        type=float,
        default=10.0,
        help="Bỏ attack nếu SFE < giá trị này (0 = không dùng ngưỡng)",
    )
    parser.add_argument(
        "--min_attack_ssip",
        type=float,
        default=10.0,
        help="Bỏ attack nếu SSIP < giá trị này (0 = không dùng ngưỡng)",
    )
    parser.add_argument(
        "--max_normal_sfe",
        type=float,
        default=0.0,
        help="Bỏ normal nếu SFE > giá trị này (0 = không lọc normal theo SFE)",
    )
    parser.add_argument(
        "--max_normal_ssip",
        type=float,
        default=0.0,
        help="Bỏ normal nếu SSIP > giá trị này (0 = không lọc normal theo SSIP)",
    )

    args = parser.parse_args()

    if not os.path.exists(args.src):
        raise FileNotFoundError(f"Không tìm thấy file nguồn: {args.src}")

    df = pd.read_csv(args.src)
    cols = list(df.columns)
    if len(cols) < 4:
        raise ValueError(f"File {args.src} không đủ 4 cột.")

    # Chuẩn hoá tên cột
    rename_map = {
        cols[0]: "sfe",
        cols[1]: "ssip",
        cols[2]: "rfip",
        cols[3]: "label",
    }
    df = df.rename(columns=rename_map)

    # Ép kiểu
    for c in ["sfe", "ssip", "rfip", "label"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["sfe", "ssip", "rfip", "label"])
    df["label"] = df["label"].astype(int)

    total_before = len(df)
    normal = df[df["label"] == 0].copy()
    attack = df[df["label"] == 1].copy()

    # Lọc attack: giữ attack "mạnh" (SFE/SSIP đủ lớn)
    if args.min_attack_sfe > 0:
        attack = attack[attack["sfe"].abs() >= args.min_attack_sfe]
    if args.min_attack_ssip > 0:
        attack = attack[attack["ssip"].abs() >= args.min_attack_ssip]

    # Tuỳ chọn: lọc normal có SFE/SSIP quá lớn (nếu đặt ngưỡng)
    if args.max_normal_sfe > 0:
        normal = normal[normal["sfe"].abs() <= args.max_normal_sfe]
    if args.max_normal_ssip > 0:
        normal = normal[normal["ssip"].abs() <= args.max_normal_ssip]

    df_out = pd.concat([normal, attack], ignore_index=True)

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    df_out.to_csv(args.out, index=False)

    print(f"Src:  {args.src}")
    print(f"Out:  {args.out}")
    print(f"Tổng trước lọc: {total_before}")
    print(f"Sau lọc: {len(df_out)} (Normal={len(normal)}, Attack={len(attack)})")
    print("Phân bố nhãn sau lọc:")
    print(df_out["label"].value_counts())


if __name__ == "__main__":
    main()


