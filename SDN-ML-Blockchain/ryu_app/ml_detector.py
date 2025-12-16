"""
Machine Learning Detector Module
Supports multiple ML algorithms for DDoS detection
"""
from __future__ import division
import numpy as np
import os
import pandas as pd
from sklearn import svm
from sklearn import tree
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score
import joblib


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)  # Parent of ryu_app/
DEFAULT_DATA_PATH = os.path.abspath(os.path.join(PROJECT_ROOT, 'dataset', 'result_filtered.csv'))


class MLDetector:
    def __init__(self, model_type='decision_tree', model_path=None):
        """
        Initialize ML detector with specified model type
        
        Args:
            model_type: 'svm', 'decision_tree', 'random_forest', or 'naive_bayes'
            model_path: Path to training data CSV
        """
        self.model_type = model_type
        self.model = None
        self.is_trained = False
        self.model_dir = BASE_DIR
        # Threshold xác suất cho class 1 (attack), sẽ được học tự động khi train
        self.threshold = 0.5
        
        # Resolve paths
        if model_path is None:
            model_path = DEFAULT_DATA_PATH
        elif not os.path.isabs(model_path):
            # Resolve relative path from project root, not from ryu_app/
            model_path = os.path.abspath(os.path.join(PROJECT_ROOT, model_path))
        
        # Always require CSV training data; no fallback to untrained/default
        if not os.path.exists(model_path):
            # Nếu file filtered chưa có, thử fallback sang dataset/result.csv để không chặn khởi động
            fallback = os.path.abspath(os.path.join(PROJECT_ROOT, "dataset", "result.csv"))
            if os.path.exists(fallback):
                print(f"Info: {model_path} not found, falling back to {fallback}")
                model_path = fallback
            else:
                raise FileNotFoundError(
                    f"Training data CSV not found at {model_path}. "
                    "Provide dataset/result_filtered.csv hoặc dataset/result.csv (sfe,ssip,rfip,label)."
                )

        ok = self.train(model_path)
        if not ok:
            raise RuntimeError(
                f"Failed to train {model_type} model from {model_path}. "
                "Check CSV format and contents."
            )

    def _create_default_model(self):
        """Create untrained model based on model_type"""
        if self.model_type == 'svm':
            # Scale features for SVM
            self.model = Pipeline([
                ('scaler', StandardScaler()),
                ('clf', svm.SVC(probability=True))
            ])
        elif self.model_type == 'decision_tree':
            self.model = tree.DecisionTreeClassifier()
        elif self.model_type == 'random_forest':
            # RF ít nhạy với scale nhưng giữ pipeline cho đồng nhất
            self.model = Pipeline([
                ('scaler', StandardScaler()),
                ('clf', RandomForestClassifier(n_estimators=100))
            ])
        elif self.model_type == 'naive_bayes':
            self.model = GaussianNB()
        else:
            # Default to decision tree
            self.model = tree.DecisionTreeClassifier()

    def train(self, data_path):
        """
        Train the model from CSV data
        
        Args:
            data_path: Path to CSV file with format: sfe, ssip, rfip, label
        """
        try:
            df = pd.read_csv(data_path)

            # Try to pick the correct columns
            expected_cols = ['sfe', 'ssip', 'rfip', 'label']
            if all(c in df.columns for c in expected_cols):
                df_num = df[expected_cols].copy()
            else:
                # Fallback: use last 4 columns
                df_num = df.iloc[:, -4:].copy()
                df_num.columns = expected_cols

            # Coerce to numeric and drop NaN
            for c in expected_cols:
                df_num[c] = pd.to_numeric(df_num[c], errors='coerce')
            before = len(df_num)
            df_num = df_num.dropna()
            after = len(df_num)
            if before - after > 0:
                print(f"Info: Dropped {before - after} rows with NaN from {data_path}")
            if after == 0:
                raise ValueError(f"No valid rows after removing NaN in {data_path}")

            X = df_num[['sfe', 'ssip', 'rfip']].to_numpy(dtype=float)
            y = df_num['label'].to_numpy(dtype=int)
            
            # Create model
            self._create_default_model()

            # Nếu dữ liệu đủ lớn và có cả 2 lớp, tách validation để tìm threshold tốt nhất
            if len(np.unique(y)) > 1 and len(y) > 50:
                X_train, X_val, y_train, y_val = train_test_split(
                    X, y, test_size=0.3, random_state=42, stratify=y
                )
                self.model.fit(X_train, y_train)

                best_t = 0.5
                best_f1 = -1.0
                try:
                    # Cố gắng dùng xác suất cho class 1 (attack)
                    probs = self.model.predict_proba(X_val)[:, 1]
                    for t in np.linspace(0.5, 0.95, 10):
                        preds = (probs >= t).astype(int)
                        f1 = f1_score(y_val, preds, zero_division=0)
                        if f1 > best_f1:
                            best_f1 = f1
                            best_t = float(t)
                    self.threshold = best_t
                    print(f"✓ Auto-selected threshold={self.threshold:.2f} (val F1={best_f1:.3f})")
                except Exception:
                    # Nếu model không hỗ trợ predict_proba thì dùng mặc định 0.5
                    self.threshold = 0.5
            else:
                # Dữ liệu quá ít hoặc chỉ có 1 lớp → train full, threshold mặc định
                self.model.fit(X, y)
                self.threshold = 0.5

            # Sau khi chọn threshold, train lại model trên toàn bộ dữ liệu
            if len(np.unique(y)) > 1:
                self.model.fit(X, y)

            self.is_trained = True
            print(f"✓ Model trained successfully with {len(X)} samples (threshold={self.threshold:.2f})")
            
            # Save the model kèm threshold
            model_file = os.path.join(self.model_dir, f'ml_model_{self.model_type}.pkl')
            joblib.dump({"model": self.model, "threshold": self.threshold}, model_file)
            print(f"✓ Model saved to {model_file}")
            
            return True
            
        except Exception as e:
            print(f"Error training model: {e}")
            return False

    def classify(self, features):
        """
        Classify traffic based on features
        
        Args:
            features: [sfe, ssip, rfip]
            
        Returns:
            (prediction, confidence): (0 for normal, 1 for attack, confidence score)
        """
        if not self.is_trained:
            print("Warning: Model not trained. Using default classification.")
            # Simple heuristic for untrained model
            sfe, ssip, rfip = features
            if sfe > 50 or ssip > 30:
                return 1, 0.7  # Likely attack
            return 0, 0.6  # Likely normal
        
        # Prepare input
        fparams = np.zeros((1, 3))
        fparams[0, 0] = features[0]  # sfe
        fparams[0, 1] = features[1]  # ssip
        fparams[0, 2] = features[2]  # rfip
        
        prediction = None
        confidence = 0.8

        # Ưu tiên dùng xác suất để áp dụng threshold đã học
        try:
            probabilities = self.model.predict_proba(fparams)[0]
            # Giả sử class 1 là attack
            if len(probabilities) == 2:
                prob_attack = float(probabilities[1])
            else:
                prob_attack = float(probabilities[0])

            t = getattr(self, "threshold", 0.5) or 0.5
            prediction = 1 if prob_attack >= t else 0
            confidence = max(probabilities)
        except Exception:
            # Fallback nếu không có predict_proba
            prediction = int(self.model.predict(fparams)[0])
            confidence = 0.8  # Default confidence
        
        print(
            f"ML Detection: Features={features}, Prediction={'Attack' if prediction==1 else 'Normal'}, "
            f"Confidence={confidence:.2%}, Threshold={getattr(self, 'threshold', 0.5):.2f}"
        )
        
        return int(prediction), float(confidence)

    def get_feature_importance(self):
        """Get feature importance (for tree-based models)"""
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            features = ['SFE', 'SSIP', 'RFIP']
            return dict(zip(features, importances))
        return None

    def save_model(self, filepath):
        """Save model to file"""
        if not os.path.isabs(filepath):
            filepath = os.path.join(self.model_dir, filepath)
        joblib.dump({"model": self.model, "threshold": self.threshold}, filepath)
        print(f"✓ Model + threshold saved to {filepath}")

    def load_model(self, filepath):
        """Load model from file"""
        if not os.path.isabs(filepath):
            filepath = os.path.join(self.model_dir, filepath)
        obj = joblib.load(filepath)
        if isinstance(obj, dict) and "model" in obj:
            self.model = obj["model"]
            self.threshold = float(obj.get("threshold", 0.5))
        else:
            self.model = obj
            self.threshold = 0.5
        self.is_trained = True
        print(f"✓ Model loaded from {filepath} (threshold={self.threshold:.2f})")


if __name__ == '__main__':
    import argparse


    parser = argparse.ArgumentParser(description='Train or save MLDetector models')
    parser.add_argument('--model', '-m', default='decision_tree', choices=['decision_tree', 'random_forest', 'svm', 'naive_bayes'], help='Model type')
    parser.add_argument('--data', '-d', default=DEFAULT_DATA_PATH, help='Path to training CSV (dataset/result.csv)')
    parser.add_argument('--force', '-f', action='store_true', help='Force retrain even if pre-trained model exists')
    parser.add_argument('--save-untrained', action='store_true', help='If training data missing, save an untrained default model to disk')
    parser.add_argument('--all', action='store_true', help='Train/save all supported models')
    args = parser.parse_args()

    SUPPORTED_MODELS = ['decision_tree', 'random_forest', 'svm', 'naive_bayes']

    def process_model(model_type, args):
        print(f"\n=== Processing model: {model_type} ===")
        detector = MLDetector(model_type=model_type, model_path=args.data)
        # If force retrain requested, run training if data exists
        if args.force:
                ok = detector.train(args.data)
                if ok:
                    detector.save_model(f'ml_model_{model_type}.pkl')
        # Ensure trained model file exists
        if detector.is_trained:
            model_file = os.path.join(detector.model_dir, f'ml_model_{model_type}.pkl')
            if os.path.exists(model_file):
                print(f"Model is available: {model_file}")
            else:
                print(f"Warning: model marked trained but file not found at {model_file}")

    # Always train/save all models in one run (per request)
    args.all = True
    if not os.path.exists(args.data):
        raise FileNotFoundError(f"Training data not found at {args.data}")

    # Nếu data tồn tại, lần lượt xử lý tất cả model
    for model_type in SUPPORTED_MODELS:
        process_model(model_type, args)


# Utility function for batch classification
def batch_classify(detector, features_list):
    """
    Classify multiple feature sets
    
    Args:
        detector: MLDetector instance
        features_list: List of [sfe, ssip, rfip] features
        
    Returns:
        List of (prediction, confidence) tuples
    """
    results = []
    for features in features_list:
        result = detector.classify(features)
        results.append(result)
    return results
