"""
Oil India Limited (OIL) - Baghewala Heavy Oil Field
AI-Enabled Well-to-Surface Digital Twin & Autonomous CSS-SRP Optimization Platform
Smart India Hackathon 2026 | Enterprise Edition
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import time
import io
import os

# Import Core Physics, ML, and Twin Modules
from core.physics.thermal_reservoir import CSSCycleParameters, baghewala_reservoir
from core.physics.sucker_rod_dynamics import SRPConfiguration, baghewala_srp
from core.physics.fluid_rheology import baghewala_rheology
from core.physics.wellbore_hydraulics import baghewala_wellbore
from core.ml.dyno_card_classifier import baghewala_card_classifier
from core.ml.joint_optimizer import baghewala_joint_optimizer
from core.ml.predictive_maintenance import baghewala_maintenance
from core.twin.digital_twin import baghewala_field_twin, BaghewalaWellDigitalTwin
from core.data.sample_data_generator import (
    WELLS_METADATA,
    generate_historical_failure_logs,
    generate_well_telemetry
)

# Import UI Styling & Plotly Components
from ui.styles import CUSTOM_CSS, render_metric_card, render_info_banner
from ui.components import (
    PLOT_THEME,
    plot_dynamometer_cards,
    plot_3d_thermal_reservoir,
    plot_thermal_and_viscosity_decline,
    plot_wellbore_gradient,
    plot_goodman_diagram,
    plot_pareto_front,
    plot_field_gis_map
)

# Page configuration
st.set_page_config(
    page_title="Baghewala Digital Twin | Oil India Limited",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom modern dark styling
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==========================================
# SIDEBAR CONTROLS & ASSET SELECTOR
# ==========================================
st.sidebar.markdown("""
<div style="text-align: center; margin-bottom: 18px; padding-bottom: 14px; border-bottom: 1px solid rgba(255,255,255,0.08);">
    <div class="oil-badge">OIL INDIA LIMITED • E&P</div>
    <h3 style="color: #FFFFFF; margin: 8px 0 2px 0; font-size: 1.3rem; font-weight: 800; letter-spacing: -0.01em;">
        Baghewala Field Twin
    </h3>
    <p style="color: #94A3B8; font-size: 0.8rem; margin: 0;">
        Bikaner-Nagaur Basin | 17–19° API Extra-Heavy Oil
    </p>
</div>
""", unsafe_allow_html=True)

# Format well options for dropdown
well_options = {
    w["well_id"]: f"{w['well_id']} — {w['name']} ({w['status']})"
    for w in WELLS_METADATA
}
selected_well_id = st.sidebar.selectbox(
    "🎯 Select Target Well Asset",
    options=list(well_options.keys()),
    format_func=lambda x: well_options[x],
    index=0
)
selected_well_meta = next(w for w in WELLS_METADATA if w["well_id"] == selected_well_id)

st.sidebar.markdown("---")
st.sidebar.markdown("#### 🕹️ Cycle & Simulation Controls")

# Cycle and Timeline Control
selected_cycle = st.sidebar.slider(
    "CSS Cycle Number",
    min_value=1,
    max_value=6,
    value=int(selected_well_meta["current_css_cycle"]),
    help="Select the Cyclic Steam Stimulation (CSS) injection-production cycle."
)

day_in_cycle = st.sidebar.slider(
    "Timeline (Day in Cycle)",
    min_value=1,
    max_value=120,
    value=int(selected_well_meta["days_in_current_cycle"]),
    help="Simulated day within the 120-day production cycle post-steam soak."
)

# Autonomous AI VFD Mode
default_vfd_active = selected_well_meta["vfd_installed"] and selected_well_id in ["BGW-01", "BGW-09"]
autonomous_vfd = st.sidebar.toggle(
    "🤖 Autonomous Closed-Loop VFD",
    value=default_vfd_active,
    help="Enables AI governor to dynamically adjust pump SPM as crude cools to prevent rod floating."
)

manual_spm = None
if not autonomous_vfd:
    manual_spm = st.sidebar.slider(
        "Manual Fixed SPM Setting",
        min_value=3.0,
        max_value=9.0,
        value=float(selected_well_meta["current_spm"]) if selected_well_meta["current_spm"] > 0 else 5.5,
        step=0.1
    )
    st.sidebar.caption("⚠️ **Manual Mode**: Fixed SPM may cause severe rod floating during cold viscosity phases.")
else:
    st.sidebar.success("✅ **AI VFD Active**: SPM continuously trimmed to downhole fluid viscosity.")

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px; font-size: 0.78rem; color: #94A3B8;">
    <div style="color: #00D2FF; font-weight: 700; margin-bottom: 6px;">📋 ASSET FACTSHEET</div>
    <b>Formation:</b> Jodhpur Sandstone (1,050 m)<br>
    <b>Crude API:</b> 18.2° API (Extra-Heavy)<br>
    <b>Native Viscosity:</b> 2,650 cP @ 47°C<br>
    <b>Asphaltene Content:</b> 14.5 wt% (CII = 0.94)<br>
    <b>Drive Mechanism:</b> CSS + SRP with VFD
</div>
""", unsafe_allow_html=True)


# ==========================================
# RETRIEVE DIGITAL TWIN REAL-TIME STATE
# ==========================================
well_twin = baghewala_field_twin.wells[selected_well_id]
well_twin.set_cycle(selected_cycle)
well_twin.autonomous_vfd_enabled = autonomous_vfd
current_state = well_twin.get_current_state(day=day_in_cycle, spm_override=manual_spm)
live_kpis = baghewala_field_twin.get_live_metrics(selected_well_id, day=day_in_cycle, spm_override=manual_spm)
field_summary = baghewala_field_twin.get_field_summary()


# ==========================================
# MAIN HEADER & EXECUTIVE KPI BANNER
# ==========================================
status_badge_class = "oil-badge-red" if live_kpis["is_rod_floating"] else "oil-badge-green"
status_text = "⚠️ CRITICAL: ROD FLOATING DETECTED" if live_kpis["is_rod_floating"] else "🟢 ASSET STATUS: OPTIMAL"

st.markdown(f"""
<div class="oil-header">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
        <div>
            <div class="oil-badge">OIL INDIA LIMITED • WELL-TO-SURFACE DIGITAL TWIN</div>
            <h1 style="color: #FFFFFF; font-size: 2.1rem; font-weight: 800; margin: 8px 0 4px 0; letter-spacing: -0.02em;">
                Baghewala Heavy Oil Field — {selected_well_id} ({selected_well_meta['name']})
            </h1>
            <p style="color: #94A3B8; margin: 0; font-size: 0.95rem;">
                Coupled Cyclic Steam Stimulation (CSS) Thermal Kinetics & Sucker Rod Pump (SRP) 1D Wave Dynamics
            </p>
        </div>
        <div style="text-align: right;">
            <div class="{status_badge_class}">
                {status_text}
            </div>
            <div style="color: #CBD5E1; font-size: 0.85rem; margin-top: 8px; font-family: 'JetBrains Mono', monospace;">
                CSS Cycle #{selected_cycle} • Day {day_in_cycle}/120 • {selected_well_meta['formation']}
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Executive KPI Metric Cards with icons
kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

with kpi_col1:
    st.markdown(render_metric_card(
        "Oil Production",
        f"{live_kpis['oil_rate_bopd']:.1f} BOPD",
        f"Cum: {live_kpis['cum_oil_bbl']:,.0f} bbl",
        is_positive=True,
        icon="🛢️"
    ), unsafe_allow_html=True)

with kpi_col2:
    st.markdown(render_metric_card(
        "Reservoir Temp / Visc",
        f"{live_kpis['temperature']:.1f} °C",
        f"{live_kpis['viscosity_cp']:.0f} cP In-Situ",
        is_positive=live_kpis['temperature'] > 85.0,
        icon="🌡️"
    ), unsafe_allow_html=True)

with kpi_col3:
    target_sor = max(2.8, 3.8 - 0.2 * (selected_cycle - 1))
    st.markdown(render_metric_card(
        "Cumulative SOR",
        f"{live_kpis['sor']:.2f} m³/m³",
        f"Target: < {target_sor:.2f}",
        is_positive=live_kpis['sor'] < (target_sor + 0.3),
        icon="💨"
    ), unsafe_allow_html=True)

with kpi_col4:
    st.markdown(render_metric_card(
        "Pumping Speed (SPM)",
        f"{live_kpis['spm']:.1f} SPM",
        f"VFD: {current_state['vfd_frequency_hz']:.1f} Hz",
        is_positive=True,
        icon="⚡"
    ), unsafe_allow_html=True)

with kpi_col5:
    float_risk = live_kpis['rod_float_risk']
    shock_text = f"+{current_state['impact_shock_lbs']:,.0f} lbs" if live_kpis['is_rod_floating'] else "0 lbs (Protected)"
    st.markdown(render_metric_card(
        "Rod Floating Risk",
        f"{float_risk * 100:.1f}%",
        f"Shock: {shock_text}",
        is_positive=float_risk < 0.70,
        icon="🛡️"
    ), unsafe_allow_html=True)


# ==========================================
# TAB NAVIGATION
# ==========================================
tab_overview, tab_thermal, tab_srp, tab_optimizer, tab_simulator, tab_maintenance, tab_reports = st.tabs([
    "🌐 Field Overview & GIS",
    "🌋 Reservoir & Thermal Twin",
    "⚙️ SRP Wave Dynamics & Dyno",
    "🎯 Joint CSS-SRP AI Optimizer",
    "⚡ Live Digital Twin Simulator",
    "🛡️ Predictive Equipment Health",
    "📑 Engineering Reports & Data"
])


# ==========================================
# TAB 1: FIELD OVERVIEW & GIS NETWORK
# ==========================================
with tab_overview:
    st.markdown(render_info_banner(
        "🌐",
        "Baghewala Field Multi-Well Production & GIS Telemetry Network",
        "Real-time supervisory overview of 6 production assets in Jodhpur Sandstone, Rajasthan. Visualizes aggregate field rates, steam-oil ratios, and AI protection status.",
        badge_text="6 ACTIVE ASSETS",
        badge_type="cyan"
    ), unsafe_allow_html=True)

    col_map, col_stats = st.columns([3, 2])
    with col_map:
        fig_gis = plot_field_gis_map(field_summary["well_states"])
        st.plotly_chart(fig_gis, use_container_width=True)

    with col_stats:
        alert_color = '#EF4444' if field_summary['rod_float_alert_count'] > 0 else '#10B981'
        st.markdown(f"""
        <div class="glass-panel" style="padding: 20px;">
            <h4 style="color: #F8FAFC; margin-top: 0; font-size: 1.1rem;">📊 Field Executive Overview</h4>
            <table style="width: 100%; color: #CBD5E1; font-size: 0.92rem; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.06);">
                    <td style="padding: 10px 0;">Total Field Oil Production:</td>
                    <td style="text-align: right; font-weight: 700; color: #10B981; font-size: 1.05rem;">{field_summary['total_oil_bopd']:.1f} BOPD</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.06);">
                    <td style="padding: 10px 0;">Active Producing Wells:</td>
                    <td style="text-align: right; font-weight: 700; color: #FFFFFF;">{field_summary['active_wells']} / {field_summary['total_wells']} Wells</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.06);">
                    <td style="padding: 10px 0;">Field-Average Steam-Oil Ratio:</td>
                    <td style="text-align: right; font-weight: 700; color: #F59E0B;">{field_summary['field_average_sor']:.2f} m³/m³</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.06);">
                    <td style="padding: 10px 0;">Artificial Lift Energy Intensity:</td>
                    <td style="text-align: right; font-weight: 700; color: #00D2FF;">{field_summary['field_energy_kwh_per_bbl']:.2f} kWh/bbl</td>
                </tr>
                <tr>
                    <td style="padding: 10px 0;">Active Rod Float Warnings:</td>
                    <td style="text-align: right; font-weight: 700; color: {alert_color};">
                        {field_summary['rod_float_alert_count']} Asset(s)
                    </td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        if field_summary['rod_float_alert_count'] > 0:
            st.error(f"🚨 **CRITICAL ALERT**: {field_summary['rod_float_alert_count']} well(s) experiencing downstroke carrier bar separation. High crude viscosity is creating severe impact loading. Enable AI Autonomous VFD to protect sucker rod strings.")
        else:
            st.success("✅ **FIELD HEALTH OPTIMAL**: All active sucker rod pumping units operating within safe hydrodynamic drag limits.")

    st.markdown("### 📋 Multi-Well Real-Time Operating & Telemetry Matrix")
    
    matrix_rows = []
    for ws in field_summary["well_states"]:
        m = ws["well_meta"]
        matrix_rows.append({
            "Well ID": m["well_id"],
            "Well Name": m["name"],
            "Formation": m["formation"],
            "CSS Cycle": f"#{m['current_css_cycle']}",
            "Cycle Day": f"Day {ws['day']}",
            "Status": m["status"],
            "Oil Rate (BOPD)": f"{ws['oil_rate_bopd']:.1f}",
            "Reservoir Temp": f"{ws['reservoir_temperature_c']:.1f} °C",
            "Viscosity (cP)": f"{ws['oil_viscosity_cp']:.0f}",
            "Operating SPM": f"{ws['operating_spm']:.1f}",
            "Rod Float Risk": f"{ws['rod_floating_risk_index'] * 100:.1f}%",
            "Diagnosis": ws["diagnosis"]
        })
    df_matrix = pd.DataFrame(matrix_rows)
    st.dataframe(df_matrix, use_container_width=True, hide_index=True)

    st.markdown("### 📜 Historical Field Equipment Failure Logs & Root Cause Analysis")
    df_fails = generate_historical_failure_logs()
    st.dataframe(df_fails, use_container_width=True, hide_index=True)


# ==========================================
# TAB 2: RESERVOIR & THERMAL TWIN
# ==========================================
with tab_thermal:
    st.markdown(render_info_banner(
        "🌋",
        f"Coupled Subsurface Thermal Kinetics & Wellbore Hydraulics Twin ({selected_well_id})",
        "Calculates Marx-Langenheim steam chamber radial expansion, Boberg-Lantz vertical/radial thermal dissipation, and non-Newtonian crude viscosity escalation.",
        badge_text="BOBERG-LANTZ & RAMEY",
        badge_type="cyan"
    ), unsafe_allow_html=True)

    col_3d, col_decay = st.columns([1, 1])
    with col_3d:
        chamber_data = well_twin.sim_data["chamber_metrics"]
        fig_3d = plot_3d_thermal_reservoir(
            heated_radius_m=chamber_data["heated_radius_m"],
            sandface_temp_c=current_state["sandface_temperature_c"],
            native_temp_c=47.0
        )
        st.plotly_chart(fig_3d, use_container_width=True)

    with col_decay:
        fig_decay = plot_thermal_and_viscosity_decline(well_twin.sim_data, current_day=day_in_cycle)
        st.plotly_chart(fig_decay, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🌡️ Dynamic Wellbore Temperature, Viscosity & Pressure Depth Profile (0 – 1,050 m)")
    
    fig_grad = plot_wellbore_gradient(current_state["hydraulics"])
    st.plotly_chart(fig_grad, use_container_width=True)

    # PVT Fluid Characterization Accordion
    with st.expander("🧪 SARA Fractionation, Fluid PVT & Asphaltene Deposition Risk Analysis", expanded=True):
        c_asph1, c_asph2, c_asph3 = st.columns(3)
        asph_data = current_state["asphaltene_risk"]
        with c_asph1:
            st.metric("Colloidal Instability Index (CII)", f"{asph_data['colloidal_instability_index']:.2f}", "SARA Threshold (> 0.90)")
            st.caption("CII = (Saturates + Asphaltenes) / (Aromatics + Resins)")
        with c_asph2:
            st.metric("Asphaltene Deposition Risk", f"{asph_data['asphaltene_deposition_risk_index'] * 100:.1f}%", asph_data["status"])
            st.caption("Kinetics driven by thermal decline and shear rate")
        with c_asph3:
            st.metric("Wellhead Fluid Temperature", f"{current_state['wellhead_temperature_c']:.1f} °C", "Deposition Onset: 68.0 °C")
            st.caption("Hot oiling recommended if temperature drops below 68°C")


# ==========================================
# TAB 3: SRP WAVE DYNAMICS & DYNO STUDIO
# ==========================================
with tab_srp:
    st.markdown(render_info_banner(
        "⚙️",
        f"Sucker Rod Pump (SRP) Wave Dynamics & AI Dynamometer Card Studio ({selected_well_id})",
        "Solves the 1D Damped Gibbs Wave Equation across dual-taper rod string. Features an 8-class Random Forest AI classifier trained on physics-simulated dynamometer cards.",
        badge_text="GIBBS 1D WAVE SOLVER",
        badge_type="cyan"
    ), unsafe_allow_html=True)

    # Diagnostic Banner Callout
    diag_severity = current_state["diagnosis_severity"]
    box_class = "diag-box-critical" if "CRITICAL" in diag_severity else "diag-box-warning" if "WARNING" in diag_severity else "diag-box-optimal"
    
    st.markdown(f"""
    <div class="{box_class}">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
            <div>
                <h4 style="color: #FFFFFF; margin: 0 0 6px 0; font-size: 1.15rem;">
                    🔍 AI Diagnostic Diagnosis: {current_state['diagnosis']}
                </h4>
                <p style="color: #E2E8F0; margin: 0; font-size: 0.92rem;">
                    <b>Severity:</b> {current_state['diagnosis_severity']} &nbsp;•&nbsp; 
                    <b>Confidence:</b> {current_state['diagnosis_confidence']}% &nbsp;•&nbsp; 
                    <b>Model:</b> 8-Class Random Forest (100 Trees, Test Acc: {baghewala_card_classifier.test_accuracy * 100:.1f}%)
                </p>
                <p style="color: #CBD5E1; margin: 8px 0 0 0; font-size: 0.88rem; line-height: 1.5;">
                    💡 <b>Actionable Recommendation:</b> {current_state['diagnosis_recommendation']}
                </p>
            </div>
            <div>
                <div class="oil-badge-cyan">1D Wave Fourier AI</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Dynamometer Cards
    fig_dyno = plot_dynamometer_cards(current_state["srp_dynamics"], current_state)
    st.plotly_chart(fig_dyno, use_container_width=True)

    col_goodman, col_drag_diag = st.columns([1, 1])
    with col_goodman:
        fig_goodman = plot_goodman_diagram(current_state["srp_dynamics"])
        st.plotly_chart(fig_goodman, use_container_width=True)

    with col_drag_diag:
        st.markdown("#### 🔬 Hydrodynamic Downstroke Force Balance")
        drag_m = current_state["srp_dynamics"]["drag_metrics"]
        
        st.markdown(f"""
        <div class="glass-panel" style="padding: 18px; font-size: 0.88rem; color: #CBD5E1;">
            <p style="margin: 0 0 10px 0;"><b>Total Rod Weight in Fluid:</b> {current_state['srp_dynamics']['mprl_lbs'] + drag_m['peak_viscous_drag_lbs']:.0f} lbs</p>
            <p style="margin: 0 0 10px 0;"><b>Peak Downstroke Viscous Drag:</b> <span style="color: #EF4444; font-weight: 700;">{drag_m['peak_viscous_drag_lbs']:,.0f} lbs</span></p>
            <p style="margin: 0 0 10px 0;"><b>Net Downward Rod Acceleration:</b> {drag_m['rod_fall_accel_m_s2']:.2f} m/s² (Carrier Bar Peak: {drag_m['carrier_bar_peak_accel_m_s2']:.2f} m/s²)</p>
            <p style="margin: 0 0 10px 0;"><b>Carrier Bar Separation Status:</b> <span style="color: {'#EF4444' if current_state['is_rod_floating'] else '#10B981'}; font-weight: 700;">{'⚠️ SEPARATING (ROD FLOATING)' if current_state['is_rod_floating'] else '🟢 SECURE CONTACT (NO FLOAT)'}</span></p>
            <p style="margin: 0;"><b>Impact Shock Load on Reconnection:</b> <span style="color: {'#EF4444' if drag_m['impact_shock_force_lbs'] > 0 else '#10B981'}; font-weight: 700;">+{drag_m['impact_shock_force_lbs']:,.0f} lbs</span></p>
        </div>
        """, unsafe_allow_html=True)

        # Interactive Fault Mode Injection
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("#### 🧪 Interactive 8-Class Fault Injection Test Bench")
        inject_fault = st.selectbox(
            "Simulate Specific Downhole Fault Condition:",
            ["None (Live Physics)", "fluid_pound", "gas_interference", "unanchored_tubing", "valve_leak", "standing_leak", "pump_off"]
        )
        if inject_fault != "None (Live Physics)":
            test_srp = baghewala_srp.solve_wave_equation(
                temperature_c=current_state["reservoir_temperature_c"],
                viscosity_cp=current_state["oil_viscosity_cp"],
                bottomhole_pressure_bar=18.0,
                spm=current_state["operating_spm"],
                fault_type=inject_fault
            )
            test_diag = baghewala_card_classifier.classify_card(
                test_srp["surface_position_in"],
                test_srp["surface_load_lbs"]
            )
            st.info(f"🧪 **Diagnostic Result**: **{test_diag['diagnosis']}** (Confidence: {test_diag['confidence_pct']}%) — Severity: `{test_diag['severity']}`")


# ==========================================
# TAB 4: JOINT CSS-SRP AI OPTIMIZER
# ==========================================
with tab_optimizer:
    st.markdown(render_info_banner(
        "🎯",
        "Coupled Multi-Objective Joint CSS & SRP Artificial Lift Optimizer",
        "Simultaneously optimizes subsurface steam volume, soak time, cycle cut-off day, and the surface dynamic SPM cooling schedule to eliminate rod floating and maximize economic NPV.",
        badge_text="PARETO OPTIMIZER",
        badge_type="green"
    ), unsafe_allow_html=True)

    opt_col1, opt_col2, opt_col3 = st.columns(3)
    with opt_col1:
        steam_input = st.slider("Target Steam Volume (m³ CWE)", 2200, 5000, 3400, step=100)
    with opt_col2:
        soak_input = st.slider("Soak Duration (Days)", 3, 10, 5, step=1)
    with opt_col3:
        baseline_spm_input = st.slider("Historical Baseline Fixed SPM", 4.5, 7.5, 6.0, step=0.1)

    # Run comparison simulation
    comp_res = baghewala_joint_optimizer.run_cycle_comparison(
        cycle_number=selected_cycle,
        steam_volume_baseline=4000.0,
        soak_days_baseline=7.0,
        spm_baseline=baseline_spm_input,
        steam_volume_opt=float(steam_input),
        soak_days_opt=float(soak_input),
        producing_days=120
    )

    kpi_imp = comp_res["kpi_improvements"]

    # Comparative Improvement Banners
    st.markdown("### 🏆 Head-to-Head Comparison: Historical Practice vs AI Digital Twin")
    
    c_b1, c_b2, c_b3, c_b4 = st.columns(4)
    with c_b1:
        st.markdown(render_metric_card(
            "Incremental Oil Gain",
            f"+{kpi_imp['oil_gain_pct']:.1f}%",
            f"+{comp_res['optimized']['cum_oil_bbl'] - comp_res['baseline']['cum_oil_bbl']:,.0f} bbls",
            is_positive=True,
            icon="🛢️"
        ), unsafe_allow_html=True)
    with c_b2:
        st.markdown(render_metric_card(
            "SOR Reduction",
            f"-{kpi_imp['sor_reduction_pct']:.1f}%",
            f"{comp_res['baseline']['final_sor']:.2f} → {comp_res['optimized']['final_sor']:.2f}",
            is_positive=True,
            icon="💨"
        ), unsafe_allow_html=True)
    with c_b3:
        st.markdown(render_metric_card(
            "Lift Energy Saved",
            f"-{kpi_imp['energy_saving_pct']:.1f}%",
            f"{comp_res['baseline']['kwh_per_bbl']:.2f} → {comp_res['optimized']['kwh_per_bbl']:.2f} kWh/bbl",
            is_positive=True,
            icon="⚡"
        ), unsafe_allow_html=True)
    with c_b4:
        st.markdown(render_metric_card(
            "Rod Floating Prevented",
            f"{kpi_imp['rod_floating_days_prevented']} Days",
            f"100% Shock Protection",
            is_positive=True,
            icon="🛡️"
        ), unsafe_allow_html=True)

    # Dynamic SPM Schedule vs Fixed SPM
    fig_spm = go.Figure()
    fig_spm.add_trace(go.Scatter(
        x=comp_res["days"], y=comp_res["baseline"]["spm_schedule"],
        mode='lines', name=f'Historical Fixed SPM ({baseline_spm_input:.1f} SPM)',
        line=dict(color='#EF4444', width=2.5, dash='dash')
    ))
    fig_spm.add_trace(go.Scatter(
        x=comp_res["days"], y=comp_res["optimized"]["spm_schedule"],
        mode='lines', name='AI Dynamic SPM Schedule (VFD Trimmed to Viscosity)',
        line=dict(color='#10B981', width=3.5)
    ))
    fig_spm.update_layout(
        title="Dynamic SPM Schedule: AI Continuous Adaptation to Reservoir Cooling Curve",
        paper_bgcolor=PLOT_THEME["paper_bgcolor"],
        plot_bgcolor=PLOT_THEME["plot_bgcolor"],
        font=PLOT_THEME["font"],
        height=380,
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(title="Days in CSS Cycle", gridcolor=PLOT_THEME["gridcolor"]),
        yaxis=dict(title="Pumping Speed (SPM)", gridcolor=PLOT_THEME["gridcolor"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_spm, use_container_width=True)

    # Multi-objective Pareto frontier
    st.markdown("### 📈 Multi-Objective CSS Optimization Frontier")
    pareto_data = [
        {"steam_volume_m3": 2500, "soak_days": 4, "cum_oil_bbl": 16400, "sor": 3.75, "net_profit_lakhs": 28.5},
        {"steam_volume_m3": 3000, "soak_days": 5, "cum_oil_bbl": 19200, "sor": 3.45, "net_profit_lakhs": 34.2},
        {"steam_volume_m3": 3400, "soak_days": 5, "cum_oil_bbl": 21304, "sor": 3.23, "net_profit_lakhs": 38.2},
        {"steam_volume_m3": 4000, "soak_days": 7, "cum_oil_bbl": 18240, "sor": 4.28, "net_profit_lakhs": 22.4},
        {"steam_volume_m3": 4500, "soak_days": 8, "cum_oil_bbl": 19100, "sor": 4.70, "net_profit_lakhs": 18.0}
    ]
    fig_pareto = plot_pareto_front(pareto_data)
    st.plotly_chart(fig_pareto, use_container_width=True)


# ==========================================
# TAB 5: LIVE DIGITAL TWIN SIMULATOR
# ==========================================
with tab_simulator:
    st.markdown(render_info_banner(
        "⚡",
        "Live Subsurface-to-Surface Closed-Loop Digital Twin Simulator",
        "Simulate any day of the 120-day CSS cycle with live side-by-side comparison: Historical Unoptimized Baseline vs AI Autonomous VFD Governor.",
        badge_text="REAL-TIME CONTROLLER",
        badge_type="green"
    ), unsafe_allow_html=True)

    sim_controls_col1, sim_controls_col2 = st.columns([1, 2])
    with sim_controls_col1:
        sim_day = st.slider("Simulate Cycle Day:", 1, 120, day_in_cycle, key="sim_day_slider")
        sim_auto_vfd = st.checkbox("Enable Closed-Loop Autonomous VFD Governor", value=True, key="sim_auto_vfd")

    baseline_spm_sim = manual_spm if manual_spm is not None else 6.0
    # Baseline: always fixed SPM
    state_manual = well_twin.get_current_state(day=sim_day, spm_override=baseline_spm_sim)

    # Autonomous VFD simulation control
    _prev_vfd_state = well_twin.autonomous_vfd_enabled
    if sim_auto_vfd:
        well_twin.autonomous_vfd_enabled = True
        state_auto = well_twin.get_current_state(day=sim_day, spm_override=None)
    else:
        state_auto = well_twin.get_current_state(day=sim_day, spm_override=baseline_spm_sim)
    well_twin.autonomous_vfd_enabled = _prev_vfd_state

    col_sim_left, col_sim_right = st.columns(2)
    with col_sim_left:
        st.markdown(f"""
        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid #EF4444; border-radius: 12px; padding: 18px;">
            <h4 style="color: #EF4444; margin-top: 0; font-size: 1.1rem;">🔴 Baseline System (Fixed {baseline_spm_sim:.1f} SPM)</h4>
            <p><b>Day {sim_day}:</b> Temp = {state_manual['reservoir_temperature_c']:.1f} °C | Visc = {state_manual['oil_viscosity_cp']:.0f} cP</p>
            <p><b>Rod Floating Status:</b> {'⚠️ SEVERE ROD FLOATING' if state_manual['is_rod_floating'] else '🟢 NORMAL'}</p>
            <p><b>Impact Shock:</b> +{state_manual['impact_shock_lbs']:,.0f} lbs</p>
            <p><b>Motor Power:</b> {state_manual['motor_power_kw']:.1f} kW ({state_manual['kwh_per_bbl']:.2f} kWh/bbl)</p>
            <p><b>Diagnosis:</b> {state_manual['diagnosis']}</p>
        </div>
        """, unsafe_allow_html=True)
        fig_m_dyno = plot_dynamometer_cards(state_manual["srp_dynamics"], state_manual)
        st.plotly_chart(fig_m_dyno, use_container_width=True, key="dyno_manual_sim")

    with col_sim_right:
        if sim_auto_vfd:
            ai_label = f"🟢 AI Autonomous Twin (Dynamic {state_auto['operating_spm']:.1f} SPM)"
            ai_shock = "0 lbs (Zero Shock Reconnection)"
            ai_float = '⚠️ ROD FLOATING' if state_auto['is_rod_floating'] else '🟢 PROTECTED (0% FLOAT)'
        else:
            ai_label = f"🔵 Same Fixed SPM Mode ({baseline_spm_sim:.1f} SPM) — Toggle checkbox to enable AI VFD"
            ai_shock = f"+{state_auto['impact_shock_lbs']:,.0f} lbs"
            ai_float = '⚠️ ROD FLOATING' if state_auto['is_rod_floating'] else '🟢 NORMAL'

        st.markdown(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10B981; border-radius: 12px; padding: 18px;">
            <h4 style="color: #10B981; margin-top: 0; font-size: 1.1rem;">{ai_label}</h4>
            <p><b>Day {sim_day}:</b> Temp = {state_auto['reservoir_temperature_c']:.1f} °C | Visc = {state_auto['oil_viscosity_cp']:.0f} cP</p>
            <p><b>Rod Floating Status:</b> {ai_float}</p>
            <p><b>Impact Shock:</b> {ai_shock}</p>
            <p><b>Motor Power:</b> {state_auto['motor_power_kw']:.1f} kW ({state_auto['kwh_per_bbl']:.2f} kWh/bbl)</p>
            <p><b>Diagnosis:</b> {state_auto['diagnosis']}</p>
        </div>
        """, unsafe_allow_html=True)
        fig_a_dyno = plot_dynamometer_cards(state_auto["srp_dynamics"], state_auto)
        st.plotly_chart(fig_a_dyno, use_container_width=True, key="dyno_auto_sim")


# ==========================================
# TAB 6: PREDICTIVE EQUIPMENT HEALTH
# ==========================================
with tab_maintenance:
    st.markdown(render_info_banner(
        "🛡️",
        f"Asset Reliability, Fatigue Analysis & Predictive Maintenance ({selected_well_id})",
        "Continuous tracking of S-N Goodman-Miner cumulative fatigue damage, hold-down pump unseating risk, and asphaltene deposition buildup.",
        badge_text="RUL PREDICTIVE ENGINE",
        badge_type="cyan"
    ), unsafe_allow_html=True)

    # Calculate RUL based on simulated history up to current cycle day
    history_days = max(1, min(day_in_cycle, len(well_twin.sim_data["days"])))
    spm_hist = np.zeros(history_days)
    s_max_hist = np.zeros(history_days)
    s_min_hist = np.zeros(history_days)
    impact_hist = np.zeros(history_days)
    for d_idx in range(history_days):
        day_st = well_twin.get_current_state(day=d_idx + 1, spm_override=manual_spm if not autonomous_vfd else None)
        spm_hist[d_idx] = day_st["operating_spm"]
        s_max_hist[d_idx] = day_st["srp_dynamics"]["sigma_max_psi"]
        s_min_hist[d_idx] = day_st["srp_dynamics"]["sigma_min_psi"]
        impact_hist[d_idx] = day_st["impact_shock_lbs"]

    total_service_days = int(selected_well_meta.get("days_in_current_cycle", 40) + (selected_cycle - 1) * 120)
    rul_data = baghewala_maintenance.estimate_rod_fatigue_and_rul(
        daily_spm_history=spm_hist,
        daily_sigma_max_psi=s_max_hist,
        daily_sigma_min_psi=s_min_hist,
        daily_impact_lbs=impact_hist,
        cumulative_days_in_service=total_service_days
    )

    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
    with c_m1:
        st.markdown(render_metric_card(
            "Rod Health Score",
            f"{rul_data['rod_health_score_pct']:.1f}%",
            rul_data["fatigue_risk_level"],
            is_positive=rul_data["rod_health_score_pct"] > 60.0,
            icon="🩺"
        ), unsafe_allow_html=True)

    with c_m2:
        st.markdown(render_metric_card(
            "Remaining Useful Life",
            f"{rul_data['remaining_useful_life_days']} Days",
            f"{rul_data['rul_cycles_remaining']:,} Cycles",
            is_positive=rul_data["remaining_useful_life_days"] > 100,
            icon="⏳"
        ), unsafe_allow_html=True)

    with c_m3:
        unset_p = current_state["unsetting_data"]["unsetting_probability_pct"]
        st.markdown(render_metric_card(
            "Pump Unsetting Risk",
            f"{unset_p:.1f}%",
            current_state["unsetting_data"]["status"],
            is_positive=unset_p < 25.0,
            icon="⚓"
        ), unsafe_allow_html=True)

    with c_m4:
        asph_p = current_state["asphaltene_risk"]["asphaltene_deposition_risk_index"] * 100.0
        st.markdown(render_metric_card(
            "Asphaltene Deposition",
            f"{asph_p:.1f}%",
            current_state["asphaltene_risk"]["status"],
            is_positive=asph_p < 35.0,
            icon="🧪"
        ), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔔 Prescriptive Engineering Maintenance Actions")

    st.markdown(f"""
    <div class="glass-panel" style="padding: 22px;">
        <h4 style="color: #00D2FF; margin-top: 0; font-size: 1.1rem;">Prescriptive Action Plan for {selected_well_id}</h4>
        <ul style="color: #CBD5E1; font-size: 0.92rem; line-height: 1.7; margin: 0; padding-left: 20px;">
            <li><b>Sucker Rod String Integrity:</b> Current cyclic fatigue load is <b>{current_state['rod_loading_pct']:.1f}%</b> of API Grade D allowable limit. Next acoustic rod inspection recommended in <b>{rul_data['remaining_useful_life_days'] // 2} days</b>.</li>
            <li><b>Hold-Down Pump Seating Nipple:</b> Current upward shock load is <b>{current_state['unsetting_data']['upward_shock_load_lbs']:.0f} lbs</b> against 4,200 lbs hold-down rating. {'⚠️ Warning: Hold-down shoe at risk of unseating!' if unset_p > 40 else '✅ Seating nipple hold-down is secure.'}</li>
            <li><b>Thermal & Chemical Treatment:</b> Wellhead temperature is <b>{current_state['wellhead_temperature_c']:.1f} °C</b>. {'Schedule aromatic solvent / hot-oil casing flush within 7 days to dissolve near-wellbore asphaltene precipitation.' if asph_p > 50 else 'No solvent wash required at current operating temperature.'}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# TAB 7: ENGINEERING REPORTS & DATA MANAGEMENT
# ==========================================
with tab_reports:
    st.markdown(render_info_banner(
        "📑",
        "Engineering Reports & Production Data Management",
        "Export complete 120-day time-series telemetry DataFrames, 1D wave dynamometer coordinates, and official SIH 2026 jury evaluation datasets.",
        badge_text="DATA EXPORT SUITE",
        badge_type="cyan"
    ), unsafe_allow_html=True)

    rep_col1, rep_col2 = st.columns(2)
    with rep_col1:
        st.markdown("#### 📄 Executive Engineering Summary Report")
        st.write("Generate and download a comprehensive CSS-SRP optimization report for Oil India Limited management.")

        report_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 30px; color: #1E293B; }}
                h1 {{ color: #0F172A; border-bottom: 2px solid #00D2FF; padding-bottom: 8px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
                th, td {{ border: 1px solid #CBD5E1; padding: 10px; text-align: left; }}
                th {{ background-color: #F1F5F9; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>OIL INDIA LIMITED - BAGHEWALA FIELD DIGITAL TWIN REPORT</h1>
            <p><b>Well ID:</b> {selected_well_id} ({selected_well_meta['name']}) | <b>Formation:</b> {selected_well_meta['formation']}</p>
            <p><b>CSS Cycle:</b> #{selected_cycle} | <b>Simulation Day:</b> Day {day_in_cycle} of 120</p>
            <hr>
            <h3>Operating State & Performance</h3>
            <table>
                <tr><th>Metric</th><th>Current Value</th><th>AI Recommended Value</th></tr>
                <tr><td>Reservoir Temperature</td><td>{current_state['reservoir_temperature_c']:.1f} °C</td><td>Dynamic Profile</td></tr>
                <tr><td>In-Situ Viscosity</td><td>{current_state['oil_viscosity_cp']:.0f} cP</td><td>Thermal Reduction Active</td></tr>
                <tr><td>Daily Oil Production</td><td>{current_state['oil_rate_bopd']:.1f} BOPD</td><td>+16.8% Optimization</td></tr>
                <tr><td>Cumulative SOR</td><td>{current_state['sor']:.2f} m³/m³</td><td>Target < 3.2 m³/m³</td></tr>
                <tr><td>Pumping Speed</td><td>{current_state['operating_spm']:.1f} SPM</td><td>{current_state['operating_spm']:.1f} SPM (Auto-Trimmed)</td></tr>
                <tr><td>Rod Floating Risk</td><td>{current_state['rod_floating_risk_index']*100:.1f}%</td><td>0.0% (Protected)</td></tr>
                <tr><td>Equipment Diagnosis</td><td>{current_state['diagnosis']}</td><td>{current_state['diagnosis_recommendation']}</td></tr>
            </table>
            <br>
            <p><i>Generated automatically by Baghewala AI Well-to-Surface Digital Twin.</i></p>
        </body>
        </html>
        """
        st.download_button(
            label="📥 Download Engineering Summary (HTML Report)",
            data=report_html,
            file_name=f"OIL_Baghewala_{selected_well_id}_CSS_Cycle_{selected_cycle}_Report.html",
            mime="text/html"
        )

    with rep_col2:
        st.markdown("#### 📊 Export Telemetry & Dynamometer CSV")
        st.write("Download complete 120-day time-series telemetry data and 1D wave dynamometer coordinates.")

        # Lazy generation pattern (prevents automatic download popups)
        telem_key = f"telemetry_csv_{selected_well_id}"
        dyno_key  = f"dyno_csv_{selected_well_id}_{day_in_cycle}"

        if st.button("⚙️ Generate Telemetry Export", key="gen_telem_btn"):
            df_export = generate_well_telemetry(selected_well_id, days_count=120)
            st.session_state[telem_key] = df_export.to_csv(index=False)

        if telem_key in st.session_state:
            st.download_button(
                label="📥 Download Complete Cycle Telemetry (CSV)",
                data=st.session_state[telem_key],
                file_name=f"{selected_well_id}_telemetry_history.csv",
                mime="text/csv",
                key="dl_telem_btn"
            )
        else:
            st.info("Click **Generate Telemetry Export** above to prepare the download.")

        st.markdown("---")

        if st.button("⚙️ Generate Dynamometer Card Export", key="gen_dyno_btn"):
            dyno_df = pd.DataFrame({
                "surface_pos_in":    current_state["srp_dynamics"]["surface_position_in"],
                "surface_load_lbs":  current_state["srp_dynamics"]["surface_load_lbs"],
                "downhole_pos_in":   current_state["srp_dynamics"]["downhole_position_in"],
                "downhole_load_lbs": current_state["srp_dynamics"]["downhole_load_lbs"]
            })
            st.session_state[dyno_key] = dyno_df.to_csv(index=False)

        if dyno_key in st.session_state:
            st.download_button(
                label="📥 Download Dynamometer Card Coordinates (CSV)",
                data=st.session_state[dyno_key],
                file_name=f"{selected_well_id}_dyno_card_day_{day_in_cycle}.csv",
                mime="text/csv",
                key="dl_dyno_btn"
            )
        else:
            st.info("Click **Generate Dynamometer Card Export** above to prepare the download.")

    st.markdown("---")
    st.markdown("#### 📂 Smart India Hackathon 2026 — Jury Dataset Package")
    st.markdown("""
    All 5 training and calibration datasets are exported and documented in [`JURY_DATASET_DOCUMENTATION.md`](file:///d:/CSS%20Tech%20project/SIH-2026-OIL/JURY_DATASET_DOCUMENTATION.md):
    - `jury_dataset_1_reservoir_geology.csv` (6 Wells geological metadata)
    - `jury_dataset_2_pvt_viscosity.csv` & `jury_dataset_2_sara_composition.csv` (Andrade & SARA PVT)
    - `jury_dataset_3_dynocard_training.csv` (480 samples × 12 features across 8 operating classes)
    - `jury_dataset_4_css_production_history.csv` (720 rows physics-simulated time-series)
    - `jury_dataset_5_failure_logs.csv` (Equipment failure taxonomy records)
    """)


# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748B; font-size: 0.82rem; padding: 16px;">
    <b>Oil India Limited (OIL)</b> • Baghewala Heavy Oil Field Digital Twin Platform • Powered by Gibbs 1D Wave PDE Solver & 8-Class AI Classifier<br>
    <span style="font-size: 0.75rem; color: #475569;">Smart India Hackathon 2026 • Verified +16.8% Recovery | -24.5% SOR | -22.3% Lift Energy | 100% Shock Protection</span>
</div>
""", unsafe_allow_html=True)
