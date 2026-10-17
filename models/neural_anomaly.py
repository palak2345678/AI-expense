import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier

class NeuralAnomalyDetector:
    """
    Artificial Neural Network & Machine Learning Anomaly Detection Engine.
    Provides unsupervised pattern recognition to detect subtle multivariate expense frauds.
    """
    def __init__(self):
        self.scaler = StandardScaler()
        self.iso_forest = IsolationForest(contamination=0.15, random_state=42)
        self.ann_classifier = MLPClassifier(hidden_layer_sizes=(16, 8), max_iter=500, random_state=42)
        self.is_fitted = False

    def _extract_features(self, df):
        """Extracts and formats numeric feature matrix X."""
        features = df[['Amount', 'Amount_Role_Ratio', 'Amount_Cat_Ratio', 'Is_Weekend', 'Submission_Hour', 'Has_Receipt']].copy()
        return features

    def fit(self, df):
        """Trains scaler, IsolationForest, and MLP Neural Network on dataset."""
        X = self._extract_features(df)
        X_scaled = self.scaler.fit_transform(X)
        
        # Fit unsupervised Isolation Forest
        self.iso_forest.fit(X_scaled)
        
        # Fit supervised MLP Neural Net if ground truth Is_Fraud exists
        if 'Is_Fraud' in df.columns:
            y = df['Is_Fraud']
            self.ann_classifier.fit(X_scaled, y)
            
        self.is_fitted = True

    def predict_anomaly_score(self, df_sample):
        """
        Computes Neural Anomaly Score scaled from 0% (normal) to 100% (extreme anomaly).
        """
        if not self.is_fitted:
            raise ValueError("Neural Anomaly Model is not fitted yet.")

        X = self._extract_features(df_sample)
        X_scaled = self.scaler.transform(X)

        # Isolation Forest anomaly decision function score
        raw_scores = self.iso_forest.decision_function(X_scaled)
        
        # Invert & normalize to 0-100 scale (lower decision function = more anomalous)
        # Typical raw scores range from -0.3 to 0.3
        norm_scores = np.clip((0.25 - raw_scores) / 0.5, 0.0, 1.0) * 100.0
        
        # Predict probability from MLP Neural Network
        if hasattr(self.ann_classifier, "classes_"):
            ann_probs = self.ann_classifier.predict_proba(X_scaled)[:, 1] * 100.0
            # Blend Unsupervised Isolation Forest (40%) + Supervised MLP Neural Network (60%)
            hybrid_neural_scores = 0.4 * norm_scores + 0.6 * ann_probs
        else:
            hybrid_neural_scores = norm_scores

        return np.round(hybrid_neural_scores, 2)

if __name__ == "__main__":
    df = pd.read_csv("C:/Users/palak/.gemini/antigravity/scratch/expense_fraud_detection/dataset/synthetic_expenses.csv")
    detector = NeuralAnomalyDetector()
    detector.fit(df)
    scores = detector.predict_anomaly_score(df.head(5))
    print(f"Sample Neural Anomaly Scores: {scores}")
