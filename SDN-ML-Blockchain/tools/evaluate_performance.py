"""
Performance Evaluation and Analysis Tools
Calculates accuracy, precision, recall, F1-score
"""
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns


def calculate_metrics(y_true, y_pred):
    """
    Calculate ML model performance metrics
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
    
    Returns:
        Dictionary of metrics
    """
    metrics = {
        'accuracy': accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred, average='binary'),
        'recall': recall_score(y_true, y_pred, average='binary'),
        'f1_score': f1_score(y_true, y_pred, average='binary')
    }
    
    return metrics


def plot_confusion_matrix(y_true, y_pred, save_path='confusion_matrix.png'):
    """Plot confusion matrix"""
    cm = confusion_matrix(y_true, y_pred)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Normal', 'Attack'],
                yticklabels=['Normal', 'Attack'])
    plt.title('Confusion Matrix - DDoS Detection')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"✓ Confusion matrix saved to {save_path}")


def evaluate_model_from_csv(predictions_file, labels_file):
    """
    Evaluate model from CSV files
    
    Args:
        predictions_file: CSV with predictions
        labels_file: CSV with true labels
    """
    try:
        # Load data
        predictions = pd.read_csv(predictions_file)
        labels = pd.read_csv(labels_file)
        
        y_pred = predictions['prediction'].values
        y_true = labels['label'].values
        
        # Calculate metrics
        metrics = calculate_metrics(y_true, y_pred)
        
        print("=" * 50)
        print("MODEL PERFORMANCE METRICS")
        print("=" * 50)
        print(f"Accuracy:  {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
        print(f"Precision: {metrics['precision']:.4f} ({metrics['precision']*100:.2f}%)")
        print(f"Recall:    {metrics['recall']:.4f} ({metrics['recall']*100:.2f}%)")
        print(f"F1-Score:  {metrics['f1_score']:.4f} ({metrics['f1_score']*100:.2f}%)")
        print("=" * 50)
        
        # Detailed report
        print("\nClassification Report:")
        print(classification_report(y_true, y_pred, 
                                     target_names=['Normal', 'Attack']))
        
        # Plot confusion matrix
        plot_confusion_matrix(y_true, y_pred)
        
        return metrics
        
    except Exception as e:
        print(f"Error evaluating model: {e}")
        return None


def generate_sample_evaluation():
    """Generate sample evaluation with synthetic data"""
    np.random.seed(42)
    
    # Synthetic test data
    n_samples = 1000
    y_true = np.random.randint(0, 2, n_samples)
    
    # Simulate 95% accuracy
    y_pred = y_true.copy()
    errors = np.random.choice(n_samples, int(n_samples * 0.05), replace=False)
    y_pred[errors] = 1 - y_pred[errors]
    
    metrics = calculate_metrics(y_true, y_pred)
    
    print("=" * 50)
    print("SAMPLE EVALUATION (Synthetic Data)")
    print("=" * 50)
    print(f"Samples: {n_samples}")
    print(f"Accuracy:  {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
    print(f"Precision: {metrics['precision']:.4f} ({metrics['precision']*100:.2f}%)")
    print(f"Recall:    {metrics['recall']:.4f} ({metrics['recall']*100:.2f}%)")
    print(f"F1-Score:  {metrics['f1_score']:.4f} ({metrics['f1_score']*100:.2f}%)")
    print("=" * 50)
    
    plot_confusion_matrix(y_true, y_pred, 'sample_confusion_matrix.png')
    
    return metrics


if __name__ == '__main__':
    print("SDN-ML-Blockchain Performance Evaluation\n")
    
    # Try to evaluate from actual data
    import os
    if os.path.exists('predictions.csv') and os.path.exists('labels.csv'):
        metrics = evaluate_model_from_csv('predictions.csv', 'labels.csv')
    else:
        print("No prediction data found. Generating sample evaluation...\n")
        metrics = generate_sample_evaluation()
