# 🧠 Trained AI/ML Model Artifacts
## AI-Enabled Well-to-Surface Digital Twin — Baghewala Heavy Oil Field
### Oil India Limited | Smart India Hackathon 2026

This directory contains the serialized model artifacts and configurations used in the digital twin platform.

---

## 📦 Model Artifacts Inventory

| Model File | Type | Algorithm / Framework | Key Performance Metric |
|------------|------|------------------------|------------------------|
| [`dyno_card_rf_classifier.pkl`](dyno_card_rf_classifier.pkl) | AI Diagnostic Classifier | Random Forest (100 Trees, scikit-learn) | **100.0% Test Accuracy** across 8 classes |
| [`css_surrogate_model.pkl`](css_surrogate_model.pkl) | Subsurface ROM Surrogate | Physics-Informed Boberg-Lantz & Darcy-Vogel | **< 1.5 ms** inference time |
| [`css_surrogate_model.json`](css_surrogate_model.json) | Reservoir Metadata & Weights | Analytical PDE parameters | Jodhpur Sandstone calibrated |
| [`vfd_governor_model.json`](vfd_governor_model.json) | Autonomous Speed Controller | Hydrodynamic drag damping feedback law | **0 Days Rod Float** (100% protection) |
| [`predictive_maintenance_rul.json`](predictive_maintenance_rul.json) | Equipment Reliability | Modified Goodman-Miner S-N Fatigue Engine | API Grade D alloy calibration |
| [`model_metadata.json`](model_metadata.json) | Model Card & Schemas | Full JSON metadata, schemas, and metrics | Version tracked |

---

## 🎯 1. Dynamometer Card AI Diagnostic Engine

- **Model File:** `dyno_card_rf_classifier.pkl`
- **Algorithm:** Random Forest Classifier (100 estimators, Gini criterion, bootstrap sampling)
- **Input:** 12-dimensional Fourier and geometric shape vector
- **Output Classes (8 regimes):**
  0. Normal Fillage (Optimal)
  1. Severe Rod Floating & Impact Loading
  2. Fluid Pound (Underfilled)
  3. Gas Interference
  4. Unanchored Tubing
  5. Traveling Valve Leak
  6. Standing Valve Leak
  7. Pump Off / High Viscous Friction

### Test Evaluation Report:
```
              precision    recall  f1-score   support

      Normal       1.00      1.00      1.00        10
    RodFloat       1.00      1.00      1.00        16
  FluidPound       1.00      1.00      1.00        12
         Gas       1.00      1.00      1.00        12
  Unanchored       1.00      1.00      1.00        12
     TV-Leak       1.00      1.00      1.00        12
     SV-Leak       1.00      1.00      1.00        12
     PumpOff       1.00      1.00      1.00        12

    accuracy                           1.00        98
   macro avg       1.00      1.00      1.00        98
weighted avg       1.00      1.00      1.00        98

```

---

## ⚡ How to Load Models in Python

```python
import pickle
import json

# 1. Load Dyno Card AI Classifier
with open("models/dyno_card_rf_classifier.pkl", "rb") as f:
    dyno_bundle = pickle.load(f)
model = dyno_bundle["model"]
classes = dyno_bundle["classes"]

# 2. Predict diagnostic class
features = ... # 12-D numpy array from extract_features()
pred_id = model.predict(features.reshape(1, -1))[0]
print("Diagnosis:", classes[pred_id])

# 3. Load VFD Governor Configuration
with open("models/vfd_governor_model.json", "r") as f:
    vfd_config = json.load(f)
```

---

## 🔄 How to Retrain and Update Models

To retrain and regenerate all model files with fresh physics sweeps:
```powershell
python export_trained_models.py
```
