"""
Plotly Visualizations and Interactive Graphical Components for Baghewala Digital Twin.
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any


PLOT_THEME = {
    "paper_bgcolor": "rgba(15, 23, 42, 0.7)",
    "plot_bgcolor": "rgba(11, 15, 25, 0.85)",
    "font": {"color": "#E2E8F0", "family": "Inter, sans-serif"},
    "gridcolor": "rgba(255, 255, 255, 0.08)",
    "zerolinecolor": "rgba(255, 255, 255, 0.15)"
}


def plot_dynamometer_cards(srp_data: Dict[str, Any], diagnosis: Dict[str, Any]) -> go.Figure:
    """
    Renders synchronized Surface Dynamometer Card and Downhole Pump Card with diagnostic limits.
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Surface Dynamometer Card (Polish Rod)", "Downhole Pump Dynamometer Card (Plunger)"),
        horizontal_spacing=0.12
    )

    surf_pos = srp_data["surface_position_in"]
    surf_load = srp_data["surface_load_lbs"]
    down_pos = srp_data["downhole_position_in"]
    down_load = srp_data["downhole_load_lbs"]
    pprl = srp_data["pprl_lbs"]
    mprl = srp_data["mprl_lbs"]
    is_float = srp_data["is_rod_floating"]
    impact_lbs = srp_data["impact_shock_force_lbs"]

    # Colors
    surf_color = "#EF4444" if is_float else "#00D2FF"
    down_color = "#F5A623"

    # Surface Card Trace (Closed loop)
    fig.add_trace(
        go.Scatter(
            x=surf_pos, y=surf_load,
            mode='lines+markers',
            name='Measured Surface Card',
            line=dict(color=surf_color, width=3.5),
            marker=dict(size=4, color=surf_color),
            fill='toself',
            fillcolor='rgba(239, 68, 68, 0.12)' if is_float else 'rgba(0, 210, 255, 0.12)',
            hoverinfo='text',
            hovertext=[f"Pos: {p:.1f} in<br>Load: {l:,.0f} lbs" for p, l in zip(surf_pos, surf_load)]
        ),
        row=1, col=1
    )

    # Allowable Load Limits on Surface Card
    stroke_max = np.max(surf_pos)
    fig.add_trace(
        go.Scatter(
            x=[0, stroke_max], y=[pprl, pprl],
            mode='lines', name=f'PPRL ({pprl:,.0f} lbs)',
            line=dict(color='#EF4444', width=1.5, dash='dash')
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=[0, stroke_max], y=[mprl, mprl],
            mode='lines', name=f'MPRL ({mprl:,.0f} lbs)',
            line=dict(color='#10B981', width=1.5, dash='dash')
        ),
        row=1, col=1
    )

    # If rod floating detected, annotate separation zone
    if is_float:
        fig.add_annotation(
            x=stroke_max * 0.45, y=mprl + 600.0,
            text=f"⚠️ ROD FLOATING / CARRIER BAR SEPARATION<br>Peak Impact Shock: +{impact_lbs:,.0f} lbs",
            showarrow=True, arrowhead=2, arrowcolor="#EF4444",
            bgcolor="rgba(239, 68, 68, 0.85)", font=dict(color="#FFFFFF", size=11, family="Inter"),
            row=1, col=1
        )

    # Downhole Card Trace
    fig.add_trace(
        go.Scatter(
            x=down_pos, y=down_load,
            mode='lines+markers',
            name='Calculated Pump Card',
            line=dict(color=down_color, width=3),
            marker=dict(size=4, color=down_color),
            fill='toself',
            fillcolor='rgba(245, 166, 35, 0.15)',
            hoverinfo='text',
            hovertext=[f"Plunger Pos: {p:.1f} in<br>Fluid Load: {l:,.0f} lbs" for p, l in zip(down_pos, down_load)]
        ),
        row=1, col=2
    )

    # Layout styling
    fig.update_layout(
        paper_bgcolor=PLOT_THEME["paper_bgcolor"],
        plot_bgcolor=PLOT_THEME["plot_bgcolor"],
        font=PLOT_THEME["font"],
        height=440,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
        hovermode="closest"
    )

    fig.update_xaxes(title_text="Polished Rod Position (inches)", gridcolor=PLOT_THEME["gridcolor"], row=1, col=1)
    fig.update_yaxes(title_text="Polish Rod Load (lbs)", gridcolor=PLOT_THEME["gridcolor"], row=1, col=1)
    fig.update_xaxes(title_text="Plunger Position (inches)", gridcolor=PLOT_THEME["gridcolor"], row=1, col=2)
    fig.update_yaxes(title_text="Downhole Load (lbs)", gridcolor=PLOT_THEME["gridcolor"], row=1, col=2)

    return fig


def plot_3d_thermal_reservoir(heated_radius_m: float, sandface_temp_c: float, native_temp_c: float = 47.0) -> go.Figure:
    """
    Renders interactive 3D thermal isotherm map of Baghewala Sandstone steam chamber.
    """
    # Radial grid
    r = np.linspace(0.1, 45.0, 35) # meters from wellbore
    theta = np.linspace(0, 2 * np.pi, 35)
    R, THETA = np.meshgrid(r, theta)
    X = R * np.cos(THETA)
    Y = R * np.sin(THETA)

    # Temperature field T(r)
    # Steam plateau inside heated_radius, then conduction decay to native reservoir temp
    decay_width = 8.5 # meters
    T = native_temp_c + (sandface_temp_c - native_temp_c) * 0.5 * (1.0 - np.tanh((R - heated_radius_m) / decay_width))

    # Pay thickness depth Z
    Z = -1050.0 + (T - native_temp_c) / (sandface_temp_c - native_temp_c + 1e-3) * 12.0

    fig = go.Figure(data=[
        go.Surface(
            x=X, y=Y, z=Z,
            surfacecolor=T,
            colorscale='Inferno',
            colorbar=dict(title="Temp (°C)", len=0.75, x=0.95),
            contours_z=dict(show=True, usecolormap=True, highlightcolor="limegreen", project_z=True)
        )
    ])

    fig.update_layout(
        title=f"3D Reservoir Steam Chamber & Thermal Isotherms (Heated Radius: {heated_radius_m:.1f} m)",
        paper_bgcolor=PLOT_THEME["paper_bgcolor"],
        plot_bgcolor=PLOT_THEME["plot_bgcolor"],
        font=PLOT_THEME["font"],
        height=480,
        margin=dict(l=20, r=20, t=50, b=20),
        scene=dict(
            xaxis=dict(title="X Offset (m)", gridcolor=PLOT_THEME["gridcolor"], backgroundcolor="rgba(0,0,0,0)"),
            yaxis=dict(title="Y Offset (m)", gridcolor=PLOT_THEME["gridcolor"], backgroundcolor="rgba(0,0,0,0)"),
            zaxis=dict(title="Formation Depth (m)", gridcolor=PLOT_THEME["gridcolor"], backgroundcolor="rgba(0,0,0,0)"),
            camera=dict(eye=dict(x=1.5, y=-1.5, z=1.2))
        )
    )
    return fig


def plot_thermal_and_viscosity_decline(sim_data: Dict[str, np.ndarray], current_day: int = 42) -> go.Figure:
    """
    Renders coupled temperature decline, exponential crude viscosity escalation, and oil rate.
    """
    days = sim_data["days"]
    temp_c = sim_data["temperature_reservoir_c"]
    visc_cp = sim_data["viscosity_cp"]
    oil_bopd = sim_data["oil_rate_bopd"]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.10,
        subplot_titles=("Reservoir Temperature (°C) & In-Situ Crude Viscosity (cP)", "Daily Oil Production (BOPD) & Cumulative SOR")
    )

    # Temperature (Left axis, row 1)
    fig.add_trace(
        go.Scatter(
            x=days, y=temp_c,
            name='Reservoir Temp (°C)',
            line=dict(color='#F5A623', width=3),
            yaxis='y1'
        ),
        row=1, col=1
    )

    # Viscosity (Right axis, row 1)
    fig.add_trace(
        go.Scatter(
            x=days, y=visc_cp,
            name='Crude Viscosity (cP)',
            line=dict(color='#EF4444', width=3, dash='dot'),
            yaxis='y2'
        ),
        row=1, col=1
    )

    # Current Day indicator line
    fig.add_vline(x=current_day, line_width=2, line_dash="dash", line_color="#00D2FF", annotation_text=f"Day {current_day}")

    # Oil Production Rate (Row 2)
    fig.add_trace(
        go.Scatter(
            x=days, y=oil_bopd,
            name='Oil Rate (BOPD)',
            line=dict(color='#10B981', width=3),
            fill='tozeroy',
            fillcolor='rgba(16, 185, 129, 0.15)'
        ),
        row=2, col=1
    )

    # Cumulative SOR (Row 2, secondary axis or line)
    fig.add_trace(
        go.Scatter(
            x=days, y=sim_data["cumulative_sor"],
            name='Cumulative SOR (m³/m³)',
            line=dict(color='#A855F7', width=2.5, dash='dash')
        ),
        row=2, col=1
    )

    fig.update_layout(
        paper_bgcolor=PLOT_THEME["paper_bgcolor"],
        plot_bgcolor=PLOT_THEME["plot_bgcolor"],
        font=PLOT_THEME["font"],
        height=520,
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5)
    )

    fig.update_xaxes(title_text="Days in CSS Cycle", gridcolor=PLOT_THEME["gridcolor"], row=2, col=1)
    fig.update_yaxes(title_text="Temperature (°C)", gridcolor=PLOT_THEME["gridcolor"], row=1, col=1)
    fig.update_yaxes(title_text="Oil Rate / SOR", gridcolor=PLOT_THEME["gridcolor"], row=2, col=1)

    return fig


def plot_wellbore_gradient(hydraulics_data: Dict[str, np.ndarray]) -> go.Figure:
    """
    Renders depth profiles of temperature, viscosity, and pressure along the wellbore.
    """
    z = hydraulics_data["depth_m"]
    t_z = hydraulics_data["temperature_c"]
    p_z = hydraulics_data["pressure_bar"]
    visc_z = hydraulics_data["viscosity_cp"]

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=("Temperature Profile T(z)", "In-Situ Viscosity μ(z)", "Tubing Pressure P(z)"),
        horizontal_spacing=0.08
    )

    # Temp profile
    fig.add_trace(
        go.Scatter(x=t_z, y=z, mode='lines', line=dict(color='#F5A623', width=3), name='Fluid Temp (°C)'),
        row=1, col=1
    )
    # Geothermal baseline
    fig.add_trace(
        go.Scatter(x=32.0 + 0.022 * z, y=z, mode='lines', line=dict(color='#64748B', width=1.5, dash='dash'), name='Geothermal Baseline'),
        row=1, col=1
    )

    # Viscosity profile
    fig.add_trace(
        go.Scatter(x=visc_z, y=z, mode='lines', line=dict(color='#EF4444', width=3), name='Viscosity (cP)'),
        row=1, col=2
    )

    # Pressure profile
    fig.add_trace(
        go.Scatter(x=p_z, y=z, mode='lines', line=dict(color='#00D2FF', width=3), name='Pressure (bar)'),
        row=1, col=3
    )

    fig.update_layout(
        paper_bgcolor=PLOT_THEME["paper_bgcolor"],
        plot_bgcolor=PLOT_THEME["plot_bgcolor"],
        font=PLOT_THEME["font"],
        height=420,
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="center", x=0.5)
    )

    for c in [1, 2, 3]:
        fig.update_yaxes(title_text="Depth (m)", autorange="reversed", gridcolor=PLOT_THEME["gridcolor"], row=1, col=c)

    fig.update_xaxes(title_text="Temp (°C)", gridcolor=PLOT_THEME["gridcolor"], row=1, col=1)
    fig.update_xaxes(title_text="Viscosity (cP)", gridcolor=PLOT_THEME["gridcolor"], row=1, col=2)
    fig.update_xaxes(title_text="Pressure (bar)", gridcolor=PLOT_THEME["gridcolor"], row=1, col=3)

    return fig


def plot_goodman_diagram(srp_data: Dict[str, Any]) -> go.Figure:
    """
    Renders Modified Goodman Fatigue Diagram with API Grade D rod operating point.
    """
    s_min = srp_data["sigma_min_psi"]
    s_max = srp_data["sigma_max_psi"]
    s_allowable = srp_data["sigma_allowable_psi"]
    rod_load_pct = srp_data["rod_loading_pct"]

    # Goodman boundary line
    # S_a = (T / 1.75 + 0.5625 * S_min) * SF
    # S_ult = 115,000 psi
    s_min_axis = np.linspace(0, 45000.0, 50)
    s_allowable_boundary = (115000.0 / 1.75 + 0.5625 * s_min_axis) * 0.90

    fig = go.Figure()

    # Allowable safe envelope (Shaded area)
    fig.add_trace(
        go.Scatter(
            x=s_min_axis, y=s_allowable_boundary,
            mode='lines',
            name='API Goodman Allowable Limit (SF=0.90)',
            line=dict(color='#10B981', width=2.5),
            fill='tozeroy',
            fillcolor='rgba(16, 185, 129, 0.08)'
        )
    )

    # Operating Point
    point_color = "#EF4444" if rod_load_pct > 90.0 else "#F5A623" if rod_load_pct > 75.0 else "#00D2FF"
    fig.add_trace(
        go.Scatter(
            x=[s_min], y=[s_max],
            mode='markers+text',
            name=f'Current Stress ({rod_load_pct:.1f}% Loading)',
            marker=dict(size=14, color=point_color, symbol='diamond', line=dict(color='#FFFFFF', width=2)),
            text=[f"  {rod_load_pct:.1f}% Rated Load"],
            textposition="top right"
        )
    )

    fig.update_layout(
        title="Goodman Fatigue Diagram & Sucker Rod Stress Envelope",
        paper_bgcolor=PLOT_THEME["paper_bgcolor"],
        plot_bgcolor=PLOT_THEME["plot_bgcolor"],
        font=PLOT_THEME["font"],
        height=380,
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(title="Minimum Rod Stress S_min (psi)", gridcolor=PLOT_THEME["gridcolor"]),
        yaxis=dict(title="Maximum Rod Stress S_max (psi)", gridcolor=PLOT_THEME["gridcolor"])
    )
    return fig


def plot_pareto_front(pareto_data: List[Dict[str, float]]) -> go.Figure:
    """
    Renders Pareto Frontier comparing candidate steam volumes, cumulative recovery, and SOR.
    """
    df = pd.DataFrame(pareto_data)

    fig = go.Figure(data=go.Scatter(
        x=df["cum_oil_bbl"],
        y=df["sor"],
        mode='markers',
        marker=dict(
            size=df["net_profit_lakhs"] / 1.5,
            color=df["steam_volume_m3"],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Steam CWE (m³)"),
            line=dict(width=1, color='#FFFFFF')
        ),
        text=[f"Steam: {r.steam_volume_m3:,.0f} m³<br>Soak: {r.soak_days:.0f} days<br>Oil: {r.cum_oil_bbl:,.0f} bbl<br>SOR: {r.sor:.2f}<br>Profit: ₹{r.net_profit_lakhs:.1f} Lakhs" for _, r in df.iterrows()],
        hoverinfo='text'
    ))

    # Mark recommended optimal point (Best profit & lowest SOR)
    best_idx = df["net_profit_lakhs"].idxmax()
    best_pt = df.iloc[best_idx]
    
    fig.add_trace(go.Scatter(
        x=[best_pt["cum_oil_bbl"]], y=[best_pt["sor"]],
        mode='markers+text',
        name='AI Recommended Optimal CSS Point',
        marker=dict(size=18, color='#EF4444', symbol='star', line=dict(color='#FFFFFF', width=2)),
        text=["  ★ AI Optimal"],
        textposition="top right"
    ))

    fig.update_layout(
        title="Multi-Objective CSS Pareto Frontier (Oil Recovery vs SOR vs Profit)",
        paper_bgcolor=PLOT_THEME["paper_bgcolor"],
        plot_bgcolor=PLOT_THEME["plot_bgcolor"],
        font=PLOT_THEME["font"],
        height=420,
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(title="Cumulative Oil Production (bbl)", gridcolor=PLOT_THEME["gridcolor"]),
        yaxis=dict(title="Cumulative Steam-Oil Ratio (m³/m³)", gridcolor=PLOT_THEME["gridcolor"])
    )
    return fig


def plot_field_gis_map(well_states: List[Dict[str, Any]]) -> go.Figure:
    """
    Renders 2D interactive GIS scatter map of Baghewala Field with live status badges.
    """
    fig = go.Figure()

    for ws in well_states:
        meta = ws["well_meta"]
        status = meta["status"]
        lat = meta["latitude"]
        lon = meta["longitude"]
        bopd = ws["oil_rate_bopd"]
        is_float = ws["is_rod_floating"]

        if is_float:
            color = "#EF4444" # Red
            symbol = "circle-x"
        elif "Active" in status:
            color = "#10B981" # Green
            symbol = "circle"
        elif "Soak" in status:
            color = "#F5A623" # Amber
            symbol = "hourglass"
        else:
            color = "#00D2FF" # Cyan
            symbol = "triangle-up"

        fig.add_trace(go.Scatter(
            x=[lon], y=[lat],
            mode='markers+text',
            name=meta["well_id"],
            marker=dict(size=np.clip(bopd / 4.5 + 14, 14, 34), color=color, line=dict(color='#FFFFFF', width=2), symbol=symbol),
            text=[f"<b>{meta['well_id']}</b><br>{bopd:.1f} BOPD"],
            textposition="top center",
            hoverinfo='text',
            hovertext=f"<b>{meta['name']}</b><br>Formation: {meta['formation']}<br>Cycle: #{meta['current_css_cycle']}<br>Status: {status}<br>Oil: {bopd:.1f} BOPD<br>Viscosity: {ws['oil_viscosity_cp']:.0f} cP<br>Temp: {ws['reservoir_temperature_c']:.1f}°C"
        ))

    fig.update_layout(
        title="Baghewala Heavy Oil Field - Subsurface Well Location & Production Network",
        paper_bgcolor=PLOT_THEME["paper_bgcolor"],
        plot_bgcolor=PLOT_THEME["plot_bgcolor"],
        font=PLOT_THEME["font"],
        height=440,
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(title="Longitude (°E)", gridcolor=PLOT_THEME["gridcolor"]),
        yaxis=dict(title="Latitude (°N)", gridcolor=PLOT_THEME["gridcolor"]),
        showlegend=False
    )
    return fig
