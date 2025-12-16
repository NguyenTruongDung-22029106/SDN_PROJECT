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


def _get_output_dir():
    """Get output directory for visualization files"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def plot_detection_rate_from_dataset():
    """Tính DR/FAR từ dataset/result.csv cho 4 thuật toán và vẽ bar chart."""
    data_path = _path_from_root("dataset", "result.csv")
    if not os.path.exists(data_path):
        print(f"Bỏ qua detection_rate_bar: không tìm thấy {data_path}")
        return

    df = pd.read_csv(data_path)
    X = df[['sfe', 'ssip', 'rfip']].values
    y = df['label'].values
    x_train, x_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    import joblib
    model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ryu_app"))
    models = {
        "DecisionTree": os.path.join(model_dir, "ml_model_decision_tree.pkl"),
        "RandomForest": os.path.join(model_dir, "ml_model_random_forest.pkl"),
        "SVM": os.path.join(model_dir, "ml_model_svm.pkl"),
        "NaiveBayes": os.path.join(model_dir, "ml_model_naive_bayes.pkl"),
    }
    dr_list = []
    far_list = []
    names = []
    for name, path in models.items():
        if not os.path.exists(path):
            print(f"{name}: Model file not found: {path}")
            continue
        clf = joblib.load(path)
        if isinstance(clf, dict) and "model" in clf:
            clf = clf["model"]
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

    output_dir = _get_output_dir()
    
    # Biểu đồ Detection Rate cho 4 thuật toán
    plt.figure(figsize=(6, 4))
    plt.bar(names, dr_list, color="g")
    plt.ylabel("Detection Rate (%)")
    plt.ylim(0, 100)
    for x, yv in zip(names, dr_list):
        plt.text(x, yv + 1, f"{yv:.1f}", ha="center", va="bottom", fontsize=9)
    plt.title("Detection Rate (dataset/result.csv)")
    plt.tight_layout()
    out1 = os.path.join(output_dir, "detection_rate_bar.png")
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
    out2 = os.path.join(output_dir, "false_alarm_bar.png")
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

    # Sử dụng absolute value cho SFE
    mean_normal = normal["sfe"].abs().mean()
    mean_attack = attack["sfe"].abs().mean()
    count_normal = len(normal)
    count_attack = len(attack)

    output_dir = _get_output_dir()
    
    plt.figure(figsize=(7, 5))
    labels = ["Normal", "Attack"]
    values = [mean_normal, mean_attack]
    plt.bar(labels, values, color=["b", "orange"])
    plt.ylabel("Average |SFE|")
    
    # Thêm số lượng vào label
    labels_with_count = [f"Normal\n(n={count_normal})", f"Attack\n(n={count_attack})"]
    plt.xticks(range(len(labels)), labels_with_count)
    
    for x, yv in zip(range(len(labels)), values):
        plt.text(x, yv, f"{yv:.1f}", ha="center", va="bottom", fontsize=10, fontweight='bold')
    
    plt.title(f"Average Speed of Flow Entries (|SFE|)\nNormal vs Attack\n(Normal: {count_normal} samples, Attack: {count_attack} samples)")
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    plt.tight_layout()
    out = os.path.join(output_dir, "network_traffic_normal_vs_attack.png")
    plt.savefig(out, dpi=200)
    plt.close()
    print(f"Đã lưu {out}")
    print(f"  Normal: {count_normal} samples, avg |SFE| = {mean_normal:.2f}")
    print(f"  Attack: {count_attack} samples, avg |SFE| = {mean_attack:.2f}")


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

    output_dir = _get_output_dir()
    
    plt.figure(figsize=(6, 4))
    plt.plot(counts["minute"], counts["count"], marker="o")
    plt.xlabel("Time (per minute)")
    plt.ylabel("Number of attack rows (label=1)")
    plt.title("DDoS Attack Frequency Over Time\n(from data/result.csv)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    out = os.path.join(output_dir, "ddos_attack_frequency_over_time.png")
    plt.savefig(out, dpi=200)
    plt.close()
    print(f"Đã lưu {out}")


def main():
    output_dir = _get_output_dir()
    plot_detection_rate_from_dataset()
    plot_network_traffic_from_runtime()
    plot_attack_frequency_over_time()
    print(f"\nĐã vẽ xong các biểu đồ high-level vào {output_dir}:")
    print("  - detection_rate_bar.png")
    print("  - false_alarm_bar.png")
    print("  - network_traffic_normal_vs_attack.png")
    print("  - ddos_attack_frequency_over_time.png")


if __name__ == "__main__":
    main()



