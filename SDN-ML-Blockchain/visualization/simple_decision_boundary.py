#!/usr/bin/env python3
"""
Vẽ decision boundary SVM cho hai cặp đặc trưng (sfe, ssip) và (sfe, rfip),
giống graph.py gốc.

Input: dataset/result.csv với 4 cột: sfe, ssip, rfip, label
Outputs: svm_graph1.png, svm_graph2.png
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from sklearn import svm
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from mlxtend.plotting import plot_decision_regions


def get_model(name: str):
    if name == "decision_tree":
        return DecisionTreeClassifier()
    if name == "random_forest":
        return RandomForestClassifier(n_estimators=100, random_state=0)
    if name == "naive_bayes":
        return GaussianNB()
    # default: SVM (RBF) với class_weight ưu tiên bảo vệ lớp 0 mạnh hơn
    return svm.SVC(kernel="rbf", C=1.0, gamma="scale", class_weight={0: 10, 1: 1})


def _get_output_dir():
    """Get output directory for visualization files"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def plot_pair(df, feats, out_name, title, xlabel, ylabel, model_name):
    X = df[feats].to_numpy()
    y = df["label"].to_numpy().astype(int)
    clf = get_model(model_name)
    clf.fit(X, y)

    output_dir = _get_output_dir()
    out_path = os.path.join(output_dir, out_name)

    fig = plt.figure(figsize=(8, 6))
    plot_decision_regions(X=X, y=y, clf=clf, legend=2)
    plt.title(f"{title} - {model_name}", size=14)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    # Giới hạn trục để nhìn rõ vùng quyết định giống style tác giả:
    # - Luôn giới hạn SFE trong [0, 200]
    # - Với SSIP, cũng giới hạn [0, 200]
    if xlabel.upper() in ("SFE", "SPEED OF FLOW ENTRY"):
        plt.xlim(0, 200)
    if ylabel.upper() in ("SSIP", "SPEED OF SOURCE IP"):
        plt.ylim(0, 200)

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"Saved {out_path}")


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.abspath(os.path.join(base_dir, "..", "dataset", "result_filtered.csv"))
    if not os.path.exists(data_path):
        # fallback để không vẽ hỏng nếu chưa lọc
        data_path = os.path.abspath(os.path.join(base_dir, "..", "dataset", "result.csv"))
    df = pd.read_csv(data_path)
    # Giữ đúng cột
    df = df.rename(columns={df.columns[0]: "sfe", df.columns[1]: "ssip", df.columns[2]: "rfip", df.columns[3]: "label"})
    models = ["decision_tree", "random_forest", "svm", "naive_bayes"]

    for m in models:
        out1 = f"{m}_graph_sfe_ssip.png"
        out2 = f"{m}_graph_sfe_rfip.png"
        plot_pair(
            df,
            ["sfe", "ssip"],
            out1,
            "Decision Boundary (SFE vs SSIP)",
            "SFE",
            "SSIP",
            m,
        )
        plot_pair(
            df,
            ["sfe", "rfip"],
            out2,
            "Decision Boundary (SFE vs RFIP)",
            "SFE",
            "RFIP",
            m,
        )


if __name__ == "__main__":
    main()

