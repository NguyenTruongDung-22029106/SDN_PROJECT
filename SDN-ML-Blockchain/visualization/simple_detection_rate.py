#!/usr/bin/env python3
"""
Tính Detection Rate (TPR cho label=1) và False Alarm Rate (FPR cho label=0)
đơn giản như detection_rate.py gốc.

Input: dataset/result.csv với 4 cột: sfe, ssip, rfip, label
"""

import os
import pandas as pd
from sklearn import svm
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split


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
        "svm_rbf": svm.SVC(),  # mặc định
        "naive_bayes": GaussianNB(),
    }

    print("=== Detection Rate (TPR) & False Alarm Rate (FPR) ===")
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

        print(f"{name:>13}: DR = {dr:6.4f} | FAR = {far:6.4f}")


if __name__ == "__main__":
    main()

