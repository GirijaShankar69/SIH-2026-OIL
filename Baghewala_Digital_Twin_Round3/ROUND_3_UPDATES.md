# Round 3 Engineering Upgrades & Technical Summary

## Baghewala Heavy Oil Field Well-to-Surface Digital Twin

This document summarizes the Round 3 engineering additions, enhancements, and validation frameworks incorporated into the AI-Enabled Digital Twin platform for Oil India Limited (OIL).

---

### Key Upgrades Overview

| Category | Round 2 State | Round 3 Upgrade |
|---|---|---|
| **Model Validation** | Qualitative comparison | **Formal Validation Framework** (`core/validation/validation_metrics.py`) calculating MAE, RMSE, MAPE, R², Confusion Matrices, and residual analysis. |
| **AI Classifier** | 6 of 8 classes trained | **Full 8-Class AI Classifier** trained on stratified wave dynamics dataset with exact train/test split. |
| **Surrogate Model** | Physics analytical wrapper | **True Multi-Output Random Forest Regressor** + Physics Analytical Accelerator. Fast inference (0.15 ms) with ensemble variance uncertainty. |
| **Safety Engine** | Open-loop recommendations | **Safety Constraint Engine** (`core/safety/safety_engine.py`) with hard/soft mechanical limits and 3-tier status (Recommended / Engineer Approval / Blocked). |
| **Prescriptive Maintenance** | Predictive RUL | **Prescriptive Decision Engine**: Risk $\rightarrow$ Mechanism $\rightarrow$ Action $\rightarrow$ Expected Effect. |
| **Climatic Coupling** | Fixed ambient temperature | **Dynamic Wellbore Heat Loss**: $Q_{loss} = U \cdot A \cdot (T_{fluid} - T_{ambient})$ coupled to surface fluid viscosity and SRP loading. |
| **What-If Scenario Lab** | Single cycle optimizer | **Interactive What-If Experimentation Lab** comparing Scenario A vs Proposed Scenario B with economic net profit proxies. |
| **Sensitivity & Uncertainty** | Deterministic outputs | **Finite-Difference Sensitivity Analysis** + 95% Confidence Intervals on all key predictions. |
| **Model Health & Drift** | Unmonitored | **Telemetry Data Quality Scorer** + Physics/AI Drift Tracker with recalibration indicators. |
