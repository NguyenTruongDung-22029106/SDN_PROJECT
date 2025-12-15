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
    X = df.iloc[:, 0:3].to_numpy()
    y = df.iloc[:, 3].to_numpy()

    x_train, x_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=0
    )

    models = {
        "decision_tree": DecisionTreeClassifier(),
        "random_forest": RandomForestClassifier(n_estimators=100, random_state=0),
        "svm_linear": svm.SVC(kernel="linear", C=0.025),
        "naive_bayes": GaussianNB(),
    }

    print("=== Accuracy & 5-fold Cross-Validation (dataset/result.csv) ===")
    for name, clf in models.items():
        clf.fit(x_train, y_train)
        preds = clf.predict(x_test)
        acc = accuracy_score(y_test, preds)
        cv_mean = cross_val_score(clf, x_train, y_train, cv=5).mean()
        print(f"{name:>13}: Accuracy = {acc*100:6.2f}% | CV-mean = {cv_mean:6.4f}")


if __name__ == "__main__":
    main()

