"""
Validation Metrics and Uncertainty Framework
Provides mathematical validation for AI models and physics predictions.
"""
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, precision_recall_fscore_support, confusion_matrix
from typing import Dict, Any, List

class ValidationFramework:
    @staticmethod
    def compute_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculates standard regression metrics for physics and surrogate models."""
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        
        # Avoid division by zero in MAPE
        mask = y_true != 0
        if np.any(mask):
            mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0
        else:
            mape = 0.0
            
        # R2 score
        if len(y_true) > 1 and np.var(y_true) > 0:
            r2 = r2_score(y_true, y_pred)
        else:
            r2 = 1.0 if np.allclose(y_true, y_pred) else 0.0
        
        return {
            "MAE": float(mae),
            "RMSE": float(rmse),
            "MAPE": float(mape),
            "R2": float(r2)
        }

    @staticmethod
    def compute_classification_metrics(y_true: np.ndarray, y_pred: np.ndarray, labels: List[int] = None) -> Dict[str, Any]:
        """Calculates standard classification metrics for the AI diagnosis model."""
        accuracy = accuracy_score(y_true, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average=None, labels=labels, zero_division=0)
        
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        
        return {
            "Accuracy": float(accuracy),
            "Precision_Macro": float(np.mean(precision)),
            "Recall_Macro": float(np.mean(recall)),
            "F1_Macro": float(np.mean(f1)),
            "Class_Precision": precision.tolist(),
            "Class_Recall": recall.tolist(),
            "Class_F1": f1.tolist(),
            "Confusion_Matrix": cm.tolist()
        }
        
    @staticmethod
    def estimate_ensemble_uncertainty(predictions: np.ndarray) -> float:
        """
        Estimates uncertainty using standard deviation of ensemble predictions.
        (e.g. standard deviation across Random Forest trees).
        Returns +/- uncertainty bound.
        """
        # Assume 1.96 standard deviations for 95% confidence interval
        std_dev = np.std(predictions, axis=0)
        if np.isscalar(std_dev):
            return float(1.96 * std_dev)
        return float(np.mean(1.96 * std_dev))

    @staticmethod
    def estimate_engineering_uncertainty(value: float, confidence_pct: float) -> float:
        """
        Calculates an engineering uncertainty range based on a declared confidence level.
        E.g., if confidence is 90%, the uncertainty is 10% of the value.
        """
        uncertainty_pct = 100.0 - confidence_pct
        return float(value * (uncertainty_pct / 100.0))
        
    @staticmethod
    def generate_data_quality_score(telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates data quality score based on missing values, spikes, and impossible values.
        """
        issues = []
        score = 100.0
        
        # Check for NaNs
        for key, val in telemetry.items():
            arr = np.array(val)
            if np.issubdtype(arr.dtype, np.number) and np.any(np.isnan(arr)):
                score -= 10.0
                issues.append(f"Missing values detected in {key}")
                
        # Check impossible SPM
        if "spm" in telemetry:
            arr_spm = np.array(telemetry["spm"])
            if np.any(arr_spm > 200) or np.any(arr_spm < 0):
                score -= 15.0
                issues.append("Impossible SPM detected (out of bounds)")
                
        # Check negative temperatures or pressures
        for key in ["temperature_c", "pressure_bar"]:
            if key in telemetry:
                arr = np.array(telemetry[key])
                if np.any(arr < -100): # Allow slightly negative Celsius if needed, but not ridiculous
                    score -= 20.0
                    issues.append(f"Invalid negative values in {key}")
                
        score = max(0.0, score)
        return {
            "score": score,
            "status": "Excellent" if score >= 95 else "Degraded" if score >= 75 else "Poor",
            "issues": issues
        }

baghewala_validation = ValidationFramework()
