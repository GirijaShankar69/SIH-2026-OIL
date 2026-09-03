"""
Modern Styling and CSS Theme for Baghewala Field Digital Twin
Customized for Oil India Limited (OIL) with dark glassmorphism and industrial palette.
"""

CUSTOM_CSS = """
<style>
    /* Main container styling */
    .stApp {
        background-color: #0B0F19;
        color: #E2E8F0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Header banner */
    .oil-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0B192C 100%);
        border: 1px solid rgba(59, 130, 246, 0.25);
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    }
    
    .oil-badge {
        background: rgba(245, 166, 35, 0.15);
        color: #F5A623;
        border: 1px solid #F5A623;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 8px;
    }
    
    .oil-badge-cyan {
        background: rgba(6, 182, 212, 0.15);
        color: #06B6D4;
        border: 1px solid #06B6D4;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        display: inline-block;
    }
    
    .oil-badge-green {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid #10B981;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
    }
    
    .oil-badge-red {
        background: rgba(239, 68, 68, 0.15);
        color: #EF4444;
        border: 1px solid #EF4444;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); }
        70% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }

    /* Metric Cards */
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(59, 130, 246, 0.4);
    }
    
    .metric-title {
        color: #94A3B8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    
    .metric-value {
        color: #F8FAFC;
        font-size: 1.85rem;
        font-weight: 800;
        line-height: 1.2;
    }
    
    .metric-delta-pos {
        color: #10B981;
        font-size: 0.82rem;
        font-weight: 600;
        margin-top: 4px;
    }
    
    .metric-delta-neg {
        color: #EF4444;
        font-size: 0.82rem;
        font-weight: 600;
        margin-top: 4px;
    }

    /* Diagnostic Callout */
    .diag-box-critical {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(153, 27, 27, 0.25) 100%);
        border: 1px solid #EF4444;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 16px;
    }
    
    .diag-box-optimal {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(6, 95, 70, 0.25) 100%);
        border: 1px solid #10B981;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 16px;
    }
    
    .diag-box-warning {
        background: linear-gradient(135deg, rgba(245, 166, 35, 0.15) 0%, rgba(180, 83, 9, 0.25) 100%);
        border: 1px solid #F5A623;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 16px;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 23, 42, 0.6);
        padding: 6px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        color: #94A3B8;
        font-weight: 600;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
    }

    /* Plotly container adjustments */
    .js-plotly-plot .plotly .modebar {
        background-color: transparent !important;
    }
</style>
"""


def render_metric_card(title: str, value: str, delta: str = None, is_positive: bool = True) -> str:
    """Generates HTML string for a stylized KPI metric card."""
    delta_html = ""
    if delta:
        delta_class = "metric-delta-pos" if is_positive else "metric-delta-neg"
        arrow = "▲" if is_positive else "▼"
        delta_html = f'<div class="{delta_class}">{arrow} {delta}</div>'

    return f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """
