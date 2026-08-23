"""
Digital Twin Management and Autonomous Closed-Loop VFD Controller
Maintains real-time synchronized state of field assets and executes real-time AI control.
"""

import numpy as np
from typing import Dict, List, Any, Optional
from core.physics.thermal_reservoir import CSSCycleParameters, baghewala_reservoir
from core.physics.sucker_rod_dynamics import SRPConfiguration, baghewala_srp
from core.physics.wellbore_hydraulics import baghewala_wellbore
from core.physics.fluid_rheology import baghewala_rheology
from core.ml.dyno_card_classifier import baghewala_card_classifier
from core.ml.predictive_maintenance import baghewala_maintenance
from core.data.sample_data_generator import WELLS_METADATA


class BaghewalaWellDigitalTwin:
    """
    Digital Twin instance representing a single well in Baghewala Field.
    """

    def __init__(self, well_meta: Dict[str, Any]):
        self.meta = well_meta
        self.well_id = well_meta["well_id"]
        self.current_day = well_meta["days_in_current_cycle"]
        self.cycle_number = well_meta["current_css_cycle"]
        self.current_spm = well_meta["current_spm"]
        self.stroke_length = well_meta["stroke_length_m"]
        self.autonomous_vfd_enabled = (self.well_id in ["BGW-01", "BGW-09"])

        # Cache simulation results for current cycle
        self.params = CSSCycleParameters(
            cycle_number=self.cycle_number,
            steam_volume_cwe=3600.0,
            injection_rate=250.0,
            soak_days=5.0,
            producing_days=120
        )
        self.sim_data = baghewala_reservoir.simulate_cycle(self.params)

    def get_current_state(self, day: Optional[int] = None, spm_override: Optional[float] = None) -> Dict[str, Any]:
        """
        Retrieves the complete physics and AI digital twin snapshot for a specific day in the CSS cycle.
        """
        cur_day = day if day is not None else self.current_day
        day_idx = int(np.clip(cur_day - 1, 0, len(self.sim_data["days"]) - 1))

        temp_res = float(self.sim_data["temperature_reservoir_c"][day_idx])
        temp_sf = float(self.sim_data["temperature_sandface_c"][day_idx])
        visc = float(self.sim_data["viscosity_cp"][day_idx])
        p_res = float(self.sim_data["reservoir_pressure_bar"][day_idx])
        q_oil = float(self.sim_data["oil_rate_bopd"][day_idx])
        wcut = float(self.sim_data["water_cut"][day_idx])
        cum_oil = float(self.sim_data["cum_oil_bbl"][day_idx])
        sor = float(self.sim_data["cumulative_sor"][day_idx])

        # Dynamic SPM logic
        if spm_override is not None:
            spm = spm_override
        elif self.autonomous_vfd_enabled:
            # Autonomous AI control target
            if temp_res >= 120.0:
                spm = 7.4
            elif temp_res >= 85.0:
                spm = 6.2 - 0.7 * ((120.0 - temp_res) / 35.0)
            else:
                spm = 4.2 - 0.5 * np.clip((visc - 250.0) / 1200.0, 0.0, 1.0)
        else:
            spm = self.current_spm

        # Wellbore profile
        hydraulics = baghewala_wellbore.compute_hydraulics_profile(
            sandface_temp_c=temp_sf,
            bottomhole_pressure_bar=p_res - 12.0,
            liquid_rate_m3d=q_oil / 6.2898 / (1.0 - wcut + 1e-4),
            water_cut=wcut
        )

        # SRP Wave Dynamics & Dyno Cards
        srp_res = baghewala_srp.solve_wave_equation(
            temperature_c=temp_res,
            viscosity_cp=visc,
            bottomhole_pressure_bar=p_res - 12.0,
            spm=spm,
            stroke_length_m=self.stroke_length,
            pump_fillage=0.92
        )

        # AI Dyno Card Classification
        diag = baghewala_card_classifier.classify_card(
            position_in=srp_res["surface_position_in"],
            load_lbs=srp_res["surface_load_lbs"],
            is_phys_floating=srp_res["is_rod_floating"],
            floating_risk=srp_res["rod_floating_risk_index"]
        )

        # Asphaltene risk
        asph_risk = baghewala_rheology.asphaltene_precipitation_risk(
            temperature_c=hydraulics["wellhead_temp_c"],
            pressure_bar=hydraulics["wellhead_pressure_bar"]
        )

        # Unsetting probability
        unsetting_data = baghewala_maintenance.compute_pump_unsetting_probability(
            impact_shock_lbs=srp_res["impact_shock_force_lbs"],
            rod_floating_risk=srp_res["rod_floating_risk_index"],
            days_since_steam=cur_day
        )

        return {
            "well_meta": self.meta,
            "day": cur_day,
            "reservoir_temperature_c": temp_res,
            "sandface_temperature_c": temp_sf,
            "wellhead_temperature_c": hydraulics["wellhead_temp_c"],
            "oil_viscosity_cp": visc,
            "reservoir_pressure_bar": p_res,
            "oil_rate_bopd": q_oil,
            "water_cut_pct": round(wcut * 100.0, 1),
            "cum_oil_bbl": round(cum_oil, 1),
            "sor": round(sor, 2),
            "operating_spm": round(spm, 2),
            "vfd_frequency_hz": round(spm * 8.5, 1),
            "autonomous_mode": self.autonomous_vfd_enabled,
            "motor_power_kw": round(srp_res["motor_power_kw"], 1),
            "kwh_per_bbl": round(srp_res["kwh_per_bbl"], 2),
            "pprl_lbs": round(srp_res["pprl_lbs"], 0),
            "mprl_lbs": round(srp_res["mprl_lbs"], 0),
            "rod_loading_pct": round(srp_res["rod_loading_pct"], 1),
            "rod_floating_risk_index": round(srp_res["rod_floating_risk_index"], 3),
            "is_rod_floating": srp_res["is_rod_floating"],
            "impact_shock_lbs": round(srp_res["impact_shock_force_lbs"], 0),
            "diagnosis": diag["diagnosis"],
            "diagnosis_severity": diag["severity"],
            "diagnosis_confidence": diag["confidence_pct"],
            "diagnosis_recommendation": diag["recommendation"],
            "asphaltene_risk": asph_risk,
            "unsetting_data": unsetting_data,
            "srp_dynamics": srp_res,
            "hydraulics": hydraulics
        }


class BaghewalaFieldDigitalTwin:
    """
    Field-level digital twin managing all 6 wells and field-wide optimization.
    """

    def __init__(self):
        self.wells = {w["well_id"]: BaghewalaWellDigitalTwin(w) for w in WELLS_METADATA}

    def get_field_summary(self) -> Dict[str, Any]:
        """Calculates aggregate field KPIs."""
        total_oil_bopd = 0.0
        total_steam_m3 = 0.0
        total_cum_oil_bbl = 0.0
        total_kwh_daily = 0.0
        active_wells_count = 0
        rod_float_alerts = 0

        well_states = []
        for well_id, well in self.wells.items():
            state = well.get_current_state()
            well_states.append(state)
            if "Active" in well.meta["status"]:
                total_oil_bopd += state["oil_rate_bopd"]
                total_cum_oil_bbl += state["cum_oil_bbl"]
                total_steam_m3 += 3600.0
                total_kwh_daily += state["motor_power_kw"] * 24.0
                active_wells_count += 1
                if state["is_rod_floating"]:
                    rod_float_alerts += 1

        field_sor = total_steam_m3 / np.maximum(total_cum_oil_bbl / 6.2898, 1.0)
        field_energy_kwh_bbl = total_kwh_daily / np.maximum(total_oil_bopd, 1.0)

        return {
            "total_oil_bopd": round(total_oil_bopd, 1),
            "active_wells": active_wells_count,
            "total_wells": len(self.wells),
            "field_average_sor": round(field_sor, 2),
            "field_energy_kwh_per_bbl": round(field_energy_kwh_bbl, 2),
            "rod_float_alert_count": rod_float_alerts,
            "well_states": well_states
        }


# Global field twin instance
baghewala_field_twin = BaghewalaFieldDigitalTwin()
