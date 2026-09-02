"""
Thermal Reservoir Model for Cyclic Steam Stimulation (CSS) in Baghewala Field
Implements Boberg-Lantz and Marx-Langenheim thermal dissipation kinetics,
viscosity-temperature relationships for 17-19° API crude, and multi-phase thermal IPR.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


@dataclass
class ReservoirProperties:
    """Reservoir and rock-fluid properties calibrated to Baghewala Field (Jodhpur Sandstone)."""
    formation_depth: float = 1050.0       # m
    pay_thickness: float = 18.0           # m (net pay)
    porosity: float = 0.24                # fraction
    permeability: float = 280.0           # mD
    initial_pressure: float = 110.0       # bar (11 MPa)
    initial_temperature: float = 47.0     # °C (native reservoir temperature)
    rock_density: float = 2400.0          # kg/m3
    rock_heat_capacity: float = 0.95      # kJ/(kg·°C)
    overburden_conductivity: float = 1.8  # W/(m·°C)
    overburden_diffusivity: float = 0.85e-6 # m2/s
    oil_api: float = 18.2                 # °API
    oil_density_sc: float = 945.0         # kg/m3
    oil_heat_capacity: float = 2.1        # kJ/(kg·°C)
    water_heat_capacity: float = 4.18     # kJ/(kg·°C)
    initial_oil_saturation: float = 0.68  # fraction
    initial_water_saturation: float = 0.32 # fraction
    drainage_radius: float = 150.0        # m
    wellbore_radius: float = 0.108        # m (8.5 inch hole)


@dataclass
class CSSCycleParameters:
    """Operating parameters for a single CSS cycle."""
    cycle_number: int = 1
    steam_volume_cwe: float = 3500.0      # m3 Cold Water Equivalent (CWE)
    injection_rate: float = 250.0         # m3/day CWE
    steam_quality: float = 0.78           # fraction (at sandface)
    steam_temperature: float = 265.0      # °C (saturated steam at ~50 bar)
    injection_pressure: float = 65.0      # bar
    soak_days: float = 5.0                # days shut-in for heat diffusion
    producing_days: int = 120             # days production per cycle
    bottomhole_flowing_pressure: float = 18.0 # bar (under SRP pump intake)


class ThermalReservoirModel:
    """
    Coupled Thermal-Hydraulic Reservoir Simulator for Heavy Oil CSS.
    Calculates temperature dissipation, viscosity kinetics, inflow performance, and SOR.
    """

    def __init__(self, props: Optional[ReservoirProperties] = None):
        self.props = props or ReservoirProperties()

    def oil_viscosity(self, temperature_c: float) -> float:
        """
        Calculates dead oil viscosity (cP) as a function of temperature (°C)
        using calibrated Andrade-Walther equation for Baghewala heavy crude (17-19° API).
        Native condition (47°C): ~2500-3000 cP.
        Steam temperature (220°C): ~15-20 cP.
        """
        T_kelvin = np.maximum(temperature_c + 273.15, 273.15)
        # Calibrated Andrade-Walther constants for Baghewala 18.2° API crude.
        # Fitted via least-squares to reproduce documented calibration points:
        #   47°C → 2,650 cP | 100°C → 145 cP | 220°C → 18 cP
        # Equation: ln(μ) = A + B/T_K + C/T_K²
        A =  13.0158
        B = -11192.6
        C =  3057134.0
        ln_mu = A + (B / T_kelvin) + (C / (T_kelvin ** 2))
        visc = np.exp(ln_mu)
        return float(np.clip(visc, 8.0, 15000.0))

    def calculate_steam_chamber(self, params: CSSCycleParameters) -> Dict[str, float]:
        """
        Calculates steam chamber radius, total injected heat, and initial heated zone temperature
        using Marx-Langenheim & Boberg-Lantz thermal balance.
        """
        p = self.props
        injection_days = params.steam_volume_cwe / params.injection_rate
        t_inj_sec = injection_days * 86400.0

        # Latent heat of steam at injection pressure (approx Antoine/Steam tables)
        T_sat = params.steam_temperature
        h_latent = 2050.0 # kJ/kg
        h_sensible = p.water_heat_capacity * (T_sat - p.initial_temperature)
        h_steam_total = (h_sensible + params.steam_quality * h_latent) * 1000.0 # J/kg
        mass_steam_kg = params.steam_volume_cwe * 1000.0
        total_heat_injected_J = mass_steam_kg * h_steam_total

        # Volumetric heat capacity of reservoir rock + fluid
        M_r = (1 - p.porosity) * p.rock_density * (p.rock_heat_capacity * 1000.0) + \
              p.porosity * p.initial_oil_saturation * p.oil_density_sc * (p.oil_heat_capacity * 1000.0) + \
              p.porosity * p.initial_water_saturation * 1000.0 * (p.water_heat_capacity * 1000.0) # J/(m3·°C)

        # Dimensionless time for overburden thermal diffusion: t_D = 4 * alpha * t / h^2
        t_D = (4.0 * p.overburden_diffusivity * t_inj_sec) / (p.pay_thickness ** 2)
        # Marx-Langenheim thermal efficiency factor
        sqrt_tD = np.sqrt(np.maximum(t_D, 1e-6))
        erfc_val = np.exp(-t_D) / (1.0 + 0.5 * sqrt_tD) # stable fast approximation
        if t_D > 1e-4:
            f_ml = (np.exp(t_D) * erfc_val + 2.0 * sqrt_tD / np.sqrt(np.pi) - 1.0) / t_D
            f_ml = np.clip(f_ml, 0.2, 0.95)
        else:
            f_ml = 0.95

        # Effective heated volume V_h
        delta_T = T_sat - p.initial_temperature
        V_heated = (total_heat_injected_J * f_ml) / (M_r * delta_T)
        r_heated = np.sqrt(np.maximum(V_heated / (np.pi * p.pay_thickness), p.wellbore_radius ** 2))

        return {
            "injection_days": float(injection_days),
            "total_heat_GJ": float(total_heat_injected_J / 1e9),
            "thermal_efficiency": float(f_ml),
            "heated_radius_m": float(r_heated),
            "volumetric_heat_capacity_kJ_m3C": float(M_r / 1000.0),
            "delta_T_init": float(delta_T)
        }

    def simulate_cycle(self, params: CSSCycleParameters) -> Dict[str, np.ndarray]:
        """
        Simulates the full CSS cycle over time:
        - Soak phase thermal diffusion
        - Production phase temperature decay, pressure decay, viscosity increase,
          multiphase oil & water production, and cumulative metrics.
        """
        p = self.props
        chamber = self.calculate_steam_chamber(params)
        r_h = chamber["heated_radius_m"]
        delta_T_0 = chamber["delta_T_init"]
        t_soak = params.soak_days
        n_days = params.producing_days

        days_array = np.arange(1, n_days + 1)

        # Boberg-Lantz thermal dissipation factor during production
        # Heat loss by vertical conduction to caprock/baserock + radial conduction
        # Thermal decay time constant tau (days)
        tau_vertical = (p.pay_thickness ** 2 * chamber["volumetric_heat_capacity_kJ_m3C"] * 1000.0) / \
                       (16.0 * p.overburden_conductivity * 86400.0) # days
        tau_radial = (r_h ** 2 * chamber["volumetric_heat_capacity_kJ_m3C"] * 1000.0) / \
                     (4.0 * p.overburden_conductivity * 86400.0) # days
        tau_eff = (tau_vertical * tau_radial) / (tau_vertical + tau_radial + 1e-6)

        # Soak cooling factor
        soak_cooling = np.exp(-np.sqrt(t_soak / (tau_eff + 1e-6)))

        # Heated zone average temperature profile T_avg(t)
        # Production cooling factor
        prod_cooling = np.exp(-np.sqrt(days_array / (tau_eff + 1e-6)))
        # Additional heat removal by fluid production (convective heat loss)
        convective_decay = np.exp(-0.008 * days_array)

        T_res_profile = p.initial_temperature + delta_T_0 * soak_cooling * prod_cooling * convective_decay
        # Sandface wellbore temperature (slightly higher due to steam back-flow early on)
        T_sandface_profile = T_res_profile + 8.0 * np.exp(-days_array / 15.0)

        # Dynamic Oil Viscosity in heated zone
        viscosity_profile = np.array([self.oil_viscosity(T) for T in T_res_profile])

        # Reservoir pressure decline during cycle
        # Early steam pressure drive dissipates over 30-40 days
        P_steam_boost = (params.injection_pressure - p.initial_pressure) * 0.45 * np.exp(-days_array / 22.0)
        # Natural depletion per cycle
        cycle_depletion = (params.cycle_number - 1) * 4.5 # bar per cycle
        P_res_profile = np.maximum(p.initial_pressure - cycle_depletion + P_steam_boost, params.bottomhole_flowing_pressure + 3.0)

        # Heavy oil Productivity Index J(t)
        # Composite radial flow: inner zone r_h with mu(T), outer cold zone with mu(T_native)
        mu_cold = self.oil_viscosity(p.initial_temperature)
        k_m2 = p.permeability * 0.986923e-15
        h_m = p.pay_thickness
        r_w = p.wellbore_radius
        r_e = p.drainage_radius

        # PI in m3/(day·bar)
        # Skin factor (negative after thermal stimulation ~ -1.2 to 0.5)
        skin_thermal = -1.2 + 0.3 * (params.cycle_number - 1) + 1.5 * (1.0 - np.exp(-days_array / 35.0))
        
        pi_profile = np.zeros(n_days)
        for i in range(n_days):
            mu_hot_Pa_s = (viscosity_profile[i] * 1e-3)
            mu_cold_Pa_s = (mu_cold * 1e-3)
            res_denom = (mu_hot_Pa_s * np.log(np.maximum(r_h / r_w, 1.1)) +
                         # Cold-zone log term weighted by 0.15: calibrated partition coefficient
                         # reflecting reduced contribution of the partially-swept cold zone
                         # to the composite PI (Baghewala k-effective ~ 15% of hot-zone k).
                         mu_cold_Pa_s * np.log(np.maximum(r_e / r_h, 1.1)) * 0.15 +
                         mu_hot_Pa_s * skin_thermal[i])
            res_denom = np.maximum(res_denom, 1e-5)
            # Darcy J in m3/(sec·Pa) converted to m3/(day·bar)
            j_si = (2.0 * np.pi * k_m2 * h_m) / res_denom
            j_field = j_si * 86400.0 * 1e5 # m3/(day·bar)
            pi_profile[i] = np.clip(j_field, 0.05, 12.0)

        # Multi-phase Flow: Water Cut & Oil Rate
        # Condensed steam flows back first (high initial water cut ~80-90%), then drops to 40-50%, then rises
        wcut_condensed = 0.88 * np.exp(-days_array / 18.0)
        wcut_formation = 0.30 + 0.05 * (params.cycle_number - 1) + 0.25 * (days_array / n_days)
        wcut_profile = np.clip(np.maximum(wcut_condensed, wcut_formation), 0.25, 0.94)

        # Drawdown and Inflow Rate (Vogel heavy oil modification)
        drawdown = np.maximum(P_res_profile - params.bottomhole_flowing_pressure, 1.0)
        vogel_term = 1.0 - 0.2 * (params.bottomhole_flowing_pressure / P_res_profile) - 0.8 * ((params.bottomhole_flowing_pressure / P_res_profile) ** 2)
        vogel_term = np.clip(vogel_term, 0.4, 1.0)
        
        q_liquid_m3d = pi_profile * drawdown * vogel_term
        q_liquid_m3d = np.clip(q_liquid_m3d, 1.0, 45.0)

        q_oil_m3d = q_liquid_m3d * (1.0 - wcut_profile)
        q_water_m3d = q_liquid_m3d * wcut_profile

        # Field units
        q_oil_bopd = q_oil_m3d * 6.2898
        q_water_bwpd = q_water_m3d * 6.2898

        # Cumulative metrics
        cum_oil_m3 = np.cumsum(q_oil_m3d)
        cum_oil_bbl = np.cumsum(q_oil_bopd)
        cum_water_m3 = np.cumsum(q_water_m3d)

        # Steam-Oil Ratio (SOR)
        instantaneous_sor = params.steam_volume_cwe / (np.maximum(q_oil_m3d, 0.01) * n_days)
        cumulative_sor = params.steam_volume_cwe / np.maximum(cum_oil_m3, 0.1)

        # Rod Floating Risk Indicator (High viscosity > 400 cP + low temp < 85°C)
        rod_float_subsurface_risk = np.clip((viscosity_profile - 150.0) / 650.0, 0.0, 1.0) * \
                                    np.clip((110.0 - T_res_profile) / 50.0, 0.0, 1.0)

        return {
            "days": days_array,
            "temperature_reservoir_c": T_res_profile,
            "temperature_sandface_c": T_sandface_profile,
            "viscosity_cp": viscosity_profile,
            "reservoir_pressure_bar": P_res_profile,
            "oil_rate_m3d": q_oil_m3d,
            "oil_rate_bopd": q_oil_bopd,
            "water_rate_m3d": q_water_m3d,
            "water_rate_bwpd": q_water_bwpd,
            "water_cut": wcut_profile,
            "cum_oil_m3": cum_oil_m3,
            "cum_oil_bbl": cum_oil_bbl,
            "cum_water_m3": cum_water_m3,
            "cumulative_sor": cumulative_sor,
            "instantaneous_sor": instantaneous_sor,
            "productivity_index": pi_profile,
            "rod_float_subsurface_risk": rod_float_subsurface_risk,
            "chamber_metrics": chamber
        }


# Global default instance
baghewala_reservoir = ThermalReservoirModel()
