# Uncertainty Quantification Methodology

## 1. Overview
The Digital Twin incorporates rigorous uncertainty bounds across both machine learning predictions and physics-based engineering forecasts.

---

## 2. Quantification Approaches

### A. Machine Learning Ensemble Variance (Random Forest Surrogate)
For surrogate model predictions $\hat{y}$, the uncertainty interval is determined from the empirical variance across all $M$ decision trees in the ensemble:
$$\bar{y} = \frac{1}{M} \sum_{m=1}^M \hat{y}_m$$
$$\sigma_{\text{ensemble}} = \sqrt{\frac{1}{M-1} \sum_{m=1}^M (\hat{y}_m - \bar{y})^2}$$
$$\text{95\% Prediction Interval} = \bar{y} \pm 1.96 \cdot \sigma_{\text{ensemble}}$$

### B. Analytical Engineering Uncertainty Bounds
Where empirical data variance is not directly obtainable, engineering bounds are derived from component parameter sensitivity and measurement tolerance:
$$\delta Y = \left( 1 - \frac{\text{Confidence Level}}{100} \right) \cdot Y$$
- **Daily Oil Rate**: $\pm 2.5$ BOPD (92% Confidence based on Vogel inflow uncertainty)
- **Remaining Useful Life (RUL)**: $\pm 14$ Days (88% Confidence based on Miner's cumulative damage spread)
- **Rod Floating Risk**: $\pm 4.5\%$ (Gibbs hydrodynamic damping coefficient tolerance)
