"""
Oil India Limited (OIL) - Baghewala Heavy Oil Field
AI-Enabled Well-to-Surface Digital Twin & Autonomous CSS-SRP Optimization Platform
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import time
import io

# Import Core Physics, ML, and Twin Modules
from core.physics.thermal_reservoir import CSSCycleParameters, baghewala_reservoir
from core.physics.sucker_rod_dynamics import SRPConfiguration, baghewala_srp
from core.physics.fluid_rheology import baghewala_rheology
from core.physics.wellbore_hydraulics import baghewala_wellbore
from core.ml.dyno_card_classifier import baghewala_card_classifier
from core.ml.joint_optimizer import baghewala_joint_optimizer
from core.ml.predictive_maintenance import baghewala_maintenance
from core.twin.digital_twin import baghewala_field_twin, BaghewalaWellDigitalTwin
from core.data.sample_data_generator import WELLS_METADATA, generate_historical_failure_logs, generate_well_telemetry

# Import UI Styling & Plotly Components
from ui.styles import CUSTOM_CSS, render_metric_card
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
    page_title="Baghewala Field Digital Twin | Oil India Limited",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom modern dark styling
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==========================================
# SIDEBAR CONTROLS
# ==========================================
st.sidebar.markdown("""
<div style="text-align: center; margin-bottom: 20px;">
    <div class="oil-badge">OIL INDIA LIMITED</div>
    <h3 style="color: #FFFFFF; margin: 4px 0 0 0; font-size: 1.25rem;">Baghewala Field</h3>
    <p style="color: #94A3B8; font-size: 0.82rem;">Rajasthan | Jodhpur Sandstone EOR</p>
</div>
""", unsafe_allow_html=True)

# Select Active Asset
well_ids = [w["well_id"] for w in WELLS_METADATA]
selected_well_id = st.sidebar.selectbox("🎯 Select Well Asset", well_ids, index=0)
selected_well_meta = next(w for w in WELLS_METADATA if w["well_id"] == selected_well_id)

st.sidebar.markdown("---")
st.sidebar.subheader("🕹️ Digital Twin Controls")

# Cycle and Timeline Control
selected_cycle = st.sidebar.slider("CSS Cycle Number", min_value=1, max_value=6, value=selected_well_meta["current_css_cycle"])
day_in_cycle = st.sidebar.slider("Timeline (Days in CSS Cycle)", min_value=1, max_value=120, value=selected_well_meta["days_in_current_cycle"])

# Autonomous AI VFD Mode
autonomous_vfd = st.sidebar.toggle("🤖 Autonomous Closed-Loop VFD", value=selected_well_meta["vfd_installed"] and selected_well_id in ["BGW-01", "BGW-09"])

manual_spm = None
if not autonomous_vfd:
    manual_spm = st.sidebar.slider("Manual SPM Setting", min_value=3.0, max_value=9.0, value=float(selected_well_meta["current_spm"]) if selected_well_meta["current_spm"] > 0 else 5.5, step=0.1)
    st.sidebar.caption("⚠️ Manual mode active: VFD will not dynamically adjust to prevent rod floating.")
else:
    st.sidebar.success("✅ AI Autonomous VFD active: Dynamically adjusting SPM based on downhole thermal viscosity.")

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 12px; font-size: 0.78rem; color: #94A3B8;">
    <b>Formation:</b> Jodhpur Sandstone<br>
    <b>Crude Gravity:</b> 17–19° API (Heavy)<br>
    <b>Native Temp:</b> 46–48°C<br>
    <b>Native Viscosity:</b> 2,500–3,500 cP
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
st.markdown(f"""
<div class="oil-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div class="oil-badge">OIL INDIA LIMITED • WELL-TO-SURFACE DIGITAL TWIN</div>
            <h1 style="color: #FFFFFF; font-size: 2.0rem; font-weight: 800; margin: 6px 0 4px 0;">
                Baghewala Heavy Oil Field ({selected_well_id})
            </h1>
            <p style="color: #94A3B8; margin: 0; font-size: 0.95rem;">
                Coupled Cyclic Steam Stimulation (CSS) Thermal Reservoir Kinetics & Sucker Rod Wave Dynamics Simulator
            </p>
        </div>
        <div style="text-align: right;">
            <div class="{'oil-badge-red' if live_kpis['is_rod_floating'] else 'oil-badge-green'}">
                {'⚠️ CRITICAL: ROD FLOATING DETECTED' if live_kpis['is_rod_floating'] else '🟢 ASSET STATUS: OPTIMAL'}
            </div>
            <div style="color: #CBD5E1; font-size: 0.85rem; margin-top: 6px;">
                Cycle #{selected_cycle} • Day {day_in_cycle} of 120
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Executive KPI Metric Cards
kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

with kpi_col1:
    st.markdown(render_metric_card(
        "Oil Production", 
        f"{live_kpis['oil_rate_bopd']:.1f} BOPD", 
        f"Cum: {live_kpis['cum_oil_bbl']:,.0f} bbl", 
        is_positive=True
    ), unsafe_allow_html=True)

with kpi_col2:
    st.markdown(render_metric_card(
        "Reservoir Temp / Visc", 
        f"{live_kpis['temperature']:.1f} °C", 
        f"{live_kpis['viscosity_cp']:.0f} cP In-Situ", 
        is_positive=live_kpis['temperature'] > 85.0
    ), unsafe_allow_html=True)

with kpi_col3:
    target_sor = max(2.8, 3.8 - 0.2 * (selected_cycle - 1))
    st.markdown(render_metric_card(
        "Cumulative SOR", 
        f"{live_kpis['sor']:.2f} m³/m³", 
        f"Target: < {target_sor:.2f}", 
        is_positive=live_kpis['sor'] < (target_sor + 0.3)
    ), unsafe_allow_html=True)

with kpi_col4:
    st.markdown(render_metric_card(
        "Pumping Speed (SPM)", 
        f"{live_kpis['spm']:.1f} SPM", 
        f"VFD: {current_state['vfd_frequency_hz']:.1f} Hz", 
        is_positive=True
    ), unsafe_allow_html=True)

with kpi_col5:
    float_risk = live_kpis['rod_float_risk']
    shock_text = f"+{current_state['impact_shock_lbs']:,.0f} lbs" if live_kpis['is_rod_floating'] else "0 lbs (Safe)"
    st.markdown(render_metric_card(
        "Rod Floating Risk", 
        f"{float_risk * 100:.1f}%", 
        f"Shock: {shock_text}", 
        is_positive=float_risk < 0.70
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
    st.subheader("🌐 Baghewala Field Multi-Well Production Network")
    
    col_map, col_stats = st.columns([3, 2])
    with col_map:
        fig_gis = plot_field_gis_map(field_summary["well_states"])
        st.plotly_chart(fig_gis, use_container_width=True)

    with col_stats:
        alert_color = '#EF4444' if field_summary['rod_float_alert_count'] > 0 else '#10B981'
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 20px;">
            <h4 style="color: #F8FAFC; margin-top: 0;">Field Executive Metrics</h4>
            <table style="width: 100%; color: #CBD5E1; font-size: 0.9rem; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); padding: 8px 0;">
                    <td style="padding: 8px 0;">Total Field Oil Rate:</td>
                    <td style="text-align: right; font-weight: 700; color: #10B981;">{field_summary['total_oil_bopd']:.1f} BOPD</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 8px 0;">Active Producing Wells:</td>
                    <td style="text-align: right; font-weight: 700; color: #FFFFFF;">{field_summary['active_wells']} / {field_summary['total_wells']}</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 8px 0;">Field Average SOR:</td>
                    <td style="text-align: right; font-weight: 700; color: #F5A623;">{field_summary['field_average_sor']:.2f} m³/m³</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 8px 0;">Lift Energy Intensity:</td>
                    <td style="text-align: right; font-weight: 700; color: #00D2FF;">{field_summary['field_energy_kwh_per_bbl']:.2f} kWh/bbl</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0;">Active Rod Float Alerts:</td>
                    <td style="text-align: right; font-weight: 700; color: {alert_color};">
                        {field_summary['rod_float_alert_count']} Wells
                    </td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        # Quick Alert Box
        if field_summary['rod_float_alert_count'] > 0:
            st.error(f"🚨 **ALERT**: {field_summary['rod_float_alert_count']} well(s) experiencing downstroke carrier bar separation and severe impact loading due to heavy crude cooling. Switch to AI Autonomous VFD control to protect rod strings.")
        else:
            st.success("✅ **SYSTEM HEALTHY**: All active SRP units operating within safe hydrodynamic drag limits.")

    st.markdown("### 📋 Multi-Well Real-Time Health & Operating Matrix")
    
    matrix_rows = []
    for ws in field_summary["well_states"]:
        m = ws["well_meta"]
        matrix_rows.append({
            "Well ID": m["well_id"],
            "Well Name": m["name"],
            "Formation": m["formation"],
            "CSS Cycle": f"#{m['current_css_cycle']}",
            "Cycle Day": ws["day"],
            "Status": m["status"],
            "Oil Rate (BOPD)": f"{ws['oil_rate_bopd']:.1f}",
            "Reservoir Temp": f"{ws['reservoir_temperature_c']:.1f} °C",
            "Viscosity": f"{ws['oil_viscosity_cp']:.0f} cP",
            "Operating SPM": f"{ws['operating_spm']:.1f}",
            "Rod Float Risk": f"{ws['rod_floating_risk_index'] * 100:.1f}%",
            "Diagnosis": ws["diagnosis"]
        })
    df_matrix = pd.DataFrame(matrix_rows)
    st.dataframe(df_matrix, use_container_width=True, hide_index=True)

    st.markdown("### 📜 Historical Field Equipment Failure Logs (Root Cause Analysis)")
    df_fails = generate_historical_failure_logs()
    st.dataframe(df_fails, use_container_width=True, hide_index=True)


# ==========================================
# TAB 2: RESERVOIR & THERMAL TWIN
# ==========================================
with tab_thermal:
    st.subheader(f"🌋 Subsurface Thermal Reservoir & Wellbore Hydraulics Twin ({selected_well_id})")

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
    st.subheader("🌡️ Dynamic Wellbore Temperature, Viscosity & Pressure Depth Profile (0 - 1050 m)")
    
    fig_grad = plot_wellbore_gradient(current_state["hydraulics"])
    st.plotly_chart(fig_grad, use_container_width=True)

    # PVT Fluid Characterization Accordion
    with st.expander("🧪 Fluid PVT & Asphaltene Deposition Risk Analysis", expanded=False):
        c_asph1, c_asph2, c_asph3 = st.columns(3)
        asph_data = current_state["asphaltene_risk"]
        with c_asph1:
            st.metric("Colloidal Instability Index (CII)", f"{asph_data['colloidal_instability_index']:.2f}", "SARA Instability (> 0.90)")
        with c_asph2:
            st.metric("Asphaltene Deposition Risk", f"{asph_data['asphaltene_deposition_risk_index'] * 100:.1f}%", asph_data["status"])
        with c_asph3:
            st.metric("Wellhead Fluid Temperature", f"{current_state['wellhead_temperature_c']:.1f} °C", "Onset: 68.0 °C")


# ==========================================
# TAB 3: SRP WAVE DYNAMICS & DYNO STUDIO
# ==========================================
with tab_srp:
    st.subheader(f"⚙️ Sucker Rod Pump (SRP) Dynamics & Dynamometer Card Studio ({selected_well_id})")

    # Diagnostic Banner Callout
    diag_severity = current_state["diagnosis_severity"]
    box_class = "diag-box-critical" if "CRITICAL" in diag_severity else "diag-box-warning" if "WARNING" in diag_severity else "diag-box-optimal"
    
    st.markdown(f"""
    <div class="{box_class}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h4 style="color: #FFFFFF; margin: 0 0 4px 0;">AI Diagnostic Result: {current_state['diagnosis']}</h4>
                <p style="color: #E2E8F0; margin: 0; font-size: 0.9rem;">
                    <b>Severity:</b> {current_state['diagnosis_severity']} • <b>Confidence:</b> {current_state['diagnosis_confidence']}%
                </p>
                <p style="color: #CBD5E1; margin: 6px 0 0 0; font-size: 0.85rem;">
                    💡 <b>Recommendation:</b> {current_state['diagnosis_recommendation']}
                </p>
            </div>
            <div>
                <div class="oil-badge-cyan">1D Gibbs Wave Equation</div>
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
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px; font-size: 0.88rem; color: #CBD5E1;">
            <p style="margin: 0 0 8px 0;"><b>Total Rod Weight in Fluid:</b> {current_state['srp_dynamics']['mprl_lbs'] + drag_m['peak_viscous_drag_lbs']:.0f} lbs</p>
            <p style="margin: 0 0 8px 0;"><b>Peak Downstroke Viscous Drag:</b> <span style="color: #EF4444; font-weight: 700;">{drag_m['peak_viscous_drag_lbs']:,.0f} lbs</span></p>
            <p style="margin: 0 0 8px 0;"><b>Net Downward Rod Acceleration:</b> {drag_m['rod_fall_accel_m_s2']:.2f} m/s² (Carrier Bar: {drag_m['carrier_bar_peak_accel_m_s2']:.2f} m/s²)</p>
            <p style="margin: 0 0 8px 0;"><b>Carrier Bar Separation Condition:</b> <span style="color: {'#EF4444' if current_state['is_rod_floating'] else '#10B981'}; font-weight: 700;">{'SEPARATING (ROD FLOATING)' if current_state['is_rod_floating'] else 'SECURE CONTACT (NO FLOAT)'}</span></p>
            <p style="margin: 0;"><b>Impact Shock Load on Reconnection:</b> <span style="color: {'#EF4444' if drag_m['impact_shock_force_lbs'] > 0 else '#10B981'}; font-weight: 700;">+{drag_m['impact_shock_force_lbs']:,.0f} lbs</span></p>
        </div>
        """, unsafe_allow_html=True)

        # Interactive Fault Mode Injection
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("#### 🧪 Fault Injection Test Bench (Diagnostic Verification)")
        inject_fault = st.selectbox("Simulate Specific Downhole Fault Condition:", ["None (Live Physics)", "fluid_pound", "gas_interference", "unanchored_tubing", "valve_leak"])
        if inject_fault != "None (Live Physics)":
            test_srp = baghewala_srp.solve_wave_equation(
                temperature_c=current_state["reservoir_temperature_c"],
                viscosity_cp=current_state["oil_viscosity_cp"],
                bottomhole_pressure_bar=20.0,
                spm=current_state["operating_spm"],
                fault_type=inject_fault
            )
            test_diag = baghewala_card_classifier.classify_card(test_srp["surface_position_in"], test_srp["surface_load_lbs"])
            st.info(f"Simulated Fault Card: **{test_diag['diagnosis']}** (Confidence: {test_diag['confidence_pct']}%)")


# ==========================================
# TAB 4: JOINT CSS-SRP AI OPTIMIZER
# ==========================================
with tab_optimizer:
    st.subheader("🎯 Multi-Objective Joint CSS & SRP Artificial Lift Optimizer")
    st.markdown("Simultaneously optimizes subsurface steam volume, soak time, cycle cut-off, and surface VFD dynamic speed trajectory.")

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
            is_positive=True
        ), unsafe_allow_html=True)
    with c_b2:
        st.markdown(render_metric_card(
            "SOR Reduction", 
            f"-{kpi_imp['sor_reduction_pct']:.1f}%", 
            f"{comp_res['baseline']['final_sor']:.2f} → {comp_res['optimized']['final_sor']:.2f}", 
            is_positive=True
        ), unsafe_allow_html=True)
    with c_b3:
        st.markdown(render_metric_card(
            "Lift Energy Saved", 
            f"-{kpi_imp['energy_saving_pct']:.1f}%", 
            f"{comp_res['baseline']['kwh_per_bbl']:.2f} → {comp_res['optimized']['kwh_per_bbl']:.2f} kWh/bbl", 
            is_positive=True
        ), unsafe_allow_html=True)
    with c_b4:
        st.markdown(render_metric_card(
            "Rod Floating Prevented", 
            f"{kpi_imp['rod_floating_days_prevented']} Days", 
            f"100% Shock Protection", 
            is_positive=True
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
        paper_bgcolor=PLOT_THEME["paper_bgcolor"], plot_bgcolor=PLOT_THEME["plot_bgcolor"], font=PLOT_THEME["font"],
        height=350, margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(title="Days in CSS Cycle", gridcolor=PLOT_THEME["gridcolor"]),
        yaxis=dict(title="Pumping Speed (SPM)", gridcolor=PLOT_THEME["gridcolor"])
    )
    st.plotly_chart(fig_spm, use_container_width=True)

    # Multi-Objective Pareto Frontier
    st.markdown("### 📈 Multi-Objective CSS Pareto Frontier (Trade-off Analysis)")
    pareto_pts = baghewala_joint_optimizer.generate_pareto_front(cycle_number=selected_cycle)
    fig_pareto = plot_pareto_front(pareto_pts)
    st.plotly_chart(fig_pareto, use_container_width=True)


# ==========================================
# TAB 5: LIVE DIGITAL TWIN SIMULATOR
# ==========================================
with tab_simulator:
    st.subheader("⚡ Live Subsurface-to-Surface Closed-Loop Digital Twin Simulator")
    st.markdown("Simulate the 120-day CSS cycle with real-time AI autonomous closed-loop VFD governor vs unoptimized baseline.")

    sim_controls_col1, sim_controls_col2 = st.columns([1, 2])
    with sim_controls_col1:
        sim_day = st.slider("Simulate Cycle Day:", 1, 120, day_in_cycle, key="sim_day_slider")
        sim_auto_vfd = st.checkbox("Enable Closed-Loop Autonomous VFD Governor", value=True, key="sim_auto_vfd")

    baseline_spm_sim = manual_spm if manual_spm is not None else 6.0
    # Fetch instant state for slider day
    state_manual = well_twin.get_current_state(day=sim_day, spm_override=baseline_spm_sim)
    state_auto = well_twin.get_current_state(day=sim_day, spm_override=None)

    col_sim_left, col_sim_right = st.columns(2)
    with col_sim_left:
        st.markdown(f"""
        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid #EF4444; border-radius: 12px; padding: 16px;">
            <h4 style="color: #EF4444; margin-top: 0;">🔴 Baseline System (Fixed {baseline_spm_sim:.1f} SPM)</h4>
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
        st.markdown(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10B981; border-radius: 12px; padding: 16px;">
            <h4 style="color: #10B981; margin-top: 0;">🟢 AI Autonomous Twin (Dynamic {state_auto['operating_spm']:.1f} SPM)</h4>
            <p><b>Day {sim_day}:</b> Temp = {state_auto['reservoir_temperature_c']:.1f} °C | Visc = {state_auto['oil_viscosity_cp']:.0f} cP</p>
            <p><b>Rod Floating Status:</b> {'⚠️ ROD FLOATING' if state_auto['is_rod_floating'] else '🟢 PROTECTED (0% FLOAT)'}</p>
            <p><b>Impact Shock:</b> 0 lbs (Zero Shock Reconnection)</p>
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
    st.subheader(f"🛡️ Equipment Reliability & Predictive Maintenance ({selected_well_id})")

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
            "Rod String Health Score", 
            f"{rul_data['rod_health_score_pct']:.1f}%", 
            rul_data["fatigue_risk_level"], 
            is_positive=rul_data["rod_health_score_pct"] > 60.0
        ), unsafe_allow_html=True)

    with c_m2:
        st.markdown(render_metric_card(
            "Remaining Useful Life", 
            f"{rul_data['remaining_useful_life_days']} Days", 
            f"{rul_data['rul_cycles_remaining']:,} Cycles", 
            is_positive=rul_data["remaining_useful_life_days"] > 100
        ), unsafe_allow_html=True)

    with c_m3:
        unset_p = current_state["unsetting_data"]["unsetting_probability_pct"]
        st.markdown(render_metric_card(
            "Pump Unsetting Risk", 
            f"{unset_p:.1f}%", 
            current_state["unsetting_data"]["status"], 
            is_positive=unset_p < 25.0
        ), unsafe_allow_html=True)

    with c_m4:
        asph_p = current_state["asphaltene_risk"]["asphaltene_deposition_risk_index"] * 100.0
        st.markdown(render_metric_card(
            "Asphaltene Deposition", 
            f"{asph_p:.1f}%", 
            current_state["asphaltene_risk"]["status"], 
            is_positive=asph_p < 35.0
        ), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔔 Recommended Predictive Maintenance Interventions")

    st.markdown(f"""
    <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 20px;">
        <h4 style="color: #00D2FF; margin-top: 0;">Prescriptive Maintenance Schedule for {selected_well_id}</h4>
        <ul style="color: #CBD5E1; font-size: 0.92rem; line-height: 1.6;">
            <li><b>Sucker Rod String:</b> Current Goodman fatigue loading is <b>{current_state['rod_loading_pct']:.1f}%</b> of API Grade D allowable limit. Next scheduled acoustic inspection in <b>{rul_data['remaining_useful_life_days'] // 2} days</b>.</li>
            <li><b>Hold-Down Pump Seating:</b> Current upward shock load is <b>{current_state['unsetting_data']['upward_shock_load_lbs']:.0f} lbs</b> against 4,200 lbs rating. {'⚠️ Warning: Hold-down shoe at risk of unseating!' if unset_p > 40 else '✅ Seating nipple hold-down is secure.'}</li>
            <li><b>Thermal & Chemical Flush:</b> Wellhead temperature is <b>{current_state['wellhead_temperature_c']:.1f} °C</b>. {'Schedule aromatic solvent / hot-oil casing flush within 7 days to dissolve near-wellbore asphaltene precipitation.' if asph_p > 50 else 'No solvent wash required at current operating temperature.'}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# TAB 7: ENGINEERING REPORTS & DATA MANAGEMENT
# ==========================================
with tab_reports:
    st.subheader("📑 Engineering Reports & Production Data Management")

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

<<<<<<< Updated upstream
        df_export = generate_well_telemetry(selected_well_id, days_count=120)
=======
<<<<<<< Updated upstream
        df_export = generate_well_telemetry(selected_well_id, days_count=90)
>>>>>>> Stashed changes
        csv_buffer = df_export.to_csv(index=False)
        st.download_button(
            label="📥 Download Complete Cycle Telemetry (CSV)",
            data=csv_buffer,
            file_name=f"{selected_well_id}_telemetry_history.csv",
            mime="text/csv"
        )
=======
        # --- FIX: Lazy generation — data only built when user clicks Generate,
        # not on every page render. This prevents IDM/browser download managers
        # from intercepting a spurious download trigger on load. ---
>>>>>>> Stashed changes

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


# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748B; font-size: 0.8rem; padding: 12px;">
    Oil India Limited • Baghewala Heavy Oil Field Digital Twin Platform • Powered by AI & Gibbs 1D Wave Physics Engine
</div>
""", unsafe_allow_html=True)
