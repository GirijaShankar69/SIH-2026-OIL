"""
Dynamometer Card AI Diagnostic and Pattern Recognition Classifier
Uses geometric Fourier shape descriptors and ML feature extraction to identify
rod floating, impact loading, fluid pound, gas interference, and valve leaks.
"""

import numpy as np
from typing import Dict, List, Tuple, Any
from sklearn.ensemble import RandomForestClassifier
from core.physics.sucker_rod_dynamics import baghewala_srp


class DynoCardAIClassifier:
    """
    AI diagnostic system for automated dynamometer card classification.
    """

    CARD_CLASSES = [
        "Normal Fillage (Optimal)",
        "Severe Rod Floating & Impact Loading",
        "Fluid Pound (Underfilled)",
        "Gas Interference",
        "Unanchored Tubing",
        "Traveling Valve Leak",
        "Standing Valve Leak",
        "Pump Off / High Viscous Friction"
    ]

    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=60, random_state=42)
        self._train_surrogate_model()

    def extract_features(self, position_in: np.ndarray, load_lbs: np.ndarray) -> np.ndarray:
        """
        Extracts 12 discriminative geometric, frequency, and load distribution features
        from normalized dynamometer card coordinates.
        """
        # Normalize position to [0, 1] and load to [0, 1]
        stroke = np.maximum(np.max(position_in) - np.min(position_in), 1e-3)
        pos_norm = (position_in - np.min(position_in)) / stroke
        
        load_range = np.maximum(np.max(load_lbs) - np.min(load_lbs), 1e-3)
        load_norm = (load_lbs - np.min(load_lbs)) / load_range

        # 1. Card normalized area (Work / Bounding Box)
        # Bounding box is 1.0 x 1.0 = 1.0
        # Polygon area via Shoelace formula
        area = 0.5 * np.abs(np.dot(pos_norm, np.roll(load_norm, 1)) - np.dot(load_norm, np.roll(pos_norm, 1)))

        # 2. Aspect Ratio / Load span ratio
        pprl = np.max(load_lbs)
        mprl = np.min(load_lbs)
        load_ratio = mprl / np.maximum(pprl, 1.0)

        # 3. Centroid coordinates (X_c, Y_c)
        x_c = np.mean(pos_norm)
        y_c = np.mean(load_norm)

        # 4. Downstroke minimum load dip (detects rod floating carrier bar separation)
        n = len(load_lbs)
        downstroke_load = load_lbs[n//2:]
        min_downstroke_norm = (np.min(downstroke_load) - np.min(load_lbs)) / load_range

        # 5. Bottom of stroke impact spike detection
        # Derivative of load near end of downstroke
        bos_load = load_lbs[int(n * 0.8):]
        load_diff = np.diff(bos_load)
        max_impact_spike = np.max(load_diff) if len(load_diff) > 0 else 0.0
        spike_norm = max_impact_spike / load_range

        # 6. Card Tilt / Skewness (detects unanchored tubing hysteresis)
        cov_matrix = np.cov(pos_norm, load_norm)
        card_tilt = cov_matrix[0, 1] / np.maximum(cov_matrix[0, 0], 1e-4)

        # 7. Fourier shape harmonics (first 4 Fourier coefficients of closed contour)
        z = pos_norm + 1j * load_norm
        fft_coeffs = np.fft.fft(z)
        fourier_mag1 = np.abs(fft_coeffs[1]) / np.maximum(np.abs(fft_coeffs[0]), 1e-3)
        fourier_mag2 = np.abs(fft_coeffs[2]) / np.maximum(np.abs(fft_coeffs[0]), 1e-3)
        fourier_mag3 = np.abs(fft_coeffs[3]) / np.maximum(np.abs(fft_coeffs[0]), 1e-3)

        # 8. Upstroke slope vs Downstroke slope
        upstroke_load = load_lbs[:n//2]
        up_slope = (upstroke_load[-1] - upstroke_load[0]) / load_range

        return np.array([
            area, load_ratio, x_c, y_c, min_downstroke_norm,
            spike_norm, card_tilt, fourier_mag1, fourier_mag2,
            fourier_mag3, up_slope, pprl / 25000.0
        ])

    def _train_surrogate_model(self):
        """Generates synthetic physics cards for training the classifier."""
        X_train = []
        y_train = []

        fault_map = {
            "normal": 0,
            "rod_floating": 1,
            "fluid_pound": 2,
            "gas_interference": 3,
            "unanchored_tubing": 4,
            "valve_leak": 5,
            "standing_leak": 6,
            "pump_off": 7
        }

        # Generate diverse conditions
        for temp_c in [48.0, 70.0, 110.0, 160.0, 210.0]:
            for visc in [18.0, 80.0, 250.0, 800.0, 2200.0]:
                for spm in [3.5, 5.0, 6.5, 8.0]:
                    # 1. Normal
                    res_norm = baghewala_srp.solve_wave_equation(temp_c, visc, 22.0, spm=spm, pump_fillage=0.95)
                    X_train.append(self.extract_features(res_norm["surface_position_in"], res_norm["surface_load_lbs"]))
                    # Label based on physics output
                    if res_norm["is_rod_floating"]:
                        y_train.append(1) # Rod floating
                    else:
                        y_train.append(0) # Normal

                    # 2. Severe Rod Floating (High visc, high SPM)
                    res_float = baghewala_srp.solve_wave_equation(46.0, 3200.0, 15.0, spm=8.5, pump_fillage=0.90)
                    X_train.append(self.extract_features(res_float["surface_position_in"], res_float["surface_load_lbs"]))
                    y_train.append(1)

                    # 3. Fluid Pound
                    res_pound = baghewala_srp.solve_wave_equation(temp_c, visc, 20.0, spm=spm, fault_type="fluid_pound")
                    X_train.append(self.extract_features(res_pound["surface_position_in"], res_pound["surface_load_lbs"]))
                    y_train.append(2)

                    # 4. Gas Interference
                    res_gas = baghewala_srp.solve_wave_equation(temp_c, visc, 20.0, spm=spm, fault_type="gas_interference")
                    X_train.append(self.extract_features(res_gas["surface_position_in"], res_gas["surface_load_lbs"]))
                    y_train.append(3)

                    # 5. Unanchored Tubing
                    res_tubing = baghewala_srp.solve_wave_equation(temp_c, visc, 20.0, spm=spm, fault_type="unanchored_tubing")
                    X_train.append(self.extract_features(res_tubing["surface_position_in"], res_tubing["surface_load_lbs"]))
                    y_train.append(4)

                    # 6. Valve Leak
                    res_leak = baghewala_srp.solve_wave_equation(temp_c, visc, 20.0, spm=spm, fault_type="valve_leak")
                    X_train.append(self.extract_features(res_leak["surface_position_in"], res_leak["surface_load_lbs"]))
                    y_train.append(5)

        self.model.fit(np.array(X_train), np.array(y_train))

    def classify_card(self, position_in: np.ndarray, load_lbs: np.ndarray, 
                      is_phys_floating: bool = False, 
                      floating_risk: float = 0.0) -> Dict[str, Any]:
        """
        Classifies a surface dynamometer card and returns predicted diagnosis,
        confidence, and actionable engineering recommendations.
        """
        feat = self.extract_features(position_in, load_lbs).reshape(1, -1)
        probs = self.model.predict_proba(feat)[0]
        
        # Override with physical rod floating indicator if physics engine detects severe drag
        if is_phys_floating or floating_risk > 0.85:
            pred_idx = 1
            confidence = float(np.clip(0.85 + 0.15 * (floating_risk - 0.85), 0.85, 0.99))
        else:
            pred_idx = int(np.argmax(probs))
            # Map index safely
            classes_in_model = self.model.classes_
            class_label_idx = classes_in_model[pred_idx] if pred_idx < len(classes_in_model) else 0
            pred_idx = class_label_idx
            confidence = float(np.max(probs))

        pred_name = self.CARD_CLASSES[pred_idx]

        # Recommendation logic
        recommendations = {
            0: "Operating within optimal parameters. Maintain current VFD frequency and continuous thermal monitoring.",
            1: "CRITICAL: Severe Rod Floating & Impact Shock Detected! Immediate Action: Reduce VFD pumping speed by 1.5 - 2.5 SPM to allow rod fall, or apply hot-oil/steam casing flush to lower fluid viscosity.",
            2: "Underfilled Pump / Fluid Pound: Reduce SPM by 1.0 SPM to allow pump barrel to fill completely (> 85% fillage) and eliminate bottom-hole impact shock.",
            3: "Gas Interference Detected: Vent casing-tubing annulus gas or increase pump submergence depth.",
            4: "Unanchored Tubing Movement: Install or reset mechanical tubing anchor to prevent cyclic stroke loss and tubing-casing wear.",
            5: "Traveling Valve Leak: Plunger / ball & seat assembly worn. Schedule downhole pump inspection.",
            6: "Standing Valve Leak: Standing valve ball not seating cleanly. Flush pump or inspect for scale/debris.",
            7: "High Viscous Drag / Over-pumped: Thermal effect from CSS is decaying. Lower SPM and prepare for next CSS cycle."
        }

        severity_levels = {
            0: "OPTIMAL",
            1: "CRITICAL - HIGH IMPACT SHOCK",
            2: "WARNING - CYCLIC POUNDING",
            3: "MODERATE",
            4: "WARNING",
            5: "MAINTENANCE REQUIRED",
            6: "MAINTENANCE REQUIRED",
            7: "WARNING"
        }

        return {
            "diagnosis": pred_name,
            "diagnosis_id": pred_idx,
            "confidence_pct": round(confidence * 100.0, 1),
            "severity": severity_levels.get(pred_idx, "NORMAL"),
            "recommendation": recommendations.get(pred_idx, "Monitor system."),
            "features": {
                "card_area_norm": float(feat[0, 0]),
                "downstroke_min_load_norm": float(feat[0, 4]),
                "impact_spike_norm": float(feat[0, 5]),
                "card_tilt": float(feat[0, 6])
            }
        }


# Global classifier instance
baghewala_card_classifier = DynoCardAIClassifier()
