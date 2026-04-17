"""
Performance Metrics Dashboard
Displays real-time performance metrics and analytics
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from pathlib import Path

# Setup page
st.set_page_config(
    page_title="FinSecAI Performance Metrics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

@st.cache_data(ttl=60)
def get_metrics_data():
    """Fetch metrics from Prometheus or local cache"""
    # This would normally query Prometheus
    # For now, return sample data
    
    now = datetime.now()
    timestamps = [now - timedelta(minutes=i) for i in range(60, 0, -1)]
    
    # Generate synthetic metrics data
    metrics = {
        "timestamp": timestamps,
        "throughput_rps": np.random.normal(100, 10, 60),
        "latency_p50_ms": np.random.normal(50, 5, 60),
        "latency_p95_ms": np.random.normal(150, 20, 60),
        "latency_p99_ms": np.random.normal(300, 50, 60),
        "error_rate_pct": np.random.normal(0.5, 0.2, 60),
        "cache_hit_rate_pct": np.random.normal(75, 5, 60),
        "active_connections": np.random.uniform(20, 100, 60),
        "cpu_usage_pct": np.random.normal(35, 10, 60),
        "memory_usage_pct": np.random.normal(50, 5, 60),
        "db_connections_active": np.random.randint(5, 20, 60),
    }
    
    return pd.DataFrame(metrics)


def create_metric_card(label: str, value: str, delta: str = None, color: str = "blue"):
    """Create a metric card"""
    col = st.columns([1])[0]
    
    if color == "green":
        icon = "✅"
    elif color == "red":
        icon = "❌"
    elif color == "yellow":
        icon = "⚠️"
    else:
        icon = "ℹ️"
    
    with col:
        st.metric(label, value, delta)


# ============================================================
# PAGE HEADER
# ============================================================

st.markdown("# 📊 Performance Metrics Dashboard")
st.markdown("Real-time monitoring of FinSecAI system performance")
st.divider()

# Refresh controls
col_refresh, col_period = st.columns(2)
with col_refresh:
    if st.button("🔄 Refresh Metrics", key="refresh_metrics"):
        st.cache_data.clear()
        st.rerun()

with col_period:
    time_period = st.selectbox(
        "Time Period",
        ["Last 5 minutes", "Last 1 hour", "Last 6 hours", "Last 24 hours", "Last 7 days"],
        index=1
    )

# ============================================================
# METRICS OVERVIEW (TOP KPIs)
# ============================================================

st.markdown("### 🎯 Key Performance Indicators")

metrics_df = get_metrics_data()
latest = metrics_df.iloc[-1]

col1, col2, col3, col4 = st.columns(4)

with col1:
    throughput = latest['throughput_rps']
    delta_throughput = f"+{(latest['throughput_rps'] - metrics_df.iloc[-10]['throughput_rps']):.1f} RPS" if len(metrics_df) > 10 else None
    st.metric(
        "Throughput",
        f"{throughput:.0f} RPS",
        delta_throughput,
        help="Requests per second"
    )

with col2:
    latency_p50 = latest['latency_p50_ms']
    delta_latency = f"{(latest['latency_p50_ms'] - metrics_df.iloc[-10]['latency_p50_ms']):+.1f} ms" if len(metrics_df) > 10 else None
    st.metric(
        "Latency (P50)",
        f"{latency_p50:.0f} ms",
        delta_latency,
        help="Median response time"
    )

with col3:
    error_rate = latest['error_rate_pct']
    delta_errors = f"{(latest['error_rate_pct'] - metrics_df.iloc[-10]['error_rate_pct']):+.2f}%" if len(metrics_df) > 10 else None
    st.metric(
        "Error Rate",
        f"{error_rate:.2f}%",
        delta_errors,
        help="Percentage of failed requests"
    )

with col4:
    cache_hit = latest['cache_hit_rate_pct']
    delta_cache = f"{(latest['cache_hit_rate_pct'] - metrics_df.iloc[-10]['cache_hit_rate_pct']):+.1f}%" if len(metrics_df) > 10 else None
    st.metric(
        "Cache Hit Rate",
        f"{cache_hit:.1f}%",
        delta_cache,
        help="Percentage of requests served from cache"
    )

st.divider()

# ============================================================
# RESPONSE TIME LATENCIES
# ============================================================

st.markdown("### ⏱️ Response Time Latencies (Percentiles)")

col_p50, col_p95, col_p99 = st.columns(3)

# Create latency chart
fig_latency = go.Figure()

fig_latency.add_trace(go.Scatter(
    x=metrics_df['timestamp'],
    y=metrics_df['latency_p50_ms'],
    name='P50 (Median)',
    line=dict(color='#22C55E', width=2),
    fill=None
))

fig_latency.add_trace(go.Scatter(
    x=metrics_df['timestamp'],
    y=metrics_df['latency_p95_ms'],
    name='P95',
    line=dict(color='#F59E0B', width=2),
    fill=None
))

fig_latency.add_trace(go.Scatter(
    x=metrics_df['timestamp'],
    y=metrics_df['latency_p99_ms'],
    name='P99 (Worst)',
    line=dict(color='#EF4444', width=2),
    fill='tonexty'
))

fig_latency.update_layout(
    title="Response Time Latencies Over Time",
    xaxis_title="Time",
    yaxis_title="Latency (ms)",
    height=300,
    hovermode="x unified",
    template="plotly_dark"
)

st.plotly_chart(fig_latency, use_container_width=True)

# Latency statistics
with col_p50:
    st.metric("P50 (Median)", f"{metrics_df['latency_p50_ms'].mean():.0f} ms")

with col_p95:
    st.metric("P95 (95th %ile)", f"{metrics_df['latency_p95_ms'].mean():.0f} ms")

with col_p99:
    st.metric("P99 (99th %ile)", f"{metrics_df['latency_p99_ms'].mean():.0f} ms")

st.divider()

# ============================================================
# THROUGHPUT & ERROR RATE
# ============================================================

st.markdown("### 📈 Throughput & Error Rate")

col_throughput, col_errors = st.columns(2)

with col_throughput:
    fig_throughput = px.line(
        metrics_df,
        x='timestamp',
        y='throughput_rps',
        title='Requests Per Second',
        labels={
            'timestamp': 'Time',
            'throughput_rps': 'RPS'
        }
    )
    fig_throughput.update_layout(height=300, hovermode="x unified")
    fig_throughput.update_traces(line_color='#60A5FA')
    st.plotly_chart(fig_throughput, use_container_width=True)

with col_errors:
    fig_errors = px.line(
        metrics_df,
        x='timestamp',
        y='error_rate_pct',
        title='Error Rate (%)',
        labels={
            'timestamp': 'Time',
            'error_rate_pct': 'Error %'
        }
    )
    fig_errors.update_layout(height=300, hovermode="x unified")
    fig_errors.update_traces(line_color='#EF4444')
    st.plotly_chart(fig_errors, use_container_width=True)

st.divider()

# ============================================================
# CACHING PERFORMANCE
# ============================================================

st.markdown("### 💾 Cache Hit Rate")

fig_cache = px.area(
    metrics_df,
    x='timestamp',
    y='cache_hit_rate_pct',
    title='Cache Hit Rate Over Time',
    labels={
        'timestamp': 'Time',
        'cache_hit_rate_pct': 'Hit Rate %'
    }
)
fig_cache.update_layout(height=300, hovermode="x unified")
fig_cache.update_traces(fillcolor='rgba(34, 197, 94, 0.2)', line_color='#22C55E')
st.plotly_chart(fig_cache, use_container_width=True)

# Cache statistics
cache_stats_col1, cache_stats_col2, cache_stats_col3 = st.columns(3)

with cache_stats_col1:
    avg_hit_rate = metrics_df['cache_hit_rate_pct'].mean()
    st.metric("Average Hit Rate", f"{avg_hit_rate:.1f}%")

with cache_stats_col2:
    min_hit_rate = metrics_df['cache_hit_rate_pct'].min()
    st.metric("Minimum Hit Rate", f"{min_hit_rate:.1f}%")

with cache_stats_col3:
    max_hit_rate = metrics_df['cache_hit_rate_pct'].max()
    st.metric("Maximum Hit Rate", f"{max_hit_rate:.1f}%")

st.divider()

# ============================================================
# INFRASTRUCTURE METRICS
# ============================================================

st.markdown("### 🖥️ Infrastructure Resources")

col_cpu, col_mem, col_db = st.columns(3)

with col_cpu:
    fig_cpu = px.line(
        metrics_df,
        x='timestamp',
        y='cpu_usage_pct',
        title='CPU Usage',
        labels={
            'timestamp': 'Time',
            'cpu_usage_pct': 'CPU %'
        }
    )
    fig_cpu.update_layout(height=300, hovermode="x unified")
    fig_cpu.update_traces(line_color='#F59E0B')
    fig_cpu.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="Warning")
    st.plotly_chart(fig_cpu, use_container_width=True)

with col_mem:
    fig_mem = px.line(
        metrics_df,
        x='timestamp',
        y='memory_usage_pct',
        title='Memory Usage',
        labels={
            'timestamp': 'Time',
            'memory_usage_pct': 'Memory %'
        }
    )
    fig_mem.update_layout(height=300, hovermode="x unified")
    fig_mem.update_traces(line_color='#60A5FA')
    fig_mem.add_hline(y=85, line_dash="dash", line_color="red", annotation_text="Warning")
    st.plotly_chart(fig_mem, use_container_width=True)

with col_db:
    fig_db = px.line(
        metrics_df,
        x='timestamp',
        y='db_connections_active',
        title='Active DB Connections',
        labels={
            'timestamp': 'Time',
            'db_connections_active': 'Connections'
        }
    )
    fig_db.update_layout(height=300, hovermode="x unified")
    fig_db.update_traces(line_color='#8B5CF6')
    st.plotly_chart(fig_db, use_container_width=True)

# Resource statistics
stat_col1, stat_col2, stat_col3 = st.columns(3)

with stat_col1:
    st.metric("Avg CPU", f"{metrics_df['cpu_usage_pct'].mean():.1f}%")

with stat_col2:
    st.metric("Avg Memory", f"{metrics_df['memory_usage_pct'].mean():.1f}%")

with stat_col3:
    st.metric("Avg DB Connections", f"{metrics_df['db_connections_active'].mean():.0f}")

st.divider()

# ============================================================
# RECENT ALERTS
# ============================================================

st.markdown("### 🚨 Recent Alerts")

alerts = [
    {
        "timestamp": datetime.now() - timedelta(minutes=5),
        "severity": "HIGH",
        "message": "Latency P99 exceeded 400ms threshold",
        "value": "425ms"
    },
    {
        "timestamp": datetime.now() - timedelta(minutes=15),
        "severity": "MEDIUM",
        "message": "Cache hit rate dropped below 70%",
        "value": "68%"
    },
    {
        "timestamp": datetime.now() - timedelta(minutes=30),
        "severity": "LOW",
        "message": "CPU usage above 75%",
        "value": "78%"
    },
]

alert_df = pd.DataFrame(alerts)

# Display alerts with styling
for idx, alert in enumerate(alerts):
    col_severity, col_msg, col_val = st.columns([1, 3, 1])
    
    with col_severity:
        if alert["severity"] == "HIGH":
            st.error(f"🔴 {alert['severity']}")
        elif alert["severity"] == "MEDIUM":
            st.warning(f"🟡 {alert['severity']}")
        else:
            st.info(f"🔵 {alert['severity']}")
    
    with col_msg:
        st.text(alert["message"])
    
    with col_val:
        st.text(alert["value"])

st.divider()

# ============================================================
# EXPORT & DOWNLOAD
# ============================================================

st.markdown("### 📥 Export Data")

col_export1, col_export2 = st.columns(2)

with col_export1:
    csv = metrics_df.to_csv(index=False)
    st.download_button(
        "⬇️ Download CSV",
        csv,
        f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "text/csv"
    )

with col_export2:
    json_str = metrics_df.to_json(orient='records', date_format='iso')
    st.download_button(
        "⬇️ Download JSON",
        json_str,
        f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        "application/json"
    )

st.divider()

# Footer
st.caption("📊 Performance metrics update every 60 seconds. Last updated: " + datetime.now().strftime("%H:%M:%S"))
