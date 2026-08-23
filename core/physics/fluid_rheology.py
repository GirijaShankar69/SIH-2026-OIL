"""
Heavy Crude Rheology and Fluid Physics Module for Baghewala Field
Implements non-Newtonian Herschel-Bulkley / Bingham Plastic models,
asphaltene precipitation risk, and water-in-oil emulsion dynamics.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class CrudeProperties:
    api_gravity: float = 18.2             # °API
    specific_gravity: float = 0.945       # fraction
    asphaltene_content_pct: float = 14.5  # wt%
    resin_content_pct: float = 22.0       # wt%
    wax_content_pct: float = 6.8          # wt%
    bubble_point_pressure: float = 38.0   # bar
    solution_gor: float = 14.0            # sm3/m3
    pour_point_c: float = 28.0            # °C
    asphaltene_onset_temp_c: float = 68.0 # °C


class BaghewalaFluidRheology:
    """
    Rheological and thermodynamic characterization of Baghewala extra-heavy crude.
    """

    def __init__(self, props: CrudeProperties = None):
        self.props = props or CrudeProperties()

    def get_density(self, temperature_c: float, pressure_bar: float = 50.0) -> float:
        """
        Calculates in-situ crude oil density (kg/m3) accounting for thermal expansion
        and isothermal compressibility.
        """
        rho_sc = 141.5 / (self.props.api_gravity + 131.5) * 1000.0 # kg/m3 (~945 kg/m3)
        thermal_expansion_coeff = 0.00072 # 1/°C
        compressibility = 6.5e-5 # 1/bar
        
        delta_T = temperature_c - 15.56
        delta_P = pressure_bar - 1.013
        
        rho = rho_sc * (1.0 - thermal_expansion_coeff * delta_T + compressibility * delta_P)
        return float(np.clip(rho, 820.0, 990.0))

    def non_newtonian_parameters(self, temperature_c: float) -> Dict[str, float]:
        """
        Yield stress (Pa), Consistency index K (Pa·s^n), and Flow behavior index n
        for Herschel-Bulkley rheology: tau = tau_y + K * (gamma_dot)^n
        At high temps (> 75°C), fluid is purely Newtonian (tau_y = 0, n = 1.0).
        At low temps (< 60°C), fluid develops yield stress and pseudoplasticity.
        """
        if temperature_c >= 75.0:
            tau_y = 0.0
            n = 1.0
            # Viscosity in Pa·s
            T_k = temperature_c + 273.15
            ln_mu = -4.85 + (2650.0 / T_k) + (385000.0 / (T_k ** 2))
            K = np.exp(ln_mu) * 1e-3 # Pa·s
        else:
            # Below crystallization / flocculation temperature
            delta_T_cold = 75.0 - temperature_c
            tau_y = 0.15 * (delta_T_cold / 10.0) ** 1.8 # Pa
            n = np.clip(1.0 - 0.08 * (delta_T_cold / 10.0), 0.65, 1.0)
            
            T_k = temperature_c + 273.15
            ln_mu = -4.85 + (2650.0 / T_k) + (385000.0 / (T_k ** 2))
            base_visc = np.exp(ln_mu) * 1e-3 # Pa·s
            K = base_visc * (1.0 + 0.12 * delta_T_cold)

        return {
            "yield_stress_pa": float(tau_y),
            "consistency_index_k": float(K),
            "flow_behavior_index_n": float(n),
            "is_newtonian": bool(temperature_c >= 75.0)
        }

    def apparent_viscosity(self, temperature_c: float, shear_rate_s1: float = 50.0) -> float:
        """
        Calculates apparent viscosity in cP at a given shear rate (s^-1).
        Standard rod pump annulus shear rate ranges between 20 s^-1 and 150 s^-1.
        """
        params = self.non_newtonian_parameters(temperature_c)
        tau_y = params["yield_stress_pa"]
        K = params["consistency_index_k"]
        n = params["flow_behavior_index_n"]

        gamma_dot = np.maximum(shear_rate_s1, 0.1)
        # Herschel-Bulkley apparent viscosity: mu_app = tau / gamma_dot = tau_y / gamma_dot + K * gamma_dot^(n-1)
        mu_app_Pa_s = (tau_y / gamma_dot) + K * (gamma_dot ** (n - 1.0))
        mu_app_cP = mu_app_Pa_s * 1000.0
        return float(np.clip(mu_app_cP, 5.0, 25000.0))

    def emulsion_viscosity(self, oil_visc_cp: float, water_cut: float, temperature_c: float) -> float:
        """
        Calculates effective emulsion viscosity for water-in-heavy-oil emulsion.
        In Baghewala, condensed steam creates tight emulsions up to inversion point (~65-70% water cut).
        Uses Richardson-Brinkman non-linear emulsion multiplier.
        """
        wcut = np.clip(water_cut, 0.0, 1.0)
        if wcut < 0.65:
            # Water-in-oil emulsion (continuous oil phase) -> Viscosity increases
            # Richardson equation: mu_e = mu_o * exp(a * wcut)
            # a is higher at lower temperature
            a = 2.8 + 0.02 * (100.0 - np.clip(temperature_c, 30.0, 100.0))
            multiplier = np.exp(a * wcut)
            # Cap maximum emulsion peak to 6x oil viscosity
            multiplier = np.clip(multiplier, 1.0, 6.5)
            return float(oil_visc_cp * multiplier)
        else:
            # Phase inversion to oil-in-water emulsion (continuous water phase) -> Viscosity drops
            water_visc_cp = 0.6 * np.exp(100.0 / (temperature_c + 150.0))
            oil_vol_frac = 1.0 - wcut
            # Brinkman equation for oil droplets in water
            multiplier = (1.0 - oil_vol_frac) ** (-2.5)
            mu_inv = water_visc_cp * np.clip(multiplier, 1.0, 8.0)
            return float(mu_inv)

    def asphaltene_precipitation_risk(self, temperature_c: float, pressure_bar: float) -> Dict[str, float]:
        """
        Computes Asphaltene Deposition & Precipitation Risk Index (0.0 to 1.0).
        Asphaltene is most unstable when temperature drops below 68°C and pressure is near bubble point.
        Colloidal Instability Index (CII) = (Saturates + Asphaltenes) / (Aromatics + Resins).
        """
        p = self.props
        # Baghewala typical SARA: Saturates 34%, Aromatics 29.5%, Resins 22%, Asphaltenes 14.5%
        cii = (34.0 + p.asphaltene_content_pct) / (29.5 + p.resin_content_pct) # ~ 0.94 (moderately unstable)
        
        # Thermal trigger
        if temperature_c < p.asphaltene_onset_temp_c:
            temp_risk = (p.asphaltene_onset_temp_c - temperature_c) / (p.asphaltene_onset_temp_c - 30.0)
        else:
            temp_risk = 0.0

        # Pressure trigger (near bubble point 38 bar)
        p_diff = np.abs(pressure_bar - p.bubble_point_pressure)
        pressure_risk = np.exp(-(p_diff ** 2) / (2.0 * (15.0 ** 2)))

        combined_risk = np.clip(0.65 * temp_risk + 0.35 * pressure_risk, 0.0, 1.0)

        return {
            "colloidal_instability_index": float(cii),
            "temperature_trigger_risk": float(temp_risk),
            "pressure_trigger_risk": float(pressure_risk),
            "asphaltene_deposition_risk_index": float(combined_risk),
            "status": "CRITICAL" if combined_risk > 0.7 else "MODERATE" if combined_risk > 0.35 else "STABLE"
        }


# Global instance
baghewala_rheology = BaghewalaFluidRheology()
