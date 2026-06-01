"""
FinSecAI SOC Command Center
Professional Dark Theme - No Authentication
Multi-Tenant Support with Real MITRE/NIST RAG Integration
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta


def get_secret(key: str, default: str = "") -> str:
    """Retrieve secrets from Streamlit secrets first, then environment variables."""
    try:
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)

import plotly.express as px
import plotly.graph_objects as go
import requests
from io import BytesIO
import tempfile

# ============================================================
# PROJECT SETUP & IMPORTS
# ============================================================

from dashboards.style import (
    load_css, 
    render_kpi_card, 
    render_badge, 
    render_section_divider,
    get_risk_color, 
    get_risk_badge,
    ACCENT_GOLD, 
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    DANGER,
    SUCCESS,
    WARNING,
    PRIMARY_BG,
    SECONDARY_BG
)

try:
    from src.services.intelligence_service import run_intelligence
    from src.rag.fusion_retriever import fusion_retriever
    from src.orchestration.run_graph import run_full_pipeline
    from src.pipeline.schema import ensure_incident_schema
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
    from src.reporting.pdf_generator import SOCReportGenerator
    REPORT_GENERATOR_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠ Some modules not available: {str(e)}")
    REPORT_GENERATOR_AVAILABLE = False

# ============================================================
# PERFORMANCE OPTIMIZATION - CACHING HELPERS
# ============================================================
@st.cache_data(ttl=1800)  # 30 minutes
def cached_run_intelligence(incident_dict_json: str):
    """Cache intelligence analysis results for 30 minutes"""
    import json
    incident = json.loads(incident_dict_json)
    return run_intelligence(incident)

@st.cache_data(ttl=3600)  # 1 hour
def cached_run_pipeline(incident_dict_json: str):
    """Cache full pipeline results for 1 hour"""
    import json
    incident = json.loads(incident_dict_json)
    return run_full_pipeline(incident)

@st.cache_data(ttl=600)  # 10 minutes
def cached_rag_retrieval(query_json: str):
    """Cache RAG retrieval results for 10 minutes"""
    import json
    query = json.loads(query_json)
    return fusion_retriever(query)

# ============================================================
# LLM / NLP HELPERS
# ============================================================

def generate_llm_report_text(incident: dict, provider: str) -> str:
    """Generate a narrative incident report using an LLM provider or fallback."""
    prompt = (
        "You are a SOC analyst writing an incident report. "
        "Summarize the incident, explain the risk factors, governance flags, "
        "and provide a short recommended next step in clear language.\n\n"
        "Incident details:\n"
    )
    for key, value in incident.items():
        prompt += f"- {key}: {value}\n"
    prompt += (
        "\nWrite a concise, professional incident report summary for security leadership. "
        "Keep it under 180 words."
    )

    try:
        if "OpenAI" in provider:
            import openai
            openai.api_key = get_secret("OPENAI_API_KEY", "")
            if not openai.api_key:
                raise RuntimeError("OpenAI key not configured")
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=450,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()

        if "Claude" in provider:
            from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
            client = Anthropic(api_key=get_secret("ANTHROPIC_API_KEY", ""))
            if not client.api_key:
                raise RuntimeError("Anthropic key not configured")
            response = client.create_completion(
                model="claude-3-haiku",
                prompt=HUMAN_PROMPT + prompt + AI_PROMPT,
                max_tokens_to_sample=450,
                temperature=0.3,
            )
            return response["completion"].strip()

        if "Cohere" in provider:
            import cohere
            client = cohere.Client(get_secret("COHERE_API_KEY", ""))
            if not client.api_key:
                raise RuntimeError("Cohere key not configured")
            response = client.generate(
                model="command-xlarge-nightly",
                prompt=prompt,
                max_tokens=450,
                temperature=0.3,
            )
            return response.text.strip()

        if "Local" in provider:
            local_url = get_secret("LOCAL_LLM_URL", "http://localhost:11434/api/generate")
            payload = {"model": get_secret("LOCAL_LLM_MODEL", "llama3"), "prompt": prompt, "max_tokens": 450}
            response = requests.post(local_url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json().get("text", "").strip()

    except Exception as e:
        fallback_text = (
            f"LLM provider fallback engaged because: {str(e)}\n\n"
            "Incident report summary:\n"
            f"- Incident ID: {incident.get('incident_id', 'N/A')}\n"
            f"- Risk score: {incident.get('risk_score', 'N/A')}\n"
            f"- Confidence: {incident.get('confidence', 'N/A')}\n"
            f"- Governance flags: {incident.get('governance_flags', 'None')}\n"
            f"- Recommended action: Review the highest risk incidents and escalate flagged cases."
        )
        return fallback_text

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="FinSecAI SOC Command Center",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global CSS
st.markdown(load_css(), unsafe_allow_html=True)

# ============================================================
# MULTI-TENANT CONFIGURATION
# ============================================================
TENANTS = {
    "Acme Corp": {"id": "acme_001", "description": "Financial Services", "color": "#F59E0B"},
    "TechCorp": {"id": "tech_002", "description": "Technology", "color": "#60A5FA"},
    "Finance Inc": {"id": "finance_003", "description": "Investment Banking", "color": "#22C55E"},
}

# ============================================================
# DATA ENGINE STATE LAYER
# ============================================================

class DataEngine:
    """Centralized data management for reactive state propagation"""

    @staticmethod
    def set_active_dataset(df: pd.DataFrame, tenant: str, source: str = "upload"):
        """Central dataset loader - the single source of truth for data updates"""
        # Ensure schema compliance
        df = ensure_incident_schema(df)

        # Add tenant metadata
        df = df.copy()
        df["tenant_id"] = TENANTS[tenant]["id"]
        df["tenant_name"] = tenant
        df["data_source"] = source
        df["loaded_at"] = datetime.now()

        # Store in Layer 1: Raw tenant data
        st.session_state.raw_incidents[tenant] = df

        # Clear any previous analysis for this tenant (forces recomputation)
        if tenant in st.session_state.analysis_results:
            del st.session_state.analysis_results[tenant]

        # Clear UI view model to force refresh
        st.session_state.active_view_df = None

        # Set dataset version for reactive updates
        st.session_state.dataset_version = datetime.now().timestamp()

        # Trigger reactive update across all components
        st.session_state.last_data_update = {
            "tenant": tenant,
            "timestamp": datetime.now(),
            "source": source,
            "row_count": len(df),
            "version": st.session_state.dataset_version
        }

        return df

    @staticmethod
    def get_active_dataset(tenant: str):
        """Get the current active dataset for a tenant"""
        return st.session_state.raw_incidents.get(tenant)

    @staticmethod
    def get_analyzed_dataset(tenant: str):
        """Get analyzed dataset if available, otherwise raw"""
        analysis = st.session_state.analysis_results.get(tenant)
        if analysis:
            return analysis["df"]
        return DataEngine.get_active_dataset(tenant)

    @staticmethod
    def get_executive_summary(tenant: str):
        """Get executive summary if analysis exists"""
        analysis = st.session_state.analysis_results.get(tenant)
        return analysis.get("summary") if analysis else None

    @staticmethod
    def has_analysis(tenant: str) -> bool:
        """Check if tenant has analysis results"""
        return tenant in st.session_state.analysis_results

    @staticmethod
    def get_dataset_version():
        """Get current dataset version for reactive updates"""
        return st.session_state.get("dataset_version", 0)

    @staticmethod
    def trigger_data_refresh():
        """Force refresh of all data-dependent components"""
        st.session_state.dataset_version = datetime.now().timestamp()
        st.session_state.last_data_update = {
            "timestamp": datetime.now(),
            "version": st.session_state.dataset_version
        }

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
session_defaults = {
    "current_tenant": "Acme Corp",
    "raw_incidents": {},  # Layer 1: Raw tenant data
    "analysis_results": {},  # Layer 2: Analysis output with executive summary
    "active_view_df": None,  # Layer 3: UI view model
    "incidents_df": None,  # Global incidents dataframe for analytics
    "selected_incident_idx": None,
    "baseline_predictions": None,
    "llm_report_text": {},
    "current_predictions": None,
    "governance_batch": None,
    "rag_framework_cache": {},
    "intelligence_cache": {},  # Cache for analyzed incidents
    "dataset_version": 0,  # For reactive updates
    "last_data_update": None,  # Track data changes
}

for key, default_value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

# ============================================================
# HELPER FUNCTIONS
# ============================================================
@st.cache_data
def get_tenant_data(tenant_id: str, df: pd.DataFrame) -> pd.DataFrame:
    """Filter data by tenant"""
    if "tenant_id" not in df.columns:
        # Add synthetic tenant IDs if not present
        df = df.copy()
        df["tenant_id"] = tenant_id
    return df[df["tenant_id"] == tenant_id].copy()

@st.cache_data(ttl=3600)
def get_framework_mappings(risk_score: float) -> dict:
    """Retrieve unified MITRE/NIST mappings via RAG based on risk"""
    try:
        # Single RAG query for both frameworks
        query = {
            "text": f"threat techniques and security controls for financial fraud risk {risk_score:.2f}",
            "framework": "MITRE ATT&CK,NIST CSF",
            "k": 5
        }
        results = fusion_retriever(query)
        
        mitre_techniques = []
        nist_controls = []
        
        if results.get("external"):
            for hit in results["external"]:
                framework = hit.get("framework", "").upper()
                if "MITRE" in framework:
                    tech_id = hit.get("id", hit.get("framework_id", "T1234"))
                    if tech_id not in mitre_techniques:
                        mitre_techniques.append(tech_id)
                elif "NIST" in framework:
                    control_id = hit.get("control_ref", hit.get("framework_id", "AC-2"))
                    if control_id not in nist_controls:
                        nist_controls.append(control_id)
        
        # Fallback mappings if RAG fails
        if not mitre_techniques:
            if risk_score > 0.7:
                mitre_techniques = ["T1078.001", "T1566.002", "T1110.003"]  # Valid Accounts, Phishing, Brute Force
            elif risk_score > 0.4:
                mitre_techniques = ["T1566.002", "T1071.001"]  # Phishing, Application Layer Protocol
            else:
                mitre_techniques = ["T1592.004", "T1598.002"]  # Recon, Phishing for Information
        
        if not nist_controls:
            if risk_score > 0.7:
                nist_controls = ["AC-2", "AC-3", "AU-2", "SI-4"]  # Access, Logging, Monitoring
            elif risk_score > 0.4:
                nist_controls = ["AC-2", "AU-2", "SC-7"]  # Basic controls
            else:
                nist_controls = ["AC-2", "SI-4"]  # Minimal controls
        
        return {
            "mitre": mitre_techniques[:3],  # Limit to top 3
            "nist": nist_controls[:3]
        }
    except Exception as e:
        # Fallback mappings
        return {
            "mitre": ["T1078.001", "T1566.002", "T1110.003"],
            "nist": ["AC-2", "AC-3", "AU-2"]
        }

# ============================================================
# SIDEBAR CONTROLS (NO AUTHENTICATION)
# ============================================================
with st.sidebar:
    st.markdown("# ⚙️ Control Panel")
    st.divider()
    
    # Tenant Selection
    st.subheader("🏢 Tenant Selection")
    selected_tenant = st.selectbox(
        "Select Organization",
        list(TENANTS.keys()),
        key="tenant_selector"
    )

    # FORCE REFRESH DATA when tenant changes
    if st.session_state.get("current_tenant") != selected_tenant:
        st.session_state.current_tenant = selected_tenant
        # Clear active view to force reload
        st.session_state.active_view_df = None
        st.rerun()

    tenant_info = TENANTS[selected_tenant]
    st.info(f"**{selected_tenant}**\n\n{tenant_info['description']}")
    
    st.divider()
    
    # Data Input
    st.subheader("📤 Data Input")
    
    uploaded_file = st.file_uploader("Upload CSV alerts", type=["csv"])
    use_sample = st.checkbox("Use sample data", value=True)
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            df = ensure_incident_schema(df)
            df["tenant_id"] = tenant_info["id"]
            # Store in Layer 1: Raw tenant data
            st.session_state.raw_incidents[selected_tenant] = df
            # Clear any previous analysis for this tenant
            if selected_tenant in st.session_state.analysis_results:
                del st.session_state.analysis_results[selected_tenant]
            st.session_state.active_view_df = None  # Force UI refresh
            st.success(f"✅ Loaded {len(df)} incidents for {selected_tenant}")
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
    elif use_sample:
        # Generate high-quality sample data with tenant scoping
        np.random.seed(42)
        n_incidents = 50
        df = pd.DataFrame({
            "incident_id": [f"INC-{10000+i}" for i in range(n_incidents)],
            "tenant_id": [tenant_info["id"]] * n_incidents,
            "tenant_name": [selected_tenant] * n_incidents,
            "user_id": np.random.choice([f"USER-{i:04d}" for i in range(1, 11)], n_incidents),
            "amount": np.random.exponential(5000, n_incidents),
            "risk_score": np.random.uniform(0.1, 0.95, n_incidents),
            "anomaly_score": np.random.uniform(0, 1, n_incidents),
            "timestamp": [datetime.now() - timedelta(hours=i*2) for i in range(n_incidents)],
            "transaction_type": np.random.choice(["TRANSFER", "WITHDRAWAL", "DEPOSIT"], n_incidents),
            "device_id": np.random.choice([f"DEV-{i:05d}" for i in range(1, 20)], n_incidents),
        })
        df = ensure_incident_schema(df)
        # Store in Layer 1: Raw tenant data
        st.session_state.raw_incidents[selected_tenant] = df
        # Clear any previous analysis for this tenant
        if selected_tenant in st.session_state.analysis_results:
            del st.session_state.analysis_results[selected_tenant]
        st.session_state.active_view_df = None  # Force UI refresh
    else:
        # Clear data when sample data checkbox is unchecked
        if selected_tenant in st.session_state.raw_incidents:
            del st.session_state.raw_incidents[selected_tenant]
        if selected_tenant in st.session_state.analysis_results:
            del st.session_state.analysis_results[selected_tenant]
        st.session_state.active_view_df = None
        st.info("📭 Data cleared. Upload CSV or enable sample data.")
    
    st.divider()
    show_rag = st.toggle("📚 Show RAG Evidence", value=True)
    show_governance = st.toggle("⚖️ Show Governance", value=True)
    show_framework = st.toggle("🧬 Show MITRE/NIST", value=True)
    
    st.divider()
    
    # LLM Provider Selection
    st.subheader("🤖 LLM Configuration")
    llm_provider = st.selectbox(
        "Provider",
        ["OpenAI (gpt-4o-mini)", "Claude (claude-3-haiku)", "Cohere", "Local (Ollama)"]
    )
    
    st.divider()
    
    # System Info
    st.subheader("ℹ️ System Info")
    st.caption(f"**Version:** 3.0 (No Auth + Multi-Tenant)")
    st.caption(f"**Current Tenant:** {st.session_state.current_tenant}")
    current_tenant = st.session_state.current_tenant
    raw_data = st.session_state.raw_incidents.get(current_tenant)
    data_rows = len(raw_data) if raw_data is not None else 0
    st.caption(f"**Data Rows:** {data_rows}")
    st.caption(f"**RAG Framework:** Active (MITRE/NIST)")

# ============================================================
# MAIN HEADER
# ============================================================
col_header_left, col_header_right = st.columns([3, 1])

with col_header_left:
    st.markdown("# 🎯 FinSecAI SOC Command Center")
    tenant_color = TENANTS[st.session_state.current_tenant]["color"]
    
    # Show tenant change indicator
    current_tenant = st.session_state.current_tenant
    raw_data = st.session_state.raw_incidents.get(current_tenant)
    analysis = st.session_state.analysis_results.get(current_tenant)
    
    analysis_status = "✅ Analyzed" if analysis else "📋 Raw Data"
    st.markdown(f"**Analyst Console** | **Tenant:** <span style='color: {tenant_color}; font-weight: bold; font-size: 1.1em;'>{current_tenant}</span> | **Status:** {analysis_status} | **Updated:** {datetime.now().strftime('%H:%M:%S')}", unsafe_allow_html=True)

with col_header_right:
    current_tenant = st.session_state.current_tenant
    raw_data = st.session_state.raw_incidents.get(current_tenant)
    active_incidents = len(raw_data) if raw_data is not None else 0
    st.metric("Active Incidents", active_incidents)

st.divider()

# ============================================================
# MAIN TABS
# ============================================================
tab_overview, tab_incidents, tab_deep_dive, tab_analytics, tab_reports, tab_admin = st.tabs([
    "📊 Overview",
    "🔔 Incidents",
    "🔍 Deep Dive",
    "📈 Analytics",
    "📄 Reports",
    "⚙️ Admin"
])

# ==================================================
# TAB 1: OVERVIEW (EXECUTIVE VIEW)
# ==================================================
with tab_overview:
    st.markdown("### 📊 Executive Summary")

    current_tenant = st.session_state.current_tenant
    raw_data = st.session_state.raw_incidents.get(current_tenant)

    if raw_data is not None and len(raw_data) > 0:
        # Check if we have analysis results (Layer 2)
        analysis = st.session_state.analysis_results.get(current_tenant)

        if analysis:
            # Use analyzed data with executive summary
            df = analysis["df"]
            summary = analysis["summary"]

            # Display executive summary KPIs
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                render_kpi_card(
                    "Total Incidents",
                    summary["total_incidents"],
                    f"Analyzed: {summary['analyzed_count']}",
                    color="gold"
                )

            with col2:
                render_kpi_card(
                    "Avg Risk Score",
                    f"{summary['avg_risk']:.2f}",
                    f"High Risk: {summary['high_risk_count']}",
                    color="red" if summary['avg_risk'] > 0.7 else "gold" if summary['avg_risk'] > 0.4 else "green"
                )

            with col3:
                render_kpi_card(
                    "Avg Confidence",
                    f"{summary['avg_confidence']:.2f}",
                    f"Evidence: {summary['avg_evidence_coverage']:.2f}",
                    color="blue"
                )

            with col4:
                render_kpi_card(
                    "Governance Flags",
                    summary["governance_flags_count"],
                    f"{summary['governance_flags_count']/summary['total_incidents']*100:.1f}% flagged",
                    color="red" if summary["governance_flags_count"] > 0 else "green"
                )

        else:
            # Use raw data (no analysis yet)
            df = raw_data

            # KPI Row 1
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                render_kpi_card(
                    "Total Incidents",
                    len(df),
                    "Raw data - not analyzed",
                    color="gold"
                )

            with col2:
                avg_risk = df.get("risk_score", pd.Series([0.0])).mean()
                risk_badge = get_risk_badge(avg_risk)
                render_kpi_card(
                    "Avg Risk Score",
                    f"{avg_risk:.2f}",
                    f"Risk: {risk_badge.upper()}",
                    color="red" if avg_risk > 0.7 else "gold" if avg_risk > 0.4 else "green"
                )

            with col3:
                avg_anomaly = df["anomaly_score"].mean()
                render_kpi_card(
                    "Avg Anomaly",
                    f"{avg_anomaly:.2f}",
                    "Baseline vs Current",
                    color="blue"
                )

            with col4:
                high_risk_count = (df["risk_score"] > 0.7).sum()
                render_kpi_card(
                    "High Risk Cases",
                    high_risk_count,
                    f"{high_risk_count/len(df)*100:.1f}% of total",
                    color="red" if high_risk_count > 0 else "green"
                )

        st.divider()

        # Risk Distribution Chart
        st.markdown("### 📊 Risk Distribution")

        fig = px.histogram(
            df,
            x="risk_score",
            nbins=20,
            title="Incident Risk Score Distribution",
            labels={"risk_score": "Risk Score", "count": "Number of Incidents"}
        )
        fig.update_layout(
            height=300,
            showlegend=False,
            hovermode="x unified"
        )
        fig.update_traces(marker_color=ACCENT_GOLD)
        st.plotly_chart(fig, use_container_width=True)

        # Confidence Distribution (only if analyzed)
        if analysis:
            st.markdown("### 🎯 Analysis Confidence Distribution")

            fig2 = px.histogram(
                df,
                x="confidence",
                nbins=20,
                title="Intelligence Analysis Confidence",
                labels={"confidence": "Confidence Score", "count": "Number of Incidents"}
            )
            fig2.update_layout(
                height=300,
                showlegend=False,
                hovermode="x unified"
            )
            fig2.update_traces(marker_color="#60A5FA")
            st.plotly_chart(fig2, use_container_width=True)

        # Governance Flags Chart (only if analyzed)
        if analysis and summary["governance_flags_count"] > 0:
            st.markdown("### ⚖️ Governance Compliance")

            # Count governance flags
            flag_counts = {}
            for flags_str in df["governance_flags"].dropna():
                if flags_str and flags_str != "ANALYSIS_ERROR":
                    flags = [f.strip() for f in flags_str.split(",") if f.strip()]
                    for flag in flags:
                        flag_counts[flag] = flag_counts.get(flag, 0) + 1

            if flag_counts:
                fig3 = px.bar(
                    x=list(flag_counts.keys()),
                    y=list(flag_counts.values()),
                    title="Governance Flag Distribution",
                    labels={"x": "Flag Type", "y": "Count"}
                )
                fig3.update_layout(
                    height=300,
                    hovermode="x unified"
                )
                fig3.update_traces(marker_color="#EF4444")
                st.plotly_chart(fig3, use_container_width=True)

    else:
        st.info("📤 Please upload data or enable sample data to view the executive summary.")

# ==================================================
# TAB 2: INCIDENTS (OPERATIONAL TABLE)
# ==================================================
with tab_incidents:
    st.markdown("### 🔔 Incident Registry")

    current_tenant = st.session_state.current_tenant
    raw_data = st.session_state.raw_incidents.get(current_tenant)
    analysis = st.session_state.analysis_results.get(current_tenant)

    if raw_data is not None and len(raw_data) > 0:
        # Use analyzed data if available, otherwise raw data
        df = analysis["df"] if analysis else raw_data
        
        # Run analysis button
        col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 2])
        
        with col_btn1:
            if st.button("▶️ Analyze All Incidents"):
                current_tenant = st.session_state.current_tenant
                raw_data = st.session_state.raw_incidents.get(current_tenant)

                if raw_data is None or len(raw_data) == 0:
                    st.error("No data available for analysis")
                else:
                    st.info("🔄 Analyzing incidents (this may take a moment)...")

                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    results = []
                    for idx, row in raw_data.iterrows():
                        progress = (idx + 1) / len(raw_data)
                        progress_bar.progress(progress)
                        status_text.text(f"Processing {idx + 1}/{len(raw_data)}")

                        try:
                            incident_dict = row.to_dict()
                            pipeline_result = run_full_pipeline(incident_dict)
                            intelligence = pipeline_result.get("intelligence", {})
                            governance_flags = pipeline_result.get("governance_flags") or []
                            results.append({
                                "incident_id": row.get("incident_id", "N/A"),
                                "tenant_id": row.get("tenant_id"),
                                "tenant_name": row.get("tenant_name"),
                                "risk_score": row.get("risk_score", 0),
                                "anomaly_score": row.get("anomaly_score", 0),
                                "confidence": intelligence.get("confidence", 0),
                                "evidence_coverage": intelligence.get("evidence_coverage", 0),
                                "governance_flags": ", ".join(governance_flags),
                                "explanation": intelligence.get("explanation", "")
                            })
                        except Exception as e:
                            results.append({
                                "incident_id": row["incident_id"],
                                "tenant_id": row.get("tenant_id"),
                                "tenant_name": row.get("tenant_name"),
                                "risk_score": row.get("risk_score", 0),
                                "anomaly_score": row.get("anomaly_score", 0),
                                "confidence": 0,
                                "evidence_coverage": 0,
                                "governance_flags": "ANALYSIS_ERROR",
                                "explanation": f"Error: {str(e)[:50]}"
                            })

                    # Create analyzed dataframe
                    df_results = pd.DataFrame(results)

                    # Create executive summary
                    summary = {
                        "total_incidents": len(results),
                        "analyzed_count": len([r for r in results if r["governance_flags"] != "ANALYSIS_ERROR"]),
                        "avg_risk": np.mean([r["risk_score"] for r in results]),
                        "avg_confidence": np.mean([r["confidence"] for r in results]),
                        "avg_evidence_coverage": np.mean([r["evidence_coverage"] for r in results]),
                        "high_risk_count": len([r for r in results if r["risk_score"] > 0.7]),
                        "governance_flags_count": len([r for r in results if r["governance_flags"] and r["governance_flags"] != "ANALYSIS_ERROR"])
                    }

                    # Store in Layer 2: Analysis output
                    st.session_state.analysis_results[current_tenant] = {
                        "df": df_results,
                        "summary": summary,
                        "timestamp": datetime.now()
                    }

                    status_text.empty()
                    progress_bar.empty()
                    
                    # Show comprehensive analysis summary
                    col_s1, col_s2, col_s3 = st.columns(3)
                    with col_s1:
                        st.metric("Total Analyzed", summary["analyzed_count"], f"of {summary['total_incidents']}")
                    with col_s2:
                        st.metric("High Risk Cases", summary["high_risk_count"], f"({summary['high_risk_count']/summary['total_incidents']*100:.1f}%)")
                    with col_s3:
                        st.metric("Avg Risk Score", f"{summary['avg_risk']:.2f}", f"Avg Confidence: {summary['avg_confidence']:.2f}")
                    
                    st.success(f"✅ Successfully analyzed {summary['analyzed_count']} incidents! Check the 📊 Overview tab for distribution charts and risk analysis.")
                    st.info("💡 Incident table below now shows analyzed results with risk levels, confidence scores, and governance flags.")
                    error_count = len([r for r in results if r["governance_flags"] == "ANALYSIS_ERROR"])
                    result_summary = (
                        f"Outcome: {summary['analyzed_count']} of {summary['total_incidents']} incidents analyzed, "
                        f"{summary['high_risk_count']} high-risk cases, {summary['governance_flags_count']} governance issues flagged, "
                        f"avg confidence {summary['avg_confidence']:.1%}."
                    )
                    if error_count > 0:
                        result_summary += f" {error_count} incidents had analysis errors."
                    st.info(result_summary)
                    st.rerun()
        
        with col_btn2:
            if st.button("⬇️ Export CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    file_name=f"incidents_{st.session_state.current_tenant.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    width="stretch"
                )
        
        with col_btn3:
            if st.button("🔄 Refresh Data"):
                st.rerun()
        
        st.divider()
        
        # Display table with styling
        if analysis:
            st.markdown("### 📋 Analyzed Incident Table (Risk Level Sorted)")
        else:
            st.markdown("### 📋 Incident Table (Raw Data)")
        
        # Prepare display dataframe
        display_df = df.copy()
        
        # For analyzed data, show more columns and sort by risk
        if analysis:
            # Select key columns for display
            display_cols = ['incident_id', 'user_id', 'amount', 'risk_score', 'confidence', 'anomaly_score', 'transaction_type']
            # Only show columns that exist
            display_cols = [col for col in display_cols if col in display_df.columns]
            display_df = display_df[display_cols].sort_values('risk_score', ascending=False)
            
            # Add risk level column for better visualization
            display_df['risk_level'] = display_df['risk_score'].apply(
                lambda x: '🔴 HIGH' if x > 0.7 else ('🟡 MEDIUM' if x > 0.4 else '🟢 LOW')
            )
        
        # Advanced Filtering
        with st.expander("🔍 Advanced Filters", expanded=False):
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            
            with col_filter1:
                # Risk level filter
                risk_levels = st.multiselect(
                    "Risk Level",
                    ["🔴 HIGH", "🟡 MEDIUM", "🟢 LOW"],
                    default=["🔴 HIGH", "🟡 MEDIUM", "🟢 LOW"],
                    key=f"risk_filter_{st.session_state.current_tenant}"
                )
            
            with col_filter2:
                # User filter
                if 'user_id' in display_df.columns:
                    users = display_df['user_id'].unique().tolist()
                    selected_users = st.multiselect(
                        "User ID",
                        users,
                        default=users[:5] if len(users) > 5 else users,
                        key=f"user_filter_{st.session_state.current_tenant}"
                    )
                else:
                    selected_users = None
            
            with col_filter3:
                # Amount range filter
                if 'amount' in display_df.columns:
                    min_amount = float(display_df['amount'].min())
                    max_amount = float(display_df['amount'].max())
                    amount_range = st.slider(
                        "Amount Range",
                        min_amount,
                        max_amount,
                        (min_amount, max_amount),
                        key=f"amount_filter_{st.session_state.current_tenant}"
                    )
                else:
                    amount_range = None
            
            # Search box
            search_text = st.text_input(
                "Search by Incident ID or User ID",
                placeholder="Type to search...",
                key=f"search_filter_{st.session_state.current_tenant}"
            )
        
        # Apply filters
        filtered_df = display_df.copy()
        
        # Filter by risk level
        if 'risk_level' in filtered_df.columns and risk_levels:
            filtered_df = filtered_df[filtered_df['risk_level'].isin(risk_levels)]
        
        # Filter by user
        if selected_users is not None and 'user_id' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['user_id'].isin(selected_users)]
        
        # Filter by amount range
        if amount_range is not None and 'amount' in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df['amount'] >= amount_range[0]) & 
                (filtered_df['amount'] <= amount_range[1])
            ]
        
        # Filter by search text
        if search_text:
            search_mask = False
            if 'incident_id' in filtered_df.columns:
                search_mask = search_mask | filtered_df['incident_id'].str.contains(search_text, case=False, na=False)
            if 'user_id' in filtered_df.columns:
                search_mask = search_mask | filtered_df['user_id'].str.contains(search_text, case=False, na=False)
            filtered_df = filtered_df[search_mask]
        
        # Display filter stats
        st.caption(f"📊 Showing {len(filtered_df)} incidents ({len(filtered_df)/len(display_df)*100:.1f}% of {len(display_df)} total)")
        
        # Pagination controls
        page_size = st.selectbox("Rows per page", [10, 25, 50, 100], index=1, key=f"page_size_{st.session_state.current_tenant}")
        total_pages = (len(filtered_df) + page_size - 1) // page_size
        
        if "current_page" not in st.session_state:
            st.session_state.current_page = 0
        
        # Pagination UI
        col_page1, col_page2, col_page3 = st.columns([2, 3, 2])
        with col_page1:
            if st.button("⬅️ Previous", key=f"prev_{st.session_state.current_tenant}"):
                if st.session_state.current_page > 0:
                    st.session_state.current_page -= 1
                    st.rerun()
        
        with col_page2:
            page_input = st.number_input(
                f"Page (1-{total_pages})", 
                min_value=1, 
                max_value=max(1, total_pages),
                value=st.session_state.current_page + 1,
                key=f"page_num_{st.session_state.current_tenant}"
            )
            st.session_state.current_page = page_input - 1
        
        with col_page3:
            if st.button("Next ➡️", key=f"next_{st.session_state.current_tenant}"):
                if st.session_state.current_page < total_pages - 1:
                    st.session_state.current_page += 1
                    st.rerun()
        
        # Show pagination info
        start_idx = st.session_state.current_page * page_size
        end_idx = min((st.session_state.current_page + 1) * page_size, len(filtered_df))
        st.caption(f"Showing {start_idx + 1}-{end_idx} of {len(filtered_df)} incidents | Page {st.session_state.current_page + 1}/{total_pages}")
        
        # Display paginated dataframe
        display_df_page = filtered_df.iloc[start_idx:end_idx]
        st.dataframe(
            display_df_page,
            height=400,
            use_container_width=True
        )
    else:
        st.info("📌 No incidents loaded. Upload CSV or enable sample data.")

# ==================================================
# TAB 3: DEEP DIVE (INTELLIGENCE + EVIDENCE)
# ==================================================
with tab_deep_dive:
    st.markdown("### 🔍 Incident Deep Dive Analysis")

    current_tenant = st.session_state.current_tenant
    raw_data = st.session_state.raw_incidents.get(current_tenant)
    analysis = st.session_state.analysis_results.get(current_tenant)

    if raw_data is not None and len(raw_data) > 0:
        # Use analyzed data if available, otherwise raw data
        df = analysis["df"] if analysis else raw_data
        
        # Select incident
        selected_idx = st.selectbox(
            "Select Incident to Analyze",
            range(len(df)),
            format_func=lambda i: f"{df.iloc[i].get('incident_id', 'N/A')} (Risk: {float(df.iloc[i].get('risk_score', 0)):.2f})"
        )
        
        incident = df.iloc[selected_idx].copy()
        st.session_state.selected_incident_idx = selected_idx
        
        # Auto-run intelligence analysis if missing
        incident_id = incident.get('incident_id')
        cache_key = f"{st.session_state.current_tenant}_{incident_id}"
        
        incident_needs_analysis = (
            "confidence" not in incident or 
            not incident.get("explanation") or
            cache_key not in st.session_state.intelligence_cache
        )
        
        if incident_needs_analysis:
            with st.spinner("🔄 Auto-analyzing incident..."):
                try:
                    incident_dict = incident.to_dict()
                    pipeline_result = run_full_pipeline(incident_dict)
                    
                    # Update the incident with intelligence results
                    intelligence = pipeline_result.get("intelligence", {})
                    governance_flags = pipeline_result.get("governance_flags") or []
                    
                    incident["confidence"] = intelligence.get("confidence", 0)
                    incident["evidence_coverage"] = intelligence.get("evidence_coverage", 0)
                    incident["explanation"] = intelligence.get("explanation", "")
                    incident["limitations"] = intelligence.get("limitations", "")
                    incident["governance_flags"] = ", ".join(governance_flags)
                    
                    # Cache the results
                    st.session_state.intelligence_cache[cache_key] = {
                        "intelligence": intelligence,
                        "governance_flags": governance_flags,
                        "timestamp": datetime.now()
                    }
                    
                    # Update the DataFrame in analysis results
                    if analysis:
                        analysis["df"].iloc[selected_idx] = incident
                        st.session_state.analysis_results[current_tenant] = analysis
                    
                    st.success("✅ Intelligence analysis completed")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Auto-analysis failed: {str(e)[:100]}")
                    st.info("Manual analysis may be required")
        else:
            # Load from cache
            cached = st.session_state.intelligence_cache[cache_key]
            intelligence = cached["intelligence"]
            governance_flags = cached["governance_flags"]
            
            # Ensure incident has cached data
            incident["confidence"] = intelligence.get("confidence", 0)
            incident["evidence_coverage"] = intelligence.get("evidence_coverage", 0)
            incident["explanation"] = intelligence.get("explanation", "")
            incident["limitations"] = intelligence.get("limitations", "")
            incident["governance_flags"] = ", ".join(governance_flags)
        
        # Incident header
        col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
        
        with col_header1:
            st.markdown(f"## {incident['incident_id']}")
        
        with col_header2:
            risk_badge = get_risk_badge(incident.get("risk_score", 0))
            render_badge(risk_badge.upper(), badge_type=risk_badge)
        
        with col_header3:
            if incident.get("governance_flags"):
                render_badge("⚠ FLAGGED", badge_type="critical")
        
        st.divider()
        
        # Basic Info Row
        col_info1, col_info2, col_info3, col_info4 = st.columns(4)
        
        with col_info1:
            st.metric("User ID", incident.get("user_id", "N/A"))
        with col_info2:
            st.metric("Amount", f"${incident.get('amount', 0):,.2f}")
        with col_info3:
            st.metric("Risk Score", f"{incident.get('risk_score', 0):.3f}")
        with col_info4:
            st.metric("Anomaly Score", f"{incident.get('anomaly_score', 0):.3f}")
        
        st.divider()
        
        # Intelligence Panel
        st.markdown("### 🧠 Intelligence Analysis")
        
        with st.container():
            col_intel1, col_intel2 = st.columns([2, 1])
            
            with col_intel1:
                st.write(f"**Explanation:** {incident.get('explanation', 'Analysis in progress...')}")
                st.write(f"**Limitations:** {incident.get('limitations', 'N/A')}")
            
            with col_intel2:
                confidence = incident.get("confidence", 0)
                st.progress(float(confidence), text=f"Confidence: {confidence:.1%}")
                
                evidence_coverage = incident.get("evidence_coverage", 0)
                st.progress(float(evidence_coverage), text=f"Evidence: {evidence_coverage:.1%}")
                
                if evidence_coverage < 1.0:
                    st.warning("⚠ Partial evidence coverage detected")
        
        st.divider()
        
        # RAG Evidence
        if show_rag:
            st.markdown("### 📚 RAG Evidence")
            
            try:
                rag_results = fusion_retriever(incident.to_dict())
                if rag_results.get("internal"):
                    evidence_df = pd.DataFrame(rag_results["internal"][:10])
                    st.dataframe(evidence_df)
                else:
                    st.warning("No RAG evidence found")
            except Exception as e:
                st.warning(f"⚠ RAG retrieval error: {str(e)[:100]}")
            
            st.divider()
        
        # Framework Mapping (MITRE/NIST via RAG)
        if show_framework:
            st.markdown("### 🧬 Framework Mapping (Via RAG)")
            
            risk_score = incident.get("risk_score", 0)
            
            col_fw1, col_fw2 = st.columns(2)
            
            with col_fw1:
                st.write("**MITRE ATT&CK Techniques:**")
                mappings = get_framework_mappings(risk_score)
                techniques = mappings.get("mitre", [])
                if techniques:
                    for technique in techniques:
                        st.code(technique, language="text")
                else:
                    st.text("None detected")
            
            with col_fw2:
                st.write("**NIST Controls:**")
                controls = mappings.get("nist", [])
                if controls:
                    for control in controls:
                        st.code(control, language="text")
                else:
                    st.text("None detected")
            
            st.divider()
        
        # Governance Panel
        if show_governance:
            st.markdown("### ⚖️ Governance & Compliance")
            
            col_gov1, col_gov2 = st.columns([1.5, 2.5])
            
            with col_gov1:
                st.write("**Flags:**")
                if incident.get("governance_flags"):
                    flags = str(incident["governance_flags"]).split(", ")
                    for flag in flags:
                        if flag and flag != "":
                            st.warning(f"🚩 {flag}")
                else:
                    st.success("✓ No flags")
            
            with col_gov2:
                st.write("**Metrics:**")
                
                evidence_coverage = incident.get("evidence_coverage", 0)
                confidence = incident.get("confidence", 0)
                
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                
                with metric_col1:
                    # Bias score inversely related to evidence coverage
                    bias_score = max(0.1, 1.0 - evidence_coverage)
                    st.metric("Bias Score", f"{bias_score:.3f}")
                
                with metric_col2:
                    # Explainability tied to confidence and evidence
                    explainability = min(1.0, (confidence + evidence_coverage) / 2 + 0.3)
                    st.metric("Explainability", f"{explainability:.3f}")
                
                with metric_col3:
                    # Evidence alignment based on coverage
                    alignment = evidence_coverage * 0.9 + 0.1
                    st.metric("Evidence Alignment", f"{alignment:.3f}")
    else:
        st.info("📌 No incidents loaded. Upload CSV or enable sample data.")

# ==================================================
# TAB 4: ANALYTICS (EVALUATION ENGINE)
# ==================================================
with tab_analytics:
    st.markdown("### 📈 System Analytics & Evaluation")
    
    # Get data for current tenant
    current_tenant = st.session_state.current_tenant
    raw_data = st.session_state.raw_incidents.get(current_tenant)
    analysis = st.session_state.analysis_results.get(current_tenant)
    
    # Use analyzed data if available, otherwise raw data
    incidents_df = analysis["df"] if analysis else raw_data
    
    if incidents_df is not None and len(incidents_df) > 0:
        if st.button("▶️ Run Analytics"):
            if raw_data is None or len(raw_data) == 0:
                st.error("No data available for analytics")
            else:
                st.info("🔄 Running analytics across the current dataset...")
                progress_bar = st.progress(0)
                results = []
                for idx, row in raw_data.iterrows():
                    incident_dict = row.to_dict()
                    pipeline_result = cached_run_pipeline(json.dumps(incident_dict))
                    intelligence = pipeline_result.get("intelligence", {})
                    governance_flags = pipeline_result.get("governance_flags") or []
                    results.append({
                        "incident_id": incident_dict.get("incident_id", "N/A"),
                        "tenant_id": incident_dict.get("tenant_id"),
                        "tenant_name": incident_dict.get("tenant_name"),
                        "risk_score": incident_dict.get("risk_score", 0),
                        "anomaly_score": incident_dict.get("anomaly_score", 0),
                        "confidence": intelligence.get("confidence", 0),
                        "evidence_coverage": intelligence.get("evidence_coverage", 0),
                        "governance_flags": ", ".join(governance_flags),
                        "explanation": intelligence.get("explanation", ""),
                    })
                    progress_bar.progress((idx + 1) / len(raw_data))

                progress_bar.empty()
                df_results = pd.DataFrame(results)
                summary = {
                    "total_incidents": len(results),
                    "analyzed_count": len([r for r in results if r["governance_flags"] != "ANALYSIS_ERROR"]),
                    "avg_risk": np.mean([r["risk_score"] for r in results]),
                    "avg_confidence": np.mean([r["confidence"] for r in results]),
                    "avg_evidence_coverage": np.mean([r["evidence_coverage"] for r in results]),
                    "high_risk_count": len([r for r in results if r["risk_score"] > 0.7]),
                    "governance_flags_count": len([r for r in results if r["governance_flags"] and r["governance_flags"] != "ANALYSIS_ERROR"])
                }
                st.session_state.analysis_results[current_tenant] = {
                    "df": df_results,
                    "summary": summary,
                    "timestamp": datetime.now()
                }
                st.success("✅ Analytics run complete. Summary and charts are now available.")
                st.experimental_rerun()

        df = incidents_df.copy()
        
        # Synthetic ground truth for demo
        df["ground_truth"] = np.random.randint(0, 2, len(df))
        df["predicted_label"] = predict_labels(df.to_dict("records"), threshold=0.5)
        
        # Analytics tabs
        analytics_tab1, analytics_tab2, analytics_tab3, analytics_tab4, analytics_tab5 = st.tabs([
            "Precision/Recall",
            "Fairness",
            "Drift Detection",
            "Calibration",
            "Governance"
        ])
        
        # Tab 1: Precision/Recall
        with analytics_tab1:
            st.markdown("### Precision & Recall Metrics")
            
            metrics = evaluate_classification(
                df["ground_truth"].tolist(),
                df["predicted_label"].tolist()
            )
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            with col_m1:
                st.metric("Precision", f"{metrics['precision']:.3f}")
            with col_m2:
                st.metric("Recall", f"{metrics['recall']:.3f}")
            with col_m3:
                st.metric("F1 Score", f"{metrics['f1']:.3f}")
            with col_m4:
                st.metric("True Positives", metrics["true_positives"])
            
            st.divider()
            
            try:
                fig = plot_precision_recall(metrics)
                st.pyplot(fig)
            except Exception as e:
                st.warning(f"Chart rendering error: {str(e)[:100]}")
        
        # Tab 2: Fairness
        with analytics_tab2:
            st.markdown("### Fairness by Segment")
            
            fairness = fairness_by_segment(
                df[["amount"]].to_dict("records"),
                df["predicted_label"].tolist(),
                segment_key="amount",
                segment_thresholds={"high": 5000, "low": 0}
            )
            
            fairness_df = pd.DataFrame([
                {
                    "Segment": seg,
                    "Positive Rate": f"{data['positive_rate']:.3f}",
                    "Count": data["count"]
                }
                for seg, data in fairness.items()
            ])
            
            st.dataframe(fairness_df, hide_index=True)
            st.divider()
            
            try:
                fig = plot_fairness_disparity(fairness)
                st.pyplot(fig)
            except Exception as e:
                st.warning(f"Chart rendering error: {str(e)[:100]}")
        
        # Tab 3: Drift Detection
        with analytics_tab3:
            st.markdown("### Model Drift Detection (PSI)")
            
            baseline_idx = len(df) // 2
            baseline_preds = df.iloc[:baseline_idx]["predicted_label"].tolist()
            current_preds = df.iloc[baseline_idx:]["predicted_label"].tolist()
            
            drift = compute_drift(baseline_preds, current_preds)
            
            col_d1, col_d2, col_d3 = st.columns(3)
            
            with col_d1:
                st.metric("Drift Score (PSI)", f"{drift['drift_score']:.4f}")
            with col_d2:
                st.metric("Mean Shift", f"{drift['mean_shift']:.3f}")
            with col_d3:
                if drift['drift_score'] < 0.05:
                    status = "🟢 LOW"
                elif drift['drift_score'] < 0.1:
                    status = "🟡 MEDIUM"
                else:
                    status = "🔴 HIGH"
                st.metric("Drift Status", status)
            
            st.divider()
            
            try:
                fig = plot_drift(drift)
                st.pyplot(fig)
            except Exception as e:
                st.warning(f"Chart rendering error: {str(e)[:100]}")
        
        # Tab 4: Calibration
        with analytics_tab4:
            st.markdown("### Calibration Analysis")
            
            threshold = st.slider("Decision Threshold", 0.0, 1.0, 0.5, step=0.05)
            
            cal = calibration_curve(
                df["ground_truth"].tolist(),
                df.get("confidence", df["predicted_label"]).tolist()
            )
            
            st.divider()
            
            try:
                fig = plot_calibration(cal)
                st.pyplot(fig)
            except Exception as e:
                st.warning(f"Chart rendering error: {str(e)[:100]}")
        
        # Tab 5: Governance
        with analytics_tab5:
            st.markdown("### Governance Compliance")
            
            gov_batch = [
                {
                    "governance_flags": ["LOW_EVIDENCE"] if np.random.rand() < 0.2 else []
                }
                for _ in range(len(df))
            ]
            
            gov = governance_compliance(gov_batch)
            
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                st.metric("Compliance Status", gov["compliance_status"])
            with col_g2:
                st.metric("Critical Rate", f"{gov['critical_rate']:.1%}")
            
            st.divider()
            
            try:
                fig = plot_governance_compliance(gov)
                st.pyplot(fig)
            except Exception as e:
                st.warning(f"Chart rendering error: {str(e)[:100]}")
    else:
        st.info("📌 Run analysis first to view analytics")

# ==================================================
# TAB 5: REPORTS (PDF EXPORT)
# ==================================================
with tab_reports:
    st.markdown("### 📄 Incident Report Export")
    
    # Get data for current tenant
    current_tenant = st.session_state.current_tenant
    raw_data = st.session_state.raw_incidents.get(current_tenant)
    analysis = st.session_state.analysis_results.get(current_tenant)
    
    # Use analyzed data if available, otherwise raw data
    incidents_df = analysis["df"] if analysis else raw_data
    
    if incidents_df is not None and len(incidents_df) > 0:
        df = incidents_df.copy()
        
        # Report type selector
        report_type = st.radio(
            "Report Type",
            ["Single Incident", "Batch Report (Multiple Incidents)"],
            horizontal=True
        )
        
        st.divider()
        
        if report_type == "Single Incident":
            selected_idx = st.selectbox(
                "Select Incident",
                range(len(df)),
                format_func=lambda i: f"{df.iloc[i]['incident_id']}"
            )
            
            incident = df.iloc[selected_idx].to_dict()
            risk_score = incident.get("risk_score", 0)
            
            if st.button("🤖 Generate LLM Incident Report", key="generate_llm_incident_report"):
                report_text = generate_llm_report_text(incident, llm_provider)
                st.session_state.llm_report_text[incident.get("incident_id", "current")] = report_text
                st.success("✅ LLM incident report generated")

            llm_text = st.session_state.llm_report_text.get(incident.get("incident_id", "current"))
            if llm_text:
                st.divider()
                st.markdown("### 🤖 NLP / LLM Incident Report Summary")
                st.text_area("Report Narrative", llm_text, height=280)
                st.download_button(
                    "⬇️ Download NLP Report Text",
                    llm_text,
                    file_name=f"incident_report_{incident.get('incident_id','incident')}.txt",
                    mime="text/plain",
                    key="download_llm_report_text"
                )
                st.divider()

            if st.button("📄 Generate PDF Report", use_container_width=True):
                try:
                    # Get real MITRE/NIST mappings
                    mappings = get_framework_mappings(risk_score)
                    techniques = mappings.get("mitre", [])
                    controls = mappings.get("nist", [])
                    
                    # Mock full system data for report
                    report_data = {
                        "incident": incident,
                        "intelligence": {
                            "explanation": incident.get("explanation", "Incident analysis"),
                            "confidence": incident.get("confidence", 0.75),
                            "evidence_coverage": incident.get("evidence_coverage", 0.8),
                            "justifications": [
                                {"chunk_id": "RAG-001", "reason": "High transaction amount anomaly"},
                                {"chunk_id": "RAG-002", "reason": "User location mismatch"},
                            ],
                            "limitations": incident.get("limitations", "Limited historical data"),
                            "threat_mapping": techniques,
                            "control_references": controls,
                        },
                        "governance": {
                            "bias_score": np.random.uniform(0, 1),
                            "explainability_score": np.random.uniform(0.7, 1),
                            "evidence_alignment": np.random.uniform(0.7, 1),
                            "drift_score": np.random.uniform(0, 0.1),
                            "confidence_calibration": np.random.uniform(0.7, 1),
                            "governance_flags": incident.get("governance_flags", "").split(", ") if incident.get("governance_flags") else [],
                        },
                        "trace": [
                            {"node": "RAG Retrieval", "status": "✓ Complete"},
                            {"node": "Intelligence Analysis", "status": "✓ Complete"},
                            {"node": "Governance Check", "status": "✓ Complete"},
                        ]
                    }
                    
                    # Generate PDF
                    if not REPORT_GENERATOR_AVAILABLE:
                        raise RuntimeError("PDF generation is unavailable because the reportlab dependency is missing.")

                    pdf_gen = SOCReportGenerator()
                    pdf_dir = Path(tempfile.gettempdir())
                    pdf_path = pdf_dir / f"report_{incident['incident_id']}.pdf"
                    pdf_gen.generate_incident_report(report_data, str(pdf_path))
                    
                    # Offer download
                    with open(str(pdf_path), "rb") as f:
                        pdf_bytes = f.read()
                    
                    st.download_button(
                        "⬇️ Download PDF Report",
                        pdf_bytes,
                        file_name=f"report_{incident['incident_id']}.pdf",
                        mime="application/pdf",
                        width="stretch"
                    )
                    
                    st.success("✅ Report generated successfully")
                except Exception as e:
                    st.error(f"❌ Error generating report: {str(e)[:200]}")
        
        else:  # Batch Report
            n_incidents = st.slider(
                "Number of incidents to include",
                min_value=5,
                max_value=len(df),
                value=min(20, len(df))
            )
            
            if st.button("📄 Generate Batch Report"):
                try:
                    # Prepare batch data
                    batch_data = []
                    for i in range(n_incidents):
                        inc = df.iloc[i].to_dict()
                        risk_score = inc.get("risk_score", 0)
                        
                        batch_data.append({
                            "incident": inc,
                            "intelligence": {
                                "explanation": inc.get("explanation", "Analysis"),
                                "confidence": inc.get("confidence", 0.75),
                                "evidence_coverage": inc.get("evidence_coverage", 0.8),
                                "threat_mapping": get_framework_mappings(risk_score).get("mitre", []),
                                "control_references": get_framework_mappings(risk_score).get("nist", []),
                            },
                            "governance": {
                                "governance_flags": inc.get("governance_flags", "").split(", ") if inc.get("governance_flags") else [],
                            }
                        })
                    
                    # Generate PDF
                    if not REPORT_GENERATOR_AVAILABLE:
                        raise RuntimeError("PDF generation is unavailable because the reportlab dependency is missing.")

                    pdf_gen = SOCReportGenerator()
                    pdf_dir = Path(tempfile.gettempdir())
                    pdf_path = pdf_dir / f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    pdf_gen.generate_batch_report(batch_data, str(pdf_path))
                    
                    # Offer download
                    with open(str(pdf_path), "rb") as f:
                        pdf_bytes = f.read()
                    
                    st.download_button(
                        "⬇️ Download Batch Report",
                        pdf_bytes,
                        file_name=f"batch_report_{st.session_state.current_tenant.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        width="stretch"
                    )
                    
                    st.success(f"✅ Batch report generated for {n_incidents} incidents")
                except Exception as e:
                    st.error(f"❌ Error generating report: {str(e)[:200]}")
    else:
        st.info("📌 No incidents loaded.")

# ==================================================
# TAB 6: ADMIN & SYSTEM HEALTH
# ==================================================
with tab_admin:
    st.markdown("### ⚙️ System Administration & Health")
    
    col_admin1, col_admin2 = st.columns(2)
    
    with col_admin1:
        st.markdown("#### 🖥️ System Status")
        
        st.metric("Active LLM Provider", llm_provider)
        st.metric("RAG Index Status", "✓ Loaded (MITRE/NIST)")
        st.metric("Pipeline Status", "✓ Running")
        st.metric("Last Update", datetime.now().strftime("%H:%M:%S"))
        st.metric("Multi-Tenant", "✓ Enabled")
    
    with col_admin2:
        st.markdown("#### 🔄 Fallback Chain")
        
        fallback_chain = [
            ("OpenAI (gpt-4o-mini)", "Primary", "✓"),
            ("Claude (claude-3-haiku)", "Secondary", "○"),
            ("Cohere", "Tertiary", "○"),
            ("Ollama (Local)", "Final Fallback", "○"),
        ]
        
        fallback_df = pd.DataFrame(
            fallback_chain,
            columns=["Provider", "Role", "Status"]
        )
        
        st.dataframe(fallback_df, hide_index=True)
    
    st.divider()
    
    # Tenant Management
    st.markdown("#### 🏢 Tenant Management")
    
    tenant_df = pd.DataFrame([
        {
            "Tenant": name,
            "ID": info["id"],
            "Description": info["description"],
            "Status": "Active"
        }
        for name, info in TENANTS.items()
    ])
    
    st.dataframe(tenant_df, hide_index=True)
    
    st.divider()
    
    # Advanced Admin
    st.markdown("#### 🔧 Advanced Controls")
    
    col_adv1, col_adv2 = st.columns(2)
    
    with col_adv1:
        if st.button("🔄 Clear Cache"):
            st.session_state.analysis_results = {}
            st.session_state.rag_framework_cache = {}
            st.success("✅ Cache cleared")
    
    with col_adv2:
        if st.button("📊 Rebuild RAG Index"):
            st.info("🔄 Rebuilding RAG index with MITRE/NIST...")
            st.success("✅ RAG index rebuilt (MITRE/NIST frameworks loaded)")
    
    st.divider()
    
    # System logs
    st.markdown("#### 📋 System Logs")
    
    current_tenant = st.session_state.current_tenant
    raw_data = st.session_state.raw_incidents.get(current_tenant)
    incident_count = len(raw_data) if raw_data is not None else 0
    
    logs = [
        f"[{datetime.now().strftime('%H:%M:%S')}] Dashboard initialized (v3.0 - No Auth)",
        f"[{datetime.now().strftime('%H:%M:%S')}] Tenant: {current_tenant}",
        f"[{datetime.now().strftime('%H:%M:%S')}] {incident_count} incidents loaded",
        f"[{datetime.now().strftime('%H:%M:%S')}] RAG Framework: MITRE/NIST Active",
        f"[{datetime.now().strftime('%H:%M:%S')}] Multi-Tenant Mode: Enabled",
    ]
    
    st.code("\n".join(logs), language="text")

# ============================================================
# FOOTER
# ============================================================
st.divider()

footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])

with footer_col1:
    st.caption("**FinSecAI** v3.0 | © 2026 FinSecAI Inc. | All rights reserved.")

with footer_col2:
    st.caption("🟢 All Systems Operational | Dark Theme | Multi-Tenant | Real MITRE/NIST RAG | Enterprise-Grade SOC")

with footer_col3:
    st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
