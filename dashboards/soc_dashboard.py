"""
FinSecAI SOC Dashboard - Production analyst console
4 tabs: Incidents, Deep Dive, Analytics, Copilot
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Project setup
PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.intelligence_service import run_intelligence
from src.rag.fusion_retriever import fusion_retriever
from src.evaluation.metrics import (
    evaluate_classification,
    predict_labels,
    fairness_by_segment,
    compute_drift,
    calibration_curve,
    governance_compliance
)
from src.evaluation.visualizations import (
    plot_precision_recall,
    plot_fairness_disparity,
    plot_drift,
    plot_calibration,
    plot_governance_compliance
)

# ============================================================
# STREAMLIT CONFIG
# ============================================================
st.set_page_config(
    page_title="FinSecAI SOC Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .metric-card {
        padding: 15px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 10px 0;
    }
    .alert-high { color: #FF6B6B; font-weight: bold; }
    .alert-medium { color: #FFB74D; font-weight: bold; }
    .alert-low { color: #4ECDC4; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================
for key in ["authenticated", "role", "incidents_df", "selected_incident_idx",
            "baseline_predictions", "current_predictions", "governance_batch"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ============================================================
# SIDEBAR - CONTROL PLANE
# ============================================================
st.sidebar.title("🎛️ Control Panel")

# Authentication
if not st.session_state.authenticated:
    st.sidebar.subheader("Authentication")
    username = st.sidebar.text_input("Username", key="user_input")
    password = st.sidebar.text_input("Password", type="password", key="pass_input")
    
    if st.sidebar.button("Login"):
        # Simple auth (extend with real system)
        if username in ["tier1", "tier2", "admin"] and password == "demo123":
            st.session_state.authenticated = True
            st.session_state.role = "TIER2" if username == "tier2" else ("LEAD" if username == "admin" else "TIER1")
            st.rerun()
        else:
            st.sidebar.error("Invalid credentials")
else:
    st.sidebar.success(f"✅ Logged in as: {st.session_state.role}")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

if not st.session_state.authenticated:
    st.error("Please login to continue")
    st.stop()

# Data upload and pipeline
st.sidebar.markdown("---")
st.sidebar.subheader("📤 Data Input")

uploaded_file = st.sidebar.file_uploader("Upload CSV alerts", type="csv")
use_sample = st.sidebar.checkbox("Use sample data", value=True)

if uploaded_file is not None:
    st.session_state.incidents_df = pd.read_csv(uploaded_file)
elif use_sample:
    # Generate sample incidents
    np.random.seed(42)
    n_incidents = 50
    st.session_state.incidents_df = pd.DataFrame({
        "incident_id": [f"INC-{1000+i}" for i in range(n_incidents)],
        "user_id": np.random.choice([f"U{i}" for i in range(1, 11)], n_incidents),
        "amount": np.random.exponential(5000, n_incidents),
        "risk_score": np.random.uniform(0, 1, n_incidents),
        "anomaly_score": np.random.uniform(0, 1, n_incidents),
        "timestamp": [datetime.now() - timedelta(hours=i) for i in range(n_incidents)]
    })

# Feature toggles
st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Display Options")
show_rag_evidence = st.sidebar.checkbox("Show RAG Evidence", value=True)
show_governance = st.sidebar.checkbox("Show Governance Metrics", value=True)
llm_provider = st.sidebar.selectbox("LLM Provider", ["OpenAI", "Cohere", "Claude", "Ollama"])

# ============================================================
# MAIN CONTENT - TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Incidents", "🔍 Deep Dive", "📈 Analytics", "🤖 Copilot"]
)

# ==================================================
# TAB 1: INCIDENTS TABLE
# ==================================================
with tab1:
    st.header("📊 Incident Overview")
    
    if st.session_state.incidents_df is not None:
        df_display = st.session_state.incidents_df.copy()
        
        # Run intelligence analysis
        if st.button("Analyze All Incidents"):
            with st.spinner("Running intelligence analysis..."):
                results = []
                for idx, row in st.session_state.incidents_df.iterrows():
                    incident_dict = row.to_dict()
                    intelligence = run_intelligence(incident_dict)
                    results.append({
                        "incident_id": row["incident_id"],
                        "risk_score": row.get("risk_score", 0),
                        "anomaly_score": row.get("anomaly_score", 0),
                        "confidence": intelligence.get("confidence", 0),
                        "evidence_coverage": intelligence.get("evidence_coverage", 0),
                        "governance_flags": ", ".join(intelligence.get("governance_flags", []))
                    })
                
                df_display = pd.DataFrame(results)
                st.session_state.incidents_df = df_display
                st.success(f"Analyzed {len(results)} incidents")
        
        # Display table
        st.dataframe(
            df_display,
            use_container_width=True,
            height=400,
            selection_mode="single-row"
        )
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Incidents",
                len(df_display),
                delta=f"+{len(df_display) % 5}"
            )
        
        with col2:
            avg_risk = df_display.get("risk_score", pd.Series([0])).mean()
            st.metric("Avg Risk Score", f"{avg_risk:.3f}")
        
        with col3:
            avg_confidence = df_display.get("confidence", pd.Series([0])).mean()
            st.metric("Avg Confidence", f"{avg_confidence:.3f}")
        
        with col4:
            high_flags = (df_display.get("governance_flags", "") != "").sum()
            st.metric("Governance Flags", high_flags)
    else:
        st.info("No data loaded. Upload CSV or enable sample data.")

# ==================================================
# TAB 2: DEEP DIVE
# ==================================================
with tab2:
    st.header("🔍 Incident Deep Dive")
    
    if st.session_state.incidents_df is not None and len(st.session_state.incidents_df) > 0:
        # Select incident
        selected_idx = st.selectbox(
            "Select Incident",
            range(len(st.session_state.incidents_df)),
            format_func=lambda i: st.session_state.incidents_df.iloc[i]["incident_id"]
        )
        
        incident = st.session_state.incidents_df.iloc[selected_idx]
        st.session_state.selected_incident_idx = selected_idx
        
        # Tabs within deep dive
        dive_col1, dive_col2 = st.columns([2, 1])
        
        with dive_col1:
            st.subheader(f"Incident {incident['incident_id']}")
            
            # Basic info
            info_cols = st.columns(3)
            with info_cols[0]:
                st.metric("User ID", incident.get("user_id", "N/A"))
            with info_cols[1]:
                st.metric("Amount", f"${incident.get('amount', 0):,.2f}")
            with info_cols[2]:
                st.metric("Timestamp", incident.get("timestamp", "N/A"))
            
            # ---- Intelligence Output ----
            st.subheader("🧠 Intelligence Output")
            
            if "confidence" in incident:
                st.progress(float(incident["confidence"]), text=f"Confidence: {incident['confidence']:.1%}")
                st.write(f"**Explanation:** {incident.get('explanation', 'No explanation available')}")
                st.write(f"**Limitations:** {incident.get('limitations', 'N/A')}")
            else:
                st.info("Run analysis on Incidents tab first")
            
            # ---- RAG Evidence ----
            if show_rag_evidence:
                st.subheader("📚 RAG Evidence")
                rag_results = fusion_retriever(incident.to_dict())
                
                if rag_results.get("internal"):
                    evidence_df = pd.DataFrame(rag_results["internal"][:5])
                    st.dataframe(evidence_df, use_container_width=True)
                else:
                    st.warning("No RAG evidence found")
            
            # ---- Framework Mapping ----
            st.subheader("🧬 Framework Mapping")
            
            col_mitre, col_controls = st.columns(2)
            
            with col_mitre:
                st.write("**MITRE Techniques:**")
                threat_mapping = incident.get("threat_mapping", [])
                if threat_mapping:
                    for technique in threat_mapping:
                        st.code(technique)
                else:
                    st.write("None detected")
            
            with col_controls:
                st.write("**NIST/ISO Controls:**")
                controls = incident.get("control_references", [])
                if controls:
                    for control in controls:
                        st.code(control)
                else:
                    st.write("None detected")
        
        with dive_col2:
            # ---- Governance Panel ----
            if show_governance:
                st.subheader("⚖️ Governance")
                
                if "governance_flags" in incident:
                    flags = str(incident["governance_flags"]).split(", ")
                    if flags and flags[0]:
                        for flag in flags:
                            if flag:
                                st.warning(f"🚩 {flag}")
                
                # Mock governance metrics
                st.metric("Bias Score", f"{np.random.uniform(0, 1):.3f}")
                st.metric("Evidence Alignment", f"{np.random.uniform(0, 1):.3f}")
                st.metric("Drift", f"{np.random.uniform(0, 0.1):.4f}")
    else:
        st.info("Select an incident from the table")

# ==================================================
# TAB 3: ANALYTICS
# ==================================================
with tab3:
    st.header("📈 System Analytics & Evaluation")
    
    if st.session_state.incidents_df is not None and "confidence" in st.session_state.incidents_df.columns:
        # Generate synthetic ground truth
        df = st.session_state.incidents_df.copy()
        df["ground_truth"] = np.random.randint(0, 2, len(df))
        df["predicted_label"] = predict_labels(df, threshold=0.5)
        
        # Sub-tabs for analytics
        analytics_tabs = st.tabs(["Precision/Recall", "Fairness", "Drift", "Calibration", "Governance"])
        
        # ---- Precision/Recall ----
        with analytics_tabs[0]:
            st.subheader("Precision & Recall")
            metrics = evaluate_classification(df["ground_truth"].tolist(), df["predicted_label"].tolist())
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Precision", f"{metrics['precision']:.3f}")
            with col2:
                st.metric("Recall", f"{metrics['recall']:.3f}")
            with col3:
                st.metric("F1 Score", f"{metrics['f1']:.3f}")
            with col4:
                st.metric("True Positives", metrics["true_positives"])
            
            fig = plot_precision_recall(metrics)
            st.pyplot(fig)
        
        # ---- Fairness ----
        with analytics_tabs[1]:
            st.subheader("Fairness by Segment")
            fairness = fairness_by_segment(
                df[["amount"]].to_dict("records"),
                df["predicted_label"].tolist(),
                segment_key="amount",
                segment_thresholds={"high": 5000, "low": 0}
            )
            
            fairness_df = pd.DataFrame([
                {
                    "Segment": seg,
                    "Positive Rate": data["positive_rate"],
                    "Count": data["count"]
                }
                for seg, data in fairness.items()
            ])
            
            st.dataframe(fairness_df, use_container_width=True)
            fig = plot_fairness_disparity(fairness)
            st.pyplot(fig)
        
        # ---- Drift ----
        with analytics_tabs[2]:
            st.subheader("Model Drift Detection")
            
            # Split into baseline and current
            baseline_idx = len(df) // 2
            baseline_preds = df.iloc[:baseline_idx]["predicted_label"].tolist()
            current_preds = df.iloc[baseline_idx:]["predicted_label"].tolist()
            
            drift = compute_drift(baseline_preds, current_preds)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Drift Score (PSI)", f"{drift['drift_score']:.4f}")
            with col2:
                st.metric("Mean Shift", f"{drift['mean_shift']:.3f}")
            with col3:
                status = "🟢 LOW" if drift['drift_score'] < 0.05 else "🟡 MED" if drift['drift_score'] < 0.1 else "🔴 HIGH"
                st.metric("Status", status)
            
            fig = plot_drift(drift)
            st.pyplot(fig)
        
        # ---- Calibration ----
        with analytics_tabs[3]:
            st.subheader("Calibration Curve")
            cal = calibration_curve(
                df["ground_truth"].tolist(),
                df["confidence"].tolist()
            )
            
            fig = plot_calibration(cal)
            st.pyplot(fig)
        
        # ---- Governance ----
        with analytics_tabs[4]:
            st.subheader("Governance Compliance")
            
            # Mock governance outputs
            gov_batch = [
                {
                    "governance_flags": ["LOW_EVIDENCE"] if np.random.rand() < 0.2 else []
                }
                for _ in range(len(df))
            ]
            
            gov = governance_compliance(gov_batch)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Compliance Status", gov["compliance_status"])
            with col2:
                st.metric("Critical Rate", f"{gov['critical_rate']:.1%}")
            
            fig = plot_governance_compliance(gov)
            st.pyplot(fig)
    else:
        st.info("Run analysis first to view analytics")

# ==================================================
# TAB 4: COPILOT (PLACEHOLDER)
# ==================================================
with tab4:
    st.header("🤖 SOC Copilot")
    
    st.info("CrewAI copilot integration placeholder. Use this for dynamic incident investigation.")
    
    query = st.text_area(
        "Ask the SOC Copilot",
        placeholder="e.g., What patterns appear in high-value transactions?",
        height=100
    )
    
    if st.button("Run Query"):
        st.info("Copilot response placeholder - integrate with CrewAI agents")
        st.write("This would call your CrewAI crew to answer analyst questions.")

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: gray; font-size: 12px;">
    FinSecAI SOC Dashboard | v1.0 | Role: """ + str(st.session_state.role) + """
    </div>
    """,
    unsafe_allow_html=True
)
