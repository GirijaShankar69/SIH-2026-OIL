"""
Modern Styling and CSS Theme for Baghewala Field Digital Twin
Customized for Oil India Limited (OIL) with dark glassmorphism, industrial telemetry aesthetic,
and clear visual hierarchy for engineering and jury presentations.
"""

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');

    /* Global Root Variables */
    :root {
        --bg-primary: #0A0E17;
        --bg-secondary: #111827;
        --bg-card: rgba(17, 24, 39, 0.75);
        --bg-card-hover: rgba(31, 41, 55, 0.85);
        --border-subtle: rgba(255, 255, 255, 0.08);
        --border-accent: rgba(0, 210, 255, 0.35);
        --text-primary: #F8FAFC;
        --text-secondary: #94A3B8;
        --text-muted: #64748B;
        --accent-cyan: #00D2FF;
        --accent-emerald: #10B981;
        --accent-amber: #F59E0B;
        --accent-rose: #EF4444;
        --accent-indigo: #6366F1;
        --accent-purple: #A855F7;
    }

    /* Main Container & Background */
    .stApp {
        background: radial-gradient(circle at 15% 15%, #0F172A 0%, #0A0E17 100%);
        color: var(--text-primary);
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Top Executive Header Banner */
    .oil-header {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.7) 50%, rgba(15, 23, 42, 0.9) 100%);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(0, 210, 255, 0.25);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 12px 32px -8px rgba(0, 0, 0, 0.6), 0 0 20px -4px rgba(0, 210, 255, 0.15);
        position: relative;
        overflow: hidden;
    }

    .oil-header::after {
        content: "";
        position: absolute;
        top: 0;
        right: 0;
        width: 320px;
        height: 100%;
        background: radial-gradient(circle, rgba(0, 210, 255, 0.08) 0%, rgba(0, 0, 0, 0) 70%);
        pointer-events: none;
    }

    /* Badges & Pills */
    .oil-badge {
        background: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.4);
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    .oil-badge-cyan {
        background: rgba(0, 210, 255, 0.12);
        color: #00D2FF;
        border: 1px solid rgba(0, 210, 255, 0.35);
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    .oil-badge-green {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-radius: 6px;
        padding: 5px 12px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    .oil-badge-red {
        background: rgba(239, 68, 68, 0.15);
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.5);
        border-radius: 6px;
        padding: 5px 12px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        animation: badge-pulse 2s infinite ease-in-out;
    }

    @keyframes badge-pulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); transform: scale(1); }
        50% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); transform: scale(1.02); }
    }

    /* Metric Cards */
    .metric-card {
        background: var(--bg-card);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border-subtle);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 12px;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    .metric-card:hover {
        transform: translateY(-3px);
        border-color: rgba(0, 210, 255, 0.4);
        box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.5), 0 0 12px rgba(0, 210, 255, 0.1);
    }

    .metric-title {
        color: var(--text-secondary);
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .metric-value {
        color: #FFFFFF;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.85rem;
        font-weight: 800;
        line-height: 1.15;
        letter-spacing: -0.02em;
    }

    .metric-delta-pos {
        color: #10B981;
        font-size: 0.82rem;
        font-weight: 600;
        margin-top: 6px;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .metric-delta-neg {
        color: #EF4444;
        font-size: 0.82rem;
        font-weight: 600;
        margin-top: 6px;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .metric-delta-neutral {
        color: #94A3B8;
        font-size: 0.82rem;
        font-weight: 600;
        margin-top: 6px;
    }

    /* Highlight Diagnostic Callout Boxes */
    .diag-box-critical {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(153, 27, 27, 0.22) 100%);
        border: 1px solid rgba(239, 68, 68, 0.6);
        border-left: 5px solid #EF4444;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 18px;
        box-shadow: 0 4px 16px rgba(239, 68, 68, 0.1);
    }

    .diag-box-optimal {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(6, 95, 70, 0.22) 100%);
        border: 1px solid rgba(16, 185, 129, 0.6);
        border-left: 5px solid #10B981;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 18px;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.1);
    }

    .diag-box-warning {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.12) 0%, rgba(180, 83, 9, 0.22) 100%);
        border: 1px solid rgba(245, 158, 11, 0.6);
        border-left: 5px solid #F59E0B;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 18px;
        box-shadow: 0 4px 16px rgba(245, 158, 11, 0.1);
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: rgba(15, 23, 42, 0.7);
        backdrop-filter: blur(8px);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid var(--border-subtle);
        margin-bottom: 16px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 18px;
        color: #94A3B8;
        font-weight: 600;
        font-size: 0.9rem;
        border: none;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #F8FAFC;
        background: rgba(255, 255, 255, 0.04);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.35);
    }

    /* Custom Glass Panel */
    .glass-panel {
        background: rgba(17, 24, 39, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 16px;
    }

    /* Info Callout Strip */
    .info-strip {
        background: rgba(14, 165, 233, 0.08);
        border: 1px solid rgba(14, 165, 233, 0.3);
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 0.88rem;
        color: #BAE6FD;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 16px;
    }

    /* Key-Value Details Grid */
    .details-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
        margin-top: 10px;
    }

    .detail-item {
        background: rgba(15, 23, 42, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 10px 14px;
    }

    .detail-label {
        font-size: 0.75rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .detail-value {
        font-size: 1.05rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-top: 2px;
    }

    /* Button Enhancement */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
</style>
"""


def render_metric_card(title: str, value: str, delta: str = None, is_positive: bool = True, icon: str = None) -> str:
    """Generates HTML string for a stylized modern KPI metric card with icon & delta."""
    icon_html = f"<span style='font-size: 1.0rem;'>{icon}</span> " if icon else ""
    delta_html = ""
    if delta:
        delta_class = "metric-delta-pos" if is_positive else "metric-delta-neg"
        arrow = "▲" if is_positive else "▼"
        delta_html = f'<div class="{delta_class}">{arrow} {delta}</div>'

    return f"""
    <div class="metric-card">
        <div class="metric-title">{icon_html}{title}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """


def render_info_banner(icon: str, title: str, description: str, badge_text: str = None, badge_type: str = "cyan") -> str:
    """Renders a modern interactive card banner with badge and description."""
    badge_html = ""
    if badge_text:
        badge_class = f"oil-badge-{badge_type}" if badge_type in ["cyan", "green", "red"] else "oil-badge"
        badge_html = f'<div class="{badge_class}">{badge_text}</div>'

    return f"""
    <div class="glass-panel" style="display: flex; justify-content: space-between; align-items: flex-start; gap: 16px;">
        <div style="display: flex; gap: 14px; align-items: flex-start;">
            <div style="font-size: 1.8rem; line-height: 1; padding: 6px 0;">{icon}</div>
            <div>
                <h4 style="color: #F8FAFC; margin: 0 0 4px 0; font-size: 1.05rem;">{title}</h4>
                <p style="color: #94A3B8; margin: 0; font-size: 0.88rem; line-height: 1.5;">{description}</p>
            </div>
        </div>
        <div>
            {badge_html}
        </div>
    </div>
    """
