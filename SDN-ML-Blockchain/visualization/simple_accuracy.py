#!/usr/bin/env python3
"""
Đo độ chính xác và cross-validation đơn giản (giống logic accuracy_score.py gốc).

Input: dataset/result.csv với 4 cột: sfe, ssip, rfip, label
"""

import os
import pandas as pd
from sklearn import svm
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.abspath(os.path.join(base_dir, "..", "dataset", "result.csv"))
    df = pd.read_csv(data_path)
    # Đồng bộ với analyze_models.py: dùng đúng cột features và label
    X = df[['sfe', 'ssip', 'rfip']].values
    y = df['label'].values
    x_train, x_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    import joblib
    model_dir = os.path.abspath(os.path.join(base_dir, "..", "ryu_app"))
    models = {
        "decision_tree": os.path.join(model_dir, "ml_model_decision_tree.pkl"),
        "random_forest": os.path.join(model_dir, "ml_model_random_forest.pkl"),
        "svm": os.path.join(model_dir, "ml_model_svm.pkl"),
        "naive_bayes": os.path.join(model_dir, "ml_model_naive_bayes.pkl"),
    }
    print("=== Accuracy (pre-trained models, dataset/result.csv) ===")
    for name, path in models.items():
        if not os.path.exists(path):
            print(f"{name:>13}: Model file not found: {path}")
            continue
        clf = joblib.load(path)
        # Nếu model là dict, lấy ra object model
        if isinstance(clf, dict) and "model" in clf:
            clf = clf["model"]
        preds = clf.predict(x_test)
        acc = accuracy_score(y_test, preds)
        print(f"{name:>13}: Accuracy = {acc*100:6.2f}%")


if __name__ == "__main__":
    main()

