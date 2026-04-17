"""
FinSecAI Design System
Professional Dark + Gold theme with excellent contrast
"""

# ============================================================
# COLOR TOKENS (DARK THEME - HIGH CONTRAST)
# ============================================================
PRIMARY_BG = "#0F172A"          # Dark slate background
SECONDARY_BG = "#1E293B"        # Slightly lighter slate
ACCENT_GOLD = "#F59E0B"         # Brighter gold (better contrast)
TEXT_PRIMARY = "#F1F5F9"        # Bright text for dark bg
TEXT_SECONDARY = "#CBD5E1"      # Secondary text (lighter)
BORDER_COLOR = "#334155"        # Subtle borders
DANGER = "#EF4444"              # Bright red
SUCCESS = "#22C55E"             # Bright green
WARNING = "#F59E0B"             # Amber
INFO = "#60A5FA"                # Bright blue

# ============================================================
# CSS STYLESHEET (GLOBAL - DARK THEME)
# ============================================================
def load_css():
    """Load global CSS styling with dark theme"""
    return """
    <style>
    /* ========== GLOBAL ========== */
    :root {
        --primary-bg: #0F172A;
        --secondary-bg: #1E293B;
        --accent-gold: #F59E0B;
        --text-primary: #F1F5F9;
        --text-secondary: #CBD5E1;
        --border-color: #334155;
        --danger: #EF4444;
        --success: #22C55E;
        --warning: #F59E0B;
        --info: #60A5FA;
    }

    body {
        background-color: #0F172A;
        color: #F1F5F9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    .block-container {
        padding: 2rem 3rem;
    }

    /* ========== CONTAINER ========== */
    .stApp {
        background-color: #0F172A;
    }

    /* ========== SIDEBAR ========== */
    [data-testid="stSidebar"] {
        background-color: #1E293B;
    }

    /* ========== CARDS ========== */
    .card {
        background: #1E293B;
        padding: 1.2rem;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }

    .card-white {
        background: #1E293B;
        padding: 1.2rem;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }

    /* ========== KPI CARDS ========== */
    .kpi-card {
        padding: 18px;
        border-radius: 14px;
        background: #1E293B;
        border: 1px solid #334155;
        text-align: center;
        transition: all 0.2s ease;
    }

    .kpi-card:hover {
        border-color: #F59E0B;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
    }

    .kpi-title {
        font-size: 12px;
        color: #CBD5E1;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }

    .kpi-value {
        font-size: 22px;
        font-weight: 700;
        color: #F59E0B;
    }

    .kpi-subtitle {
        font-size: 11px;
        color: #94A3B8;
        margin-top: 4px;
    }

    /* ========== HEADERS ========== */
    .section-title {
        font-size: 18px;
        font-weight: 600;
        color: #F1F5F9;
        margin-bottom: 0.5rem;
        border-bottom: 2px solid #F59E0B;
        padding-bottom: 0.5rem;
    }

    h1, h2, h3 {
        color: #F1F5F9;
    }

    h1 {
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 1rem;
    }

    h2 {
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }

    /* ========== BUTTONS ========== */
    .stButton>button {
        background-color: #F59E0B;
        color: #000000;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .stButton>button:hover {
        background-color: #FBBF24;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
    }

    /* ========== BADGES ========== */
    .badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 8px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 2px;
    }

    .badge-low {
        background: rgba(34, 197, 94, 0.2);
        color: #22C55E;
    }

    .badge-medium {
        background: rgba(245, 158, 11, 0.2);
        color: #F59E0B;
    }

    .badge-high {
        background: rgba(239, 68, 68, 0.2);
        color: #EF4444;
    }

    .badge-critical {
        background: rgba(239, 68, 68, 0.3);
        color: #FCA5A5;
    }

    .badge-info {
        background: rgba(96, 165, 250, 0.2);
        color: #93C5FD;
    }

    /* ========== RISK INDICATORS ========== */
    .risk-high {
        color: #EF4444;
        font-weight: bold;
    }

    .risk-medium {
        color: #F59E0B;
        font-weight: bold;
    }

    .risk-low {
        color: #22C55E;
        font-weight: bold;
    }

    /* ========== PROGRESS BARS ========== */
    .stProgress > div > div > div {
        background-color: #F59E0B;
    }

    /* ========== METRICS ========== */
    .metric-label {
        font-size: 12px;
        color: #CBD5E1;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #F1F5F9;
    }

    /* ========== DIVIDER ========== */
    .section {
        margin-top: 20px;
        padding-top: 10px;
        border-top: 1px solid #334155;
    }

    .divider-gold {
        border-top: 2px solid #F59E0B;
        margin: 20px 0;
    }

    /* ========== ALERTS ========== */
    .stAlert {
        border-radius: 8px;
    }

    /* ========== DATAFRAME ========== */
    .stDataframe {
        border-radius: 8px;
        border: 1px solid #334155;
    }

    /* ========== TABS ========== */
    .stTabs {
        margin-top: 1rem;
    }

    [data-testid="stTabs"] {
        border-bottom: 2px solid #334155;
    }

    /* ========== TEXT COLORS ========== */
    .text-gold {
        color: #F59E0B;
        font-weight: 600;
    }

    .text-danger {
        color: #EF4444;
        font-weight: 600;
    }

    .text-success {
        color: #22C55E;
        font-weight: 600;
    }

    /* ========== RESPONSIVE ========== */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 1.5rem;
        }

        h1 {
            font-size: 24px;
        }

        .kpi-card {
            margin: 0.5rem 0;
        }
    }

    </style>
    """


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def render_kpi_card(title, value, subtitle="", color="gold"):
    """Render KPI card"""
    import streamlit as st
    
    color_map = {
        "gold": "#F59E0B",
        "green": "#22C55E",
        "red": "#EF4444",
        "blue": "#60A5FA"
    }
    
    color_val = color_map.get(color, "#F59E0B")
    
    html = f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value" style="color: {color_val};">{value}</div>
        {f'<div class="kpi-subtitle">{subtitle}</div>' if subtitle else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_badge(text, badge_type="info"):
    """Render badge"""
    import streamlit as st
    
    badge_classes = {
        "low": "badge-low",
        "medium": "badge-medium",
        "high": "badge-high",
        "critical": "badge-critical",
        "info": "badge-info"
    }
    
    badge_class = badge_classes.get(badge_type, "badge-info")
    
    html = f'<span class="badge {badge_class}">{text}</span>'
    st.markdown(html, unsafe_allow_html=True)


def render_section_divider():
    """Render gold divider"""
    import streamlit as st
    st.markdown('<div class="divider-gold"></div>', unsafe_allow_html=True)


def get_risk_color(risk_score):
    """Get color for risk score"""
    if risk_score > 0.7:
        return DANGER
    elif risk_score > 0.4:
        return WARNING
    else:
        return SUCCESS


def get_risk_badge(risk_score):
    """Get badge type for risk score"""
    if risk_score > 0.7:
        return "high"
    elif risk_score > 0.4:
        return "medium"
    else:
        return "low"
