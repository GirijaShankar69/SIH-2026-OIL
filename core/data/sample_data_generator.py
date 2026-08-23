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
    """Generates synthetic time series sensor telemetry for a given well."""
    well_meta = next((w for w in WELLS_METADATA if w["well_id"] == well_id), WELLS_METADATA[0])
    
    np.random.seed(hash(well_id) % 10000)
    time_index = pd.date_range(end=pd.Timestamp.now(), periods=days_count, freq='D')
    
    cycle_day = np.arange(1, days_count + 1)
    
    # Thermal decay
    t_init = 195.0
    temp_c = 47.0 + (t_init - 47.0) * np.exp(-np.sqrt(cycle_day / 28.0)) + np.random.normal(0, 1.2, days_count)
    temp_c = np.clip(temp_c, 47.0, 220.0)

    # Viscosity
    from core.physics.thermal_reservoir import baghewala_reservoir
    visc_cp = np.array([baghewala_reservoir.oil_viscosity(t) for t in temp_c])

    # Dynamic SPM vs Static SPM
    if well_id in ["BGW-01", "BGW-09"]:
        # AI Dynamic Control
        spm = np.clip(7.5 - 2.8 * (cycle_day / days_count), 4.2, 7.8) + np.random.normal(0, 0.05, days_count)
        is_float = np.zeros(days_count, dtype=bool)
        float_risk = np.clip((visc_cp - 200.0) / 1200.0 * 0.35, 0.05, 0.45)
    else:
        # Static control
        spm = np.full(days_count, well_meta["current_spm"])
        float_risk = np.clip((visc_cp - 180.0) / 750.0, 0.0, 1.0)
        is_float = (float_risk > 0.72) & (cycle_day > 35)

    # Production rates
    oil_rate_bopd = np.clip(160.0 * np.exp(-cycle_day / 35.0) + 12.0 + np.random.normal(0, 2.5, days_count), 8.0, 210.0)
    water_cut = np.clip(0.85 * np.exp(-cycle_day / 15.0) + 0.38 + 0.35 * (cycle_day / days_count), 0.30, 0.95)
    motor_power_kw = (spm * 2.1) + (visc_cp / 800.0) * 2.8 + np.random.normal(0, 0.3, days_count)
    pprl_lbs = 14500.0 + (spm * 450.0) + np.random.normal(0, 200.0, days_count)
    mprl_lbs = np.maximum(8200.0 - (visc_cp * 3.8) - np.random.normal(0, 150.0, days_count), 800.0)

    df = pd.DataFrame({
        "timestamp": time_index,
        "cycle_day": cycle_day,
        "wellhead_temp_c": temp_c * 0.78,
        "sandface_temp_c": temp_c,
        "crude_viscosity_cp": visc_cp,
        "spm": spm,
        "oil_rate_bopd": oil_rate_bopd,
        "water_cut": water_cut,
        "motor_power_kw": motor_power_kw,
        "pprl_lbs": pprl_lbs,
        "mprl_lbs": mprl_lbs,
        "rod_floating_risk": float_risk,
        "is_rod_floating": is_float
    })

    return df
