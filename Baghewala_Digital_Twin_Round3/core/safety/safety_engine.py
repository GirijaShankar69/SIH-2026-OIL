"""
Safety Constraint Engine for Autonomous VFD Control.
Ensures AI recommendations do not violate engineering safety limits.
"""
from typing import Dict, Any

class SafetyConstraintEngine:
    def __init__(self):
        # Operational limits for Baghewala SRP units
        self.max_spm = 8.5
        self.min_spm = 2.0
        self.max_rod_load_lbs = 28000.0
        self.max_impact_shock_lbs = 1500.0
        self.min_pump_fillage = 0.60
        self.max_unsetting_risk = 0.50

    def evaluate_action(self, recommended_spm: float, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a recommended SPM against safety constraints.
        Returns:
            status: 'RECOMMENDED', 'ENGINEER_APPROVAL_REQUIRED', or 'BLOCKED'
            safe_spm: The constrained SPM to actually apply.
            reasons: List of reasons for blocking or requiring approval.
        """
        reasons = []
        status = 'RECOMMENDED'
        safe_spm = recommended_spm

        # 1. Hard Limits on SPM
        if recommended_spm > self.max_spm:
            reasons.append(f"Requested SPM ({recommended_spm:.1f}) exceeds mechanical limit ({self.max_spm}). Blocked.")
            safe_spm = self.max_spm
            status = 'BLOCKED'
        
        if recommended_spm < self.min_spm:
            reasons.append(f"Requested SPM ({recommended_spm:.1f}) is below minimum limit ({self.min_spm}). Blocked.")
            safe_spm = self.min_spm
            status = 'BLOCKED'

        # 2. Hard Limits on Rod Loading (from physics simulation)
        if "srp_dynamics" in current_state:
            dyn = current_state["srp_dynamics"]
            if dyn.get("pprl_lbs", 0) > self.max_rod_load_lbs:
                reasons.append(f"Peak Polished Rod Load ({dyn['pprl_lbs']:.0f} lbs) exceeds safety limit. VFD increase blocked.")
                if recommended_spm >= current_state.get("operating_spm", recommended_spm):
                    safe_spm = max(self.min_spm, current_state.get("operating_spm", recommended_spm) - 0.5)
                    status = 'BLOCKED'

        # 3. Hard Limits on Impact Shock (Rod Floating)
        impact_shock = current_state.get("impact_shock_lbs", 0)
        if impact_shock > self.max_impact_shock_lbs:
            reasons.append(f"Impact Shock ({impact_shock:.0f} lbs) exceeds fatigue safety limit. VFD increase blocked.")
            if recommended_spm >= current_state.get("operating_spm", recommended_spm):
                safe_spm = max(self.min_spm, current_state.get("operating_spm", recommended_spm) - 1.0)
                status = 'BLOCKED'

        # 4. Engineer Approval (Soft Limits)
        unsetting_risk = current_state.get("unsetting_data", {}).get("unsetting_probability_pct", 0) / 100.0
        if unsetting_risk > self.max_unsetting_risk:
            if status != 'BLOCKED':
                reasons.append(f"High pump unsetting risk ({unsetting_risk*100:.1f}%). Requires Engineer Approval to proceed.")
                status = 'ENGINEER_APPROVAL_REQUIRED'
                # Safe SPM remains the recommended, but needs human click
                
        # 5. Low Fillage (Fluid Pound risk)
        if current_state.get("pump_fillage", 1.0) < self.min_pump_fillage:
            if recommended_spm >= current_state.get("operating_spm", recommended_spm):
                reasons.append("Low pump fillage detected (Fluid Pound). Increasing SPM requires Engineer Approval.")
                if status != 'BLOCKED':
                    status = 'ENGINEER_APPROVAL_REQUIRED'

        if not reasons:
            reasons.append("Operating within safe artificial-lift envelope.")

        return {
            "status": status,
            "recommended_spm": recommended_spm,
            "safe_spm": safe_spm,
            "reasons": reasons
        }

baghewala_safety = SafetyConstraintEngine()
