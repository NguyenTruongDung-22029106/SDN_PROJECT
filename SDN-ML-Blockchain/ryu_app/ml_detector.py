"""
Machine Learning Detector Module
Supports multiple ML algorithms for DDoS detection
"""
from __future__ import division
import numpy as np
import os
import logging
from sklearn import svm
from sklearn import tree
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
import joblib


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)  # Parent of ryu_app/
DEFAULT_DATA_PATH = os.path.abspath(os.path.join(PROJECT_ROOT, 'dataset', 'result.csv'))

# Setup logger
logger = logging.getLogger(__name__)


class MLDetector:
    def __init__(self, model_type='decision_tree', model_path=None):
        """
        Initialize ML detector with specified model type (GIỐNG TÁC GIẢ GỐC)
        
        Args:
            model_type: 'svm', 'decision_tree', 'random_forest', or 'naive_bayes'
            model_path: Path to training data CSV
        """
        self.model_type = model_type
        self.model = None
        self.is_trained = False
        self.model_dir = BASE_DIR
        
        # Resolve paths
        if model_path is None:
            model_path = DEFAULT_DATA_PATH
        elif not os.path.isabs(model_path):
            model_path = os.path.abspath(os.path.join(PROJECT_ROOT, model_path))
        
        # Kiểm tra xem đã có model đã train sẵn chưa
        model_file = os.path.join(self.model_dir, f'ml_model_{self.model_type}.pkl')
        
        if os.path.exists(model_file):
            # Load model đã train sẵn
            try:
                self.load_model(model_file)
                logger.info(f"✓ Loaded pre-trained {model_type} model from {model_file}")
            except Exception as e:
                logger.warning(f"Failed to load pre-trained model: {e}. Will train new model.")
                # Nếu load thất bại, train lại
                if not os.path.exists(model_path):
                    raise FileNotFoundError(
                        f"Training data CSV not found at {model_path}. "
                        "Please run in data collection mode (APP_TYPE=0) to create data/result.csv"
                    )
                ok = self.train(model_path)
                if not ok:
                    raise RuntimeError(
                        f"Failed to train {model_type} model from {model_path}. "
                        "Check CSV format and contents."
                    )
        else:
            # Chưa có model → cần train mới
            if not os.path.exists(model_path):
                raise FileNotFoundError(
                    f"Training data CSV not found at {model_path}. "
                    "Please run in data collection mode (APP_TYPE=0) to create data/result.csv"
                )

            logger.info(f"No pre-trained model found. Training new {model_type} model from {model_path}")
            ok = self.train(model_path)
            if not ok:
                raise RuntimeError(
                    f"Failed to train {model_type} model from {model_path}. "
                    "Check CSV format and contents."
                )

    def _create_default_model(self):
        """Create model instance based on type"""
        if self.model_type == 'svm':
            self.model = svm.SVC(kernel='rbf', gamma='scale')
        elif self.model_type == 'decision_tree':
            self.model = tree.DecisionTreeClassifier()
        elif self.model_type == 'random_forest':
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        elif self.model_type == 'naive_bayes':
            self.model = GaussianNB()
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

    def train(self, data_path):
        """
        Train the model from CSV data (GIỐNG TÁC GIẢ GỐC)
        
        Args:
            data_path: Path to CSV file with format: sfe, ssip, rfip, label
        """
        try:
            # Load trực tiếp giống tác giả: numpy.loadtxt với dtype='str'
            # Skip header nếu có (dòng đầu chứa 'sfe,ssip,rfip,label')
            data = np.loadtxt(open(data_path, 'rb'), delimiter=',', dtype='str', skiprows=1)
            
            # Kiểm tra số lượng class (y vẫn là string)
            unique_labels = np.unique(data[:, 3])
            num_classes = len(unique_labels)
            
            if num_classes < 2:
                from collections import Counter
                label_counts = Counter(data[:, 3])
                raise ValueError(
                    f"Dataset chỉ có {num_classes} class (cần ít nhất 2 class để train model). "
                    f"Phân bố label: {dict(label_counts)}. "
                    f"Vui lòng thu thập thêm dữ liệu: "
                    f"chạy với APP_TYPE=0 TEST_TYPE=0 để thu thập normal traffic (label=0), "
                    f"và APP_TYPE=0 TEST_TYPE=1 để thu thập attack traffic (label=1)."
                )
            
            # Create model
            self._create_default_model()

            # Train trực tiếp giống tác giả: sklearn tự convert string sang numeric
            X = data[:, 0:3]
            y = data[:, 3]
            
            # Naive Bayes cần convert sang numeric trước (các model khác sklearn tự convert)
            if self.model_type == 'naive_bayes':
                X = X.astype(float)
                y = y.astype(int)
            
                self.model.fit(X, y)

            self.is_trained = True
            logger.info(f"✓ Model trained successfully with {len(X)} samples")
            
            # Save model (không cần threshold)
            model_file = os.path.join(self.model_dir, f'ml_model_{self.model_type}.pkl')
            joblib.dump(self.model, model_file)
            logger.info(f"✓ Model saved to {model_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return False

    def classify(self, features):
        """
        Classify traffic based on features (GIỐNG TÁC GIẢ GỐC)
        
        Args:
            features: [sfe, ssip, rfip]
            
        Returns:
            prediction array (giống tác giả gốc)
        """
        if not self.is_trained:
            logger.warning("Warning: Model not trained. Using default classification.")
            sfe, ssip, rfip = features
            if sfe > 50 or ssip > 30:
                return ['1']
            return ['0']
        
        # Prepare input giống tác giả gốc
        fparams = np.zeros((1, 3))
        fparams[:, 0] = features[0]  # sfe
        fparams[:, 1] = features[1]  # ssip
        fparams[:, 2] = features[2]  # rfip
        
        # Predict trực tiếp giống tác giả - KHÔNG CÓ threshold, KHÔNG CÓ confidence
        prediction = self.model.predict(fparams)
        
        logger.debug(
            f"ML Detection: Features={features}, Prediction={prediction}"
        )
        
        return prediction

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
        joblib.dump(self.model, filepath)
        print(f"✓ Model saved to {filepath}")

    def load_model(self, filepath):
        """Load model from file"""
        if not os.path.isabs(filepath):
            filepath = os.path.join(self.model_dir, filepath)
        obj = joblib.load(filepath)
        if isinstance(obj, dict) and "model" in obj:
            # Backward compatibility: old format có threshold
            self.model = obj["model"]
        else:
            self.model = obj
        self.is_trained = True
        logger.info(f"✓ Model loaded from {filepath}")


if __name__ == "__main__":
    """Train and test ML models"""
    import argparse

    parser = argparse.ArgumentParser(description='Train ML models for DDoS detection')
    parser.add_argument('--model', type=str, default='decision_tree', 
                        choices=['decision_tree', 'random_forest', 'svm', 'naive_bayes'],
                        help='Model type to train')
    parser.add_argument('--data', type=str, default=DEFAULT_DATA_PATH,
                        help='Path to training data CSV')
    parser.add_argument('--force', action='store_true',
                        help='Force retrain even if model exists')
    parser.add_argument('--all', action='store_true', help='Train/save all supported models')
    args = parser.parse_args()

    SUPPORTED_MODELS = ['decision_tree', 'random_forest', 'svm', 'naive_bayes']

    def process_model(model_type, args):
        print(f"\n=== Processing model: {model_type} ===")
        try:
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
                    print(f"✓ Model is available: {model_file}")
                else:
                    print(f"⚠ Warning: model marked trained but file not found at {model_file}")
        except (ValueError, RuntimeError, FileNotFoundError) as e:
            print(f"❌ Failed to process {model_type}: {e}")
            print(f"   Skipping {model_type} and continuing with other models...")
            return False
        except Exception as e:
            print(f"❌ Unexpected error processing {model_type}: {e}")
            return False
        return True

    if args.all:
        print("Training all supported models...")
    success_count = 0
        for model in SUPPORTED_MODELS:
            if process_model(model, args):
            success_count += 1
        print(f"\n✓ Successfully trained {success_count}/{len(SUPPORTED_MODELS)} models")
        else:
        process_model(args.model, args)
