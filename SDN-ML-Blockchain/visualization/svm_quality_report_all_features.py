import os
import pandas as pd
from sklearn import svm
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix
from itertools import combinations

# Load data
base_dir = os.path.dirname(os.path.abspath(__file__))
# Sử dụng dataset/result.csv (không còn result_filtered.csv)
data_path = os.path.abspath(os.path.join(base_dir, "..", "dataset", "result.csv"))
if not os.path.exists(data_path):
    raise FileNotFoundError(f"Dataset not found: {data_path}. Please run: python3 ryu_app/build_dataset.py")
df = pd.read_csv(data_path, on_bad_lines='skip')
df = df.rename(columns={df.columns[0]: "sfe", df.columns[1]: "ssip", df.columns[2]: "rfip", df.columns[3]: "label"})
df = df[['sfe', 'ssip', 'rfip', 'label']]

features = ['sfe', 'ssip', 'rfip']

# Kiểm tra tất cả các tổ hợp 2 và 3 đặc trưng
feature_sets = [list(c) for c in combinations(features, 2)] + [features]

for feats in feature_sets:
    desc = ' + '.join([f.upper() for f in feats])
    X = df[feats].to_numpy()
    y = df['label'].to_numpy().astype(int)
    clf = svm.SVC(kernel="rbf", C=1.0, gamma="scale", class_weight={0: 10, 1: 1})
    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(clf, X, y, cv=cv, scoring='accuracy')
    print(f"\n==== {desc} ====")
    print(f"Cross-validation accuracy: {scores.mean():.4f} ± {scores.std():.4f}")
    # Fit & classification report
    clf.fit(X, y)
    y_pred = clf.predict(X)
    print("Confusion matrix:")
    print(confusion_matrix(y, y_pred))
    print("Classification report:")
    print(classification_report(y, y_pred, digits=4))
