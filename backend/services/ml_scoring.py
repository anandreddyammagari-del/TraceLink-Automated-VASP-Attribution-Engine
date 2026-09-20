import os
import logging
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, GradientBoostingRegressor

logger = logging.getLogger(__name__)

FEATURE_NAMES = [
    "hop_count",
    "volume_ratio",
    "time_delta_hours",
    "mixer_hops",
    "peel_layer_depth",
    "is_known_cluster",
    "anomaly_score"
]

class MLConfidenceEngine:
    """
    Machine Learning Attribution Confidence Engine.
    Combines Isolation Forest anomaly detection for smurfing/structuring patterns
    with a calibrated Gradient Boosted Trees Regressor (scikit-learn / XGBoost architecture)
    to output an evidentiary confidence score (0-100) and statutory rationale factors.
    """
    def __init__(self):
        self.anomaly_detector: Optional[IsolationForest] = None
        self.regressor: Optional[GradientBoostingRegressor] = None
        self._is_trained = False
        self._initialize_and_train_models()

    def _initialize_and_train_models(self):
        """Train or calibrate the models using packaged forensic baseline datasets."""
        # 1. Train Isolation Forest on structuring / smurfing baselines
        # Features for anomaly: [amount_eth, delta_seconds, output_count]
        baseline_normal = np.array([
            [15.5, 3600, 2],
            [12.0, 7200, 2],
            [8.5, 14400, 1],
            [22.0, 86400, 2],
            [5.0, 28800, 1],
            [18.2, 54000, 2]
        ])
        baseline_structuring = np.array([
            [0.99, 12, 12],   # Rapid high-output fan-out
            [0.98, 15, 10],
            [0.95, 20, 15],
            [0.99, 8, 20]
        ])
        training_samples = np.vstack([baseline_normal, baseline_structuring])

        self.anomaly_detector = IsolationForest(
            n_estimators=50,
            contamination=0.25,
            random_state=42
        )
        self.anomaly_detector.fit(training_samples)

        # 2. Calibrate Gradient Boosting Confidence Regressor
        fixture_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "infra", "fixtures", "synthetic_training_data.csv"
        )
        if os.path.exists(fixture_path):
            try:
                df = pd.read_csv(fixture_path)
                X = df[FEATURE_NAMES].values
                y = df["attribution_confidence"].values

                self.regressor = GradientBoostingRegressor(
                    n_estimators=100,
                    learning_rate=0.08,
                    max_depth=3,
                    random_state=42
                )
                self.regressor.fit(X, y)
                self._is_trained = True
                logger.info("MLConfidenceEngine: Calibrated Gradient Boosted confidence regressor successfully.")
            except Exception as e:
                logger.error(f"Failed to load training data from {fixture_path}: {e}")
                self._fallback_train()
        else:
            self._fallback_train()

    def _fallback_train(self):
        """Fallback synthetic training in case dataset is missing."""
        X_dummy = np.array([
            [1, 0.98, 1.0, 0, 0, 1, 0.1],
            [2, 0.85, 4.0, 0, 1, 1, 0.2],
            [3, 0.70, 12.0, 0, 2, 1, 0.3],
            [2, 0.80, 2.0, 1, 0, 1, 0.7],  # Mixer penalty
            [5, 0.20, 72.0, 2, 4, 0, 0.9]
        ])
        y_dummy = np.array([98.0, 90.0, 82.0, 40.0, 15.0])

        self.regressor = GradientBoostingRegressor(n_estimators=30, random_state=42)
        self.regressor.fit(X_dummy, y_dummy)
        self._is_trained = True

    def detect_structuring_anomaly(self, amount: float, delta_seconds: float, output_count: int) -> float:
        """
        Evaluate whether transfer exhibits structuring / smurfing behavior.
        Returns normalized anomaly score between 0.0 (normal) and 1.0 (highly anomalous).
        """
        if not self.anomaly_detector:
            return 0.2

        sample = np.array([[amount, delta_seconds, output_count]])
        # decision_function returns negative for anomalies
        raw_score = self.anomaly_detector.decision_function(sample)[0]
        # Normalize into 0.0 - 1.0 range
        anomaly_score = float(np.clip(0.5 - raw_score, 0.0, 1.0))
        return round(anomaly_score, 3)

    def calculate_confidence(
        self,
        hop_count: int,
        initial_volume: float,
        arriving_volume: float,
        time_delta_hours: float,
        mixer_hops: int,
        peel_layer_depth: int,
        is_known_cluster: bool,
        anomaly_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Compute end-to-end attribution confidence score (0-100), tier, and evidence breakdown.
        """
        vol_ratio = arriving_volume / initial_volume if initial_volume > 0 else 0.0
        vol_ratio = min(1.0, max(0.0, vol_ratio))

        if anomaly_score is None:
            # Default normal transfer
            anomaly_score = 0.15

        features = np.array([[
            float(hop_count),
            float(vol_ratio),
            float(time_delta_hours),
            float(mixer_hops),
            float(peel_layer_depth),
            1.0 if is_known_cluster else 0.0,
            float(anomaly_score)
        ]])

        if self.regressor and self._is_trained:
            raw_pred = float(self.regressor.predict(features)[0])
        else:
            # Deterministic rule-based calculation
            raw_pred = 100.0 - (hop_count * 5.0) - (mixer_hops * 35.0) - (peel_layer_depth * 4.0)
            if not is_known_cluster:
                raw_pred -= 25.0
            raw_pred = raw_pred * vol_ratio

        # Forensic penalties
        if not is_known_cluster:
            raw_pred -= 20.0

        # Heavy deterministic penalty for mixer involvement
        if mixer_hops > 0:
            raw_pred = min(raw_pred, 45.0)

        # Clamping to valid forensic range 0.0 - 99.9%
        confidence_score = round(float(np.clip(raw_pred, 5.0, 99.5)), 1)

        # Classification Tier
        if confidence_score >= 80.0:
            tier = "HIGH"
        elif confidence_score >= 50.0:
            tier = "MEDIUM"
        else:
            tier = "LOW"

        # Construct statutory evidence breakdown
        evidence = []
        evidence.append(f"Topological Hop Distance: {hop_count} hop(s) to target VASP deposit cluster")
        evidence.append(f"Volume Conservation Ratio: {round(vol_ratio * 100, 1)}% ({arriving_volume} of {initial_volume} ETH preserved)")

        if is_known_cluster:
            evidence.append("Attributed to verified FIU-registered VASP nodal infrastructure")
        else:
            evidence.append("Target is an unverified or secondary cluster (confidence penalized)")

        if mixer_hops > 0:
            evidence.append(f"CRITICAL OBFUSCATION DETECTED: {mixer_hops} mixer/tumbler hops traversed (confidence heavily degraded)")
        else:
            evidence.append("Zero privacy mixer / tumbler obfuscation detected along primary path")

        if peel_layer_depth > 0:
            evidence.append(f"Structured Layering: {peel_layer_depth} peel intermediary steps identified")

        if anomaly_score > 0.6:
            evidence.append(f"Structuring Warning: Smurfing anomaly detected (Score: {anomaly_score})")

        return {
            "confidence_score": confidence_score,
            "confidence_tier": tier,
            "features_evaluated": {
                "hop_count": hop_count,
                "volume_ratio": round(vol_ratio, 3),
                "time_delta_hours": time_delta_hours,
                "mixer_hops": mixer_hops,
                "peel_layer_depth": peel_layer_depth,
                "is_known_cluster": is_known_cluster,
                "anomaly_score": anomaly_score
            },
            "evidence_breakdown": evidence
        }

ml_confidence_engine = MLConfidenceEngine()
