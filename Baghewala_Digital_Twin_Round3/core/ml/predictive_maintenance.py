"""
Predictive Maintenance and Equipment Reliability Module for Baghewala Field
Implements Goodman-Miner cyclic fatigue accumulation, sucker rod Remaining Useful Life (RUL),
pump unsetting probability, and asphaltene deposition forecasting.
"""

import numpy as np
from typing import Dict, List, Tuple, Any
from core.physics.sucker_rod_dynamics import SRPConfiguration


class PredictiveMaintenanceEngine:
    """
    Predictive analytics for equipment reliability and failure prevention.
    """

    def __init__(self, config: SRPConfiguration = None):
        self.config = config or SRPConfiguration()

    def estimate_rod_fatigue_and_rul(self, 
                                     daily_spm_history: np.ndarray, 
                                     daily_sigma_max_psi: np.ndarray, 
                                     daily_sigma_min_psi: np.ndarray,
                                     daily_impact_lbs: np.ndarray,
                                     cumulative_days_in_service: int = 180) -> Dict[str, Any]:
        """
        Calculates cumulative Miner's rule fatigue damage: D = sum(n_i / N_i)
        where N_i is the number of cycles to failure from S-N curve with impact penalty.
        """
        total_damage = 0.0
        n_days = len(daily_spm_history)

        # Baseline S-N curve parameters for API Grade D Rods (in sour/heavy oil environment)
        # log10(N) = A - B * (Sigma_equivalent / S_ult)
        # S_ult = 115,000 psi
        s_ult = 115000.0

        for i in range(n_days):
            spm = daily_spm_history[i]
            s_max = daily_sigma_max_psi[i]
            s_min = daily_sigma_min_psi[i]
            impact = daily_impact_lbs[i]

            # Daily cycle count: n_i = SPM * 1440
            n_cycles_day = spm * 1440.0

            # Equivalent stress amplitude (Goodman relation)
            s_range = s_max - s_min
            s_mean = (s_max + s_min) / 2.0
            s_eq = (s_range / 2.0) / (1.0 - (s_mean / s_ult))

            # Impact shock penalty (impact load creates localized micro-yielding at thread roots)
            impact_penalty = 1.0 + (impact / 3000.0) ** 1.5

            # Cycles to failure N_i
            # Basquin's equation: N = C * (s_eq * penalty)^(-m)
            # Grade D steel: C ~ 1e38, m ~ 6.8
            stress_ksi = np.maximum((s_eq * impact_penalty) / 1000.0, 10.0)
            if stress_ksi < 32.0:
                # Below endurance limit
                n_failure = 1e8
            else:
                n_failure = 10.0 ** (14.2 - 4.6 * np.log10(stress_ksi))
                n_failure = np.clip(n_failure, 5e4, 1e8)

            daily_damage = n_cycles_day / n_failure
            total_damage += daily_damage

        # Adjust for total historical days in service
        extrapolated_cum_damage = total_damage * (cumulative_days_in_service / np.maximum(n_days, 1))
        extrapolated_cum_damage = np.clip(extrapolated_cum_damage, 0.01, 1.5)

        # Remaining Useful Life (RUL) in days
        avg_daily_damage = np.mean(total_damage / np.maximum(n_days, 1))
        remaining_damage_capacity = np.maximum(1.0 - extrapolated_cum_damage, 0.0)
        rul_days = remaining_damage_capacity / np.maximum(avg_daily_damage, 1e-6)
        rul_days = int(np.clip(rul_days, 0, 750))

        # Health score (0 to 100%)
        health_score_pct = float(np.clip((1.0 - extrapolated_cum_damage) * 100.0, 0.0, 100.0))

        return {
            "cumulative_fatigue_damage": float(extrapolated_cum_damage),
            "rod_health_score_pct": round(health_score_pct, 1),
            "remaining_useful_life_days": rul_days,
            "rul_cycles_remaining": int(rul_days * 5.5 * 1440),
            "fatigue_risk_level": "HIGH RISK" if health_score_pct < 35.0 else "MODERATE" if health_score_pct < 70.0 else "HEALTHY",
            "estimated_replacement_date_days": rul_days
        }

    def compute_pump_unsetting_probability(self, 
                                           impact_shock_lbs: float, 
                                           rod_floating_risk: float, 
                                           days_since_steam: int) -> Dict[str, Any]:
        """
        Calculates the probability of downhole insert pump unsetting from mechanical seating nipple.
        Mechanical hold-down friction capacity: ~ 3500 - 4500 lbs.
        Severe downstroke impact rebound creates upward shock pulling pump out of seat.
        """
        hold_down_capacity_lbs = 4200.0
        
        # Upward shock wave transmission to pump barrel
        upward_shock_lbs = impact_shock_lbs * 0.45
        
        # Risk ratio
        unsetting_ratio = upward_shock_lbs / hold_down_capacity_lbs
        
        # Sigmoid probability
        prob = 1.0 / (1.0 + np.exp(-5.0 * (unsetting_ratio - 0.75)))
        prob = float(np.clip(prob, 0.01, 0.98))

        status = "CRITICAL" if prob > 0.65 else "WARNING" if prob > 0.30 else "SECURE"

        return {
            "unsetting_probability": round(prob, 3),
            "unsetting_probability_pct": round(prob * 100.0, 1),
            "status": status,
            "upward_shock_load_lbs": round(upward_shock_lbs, 1),
            "hold_down_rating_lbs": hold_down_capacity_lbs,
            "alert": "DANGER: High risk of pump unseating! Reduce stroke speed immediately." if prob > 0.65 else "Hold-down seating secure."
        }

    def generate_prescriptive_actions(self, 
                                      rul_data: Dict[str, Any], 
                                      unsetting_data: Dict[str, Any], 
                                      asphaltene_data: Dict[str, Any],
                                      current_spm: float,
                                      is_rod_floating: bool) -> List[Dict[str, str]]:
        """
        Generates structured prescriptive maintenance recommendations:
        Risk -> Failure Mechanism -> Recommended Action -> Expected Effect.
        """
        actions = []

        # 1. High Rod Fatigue
        if rul_data["rod_health_score_pct"] < 50.0 or rul_data["remaining_useful_life_days"] < 90:
            actions.append({
                "risk": "High Rod String Fatigue Damage",
                "mechanism": f"Cumulative cyclic loading with Miner's damage = {rul_data['cumulative_fatigue_damage']:.2f}",
                "recommended_action": f"Trim pumping speed by 1.0 SPM (to {max(2.5, current_spm - 1.0):.1f} SPM) to lower peak cyclic stress.",
                "expected_effect": f"Reduces daily fatigue rate by ~35% and extends RUL by +{int(rul_data['remaining_useful_life_days'] * 0.4)} days."
            })

        # 2. Rod Floating
        if is_rod_floating:
            actions.append({
                "risk": "Severe Rod Floating & Impact Shock",
                "mechanism": "Hydrodynamic viscous drag exceeds rod buoyant weight on downstroke, causing carrier bar separation.",
                "recommended_action": f"Reduce VFD speed to {max(2.5, current_spm - 1.5):.1f} SPM or apply annular hot water flush.",
                "expected_effect": "Restores solid carrier bar contact and eliminates destructive +2,000 lbs bottom-hole shock waves."
            })

        # 3. Pump Unsetting
        if unsetting_data["unsetting_probability_pct"] > 35.0:
            actions.append({
                "risk": "Insert Pump Hold-Down Unseating",
                "mechanism": f"Upward shock load ({unsetting_data['upward_shock_load_lbs']} lbs) approaching mechanical hold-down capacity.",
                "recommended_action": "Throttle SPM and inspect mechanical seating cup / spring tension during next well service.",
                "expected_effect": "Prevents catastrophic pump unseating and eliminates un-scheduled workover rig pull."
            })

        # 4. Asphaltene Deposition
        if asphaltene_data.get("asphaltene_deposition_risk_index", 0) > 0.40:
            actions.append({
                "risk": "Near-Wellbore / Tubing Asphaltene Precipitation",
                "mechanism": f"Fluid temperature cooled below onset envelope (CII = {asphaltene_data.get('colloidal_instability_index', 0.95):.2f}).",
                "recommended_action": "Schedule continuous xylene/toluene aromatic solvent wash or next CSS steam cycle initiation.",
                "expected_effect": "Dissolves organic pore plugging, recovering 15-25% inflow productivity index."
            })

        if not actions:
            actions.append({
                "risk": "Normal / Low Risk",
                "mechanism": "All operational parameters within API Spec 11L limits.",
                "recommended_action": "Maintain current operating parameters and continuous SCADA telemetry monitoring.",
                "expected_effect": "Optimal steady-state heavy oil production."
            })

        return actions


# Global instance
baghewala_maintenance = PredictiveMaintenanceEngine()
