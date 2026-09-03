"""
Wellbore Hydraulics and Thermal Gradient Module for Baghewala Field
Implements Ramey wellbore heat transfer and multiphase pressure drop in rod-pumped wells.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple
from core.physics.fluid_rheology import BaghewalaFluidRheology, baghewala_rheology


@dataclass
class WellboreGeometry:
    well_depth: float = 1050.0          # m
    pump_depth: float = 1000.0          # m
    casing_od_in: float = 7.0           # in
    casing_id_m: float = 0.1594         # m (6.276 in)
    tubing_od_in: float = 2.875         # in (0.0730 m)
    tubing_id_m: float = 0.0620         # m (2.441 in)
    surface_ambient_temp_c: float = 32.0 # °C (Rajasthan desert ambient)
    geothermal_gradient_c_per_m: float = 0.022 # °C/m (22 °C/km)


class WellboreHydraulicsModel:
    """
    Computes temperature and pressure profiles along the wellbore from pump intake to wellhead.
    """

    def __init__(self, geometry: WellboreGeometry = None, rheology: BaghewalaFluidRheology = None):
        self.geo = geometry or WellboreGeometry()
        self.rheology = rheology or baghewala_rheology

    def compute_temperature_profile(self, 
                                    sandface_temp_c: float, 
                                    liquid_rate_m3d: float, 
                                    n_nodes: int = 50,
                                    ambient_temp_c: Optional[float] = None) -> Dict[str, np.ndarray]:
        """
        Computes dynamic temperature profile T(z) from surface (z=0) to pump depth (z=pump_depth)
        using modified Ramey heat transfer for flowing heavy crude.
        """
        g = self.geo
        amb_temp = ambient_temp_c if ambient_temp_c is not None else g.surface_ambient_temp_c
        z = np.linspace(0.0, g.pump_depth, n_nodes) # 0 is surface, 1000 is pump
        
        # Undisturbed geothermal temperature
        T_earth = amb_temp + g.geothermal_gradient_c_per_m * z

        # Mass flow rate kg/s
        liquid_rate_m3s = liquid_rate_m3d / 86400.0
        rho_mix = self.rheology.get_density(sandface_temp_c)
        mass_rate_kgs = np.maximum(liquid_rate_m3s * rho_mix, 0.05)

        # Fluid heat capacity
        cp_mix = 2.8e3 # J/(kg·°C)

        # Ramey relaxation distance parameter A (m)
        # A = m_dot * Cp * [ k_earth + r_to * U * f(t) ] / [ 2 * pi * r_to * U * k_earth ]
        # Baghewala typical A: ~ 300 - 800 m
        A_ramey = (mass_rate_kgs * cp_mix) / (2.0 * np.pi * (g.tubing_od_in * 0.0254 / 2.0) * 18.0) # ~ 450 m
        A_ramey = np.clip(A_ramey, 150.0, 1200.0)

        # Flow direction is upwards: from z = pump_depth to z = 0
        # Distance from pump entry delta_z_up = (g.pump_depth - z)
        dist_from_bottom = g.pump_depth - z
        
        # Fluid temperature cooling as it travels upwards
        exp_factor = np.exp(-dist_from_bottom / A_ramey)
        T_fluid = T_earth + (sandface_temp_c - (g.surface_ambient_temp_c + g.geothermal_gradient_c_per_m * g.pump_depth)) * exp_factor + \
                  g.geothermal_gradient_c_per_m * A_ramey * (1.0 - exp_factor)

        # Wellhead temperature is at z=0
        wellhead_temp_c = float(T_fluid[0])

        return {
            "depth_m": z,
            "undisturbed_geothermal_c": T_earth,
            "fluid_temperature_c": T_fluid,
            "wellhead_temp_c": wellhead_temp_c,
            "bottomhole_temp_c": float(T_fluid[-1]),
            "ramey_parameter_m": float(A_ramey)
        }

    def compute_hydraulics_profile(self, 
                                   sandface_temp_c: float, 
                                   bottomhole_pressure_bar: float,
                                   liquid_rate_m3d: float, 
                                   water_cut: float,
                                   rod_od_m: float = 0.0222,
                                   n_nodes: int = 50,
                                   ambient_temp_c: Optional[float] = None) -> Dict[str, np.ndarray]:
        """
        Calculates pressure profile, viscous shear stresses, and hydraulic gradients along the tubing.
        """
        temp_dict = self.compute_temperature_profile(sandface_temp_c, liquid_rate_m3d, n_nodes, ambient_temp_c=ambient_temp_c)
        z = temp_dict["depth_m"]
        T_z = temp_dict["fluid_temperature_c"]
        dz = z[1] - z[0]

        # Geometry of annular cross-section between tubing ID and sucker rod OD
        r_tubing_inner = self.geo.tubing_id_m / 2.0
        r_rod_outer = rod_od_m / 2.0
        annular_area = np.pi * (r_tubing_inner ** 2 - r_rod_outer ** 2)
        hydraulic_diam = 2.0 * (r_tubing_inner - r_rod_outer)

        # Upward flow velocity
        q_m3s = liquid_rate_m3d / 86400.0
        v_fluid = q_m3s / annular_area

        pressures = np.zeros(n_nodes)
        viscosities = np.zeros(n_nodes)
        shear_rates = np.zeros(n_nodes)

        # Calculate upwards from pump (node -1) to surface (node 0)
        pressures[-1] = bottomhole_pressure_bar

        for i in reversed(range(n_nodes)):
            t_curr = T_z[i]
            rho_curr = self.rheology.get_density(t_curr, pressures[min(i+1, n_nodes-1)])
            
            # Annular shear rate: gamma_dot = 2 * v / (r_tubing - r_rod)
            gamma_dot = 2.0 * v_fluid / np.maximum(r_tubing_inner - r_rod_outer, 1e-4)
            shear_rates[i] = gamma_dot

            # Apparent oil viscosity and emulsion viscosity
            mu_oil_cp = self.rheology.apparent_viscosity(t_curr, gamma_dot)
            mu_eff_cp = self.rheology.emulsion_viscosity(mu_oil_cp, water_cut, t_curr)
            viscosities[i] = mu_eff_cp
            mu_eff_Pa_s = mu_eff_cp * 1e-3

            # Pressure gradient: Hydrostatic (g * rho) + Friction
            # Reynolds number for annular flow
            reynolds = (rho_curr * v_fluid * hydraulic_diam) / np.maximum(mu_eff_Pa_s, 1e-4)
            if reynolds < 2100:
                fanning_f = 16.0 / np.maximum(reynolds, 1e-3)
            else:
                fanning_f = 0.079 / (reynolds ** 0.25)
            fanning_f = np.clip(fanning_f, 0.005, 10.0)

            # dp/dz in Pa/m
            dp_fric_dz = 2.0 * fanning_f * rho_curr * (v_fluid ** 2) / hydraulic_diam
            dp_grav_dz = rho_curr * 9.81
            dp_total_dz = (dp_grav_dz + dp_fric_dz) # Pa/m

            if i < n_nodes - 1:
                # Pressure at shallower depth (going upwards, pressure decreases)
                dp_bar = (dp_total_dz * dz) / 1e5
                pressures[i] = np.maximum(pressures[i+1] - dp_bar, 1.013)

        wellhead_pressure_bar = float(pressures[0])

        return {
            "depth_m": z,
            "temperature_c": T_z,
            "pressure_bar": pressures,
            "viscosity_cp": viscosities,
            "shear_rate_s1": shear_rates,
            "wellhead_temp_c": float(T_z[0]),
            "wellhead_pressure_bar": wellhead_pressure_bar,
            "bottomhole_temp_c": float(T_z[-1]),
            "bottomhole_pressure_bar": float(pressures[-1])
        }


# Global instance
baghewala_wellbore = WellboreHydraulicsModel()
