# FinSecAI Streamlit app - Qwen LoRA version (single-file, offline)

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import torch
import json

# -----------------------
# PROJECT ROOT
# -----------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nlp.feedback_handler import record_feedback
from utils.risk_scoring import apply_feedback_adjustment

# -----------------------
# ML / Transformers / PEFT
# -----------------------
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    HAS_TRANSFORMERS = True
except Exception:
    HAS_TRANSFORMERS = False

try:
    from peft import PeftModel
    HAS_PEFT = True
except Exception:
    HAS_PEFT = False

# -----------------------
# DEVICE DETECTION
# -----------------------
def detect_device():
    try:
        if HAS_TRANSFORMERS and torch.cuda.is_available():
            return "cuda"
        if HAS_TRANSFORMERS and getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"

DEVICE = detect_device()


# -----------------------
# MODEL PATHS
# -----------------------
# -----------------------
# MODEL FALLBACK ORDER (OFFLINE, DETERMINISTIC)
# -----------------------
MODEL_FALLBACKS = [
    {
        "name": "qwen",
        "base": Path("models/Qwen-7B").resolve(),
        "lora": Path("models/philian_soc_narrator_lora").resolve(),
        "trust_remote_code": True,
    },
    {
        "name": "gpt-neo",
        "base": Path("models/gpt-neo-125M").resolve(),
        "lora": None,
        "trust_remote_code": False,
    },
    {
        "name": "distilgpt2",
        "base": Path("models/distilgpt2").resolve(),
        "lora": None,
        "trust_remote_code": False,
    },
]

PRIMARY_ML_COL = "ml_fraud_score"


# -----------------------
# STREAMLIT CONFIG
# -----------------------
st.set_page_config(page_title="FinSecAI SOC Dashboard", layout="wide", initial_sidebar_state="expanded")
st.sidebar.markdown(f"**Compute device:** `{DEVICE}`")

# -----------------------
# SESSION STATE INIT
# -----------------------
for key in ["model_status","model_loaded","tokenizer","model","df_alerts","theme","authenticated","username","role"]:
    if key not in st.session_state:
        st.session_state[key] = None
st.session_state.model_loaded = st.session_state.model_loaded or False
st.session_state.theme = st.session_state.theme or "Light"
st.session_state.authenticated = st.session_state.authenticated or False

# -----------------------
# THEME
# -----------------------
st.session_state.theme = st.sidebar.radio("Theme", ["Light", "Dark"], index=0)
if st.session_state.theme == "Dark":
    st.markdown("""
        <style>
        .stApp { background: #0b1220; color: #dbeafe; }
        .stButton>button { background: #2563eb; color: white; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .stApp { background: white; color: black; }
        .stButton>button { background: #0b5cff; color: white; }
        </style>
    """, unsafe_allow_html=True)
st.markdown("""
<style>
.badge {
    padding: 4px 10px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.8rem;
    color: white;
}
.badge.low { background-color: #2ecc71; }
.badge.medium { background-color: #f39c12; }
.badge.high { background-color: #e74c3c; }
.badge.critical { background-color: #8e44ad; }
</style>
""", unsafe_allow_html=True)

# -----------------------
# SAFE MODEL LOADER (QWEN → GPT-NEO → DISTILGPT2)
# -----------------------
@st.cache_resource
def load_soc_model(device="cpu"):
    if not HAS_TRANSFORMERS:
        return None, None, None, "transformers_missing"

    errors = []

    for cfg in MODEL_FALLBACKS:
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                cfg["base"],
                local_files_only=True,
                trust_remote_code=cfg["trust_remote_code"]
            )

            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            model = AutoModelForCausalLM.from_pretrained(
                cfg["base"],
                local_files_only=True,
                trust_remote_code=cfg["trust_remote_code"],
                torch_dtype=torch.float32,
                device_map="auto",
                low_cpu_mem_usage=True
            )

            if cfg["lora"] and cfg["lora"].exists() and HAS_PEFT:
                model = PeftModel.from_pretrained(
                    model,
                    str(cfg["lora"]),
                    is_trainable=False
                )

            model.eval()
            return tokenizer, model, cfg["name"], f"ok:{cfg['name']}"

        except Exception as e:
            errors.append(f"{cfg['name']} → {e}")

    return None, None, None, "model_load_failed\n" + "\n".join(errors)

# -----------------------
# GUARDED GENERATION (NO PROMPT ECHO, NO RUNAWAY)
# -----------------------
def guarded_generate(prompt, tokenizer, model, max_new_tokens=220):
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True)

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=0.0,
            repetition_penalty=1.15,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id
        )

    text = tokenizer.decode(output[0], skip_special_tokens=True)

    if text.startswith(prompt):
        text = text[len(prompt):]

    return " ".join(text.strip().split()[:300])

# -----------------------
# STRICT SOC JSON ENFORCEMENT
# -----------------------
def parse_soc_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON block found")

    obj = json.loads(match.group())

    return {
        "summary": str(obj.get("summary", "")),
        "severity": str(obj.get("severity", "low")),
        "recommended_action": list(obj.get("recommended_action", []))[:3]
    }

    
# -----------------------
# AUTHENTICATION
# -----------------------
DEMO_USERS = {
    "analyst": {"password": "soc123", "role": "analyst"},
    "admin": {"password": "admin123", "role": "admin"},
}

def get_secrets_auth():
    try:
        s = st.secrets.get("auth", None)
        if not s:
            return {}
        users = s.get("users", s)
        return users
    except Exception:
        return {}

SECRETS_USERS = get_secrets_auth()

def check_credentials(user, pwd):
    if SECRETS_USERS and user in SECRETS_USERS:
        val = SECRETS_USERS[user]
        if isinstance(val, str):
            return val == pwd, "analyst"
        if isinstance(val, dict):
            return val.get("password") == pwd, val.get("role", "analyst")
    if user in DEMO_USERS and DEMO_USERS[user]["password"] == pwd:
        return True, DEMO_USERS[user]["role"]
    return False, None

if not st.session_state.authenticated:
    st.sidebar.header("🔐 Login")
    input_user = st.sidebar.text_input("Username")
    input_pwd = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        ok, role = check_credentials(input_user, input_pwd)
        if ok:
            st.session_state.authenticated = True
            st.session_state.username = input_user
            st.session_state.role = role or "analyst"
            st.success(f"Welcome {st.session_state.username}! Loading dashboard…Please click login again")
            st.stop()
        else:
            st.sidebar.error("Invalid credentials.")
    st.sidebar.markdown("---")
    st.sidebar.info("Demo: `analyst`/`soc123` or `admin`/`admin123`")
    st.stop()

# -----------------------
# LOAD MODEL AFTER LOGIN
# -----------------------
if st.session_state.authenticated and not st.session_state.model_loaded:
    with st.spinner("Loading model… this may take a while on CPU"):
        tokenizer, model, model_backend, model_status = load_soc_model()


        st.session_state.tokenizer = tokenizer
        st.session_state.model = model
        st.session_state.model_backend = model_backend
        st.session_state.model_status = model_status
        st.session_state.model_loaded = model is not None


    if st.session_state.model_loaded:
        st.success(f"Model loaded successfully: {st.session_state.model_status}")
    else:
        st.error(f"Model failed to load: {st.session_state.model_status}")

import streamlit as st
import pandas as pd
import numpy as np
import os

# -----------------------
# PRIMARY ML COLUMN
# -----------------------
PRIMARY_ML_COL = "ml_fraud_score"  # change if your CSV has a different primary score column

# -----------------------
# Normalize alerts function
# -----------------------
def normalize_alerts(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()

    # Ensure alert_id exists
    if "alert_id" in df.columns:
        df["alert_id"] = df["alert_id"].astype(str)
    elif "txn_id" in df.columns:
        df["alert_id"] = df["txn_id"].astype(str)
    elif "id" in df.columns:
        df["alert_id"] = df["id"].astype(str)
    else:
        df = df.reset_index(drop=True)
        df["alert_id"] = df.index.astype(str)

    # Risk column
    risk_candidates = [PRIMARY_ML_COL, "ml_fraud_score", "risk", "risk_score", "score"]
    found = next((c for c in risk_candidates if c in df.columns), None)
    df["risk"] = pd.to_numeric(df[found], errors="coerce") if found else np.nan

    # Timestamp parsing
    for tcol in ("timestamp", "created_at", "time", "ts"):
        if tcol in df.columns:
            try:
                df[tcol] = pd.to_datetime(df[tcol], errors="coerce")
            except:
                pass

    # user_id as string
    if "user_id" in df.columns:
        df["user_id"] = df["user_id"].astype(str)

    # severity normalization
    if "severity_label" in df.columns:
        df["severity_label"] = df["severity_label"].astype(str).str.strip().str.lower()
        df["severity_label"] = df["severity_label"].map({
            "low": "Low",
            "medium": "Medium",
            "high": "High",
            "critical": "Critical"
        }).fillna(df["severity_label"])

    return df

# -----------------------
# SIDEBAR — DATASET UPLOAD
# -----------------------
st.sidebar.markdown("### 📁 Load Threat Alerts")

# File uploader
uploaded_file = st.sidebar.file_uploader("Upload CSV with alerts", type=["csv"])
# Or manual path input
live_csv_path = st.sidebar.text_input("Or enter CSV file path", "")

# Optional DB connection
use_db = st.sidebar.checkbox("Connect to database?")
db_df = None
if use_db:
    db_type = st.sidebar.selectbox("DB Type", ["PostgreSQL", "MySQL", "SQLite"])
    db_conn_str = st.sidebar.text_input("DB Connection String / DSN")
    db_table = st.sidebar.text_input("Table name with alerts")
    if st.sidebar.button("Load from DB"):
        try:
            import sqlalchemy
            engine = sqlalchemy.create_engine(db_conn_str)
            db_df = pd.read_sql_table(db_table, engine)
            st.sidebar.success(f"Loaded {len(db_df)} alerts from DB")
        except Exception as e:
            st.sidebar.error(f"Failed to load from DB: {e}")

# -----------------------
# LOAD CSV / PATH
# -----------------------
df_alerts = None
if uploaded_file is not None:
    try:
        df_alerts = pd.read_csv(uploaded_file)
    except Exception as e:
        st.sidebar.error(f"Failed to load CSV: {e}")
elif live_csv_path and os.path.exists(live_csv_path):
    try:
        df_alerts = pd.read_csv(live_csv_path)
    except Exception as e:
        st.sidebar.error(f"Failed to read CSV from path: {e}")

# Prioritize DB if loaded
if db_df is not None:
    df_alerts = db_df.copy()

# Normalize and store in session state
if df_alerts is not None:
    df_alerts = normalize_alerts(df_alerts)
    st.session_state.df_alerts = df_alerts
    st.sidebar.success(f"Loaded {len(df_alerts)} alerts successfully!")
else:
    st.session_state.df_alerts = pd.DataFrame()



# -----------------------
# NARRATIVE GENERATION (SAFE ENTRY POINT)
# -----------------------
def generate_qwen_narrative(alert_row):
    model = st.session_state.get("model")
    tokenizer = st.session_state.get("tokenizer")

    if model is None or tokenizer is None:
        return "⚠ Narrative model not loaded."

    parts = []
    for k in ("user_id","txn_id","alert_id","timestamp","reason_text","alert_type","severity_label","risk"):
        if k in alert_row.index and not pd.isna(alert_row[k]):
            parts.append(f"{k}: {alert_row[k]}")

    context_text = " | ".join(parts)

    conversation = [
        {"role": "system", "content": "You are a SOC analyst. Output ONLY valid JSON."},
        {"role": "user", "content": f"""
Context: {context_text}

Rules:
- summary: 1–2 sentences
- severity: one of [low, medium, high, critical]
- recommended_action: 1–3 short bullet points
"""}
    ]

    prompt = tokenizer.apply_chat_template(conversation, tokenize=False)

    raw = guarded_generate(prompt, tokenizer, model)

    try:
        return parse_soc_json(raw)
    except Exception:
        return {
            "summary": raw[:200],
            "severity": "low",
            "recommended_action": ["Escalate to human analyst"]
        }

# Alias preserved
generate_narrative = generate_qwen_narrative

# -----------------------
# LAYOUT - TABS
# -----------------------
tabs = st.tabs(["🏠 Overview","🚨 Alerts","🕵️ Threat Narratives","📄 Incident Reports","⚙️ Admin"])

# -----------------------
# TAB 0 Overview
# -----------------------
with tabs[0]:
    st.markdown("<div class='title-font'>FinSecAI Threat Detection Dashboard — Overview</div>", unsafe_allow_html=True)

    alerts_df = st.session_state.df_alerts.copy() if st.session_state.get("df_alerts") is not None else pd.DataFrame()
    filtered_alerts = alerts_df.copy()

    # KPI columns
    col1, col2, col3, col4, col5 = st.columns([1,1,1,1,1])
    col1.markdown(
        f"<div class='kpi-card'><div class='kpi-title'>Total Events</div><div class='kpi-value'>{len(alerts_df)}</div></div>",
        unsafe_allow_html=True
    )
    col2.markdown(
        f"<div class='kpi-card'><div class='kpi-title'>Total Alerts</div><div class='kpi-value'>{len(filtered_alerts)}</div></div>",
        unsafe_allow_html=True
    )

    if not filtered_alerts.empty and PRIMARY_ML_COL in filtered_alerts.columns:
        avg_val = filtered_alerts[PRIMARY_ML_COL].mean()
        avg_color = "green"
        if avg_val >= 0.75:
            avg_color = "red"
        elif avg_val >= 0.4:
            avg_color = "orange"

        col3.markdown(
            f"<div class='kpi-card'><div class='kpi-title'>Avg Fraud Score</div>"
            f"<div class='kpi-value' style='color:{avg_color}'>{avg_val:.2f}</div></div>",
            unsafe_allow_html=True
        )
    else:
        col3.markdown(
            "<div class='kpi-card'><div class='kpi-title'>Avg Fraud Score</div><div class='kpi-value'>N/A</div></div>",
            unsafe_allow_html=True
        )

    high_count = (
        int((filtered_alerts["severity_label"].astype(str) == "High").sum())
        if not filtered_alerts.empty and "severity_label" in filtered_alerts.columns
        else 0
    )
    col4.markdown(
        f"<div class='kpi-card'><div class='kpi-title'>High Severity Alerts</div>"
        f"<div class='kpi-value' style='color:{'red' if high_count > 0 else 'black'}'>{high_count}</div></div>",
        unsafe_allow_html=True
    )

    sample_html = "<div class='kpi-card'><div class='kpi-title'>Sample Alert Summary</div>"
    if not filtered_alerts.empty:
        ordering = {"High": 3, "Medium": 2, "Low": 1}
        sev_series = (
            filtered_alerts["severity_label"].astype(str)
            if "severity_label" in filtered_alerts.columns
            else pd.Series([""] * len(filtered_alerts), index=filtered_alerts.index)
        )
        filtered_alerts["_ord"] = sev_series.map(ordering).fillna(0).astype(int)

        sort_cols = ["_ord"]
        ascending = [False]
        if PRIMARY_ML_COL in filtered_alerts.columns:
            sort_cols.append(PRIMARY_ML_COL)
            ascending.append(False)

        try:
            sample_row = filtered_alerts.sort_values(sort_cols, ascending=ascending).iloc[0]
            sev = sample_row.get("severity_label", "Low")
            reason = sample_row.get("reason_text", "No explanation available.")

            # ---- FIX: lowercase severity class ----
            badge = f"<span class='badge {sev.lower()}'>{sev}</span>"

            sample_html += f"<div style='color:#0b3d91;font-weight:700'>{sample_row.get('user_id','N/A')} {badge}</div>"
            sample_html += f"<div style='color:#0b3d91;font-size:13px'>{reason}</div>"
        except Exception:
            sample_html += "<div style='color:#0b3d91;font-size:13px'>No sample available</div>"
    else:
        sample_html += "<div style='color:#0b3d91;font-size:13px'>No alerts</div>"

    sample_html += "</div>"
    col5.markdown(sample_html, unsafe_allow_html=True)

    # Fraud Score Distribution
    st.markdown("### 📊 Fraud Score Distribution")
    if not filtered_alerts.empty and PRIMARY_ML_COL in filtered_alerts.columns:
        fig = px.histogram(
            filtered_alerts,
            x=PRIMARY_ML_COL,
            nbins=20,
            color="severity_label" if "severity_label" in filtered_alerts else None,
            color_discrete_map={"High": "red", "Medium": "orange", "Low": "green"},
            labels={PRIMARY_ML_COL: "ML Fraud Score"},
            title="Fraud Score Distribution by Severity"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No alerts to display. Upload threat file in the Side bar")

# -----------------------
# TAB 1: Alerts (DISPLAY ONLY — GLOBAL)
# -----------------------
with tabs[1]:
    st.header("🚨 Alerts Overview")

    # ---- Safe retrieval ----
    df_alerts = st.session_state.get("df_alerts")
    if df_alerts is None or df_alerts.empty:
        st.info("No alerts loaded. Please load alerts from the sidebar.")
        st.stop()

    df_alerts = normalize_alerts(df_alerts.copy())
    st.session_state.df_alerts = df_alerts

    # -----------------------
    # Summary Metrics
    # -----------------------
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Alerts", len(df_alerts))
    c2.metric("High Severity", (df_alerts["severity_label"] == "High").sum())
    c3.metric("Unique Users", df_alerts["user_id"].nunique())

    # -----------------------
    # Filters (SEVERITY ONLY)
    # -----------------------
    st.subheader("Filter Alerts")

    severities = st.multiselect(
        "Severity",
        options=sorted(df_alerts["severity_label"].dropna().unique()),
        default=sorted(df_alerts["severity_label"].dropna().unique())
    )

    filtered_alerts = df_alerts[
        df_alerts["severity_label"].isin(severities)
    ].copy()

    if filtered_alerts.empty:
        st.info("No alerts match the selected severity levels.")
        st.stop()

    # -----------------------
    # Global Alert Timeline
    # -----------------------
    st.subheader("🕒 Alert Timeline (All Users)")

    timeline_df = filtered_alerts.copy()
    timeline_df["timestamp"] = pd.to_datetime(
        timeline_df["timestamp"], errors="coerce"
    )
    timeline_df = timeline_df.dropna(subset=["timestamp"])

    if not timeline_df.empty:
        fig = px.scatter(
            timeline_df,
            x="timestamp",
            y="severity_label",
            color="severity_label",
            hover_data=["user_id", "txn_id"],
            title="Alert Timeline by Severity",
            height=420
        )
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Severity",
            legend_title="Severity"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Timeline unavailable — timestamp missing or invalid.")

    # -----------------------
    # Alerts Table (Deep-Link Navigation)
    # -----------------------
    st.subheader("🚨 Alerts Table")

    display_cols = [
        c for c in [
            "user_id",
            "txn_id",
            "timestamp",
            "severity_label",
            "reason_text"
        ]
        if c in filtered_alerts.columns
    ]

    table_df = filtered_alerts[display_cols].copy()

    # Deep-link column (alert index only — NO USER CONTEXT)
    table_df["view"] = table_df.index.map(
        lambda i: f"<a href='?alert_idx={i}'>View</a>"
    )

    # Severity badge rendering
    table_df["severity_label"] = table_df["severity_label"].apply(
        lambda s: f"<span class='badge {str(s).lower()}'>{s}</span>"
    )

    st.write(
        table_df[["view"] + display_cols].to_html(
            escape=False, index=False
        ),
        unsafe_allow_html=True
    )

    # -----------------------
    # Alert Drilldown (READ-ONLY)
    # -----------------------
    st.subheader("🔍 Alert Drilldown")

    query_params = st.query_params
    default_idx = (
        int(query_params["alert_idx"][0])
        if "alert_idx" in query_params
        and query_params["alert_idx"][0].isdigit()
        and int(query_params["alert_idx"][0]) in filtered_alerts.index
        else filtered_alerts.index[0]
    )

    selected_idx = st.selectbox(
        "Selected Alert",
        options=filtered_alerts.index,
        index=list(filtered_alerts.index).index(default_idx),
        format_func=lambda i: (
            filtered_alerts.loc[i, "txn_id"]
            if "txn_id" in filtered_alerts.columns else str(i)
        )
    )

    st.json(filtered_alerts.loc[selected_idx].to_dict())


# -----------------------
# TAB 2 Threat Narratives
# -----------------------
from nlp.feedback_handler import record_feedback
from utils.risk_scoring import apply_feedback_adjustment

with tabs[2]:
    st.header("🕵️ Threat Narratives")

    if 'df_alerts' not in st.session_state or st.session_state.df_alerts.empty:
        st.info("No alerts available. Please upload CSV, provide path, or connect to a database in the Alerts tab.")
    else:
        df_alerts = st.session_state.df_alerts.copy()
        if "alert_id" in df_alerts.columns:
            df_alerts["alert_id"] = df_alerts["alert_id"].astype(str)
        if "user_id" in df_alerts.columns:
            df_alerts["user_id"] = df_alerts["user_id"].astype(str)

        # User selector
        user_ids = df_alerts["user_id"].dropna().unique().tolist() if "user_id" in df_alerts.columns else []
        selected_user = st.selectbox(
            "Insert / Select a User ID to view alerts",
            [None] + user_ids,
            format_func=lambda x: f"{x}" if x else "No user selected"
        )

        if selected_user:
            user_alerts = df_alerts[df_alerts["user_id"] == selected_user].copy()
            if user_alerts.empty:
                st.info(f"No alerts found for user {selected_user}.")
            else:
                st.subheader(f"Alerts for User: {selected_user}")
                st.dataframe(user_alerts)

                # Alert selector
                alert_options = user_alerts["alert_id"].astype(str).tolist()
                selected_alert_id = st.selectbox(
                    "Select an alert to generate SOC narrative",
                    [None] + alert_options,
                    format_func=lambda x: f"Alert #{x}" if x else "No alert selected"
                )

                if selected_alert_id:
                    aid = str(selected_alert_id)
                    alert_row = user_alerts.loc[user_alerts["alert_id"] == aid].iloc[0]

                    st.subheader(f"🔔 Alert #{alert_row['alert_id']} — {alert_row.get('alert_type', '-')}")
                    st.write(f"**Summary:** {alert_row.get('summary', '-')}")
                    st.write(f"**Risk Score:** {alert_row.get('risk', alert_row.get('ml_fraud_score', '-'))}")
                    st.write(f"**Severity:** {alert_row.get('severity_label', '-')}")

                    # Risk trend chart
                    st.subheader("User Alerts Risk Trend")
                    user_plot_df, _, _ = get_risk_df(user_alerts)
                    if user_plot_df is None or user_plot_df.empty:
                        st.info("No numeric risk data available for this user's alerts.")
                    else:
                        st.line_chart(user_plot_df)

                    # Generate narrative
                    btn_key = f"gen_{aid}"
                    if st.button("Generate SOC Narrative", key=btn_key):
                        st.session_state.pop(f"gen_output_{aid}", None)
                        st.session_state[f"gen_status_{aid}"] = "running"
                        with st.spinner("Generating SOC-grade narrative…"):
                            try:
                                out = generate_narrative(alert_row)
                                st.session_state[f"gen_output_{aid}"] = out
                                st.session_state[f"gen_status_{aid}"] = "done"
                            except Exception as e:
                                st.session_state[f"gen_output_{aid}"] = f"⚠ Error: {e}"
                                st.session_state[f"gen_status_{aid}"] = "error"

                    # Display narrative
                    status = st.session_state.get(f"gen_status_{aid}")
                    raw_out = st.session_state.get(f"gen_output_{aid}", "")
                    if status == "done" and raw_out:
                        st.success("Narrative generated")
                        # Attempt JSON parse
                        try:
                            parsed = json.loads(raw_out)
                        except Exception:
                            parsed = None

                        if parsed:
                            st.markdown("**Parsed Narrative**")
                            st.markdown(f"**Summary:** {parsed.get('summary','-')}")
                            st.markdown(f"**Severity:** {parsed.get('severity','-')}")
                            st.markdown("**Recommended actions:**")
                            for act in parsed.get("recommended_action", []):
                                st.markdown(f"- {act}")
                        else:
                            st.markdown("**Model Output (raw)**")
                            st.code(raw_out)

                    elif status == "error":
                        st.error(raw_out)

                    # -----------------------
                    # Analyst Feedback Buttons
                    # -----------------------
                    st.markdown("### Analyst Feedback")
                    col_fp, col_tp = st.columns(2)

                    if col_fp.button(" False Positive", key=f"fp_{aid}"):
                        record_feedback(alert_id=aid, analyst=st.session_state.username, label="false_positive")
                        # Update risk score in DataFrame
                        df_alerts.loc[df_alerts["alert_id"] == aid, "risk"] = apply_feedback_adjustment(
                            float(df_alerts.loc[df_alerts["alert_id"] == aid, "risk"]), "false_positive"
                        )
                        st.session_state.df_alerts = df_alerts
                        st.success("Feedback recorded. Risk trend updated.")
                        
                        # Instead of rerun, just redraw chart inline
                        user_plot_df, _, _ = get_risk_df(df_alerts[df_alerts["user_id"] == selected_user])
                        if not user_plot_df.empty:
                            st.line_chart(user_plot_df)                  
                    
                    if col_tp.button("✅ True Positive", key=f"tp_{aid}"):
                        record_feedback(alert_id=aid, analyst=st.session_state.username, label="true_positive")
                        # Update risk score in DataFrame
                        df_alerts.loc[df_alerts["alert_id"] == aid, "risk"] = apply_feedback_adjustment(
                            float(df_alerts.loc[df_alerts["alert_id"] == aid, "risk"]), "true_positive"
                        )
                        st.session_state.df_alerts = df_alerts
                        st.success("Feedback recorded. Risk trend updated.")
                        st.rerun()  # refresh chart

# -----------------------
# TAB 3 Incident Reports
# -----------------------
with tabs[3]:
    st.header("📄 Incident Reports (IR)")
    if 'df_alerts' not in st.session_state or st.session_state.df_alerts.empty:
        st.info("No alerts available. Please upload CSV, connect to DB, or provide live feed in the Alerts tab.")
    else:
        st.session_state.df_alerts["alert_id"] = st.session_state.df_alerts["alert_id"].astype(str)
        user_ids = st.session_state.df_alerts["user_id"].dropna().unique().tolist() if "user_id" in st.session_state.df_alerts.columns else []
        selected_user = st.selectbox(
            "Insert / Select a User ID to generate IR",
            [None] + user_ids,
            format_func=lambda x: f"{x}" if x else "No user selected",
            key="ir_user_select"
        )

        if selected_user:
            user_alerts = st.session_state.df_alerts[st.session_state.df_alerts["user_id"] == selected_user].copy()
            if user_alerts.empty:
                st.info(f"No alerts found for user {selected_user}.")
            else:
                st.subheader(f"Alerts for User: {selected_user}")
                st.dataframe(user_alerts)
                alert_options = user_alerts["alert_id"].astype(str).tolist()
                seen = set()
                alert_options_unique = []
                for a in alert_options:
                    if a not in seen:
                        seen.add(a)
                        alert_options_unique.append(a)

                selected_alerts = st.multiselect(
                    "Select alert(s) to include in the Incident Report",
                    options=alert_options_unique,
                    format_func=lambda x: f"Alert #{x}"
                )

                if selected_alerts:
                    ir_alerts = user_alerts[user_alerts["alert_id"].isin([str(x) for x in selected_alerts])].copy()

                    def generate_incident_report(alerts_df):
                        report_lines = [
                            f"Incident Report for User ID: {selected_user}",
                            f"Total Alerts Selected: {len(alerts_df)}",
                            "----------------------------------------------------"
                        ]
                        for _, row in alerts_df.iterrows():
                            aid = str(row["alert_id"])
                            narrative = st.session_state.get(narrative_key, {})
                            if isinstance(narrative, dict):
                                soc_summary = narrative.get("summary", "-")
                                soc_severity = narrative.get("severity", "-")
                                soc_actions = "\n".join([f"- {a}" for a in narrative.get("recommended_action", [])])
                            else:
                                soc_summary, soc_severity, soc_actions = narrative, "-", "-"

                            report_lines.append(
                                f"Alert #{aid} - {row.get('alert_type','-')}\n"
                                f"Summary: {soc_summary}\n"
                                f"Risk Score: {row.get('risk','-')}\n"
                                f"Severity: {soc_severity}\n"
                                f"Recommended Actions:\n{soc_actions}\n"
                                "----------------------------------------------------"
                            )
                        return "\n".join(report_lines)

                    if st.button("Generate Incident Report"):
                        with st.spinner("Generating Incident Report…"):
                            incident_report = generate_incident_report(ir_alerts)
                        st.session_state["incident_report_text"] = incident_report
                        st.success("Incident Report Generated!")

                    if "incident_report_text" in st.session_state:
                        st.subheader("📄 Incident Report Preview")
                        st.text_area("Incident Report", st.session_state["incident_report_text"], height=400)
                        st.download_button("Download Report as TXT", st.session_state["incident_report_text"], file_name=f"Incident_Report_User_{selected_user}.txt")
                        st.download_button("Download Report as CSV", ir_alerts.to_csv(index=False), file_name=f"Incident_Report_User_{selected_user}.csv")
                        st.info("✅ You can now share the report with stakeholders via email or other channels.")
                else:
                    st.info("⚠ Please select one or more alerts to include in the Incident Report.")
        else:
            st.info("⚠ Please insert or select a User ID to generate Incident Report.")

# -----------------------
# TAB 4: Admin / Debug
# -----------------------
from pathlib import Path

DATA_PROCESSED_DIR = Path("data/processed")  # adjust this path to your actual folder

with tabs[4]:
    st.header("⚙️ Admin / Debug")

    # -----------------------
    # Logged-in user info
    # -----------------------
    st.subheader("User Info")
    st.write("Username:", st.session_state.get("username", "N/A"))
    st.write("Role:", st.session_state.get("role", "N/A"))

    # -----------------------
    # Model info
    # -----------------------
    st.subheader("Model Info")
    st.write("Model loaded:", bool(st.session_state.get("model", None)))
    st.write("Model status:", st.session_state.get("model_status", "Not loaded"))

    # Installed packages / capabilities
    st.write("Has transformers:", bool(HAS_TRANSFORMERS))
    st.write("Has PEFT:", bool(HAS_PEFT))
    st.write("Device:", DEVICE)

    # -----------------------
    # Base model & LoRA adapter
    # -----------------------
    st.subheader("Base Model & LoRA Adapter")

    # Use first fallback in MODEL_FALLBACKS as primary
    primary_model_cfg = MODEL_FALLBACKS[0]
    base_model_path = primary_model_cfg.get("base")
    lora_adapter_path = primary_model_cfg.get("lora")

    if base_model_path:
        st.write("Base model exists:", base_model_path.exists())
    else:
        st.write("Base model: None (Hub or fallback)")

    if lora_adapter_path:
        st.write("LoRA adapter exists:", lora_adapter_path.exists())
    else:
        st.write("LoRA adapter: None")

    # -----------------------
    # Sample alert files
    # -----------------------
    st.subheader("Sample Alerts Data")
    try:
        sample_files = list(DATA_PROCESSED_DIR.glob("alerts_*.csv"))
    except Exception as e:
        st.warning(f"Unable to list sample files: {e}")
        sample_files = []

    st.write("Sample alert files:", sample_files if sample_files else "No sample files found")

    # -----------------------
    # Streamlit cache clearing
    # -----------------------
    st.subheader("Cache Management")
    if st.button("Clear Streamlit caches"):
        try:
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("Streamlit caches cleared successfully!")
        except Exception as e:
            st.error(f"Failed to clear caches: {e}")

    # -----------------------
    # Model loader notes
    # -----------------------
    st.markdown("---")
    st.subheader("Model Loader Notes")
    model_status = st.session_state.get("model_status", None)

    if model_status in ("ok_with_lora", "ok_base_only", "ok:qwen"):
        st.success(f"Model loaded successfully: {model_status}")
    elif model_status == "peft_missing":
        st.warning("Adapter found, but `peft` package is missing. Install `peft` to apply LoRA adapters.")
    elif model_status == "adapter_missing":
        st.warning("Adapter folder not found; base model loaded instead. Place LoRA files in adapter dir to use LoRA.")
    elif model_status and str(model_status).startswith("error:"):
        st.error(model_status)
    else:
        st.info(f"Model loader returned status: {model_status or 'Unknown'}")

    # -----------------------
    # Notes / tips
    # -----------------------
    st.markdown("---")
    st.markdown(
        "⚠️ Notes:\n"
        "- Ensure `transformers` and `peft` are installed.\n"
        "- GPU available = faster inference.\n"
        "- If generation is slow, check device and model selection."
    )
