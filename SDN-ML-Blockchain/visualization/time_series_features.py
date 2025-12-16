#!/usr/bin/env python3
"""
Vẽ các biểu đồ thời gian đơn giản cho SFE, SSIP, RFIP, Flowcount
giống phần case study của tác giả, nhưng đọc trực tiếp từ CSV.

Nguồn dữ liệu đề xuất:
- data/result.csv  (runtime log của controller)
  các cột: time,sfe,ssip,rfip,label,reason,confidence,dpid

Script này cố tình viết đơn giản, dễ sửa số liệu / file nguồn.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt


def _get_output_dir():
    """Get output directory for visualization files"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # mặc định đọc từ data/result.csv (runtime)
    data_path = os.path.abspath(os.path.join(base_dir, "..", "data", "result.csv"))
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Không tìm thấy file dữ liệu: {data_path}")
    df = pd.read_csv(data_path)
    return df


def plot_sfe_ssip_rfip(df):
    output_dir = _get_output_dir()
    
    # Giả sử mỗi dòng là một "thời điểm" liên tiếp
    x = range(len(df))

    # Dùng trị tuyệt đối cho SFE, SSIP để đồ thị dễ nhìn hơn (không âm)
    sfe = df["sfe"].abs()
    ssip = df["ssip"].abs()
    rfip = df["rfip"]

    # (a) SFE
    plt.figure(figsize=(6, 4))
    plt.plot(x, sfe, linewidth=1.5)
    plt.xlabel("Sample index")
    plt.ylabel("Speed of Flow entries (SFE)")
    plt.title("Speed of Flow Entries (SFE) over time")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "sfe_timeseries.png"), dpi=200)
    plt.close()

    # (b) SSIP
    plt.figure(figsize=(6, 4))
    plt.plot(x, ssip, linewidth=1.5)
    plt.xlabel("Sample index")
    plt.ylabel("Speed of Source IP (SSIP)")
    plt.title("Speed of Source IP (SSIP) over time")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "ssip_timeseries.png"), dpi=200)
    plt.close()

    # (c) RFIP
    plt.figure(figsize=(6, 4))
    plt.plot(x, rfip, linewidth=1.5)
    plt.xlabel("Sample index")
    plt.ylabel("Ratio of Flow Pair (RFIP)")
    plt.title("Ratio of Flow Pair (RFIP) over time")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "rfip_timeseries.png"), dpi=200)
    plt.close()


def plot_flowcount(df):
    """
    Flowcount đơn giản: dùng cột 'sfe' làm proxy số flow entries,
    hoặc nếu sau này bạn có cột flowcount riêng thì sửa lại ở đây.
    """
    output_dir = _get_output_dir()
    
    x = range(len(df))
    flowcount = df["sfe"].cumsum()

    plt.figure(figsize=(6, 4))
    plt.plot(x, flowcount, linewidth=1.5)
    plt.xlabel("Sample index")
    plt.ylabel("Flowcount (cumulative)")
    plt.title("Flowcount over time")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "flowcount_timeseries.png"), dpi=200)
    plt.close()


def main():
    output_dir = _get_output_dir()
    df = load_data()
    plot_sfe_ssip_rfip(df)
    plot_flowcount(df)
    print(f"Đã vẽ xong các file vào {output_dir}:")
    print("  - sfe_timeseries.png")
    print("  - ssip_timeseries.png")
    print("  - rfip_timeseries.png")
    print("  - flowcount_timeseries.png")


if __name__ == "__main__":
    main()


