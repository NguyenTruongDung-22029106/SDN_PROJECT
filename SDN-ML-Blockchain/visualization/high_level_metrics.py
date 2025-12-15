#!/usr/bin/env python3
"""
Vẽ các biểu đồ "tổng quan" dựa trên CHÍNH dữ liệu của bạn.

Nguồn:
- dataset/result.csv: tập train (sfe, ssip, rfip, label)
- data/result.csv: log runtime (time,sfe,ssip,rfip,label,reason,confidence,dpid)

Biểu đồ:
- detection_rate_bar.png: Detection Rate & False Alarm Rate của SVM trên dataset/result.csv
- network_traffic_normal_vs_attack.png: SFE trung bình của normal vs attack (từ data/result.csv)
- ddos_attack_frequency_over_time.png: số dòng label=1 theo thời gian (từ data/result.csv)
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from sklearn import svm
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split


def _path_from_root(*parts):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(base_dir, "..", *parts))


def plot_detection_rate_from_dataset():
    """Tính DR/FAR từ dataset/result.csv cho 4 thuật toán và vẽ bar chart."""
    data_path = _path_from_root("dataset", "result.csv")
    if not os.path.exists(data_path):
        print(f"Bỏ qua detection_rate_bar: không tìm thấy {data_path}")
        return

    df = pd.read_csv(data_path)
    X = df.iloc[:, 0:3].to_numpy()
    y = df.iloc[:, 3].to_numpy()

    x_train, x_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=0
    )

    models = {
        "DecisionTree": DecisionTreeClassifier(),
        "RandomForest": RandomForestClassifier(n_estimators=100, random_state=0),
        "SVM": svm.SVC(),
        "NaiveBayes": GaussianNB(),
    }

    dr_list = []
    far_list = []
    names = []

    for name, clf in models.items():
        clf.fit(x_train, y_train)
        preds = clf.predict(x_test)

        DD = DN = FD = TN = 0
        for yt, yp in zip(y_test, preds):
            if yt == 1:
                if yp == 1:
                    DD += 1
                else:
                    DN += 1
            else:
                if yp == 1:
                    FD += 1
                else:
                    TN += 1

        dr = DD / (DD + DN) if (DD + DN) else 0
        far = FD / (FD + TN) if (FD + TN) else 0

        names.append(name)
        dr_list.append(dr * 100)
        far_list.append(far * 100)

    # Biểu đồ Detection Rate cho 4 thuật toán
    plt.figure(figsize=(6, 4))
    plt.bar(names, dr_list, color="g")
    plt.ylabel("Detection Rate (%)")
    plt.ylim(0, 100)
    for x, yv in zip(names, dr_list):
        plt.text(x, yv + 1, f"{yv:.1f}", ha="center", va="bottom", fontsize=9)
    plt.title("Detection Rate (dataset/result.csv)")
    plt.tight_layout()
    out1 = "detection_rate_bar.png"
    plt.savefig(out1, dpi=200)
    plt.close()
    print(f"Đã lưu {out1}")

    # Biểu đồ False Alarm Rate cho 4 thuật toán
    plt.figure(figsize=(6, 4))
    plt.bar(names, far_list, color="r")
    plt.ylabel("False Alarm Rate (%)")
    plt.ylim(0, 100)
    for x, yv in zip(names, far_list):
        plt.text(x, yv + 1, f"{yv:.2f}", ha="center", va="bottom", fontsize=9)
    plt.title("False Alarm Rate (dataset/result.csv)")
    plt.tight_layout()
    out2 = "false_alarm_bar.png"
    plt.savefig(out2, dpi=200)
    plt.close()
    print(f"Đã lưu {out2}")


def plot_network_traffic_from_runtime():
    """So sánh SFE trung bình giữa normal (label=0) và attack (label=1) từ data/result.csv."""
    data_path = _path_from_root("data", "result.csv")
    if not os.path.exists(data_path):
        print(f"Bỏ qua network_traffic_normal_vs_attack: không tìm thấy {data_path}")
        return

    df = pd.read_csv(data_path)
    # dùng label làm ground truth: 0 = normal, 1 = attack trong các lần collect
    normal = df[df["label"] == 0]
    attack = df[df["label"] == 1]
    if normal.empty or attack.empty:
        print("Không đủ cả normal và attack trong data/result.csv để vẽ network_traffic_normal_vs_attack.")
        return

    mean_normal = normal["sfe"].mean()
    mean_attack = attack["sfe"].mean()

    plt.figure(figsize=(5, 4))
    labels = ["Normal", "Attack"]
    values = [mean_normal, mean_attack]
    plt.bar(labels, values, color=["b", "orange"])
    plt.ylabel("Average SFE")
    for x, yv in zip(labels, values):
        plt.text(x, yv, f"{yv:.1f}", ha="center", va="bottom", fontsize=9)
    plt.title("Average Speed of Flow Entries (SFE)\nNormal vs Attack (data/result.csv)")
    plt.tight_layout()
    out = "network_traffic_normal_vs_attack.png"
    plt.savefig(out, dpi=200)
    plt.close()
    print(f"Đã lưu {out}")


def plot_attack_frequency_over_time():
    """Đếm số dòng label=1 theo thời gian (theo phút) để thấy tần suất DDoS."""
    data_path = _path_from_root("data", "result.csv")
    if not os.path.exists(data_path):
        print(f"Bỏ qua ddos_attack_frequency_over_time: không tìm thấy {data_path}")
        return

    df = pd.read_csv(data_path)
    if "time" not in df.columns:
        print("Không có cột 'time' trong data/result.csv, bỏ qua ddos_attack_frequency_over_time.")
        return

    # Chỉ lấy những dòng label=1 (attack)
    df_attack = df[df["label"] == 1].copy()
    if df_attack.empty:
        print("Không có dòng label=1 trong data/result.csv, bỏ qua ddos_attack_frequency_over_time.")
        return

    # Chuẩn hoá time về dạng datetime và group theo phút
    df_attack["time_parsed"] = pd.to_datetime(df_attack["time"], errors="coerce")
    df_attack = df_attack.dropna(subset=["time_parsed"])
    if df_attack.empty:
        print("Không parse được timestamp trong cột time, bỏ qua ddos_attack_frequency_over_time.")
        return

    df_attack["minute"] = df_attack["time_parsed"].dt.floor("T")
    counts = df_attack.groupby("minute").size().reset_index(name="count")

    plt.figure(figsize=(6, 4))
    plt.plot(counts["minute"], counts["count"], marker="o")
    plt.xlabel("Time (per minute)")
    plt.ylabel("Number of attack rows (label=1)")
    plt.title("DDoS Attack Frequency Over Time\n(from data/result.csv)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    out = "ddos_attack_frequency_over_time.png"
    plt.savefig(out, dpi=200)
    plt.close()
    print(f"Đã lưu {out}")


def main():
    plot_detection_rate_from_dataset()
    plot_network_traffic_from_runtime()
    plot_attack_frequency_over_time()
    print("Đã vẽ xong các biểu đồ high-level dựa trên dữ liệu thực.")


if __name__ == "__main__":
    main()



