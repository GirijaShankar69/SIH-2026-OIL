"""
Sample Historical and Operational Data Generator for Baghewala Field
Produces calibrated field datasets for 6 major heavy oil wells in Rajasthan.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any


WELLS_METADATA = [
    {
        "well_id": "BGW-01",
        "name": "Baghewala-01 (Discovery Well)",
        "formation": "Jodhpur Sandstone (Unit-A)",
        "depth_m": 1045.0,
        "pay_thickness_m": 19.5,
        "permeability_md": 320.0,
        "porosity": 0.25,
        "api_gravity": 18.4,
        "current_css_cycle": 3,
        "status": "Active Production",
        "days_in_current_cycle": 42,
        "surface_unit": "Mark II M-320D-256-120",
        "rod_string": "76% 7/8\" + 24% 3/4\" Grade D",
        "pump_type": "2.25\" Insert Rod Pump (RHAM)",
        "vfd_installed": True,
        "current_spm": 5.4,
        "stroke_length_m": 2.54,
        "latitude": 27.6842,
        "longitude": 72.8241
    },
    {
        "well_id": "BGW-04",
        "name": "Baghewala-04 (Thermal Pilot)",
        "formation": "Jodhpur Sandstone (Unit-A/B)",
        "depth_m": 1052.0,
        "pay_thickness_m": 22.0,
        "permeability_md": 380.0,
        "porosity": 0.26,
        "api_gravity": 18.0,
        "current_css_cycle": 4,
        "status": "Active Production (Rod Float Alert)",
        "days_in_current_cycle": 78,
        "surface_unit": "Conventional C-456-305-144",
        "rod_string": "70% 7/8\" + 30% 3/4\" Grade D",
        "pump_type": "2.25\" Tubing Pump (THM)",
        "vfd_installed": True,
        "current_spm": 6.8,
        "stroke_length_m": 2.80,
        "latitude": 27.6910,
        "longitude": 72.8315
    },
    {
        "well_id": "BGW-07",
        "name": "Baghewala-07 (North Flank)",
        "formation": "Jodhpur Sandstone (Unit-B)",
        "depth_m": 1038.0,
        "pay_thickness_m": 16.5,
        "permeability_md": 240.0,
        "porosity": 0.23,
        "api_gravity": 17.6,
        "current_css_cycle": 2,
        "status": "Steam Soaking (Shut-in)",
        "days_in_current_cycle": 4,
        "surface_unit": "Mark II M-320D-256-120",
        "rod_string": "80% 7/8\" + 20% 3/4\" Grade KD",
        "pump_type": "2.00\" Insert Rod Pump",
        "vfd_installed": True,
        "current_spm": 0.0,
        "stroke_length_m": 2.54,
        "latitude": 27.6985,
        "longitude": 72.8210
    },
    {
        "well_id": "BGW-09",
        "name": "Baghewala-09 (Central Crest)",
        "formation": "Jodhpur Sandstone (Unit-A)",
        "depth_m": 1048.0,
        "pay_thickness_m": 21.0,
        "permeability_md": 350.0,
        "porosity": 0.25,
        "api_gravity": 18.6,
        "current_css_cycle": 5,
        "status": "Active Production (Optimized)",
        "days_in_current_cycle": 24,
        "surface_unit": "Mark II M-456-305-144",
        "rod_string": "75% 7/8\" + 25% 3/4\" Special Alloy",
        "pump_type": "2.25\" Insert Rod Pump",
        "vfd_installed": True,
        "current_spm": 6.2,
        "stroke_length_m": 2.54,
        "latitude": 27.6880,
        "longitude": 72.8280
    },
    {
        "well_id": "BGW-12",
        "name": "Baghewala-12 (South Flank)",
        "formation": "Jodhpur Sandstone (Unit-C)",
        "depth_m": 1065.0,
        "pay_thickness_m": 15.0,
        "permeability_md": 210.0,
        "porosity": 0.22,
        "api_gravity": 17.2,
        "current_css_cycle": 2,
        "status": "Active Production (Cycle Cutoff Due)",
        "days_in_current_cycle": 115,
        "surface_unit": "Conventional C-320-256-120",
        "rod_string": "70% 7/8\" + 30% 3/4\" Grade D",
        "pump_type": "2.00\" Insert Rod Pump",
        "vfd_installed": False,
        "current_spm": 5.8,
        "stroke_length_m": 2.54,
        "latitude": 27.6790,
        "longitude": 72.8190
    },
    {
        "well_id": "BGW-15",
        "name": "Baghewala-15 (East Stepout)",
        "formation": "Jodhpur Sandstone (Unit-A)",
        "depth_m": 1055.0,
        "pay_thickness_m": 18.0,
        "permeability_md": 290.0,
        "porosity": 0.24,
        "api_gravity": 18.1,
        "current_css_cycle": 3,
        "status": "Steam Injection Phase",
        "days_in_current_cycle": 8,
        "surface_unit": "Mark II M-320D-256-120",
        "rod_string": "75% 7/8\" + 25% 3/4\" Grade D",
        "pump_type": "2.25\" Insert Rod Pump",
        "vfd_installed": True,
        "current_spm": 0.0,
        "stroke_length_m": 2.54,
        "latitude": 27.6865,
        "longitude": 72.8390
    }
]


def generate_historical_failure_logs() -> pd.DataFrame:
    """Generates historical equipment failure logs for Baghewala Field."""
    failures = [
        {"date": "2024-03-14", "well_id": "BGW-04", "cycle": 2, "day_in_cycle": 65, "event": "Sucker Rod Parted", "depth_m": 620, "root_cause": "Severe Rod Floating & Downstroke Impact Shock", "downtime_days": 4.5, "repair_cost_inr": 285000},
        {"date": "2024-06-22", "well_id": "BGW-12", "cycle": 1, "day_in_cycle": 82, "event": "Pump Unsetting", "depth_m": 1010, "root_cause": "Carrier Bar Separation & Bottomhole Impact Rebound", "downtime_days": 3.0, "repair_cost_inr": 195000},
        {"date": "2024-09-05", "well_id": "BGW-01", "cycle": 2, "day_in_cycle": 94, "event": "Rod Pin Fatigue Failure", "depth_m": 450, "root_cause": "Cyclic High Viscous Overload (> 1200 cP)", "downtime_days": 4.0, "repair_cost_inr": 240000},
        {"date": "2024-11-18", "well_id": "BGW-09", "cycle": 3, "day_in_cycle": 72, "event": "Asphaltene Deposition & Valve Jamming", "depth_m": 995, "root_cause": "Temperature Drop below Asphaltene Onset Point (64°C)", "downtime_days": 2.5, "repair_cost_inr": 160000},
        {"date": "2025-02-10", "well_id": "BGW-04", "cycle": 3, "day_in_cycle": 70, "event": "Sucker Rod Buckling & Tubing Wear", "depth_m": 710, "root_cause": "Negative Rod Tension on Downstroke (Rod Float)", "downtime_days": 5.0, "repair_cost_inr": 340000},
        {"date": "2025-05-29", "well_id": "BGW-15", "cycle": 2, "day_in_cycle": 88, "event": "Traveling Valve Seal Failure", "depth_m": 1005, "root_cause": "Abrasive Sand & High Viscosity Fluid Pound", "downtime_days": 3.5, "repair_cost_inr": 210000}
    ]
    return pd.DataFrame(failures)


def generate_well_telemetry(well_id: str, days_count: int = 60) -> pd.DataFrame:
    """
    Generates physics-derived time series sensor telemetry for a given well asset.
    Derived directly from Boberg-Lantz thermal dissipation, Andrade viscosity kinetics,
    Gibbs 1D wave equation dynamics, and closed-loop VFD governor laws.
    """
    from core.physics.thermal_reservoir import CSSCycleParameters, baghewala_reservoir
    from core.physics.sucker_rod_dynamics import baghewala_srp

    well_meta = next((w for w in WELLS_METADATA if w["well_id"] == well_id), WELLS_METADATA[0])
    
    np.random.seed(hash(well_id) % 10000)
    time_index = pd.date_range(end=pd.Timestamp.now(), periods=days_count, freq='D')
    cycle_day = np.arange(1, days_count + 1)
    
    # 1. Boberg-Lantz Reservoir Physics Simulation
    cycle_num = int(well_meta.get("current_css_cycle", 3))
    sim_params = CSSCycleParameters(
        cycle_number=cycle_num,
        steam_volume_cwe=3600.0,
        injection_rate=250.0,
        soak_days=5.0,
        producing_days=max(days_count, 120)
    )
    sim = baghewala_reservoir.simulate_cycle(sim_params)

    temp_res_c = sim["temperature_reservoir_c"][:days_count]
    sandface_temp_c = sim["temperature_sandface_c"][:days_count]
    visc_cp = sim["viscosity_cp"][:days_count]
    oil_rate_bopd = sim["oil_rate_bopd"][:days_count]
    water_cut = sim["water_cut"][:days_count]
    p_res = sim["reservoir_pressure_bar"][:days_count]

    # 2. VFD Governor Law vs Fixed SPM
    is_auto = (well_id in ["BGW-01", "BGW-09"])
    spm = np.zeros(days_count)
    if is_auto:
        for i in range(days_count):
            t = temp_res_c[i]
            mu = visc_cp[i]
            if t >= 120.0:
                spm[i] = 7.4
            elif t >= 85.0:
                spm[i] = 6.2 - 0.7 * ((120.0 - t) / 35.0)
            else:
                spm[i] = 4.2 - 0.5 * np.clip((mu - 250.0) / 1200.0, 0.0, 1.0)
    else:
        fixed_val = float(well_meta.get("current_spm", 5.5))
        spm[:] = fixed_val if fixed_val > 0 else 5.5

    # 3. Sucker Rod Wave Equation Dynamics
    stroke_m = float(well_meta.get("stroke_length_m", 2.54))
    pprl_lbs = np.zeros(days_count)
    mprl_lbs = np.zeros(days_count)
    motor_power_kw = np.zeros(days_count)
    float_risk = np.zeros(days_count)
    is_float = np.zeros(days_count, dtype=bool)
    wellhead_temp_c = np.zeros(days_count)

    for i in range(days_count):
        srp_out = baghewala_srp.solve_wave_equation(
            temperature_c=float(temp_res_c[i]),
            viscosity_cp=float(visc_cp[i]),
            bottomhole_pressure_bar=float(p_res[i] - 12.0),
            spm=float(spm[i]),
            stroke_length_m=stroke_m,
            pump_fillage=0.92
        )
        pprl_lbs[i] = srp_out["pprl_lbs"]
        mprl_lbs[i] = srp_out["mprl_lbs"]
        motor_power_kw[i] = srp_out["motor_power_kw"]
        float_risk[i] = srp_out["rod_floating_risk_index"]
        is_float[i] = srp_out["is_rod_floating"]
        wellhead_temp_c[i] = round(float(sandface_temp_c[i] * 0.78), 2)

    df = pd.DataFrame({
        "timestamp": time_index,
        "cycle_day": cycle_day,
        "wellhead_temp_c": wellhead_temp_c,
        "sandface_temp_c": np.round(sandface_temp_c, 2),
        "crude_viscosity_cp": np.round(visc_cp, 2),
        "spm": np.round(spm, 2),
        "oil_rate_bopd": np.round(oil_rate_bopd, 2),
        "water_cut": np.round(water_cut, 3),
        "motor_power_kw": np.round(motor_power_kw, 2),
        "pprl_lbs": np.round(pprl_lbs, 1),
        "mprl_lbs": np.round(mprl_lbs, 1),
        "rod_floating_risk": np.round(float_risk, 3),
        "is_rod_floating": is_float
    })

    return df

