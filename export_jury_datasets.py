"""
export_jury_datasets.py
One-command script to export all 5 training datasets as CSV files for SIH 2026 jury evaluation.
Run: python export_jury_datasets.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Fix Windows console encoding for emoji output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from core.data.sample_data_generator import (
    WELLS_METADATA, generate_well_telemetry, generate_historical_failure_logs
)
from core.ml.dyno_card_classifier import baghewala_card_classifier, DynoCardAIClassifier
from core.physics.sucker_rod_dynamics import baghewala_srp
import pandas as pd
import numpy as np

print("=" * 60)
print("  Baghewala Field Digital Twin — Jury Dataset Exporter")
print("  Oil India Limited | SIH 2026")
print("=" * 60)
print()

# ── Dataset 1: Reservoir & Geological Calibration ──────────────
df1 = pd.DataFrame(WELLS_METADATA)
df1.to_csv("jury_dataset_1_reservoir_geology.csv", index=False)
print(f"✅ Dataset 1 → jury_dataset_1_reservoir_geology.csv")
print(f"   Wells: {len(df1)} | Columns: {list(df1.columns)}")
print()

# ── Dataset 2: PVT & SARA Fluid Composition ────────────────────
df2_visc = pd.DataFrame({
    'temperature_c':   [47,   70,  100,  140,  180,  220],
    'viscosity_cp':    [2650, 620, 145,   42,   24,   18],
    'measurement_method': [
        'Rolling ball viscometer',
        'Rotational viscometer',
        'Rotational viscometer',
        'Capillary viscometer',
        'Capillary viscometer',
        'High-temp viscometer'
    ]
})
df2_sara = pd.DataFrame([{
    'Saturates_wt_pct':   34.0,
    'Aromatics_wt_pct':   29.5,
    'Resins_wt_pct':      22.0,
    'Asphaltenes_wt_pct': 14.5,
    'CII_Colloidal_Instability_Index': 0.94,
    'Asphaltene_Onset_Temp_C':         68.0,
    'Bubble_Point_Pressure_bar':        38.0,
    'Solution_GOR_sm3_m3':             14.0,
    'API_Gravity':                      18.2,
}])
df2_visc.to_csv("jury_dataset_2_pvt_viscosity.csv", index=False)
df2_sara.to_csv("jury_dataset_2_sara_composition.csv", index=False)
print(f"✅ Dataset 2a → jury_dataset_2_pvt_viscosity.csv  ({len(df2_visc)} viscosity calibration points)")
print(f"✅ Dataset 2b → jury_dataset_2_sara_composition.csv  (SARA fractions + PVT constants)")
print()

# ── Dataset 3: Dynamometer Card AI Training Corpus ─────────────
# Regenerate the training corpus from the same physics engine used to train the classifier
print("   Regenerating Dyno Card training corpus from physics engine...")
X_list, y_list = [], []
fault_configs = [
    ("normal",          0, 0.95, None),
    ("rod_floating",    1, 0.90, None),
    ("fluid_pound",     2, 0.55, "fluid_pound"),
    ("gas_interference",3, 0.70, "gas_interference"),
    ("unanchored_tubing",4,0.88, "unanchored_tubing"),
    ("valve_leak",      5, 0.85, "valve_leak"),
    ("standing_leak",   6, 0.85, "standing_leak"),
    ("pump_off",        7, 0.50, "pump_off"),
]
for temp_c in [48.0, 70.0, 110.0, 160.0, 210.0]:
    for visc in [18.0, 80.0, 800.0, 3200.0]:
        for spm in [4.0, 6.5, 8.5]:
            for fault_name, class_id, fillage, fault_type in fault_configs:
                try:
                    kw = dict(temperature_c=temp_c, viscosity_cp=visc,
                              bottomhole_pressure_bar=22.0, spm=spm, pump_fillage=fillage)
                    if fault_type:
                        kw['fault_type'] = fault_type
                    res = baghewala_srp.solve_wave_equation(**kw)
                    feats = baghewala_card_classifier.extract_features(
                        res["surface_position_in"], res["surface_load_lbs"]
                    )
                    # physics override for rod float
                    lbl = 1 if res["is_rod_floating"] and class_id == 0 else class_id
                    X_list.append(feats)
                    y_list.append(lbl)
                except Exception:
                    pass

feature_names = [
    'card_area_normalized', 'mprl_pprl_ratio', 'centroid_x', 'centroid_y',
    'downstroke_min_dip', 'impact_spike_amplitude', 'tilt_covariance_skew',
    'fourier_harmonic_1_magnitude', 'fourier_harmonic_2_magnitude',
    'fourier_harmonic_3_magnitude', 'upstroke_slope', 'peak_load_normalized_to_api_limit'
]
X_arr = np.array(X_list)
y_arr = np.array(y_list)
labels = baghewala_card_classifier.CARD_CLASSES

df3 = pd.DataFrame(X_arr, columns=feature_names[:X_arr.shape[1]])
df3['class_id']    = y_arr
df3['class_label'] = [labels[int(i)] for i in y_arr]
df3.to_csv("jury_dataset_3_dynocard_training.csv", index=False)
print(f"[OK] Dataset 3 exported: jury_dataset_3_dynocard_training.csv")
print(f"     Samples: {len(df3)} | Features: {X_arr.shape[1]} | Classes: {len(labels)}")
print(f"     Class distribution:")
for lbl in labels:
    cnt = (df3['class_label'] == lbl).sum()
    if cnt > 0:
        print(f"       {lbl}: {cnt} samples")
print()

# ── Dataset 4: CSS Production History (Physics-Simulated) ───────
all_dfs = []
for meta in WELLS_METADATA:
    df = generate_well_telemetry(meta['well_id'], days_count=120)
    df.insert(0, 'well_id', meta['well_id'])
    df.insert(1, 'css_cycle', meta['current_css_cycle'])
    all_dfs.append(df)
df4 = pd.concat(all_dfs, ignore_index=True)
df4.to_csv("jury_dataset_4_css_production_history.csv", index=False)
print(f"✅ Dataset 4 → jury_dataset_4_css_production_history.csv")
print(f"   Rows: {len(df4)} ({len(WELLS_METADATA)} wells × 120 days) | Columns: {len(df4.columns)}")
print()

# ── Dataset 5: Historical Failure Logs ──────────────────────────
logs = generate_historical_failure_logs()
df5 = pd.DataFrame(logs)
df5.to_csv("jury_dataset_5_failure_logs.csv", index=False)
print(f"✅ Dataset 5 → jury_dataset_5_failure_logs.csv")
print(f"   Records: {len(df5)} failure events | Columns: {list(df5.columns)}")
print()

print("=" * 60)
print("🎯 All 5 jury datasets exported successfully!")
print("   Hand these 7 CSV files to the jury for data review.")
print("=" * 60)
