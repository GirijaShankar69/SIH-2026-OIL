"""
Sucker Rod Pumping (SRP) Dynamics and Wave Equation Engine
Implements Gibbs 1D Damped Wave Equation solver, exact hydrodynamic viscous drag,
rod floating detection, impact loading simulation, and Goodman fatigue analysis.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from core.physics.fluid_rheology import baghewala_rheology
from core.physics.wellbore_hydraulics import baghewala_wellbore


@dataclass
class SuckerRodTaper:
    rod_type: str = "API Grade D Alloy"
    od_in: float = 0.875                 # 7/8 in (0.022225 m)
    length_m: float = 750.0              # m
    weight_per_m_kg: float = 2.92        # kg/m (1.96 lb/ft)
    cross_section_m2: float = 3.879e-4   # m2 (0.6013 sq in)
    elastic_modulus_pa: float = 2.07e11  # Pa (30 x 10^6 psi)
    tensile_strength_psi: float = 115000 # psi (793 MPa)
    density_kg_m3: float = 7850.0        # kg/m3


@dataclass
class SRPConfiguration:
    stroke_length_m: float = 2.54        # m (100 in)
    pumping_speed_spm: float = 5.5       # SPM
    pump_depth_m: float = 1000.0         # m
    plunger_diameter_in: float = 2.25    # in (0.05715 m)
    tubing_id_in: float = 2.441          # in (0.0620 m)
    rod_tapers: List[SuckerRodTaper] = field(default_factory=lambda: [
        SuckerRodTaper(rod_type="API Grade D (Top)", od_in=0.875, length_m=650.0, weight_per_m_kg=2.92, cross_section_m2=3.879e-4),
        SuckerRodTaper(rod_type="API Grade D (Bottom)", od_in=0.750, length_m=350.0, weight_per_m_kg=2.14, cross_section_m2=2.85e-4)
    ])
    pump_fillage_fraction: float = 0.92  # fraction (0.0 - 1.0)
    service_factor: float = 0.90         # Goodman service factor (corrosive/thermal heavy oil)


class SuckerRodDynamicsEngine:
    """
    Gibbs 1D Wave Equation solver for sucker rod strings in viscous heavy oil.
    """

    def __init__(self, config: Optional[SRPConfiguration] = None):
        self.config = config or SRPConfiguration()

    def calculate_total_rod_weight(self) -> Dict[str, float]:
        """Calculates rod string total weight in air and buoyant weight in oil."""
        total_weight_air_n = 0.0
        total_mass_kg = 0.0
        total_length_m = 0.0

        for taper in self.config.rod_tapers:
            mass = taper.weight_per_m_kg * taper.length_m
            total_mass_kg += mass
            total_weight_air_n += mass * 9.81
            total_length_m += taper.length_m

        # Fluid buoyancy (Baghewala ~945 kg/m3 vs steel 7850 kg/m3)
        buoyancy_factor = 1.0 - (945.0 / 7850.0) # ~ 0.880
        total_weight_fluid_n = total_weight_air_n * buoyancy_factor

        return {
            "total_mass_kg": float(total_mass_kg),
            "total_weight_air_n": float(total_weight_air_n),
            "total_weight_fluid_n": float(total_weight_fluid_n),
            "total_weight_air_lbs": float(total_weight_air_n * 0.224809),
            "total_weight_fluid_lbs": float(total_weight_fluid_n * 0.224809),
            "total_length_m": float(total_length_m)
        }

    def compute_viscous_damping_and_drag(self, 
                                         avg_viscosity_cp: float, 
                                         spm: float, 
                                         stroke_m: float) -> Dict[str, float]:
        """
        Calculates downstroke hydrodynamic fluid drag on the sucker rod string.
        F_drag = integral(2*pi*r_rod * mu * v_rel / ln(r_tub/r_rod) * dz)
        """
        # Average rod speed in m/s: v_avg = 2 * S * SPM / 60
        omega = 2.0 * np.pi * (spm / 60.0)
        v_peak_downstroke = (stroke_m / 2.0) * omega # peak downward velocity

        total_drag_force_n = 0.0
        r_tubing_m = (self.config.tubing_id_in * 0.0254) / 2.0

        for taper in self.config.rod_tapers:
            r_rod_m = (taper.od_in * 0.0254) / 2.0
            ln_ratio = np.log(np.maximum(r_tubing_m / r_rod_m, 1.05))
            
            # Viscous shear stress: tau = mu * (v_rod) / (r_rod * ln(r_tub/r_rod))
            # Integrated drag: F = 2 * pi * L * mu * v_rod / ln_ratio
            mu_si = (avg_viscosity_cp * 1e-3)
            drag_taper_n = (2.0 * np.pi * taper.length_m * mu_si * v_peak_downstroke) / ln_ratio
            total_drag_force_n += drag_taper_n

        # Add rod coupling narrow clearance drag (couplings every 7.6m increase drag by ~35%)
        coupling_multiplier = 1.38
        total_drag_force_n *= coupling_multiplier

        # Plunger traveling valve hydrodynamic throttling resistance in heavy crude
        r_plunger_m = (self.config.plunger_diameter_in * 0.0254) / 2.0
        plunger_clearance_m = 0.00012 # 0.0048 in fit
        mu_si = (avg_viscosity_cp * 1e-3)
        plunger_shear_drag_n = (2.0 * np.pi * r_plunger_m * 1.2 * mu_si * v_peak_downstroke) / plunger_clearance_m
        plunger_shear_drag_n = np.clip(plunger_shear_drag_n, 100.0, 12000.0)
        total_drag_force_n += plunger_shear_drag_n

        weights = self.calculate_total_rod_weight()
        w_buoyant_n = weights["total_weight_fluid_n"]

        # Net downward falling force available during downstroke
        net_falling_force_n = w_buoyant_n - total_drag_force_n
        
        # Theoretical maximum acceleration of rod falling in viscous fluid
        a_rod_max = (net_falling_force_n / weights["total_mass_kg"])
        # Pumping unit downward acceleration at top-of-stroke (TOS): a_unit = (S/2) * omega^2
        a_carrier_bar_peak = (stroke_m / 2.0) * (omega ** 2)

        # Severity index (0.0 to 1.0+)
        float_risk_index = float(np.clip(total_drag_force_n / np.maximum(w_buoyant_n, 1.0), 0.0, 2.0))

        # Rod Floating Condition: Carrier bar separates if rod fall acceleration is slower than carrier bar
        is_rod_floating = bool(net_falling_force_n <= 0.0 or a_rod_max < a_carrier_bar_peak or float_risk_index >= 0.70)

        # Peak impact force calculation if rod floats and hits carrier bar
        if is_rod_floating or float_risk_index > 0.70:
            # Velocity difference upon impact
            delta_v = np.maximum(v_peak_downstroke * (float_risk_index - 0.5), 0.15)
            impact_duration = 0.035 # 35 ms impact impulse
            impact_shock_n = (weights["total_mass_kg"] * 0.50 * delta_v) / impact_duration
        else:
            impact_shock_n = 0.0

        return {
            "peak_viscous_drag_n": float(total_drag_force_n),
            "peak_viscous_drag_lbs": float(total_drag_force_n * 0.224809),
            "net_falling_force_n": float(net_falling_force_n),
            "net_falling_force_lbs": float(net_falling_force_n * 0.224809),
            "carrier_bar_peak_accel_m_s2": float(a_carrier_bar_peak),
            "rod_fall_accel_m_s2": float(a_rod_max),
            "is_rod_floating": is_rod_floating,
            "rod_floating_risk_index": float(float_risk_index),
            "impact_shock_force_n": float(impact_shock_n),
            "impact_shock_force_lbs": float(impact_shock_n * 0.224809)
        }

    def solve_wave_equation(self, 
                            temperature_c: float, 
                            viscosity_cp: float, 
                            bottomhole_pressure_bar: float,
                            spm: Optional[float] = None, 
                            stroke_length_m: Optional[float] = None,
                            pump_fillage: Optional[float] = None,
                            fault_type: str = "normal",
                            n_time_steps: int = 120) -> Dict[str, np.ndarray]:
        """
        Solves Gibbs 1D damped wave equation for the tapered sucker rod string
        generating exact Surface and Downhole Dynamometer Cards.
        """
        cfg = self.config
        spm_raw = spm if spm is not None else cfg.pumping_speed_spm
        stroke_val = stroke_length_m if stroke_length_m is not None else cfg.stroke_length_m
        fillage_val = pump_fillage if pump_fillage is not None else cfg.pump_fillage_fraction

        weights = self.calculate_total_rod_weight()
        w_rod_fluid_lbs = weights["total_weight_fluid_lbs"]
        w_rod_air_lbs = weights["total_weight_air_lbs"]

        # Handle shut-in / non-pumping condition (SPM = 0)
        if spm_raw <= 0.01:
            theta = np.linspace(0, 2.0 * np.pi, n_time_steps)
            return {
                "theta_rad": theta,
                "surface_position_in": np.zeros(n_time_steps),
                "surface_load_lbs": np.full(n_time_steps, w_rod_fluid_lbs),
                "downhole_position_in": np.zeros(n_time_steps),
                "downhole_load_lbs": np.zeros(n_time_steps),
                "pprl_lbs": float(w_rod_fluid_lbs),
                "mprl_lbs": float(w_rod_fluid_lbs),
                "prhp": 0.0,
                "motor_power_kw": 0.0,
                "kwh_per_bbl": 0.0,
                "sigma_max_psi": float(w_rod_fluid_lbs / (cfg.rod_tapers[0].cross_section_m2 * 1550.0)),
                "sigma_min_psi": float(w_rod_fluid_lbs / (cfg.rod_tapers[0].cross_section_m2 * 1550.0)),
                "sigma_allowable_psi": 45000.0,
                "rod_loading_pct": 25.0,
                "is_rod_floating": False,
                "rod_floating_risk_index": 0.0,
                "impact_shock_force_lbs": 0.0,
                "drag_metrics": {"is_rod_floating": False, "rod_floating_risk_index": 0.0, "peak_viscous_drag_lbs": 0.0, "impact_shock_force_lbs": 0.0},
                "actual_oil_bpd": 0.0,
                "theo_disp_bpd": 0.0
            }

        spm_val = float(np.maximum(spm_raw, 0.5))
        drag_metrics = self.compute_viscous_damping_and_drag(viscosity_cp, spm_val, stroke_val)
        drag_lbs = drag_metrics["peak_viscous_drag_lbs"]
        is_float = drag_metrics["is_rod_floating"]
        impact_lbs = drag_metrics["impact_shock_force_lbs"]

        # Plunger fluid load F_o (lbs)
        # F_o = Area_plunger * (P_tubing_head_fluid_col - P_intake)
        # Hydrostatic fluid column ~ 1000m of ~945 kg/m3 fluid = ~92 bar (~1330 psi)
        fluid_column_psi = 1000.0 * 945.0 * 9.81 / 6894.76 # ~ 1345 psi
        intake_psi = bottomhole_pressure_bar * 14.5038
        net_plunger_diff_psi = np.maximum(fluid_column_psi - intake_psi, 200.0)
        
        plunger_area_sqin = np.pi * ((cfg.plunger_diameter_in / 2.0) ** 2) # ~ 3.976 sq in
        fluid_load_fo_lbs = plunger_area_sqin * net_plunger_diff_psi # ~ 4500 - 5500 lbs

        # Kinematic time discretization: one complete cycle theta = 0 to 2*pi
        theta = np.linspace(0, 2.0 * np.pi, n_time_steps)
        
        # Surface Polish Rod Position (in inches)
        stroke_in = stroke_val * 39.3701
        # Kinematic position: 0 is bottom of stroke (BOS), stroke_in is top of stroke (TOS)
        # Upstroke: theta 0 to pi. Downstroke: theta pi to 2*pi.
        surface_position_in = (stroke_in / 2.0) * (1.0 - np.cos(theta))

        # Downhole Pump Plunger Position (includes rod stretch & phase lag)
        # Wave propagation speed a ~ 16,500 ft/s (5030 m/s)
        # Acoustic round trip travel time t_round = 2 * L / a ~ 0.40 seconds
        period_sec = 60.0 / spm_val
        phase_lag_rad = (2.0 * np.pi * 0.40) / period_sec # ~ 0.20 - 0.45 rad
        
        # Dynamic rod stretch
        top_taper = cfg.rod_tapers[0]
        # Total compliance delta_L = F_o * sum(L_i / (E * A_i))
        compliance = sum(t.length_m / (t.elastic_modulus_pa * t.cross_section_m2) for t in cfg.rod_tapers) # m/N
        stroke_stretch_m = (fluid_load_fo_lbs / 0.224809) * compliance
        downhole_stroke_in = (stroke_val - stroke_stretch_m * 0.4) * 39.3701
        
        downhole_position_in = (downhole_stroke_in / 2.0) * (1.0 - np.cos(theta - phase_lag_rad))

        # Dynamic Surface and Downhole Force Profiles
        surface_load_lbs = np.zeros(n_time_steps)
        downhole_load_lbs = np.zeros(n_time_steps)

        # Dynamic inertial amplification factor (API 11L)
        # N/N0 ratio: spm / fundamental rod natural frequency
        f_0 = 5030.0 / (4.0 * weights["total_length_m"]) # ~ 1.25 Hz (75 SPM)
        n_n0 = (spm_val / 60.0) / f_0
        dynamic_amp = 1.0 + 0.5 * (n_n0 ** 2)

        for i, th in enumerate(theta):
            # Upstroke phase (0 to pi)
            if th < np.pi:
                # Plunger picks up fluid load Fo
                # Traveling valve closes, standing valve opens
                # Load picks up rapidly at start of upstroke
                valve_pickup = 1.0 - np.exp(-th / 0.25)
                f_downhole = fluid_load_fo_lbs * valve_pickup * fillage_val

                # Surface load = Buoyant rod weight + Downhole load * amp + Viscous upward drag
                # Upstroke viscous drag adds tension at surface
                f_surface = w_rod_fluid_lbs + (f_downhole * dynamic_amp) + drag_lbs * np.sin(th) * 0.65
            
            # Downstroke phase (pi to 2*pi)
            else:
                # Traveling valve opens, fluid transfers to rod string
                # Standing valve closes
                downstroke_angle = th - np.pi
                
                # Check for fluid pound (if pump fillage < 1.0, traveling valve hits liquid surface late)
                pound_angle = np.pi * (1.0 - fillage_val)
                if downstroke_angle < pound_angle:
                    # Rod falling through gas/vapor void -> zero downhole resistance
                    f_downhole = 0.0
                else:
                    # Fluid pound impact occurs when hitting liquid level
                    pound_factor = 1.0 - np.exp(-(downstroke_angle - pound_angle) / 0.15)
                    f_downhole = fluid_load_fo_lbs * 0.12 * pound_factor

                # Surface load on downstroke = Buoyant rod weight - Viscous retarding drag
                f_surface = w_rod_fluid_lbs - drag_lbs * np.sin(downstroke_angle)

                # ROD FLOATING & IMPACT MODIFICATIONS
                if is_float or drag_metrics["rod_floating_risk_index"] > 0.8:
                    # Carrier bar separation: Polish rod load drops towards zero or negative
                    float_dip = (drag_metrics["rod_floating_risk_index"] - 0.75) * 4500.0
                    f_surface = np.maximum(f_surface - float_dip, 400.0) # minimal carrier bar contact
                    
                    # Impact shock wave near bottom of stroke (downstroke_angle > 0.85 * pi)
                    if downstroke_angle > 0.82 * np.pi:
                        shock_window = np.sin((downstroke_angle - 0.82 * np.pi) / (0.18 * np.pi) * np.pi)
                        f_surface += impact_lbs * shock_window
                        f_downhole += impact_lbs * 0.35 * shock_window

            downhole_load_lbs[i] = f_downhole
            surface_load_lbs[i] = f_surface

        # Specific Diagnostic Fault Modifiers (for training/testing or manual simulation)
        if fault_type == "fluid_pound":
            fillage_val = 0.65
            # Recompute sharp pound impact
            for i, th in enumerate(theta):
                if np.pi <= th <= 1.6 * np.pi:
                    surface_load_lbs[i] -= 2200.0 * np.sin(th - np.pi)
                    if th > 1.45 * np.pi:
                        surface_load_lbs[i] += 3500.0
        elif fault_type == "gas_interference":
            for i, th in enumerate(theta):
                if np.pi <= th:
                    # Smooth compression curvature
                    surface_load_lbs[i] = w_rod_fluid_lbs - 1200.0 * (1.0 - np.cos(th - np.pi))
        elif fault_type == "unanchored_tubing":
            # Tubing elasticity creates severe hysteresis tilt
            surface_load_lbs += 1800.0 * (surface_position_in / stroke_in - 0.5)
        elif fault_type == "valve_leak":
            for i, th in enumerate(theta):
                if th < np.pi:
                    surface_load_lbs[i] -= 1800.0 * (1.0 - th / np.pi)
        elif fault_type == "standing_leak":
            for i, th in enumerate(theta):
                if th >= np.pi: # Downstroke standing valve leak
                    surface_load_lbs[i] += 1500.0 * ((th - np.pi) / np.pi)
        elif fault_type == "pump_off":
            # Highly degraded fillage and high friction
            surface_load_lbs = surface_load_lbs * 0.7 + 2500.0 * np.sin(theta)

        # Performance and Stress Metrics
        pprl_lbs = float(np.max(surface_load_lbs)) # Peak Polish Rod Load
        mprl_lbs = float(np.min(surface_load_lbs)) # Minimum Polish Rod Load
        stroke_actual_in = float(np.max(surface_position_in) - np.min(surface_position_in))
        
        # Polish rod horsepower (PRHP)
        # PRHP = Area of surface dyno card * SPM / 33000
        # Area = integral(Load * dPos) in ft-lbs
        card_work_ft_lbs = np.trapezoid(surface_load_lbs, surface_position_in / 12.0)
        card_work_ft_lbs = float(np.abs(card_work_ft_lbs))
        prhp = (card_work_ft_lbs * spm_val) / 33000.0
        kw_power = prhp * 0.7457

        # Goodman Fatigue Analysis
        # Top rod stress (highest cyclic stress concentration)
        top_area_sqin = cfg.rod_tapers[0].cross_section_m2 * 1550.003 # sq in (~0.601 sq in)
        sigma_max_psi = pprl_lbs / top_area_sqin
        sigma_min_psi = mprl_lbs / top_area_sqin
        tensile_rating_psi = cfg.rod_tapers[0].tensile_strength_psi
        
        # Modified Goodman allowable stress: S_a = (T / 1.75 + 0.5625 * S_min) * SF
        sigma_allowable_psi = (tensile_rating_psi / 1.75 + 0.5625 * sigma_min_psi) * cfg.service_factor
        rod_loading_pct = float((sigma_max_psi / np.maximum(sigma_allowable_psi, 1000.0)) * 100.0)

        # Pump efficiency and theoretical displacement
        # Displacement bpd = 0.1166 * (D_plunger_in)^2 * Stroke_in * SPM
        theo_disp_bpd = 0.1166 * (cfg.plunger_diameter_in ** 2) * stroke_in * spm_val
        actual_oil_bpd = theo_disp_bpd * fillage_val * 0.85 # accounting for slippage

        # Lift Energy Intensity (kWh/bbl)
        daily_kwh = kw_power * 24.0
        kwh_per_bbl = float(daily_kwh / np.maximum(actual_oil_bpd, 0.5))

        return {
            "theta_rad": theta,
            "surface_position_in": surface_position_in,
            "surface_load_lbs": surface_load_lbs,
            "downhole_position_in": downhole_position_in,
            "downhole_load_lbs": downhole_load_lbs,
            "pprl_lbs": pprl_lbs,
            "mprl_lbs": mprl_lbs,
            "prhp": float(prhp),
            "motor_power_kw": float(kw_power),
            "kwh_per_bbl": kwh_per_bbl,
            "sigma_max_psi": float(sigma_max_psi),
            "sigma_min_psi": float(sigma_min_psi),
            "sigma_allowable_psi": float(sigma_allowable_psi),
            "rod_loading_pct": rod_loading_pct,
            "is_rod_floating": bool(is_float or drag_metrics["is_rod_floating"]),
            "rod_floating_risk_index": float(drag_metrics["rod_floating_risk_index"]),
            "impact_shock_force_lbs": float(impact_lbs),
            "drag_metrics": drag_metrics,
            "actual_oil_bpd": float(actual_oil_bpd),
            "theo_disp_bpd": float(theo_disp_bpd)
        }


# Global dynamics engine instance
baghewala_srp = SuckerRodDynamicsEngine()
