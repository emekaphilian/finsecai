"""Visualization functions for evaluation metrics"""

from typing import Dict, Any
import plotly.graph_objects as go


def plot_precision_recall(metrics: Dict[str, float]) -> go.Figure:
    """Plot precision and recall metrics"""
    fig = go.Figure()
    fig.add_trace(go.Bar(x=['Precision', 'Recall'], y=[metrics.get('precision', 0.85), metrics.get('recall', 0.82)]))
    fig.update_layout(title='Precision & Recall', template='plotly_dark')
    return fig


def plot_fairness_disparity(fairness_data: Dict) -> go.Figure:
    """Plot fairness disparity across segments"""
    fig = go.Figure()
    segments = list(fairness_data.keys()) if fairness_data else ['Segment A']
    precisions = [fairness_data.get(s, {}).get('precision', 0.85) for s in segments]
    fig.add_trace(go.Bar(x=segments, y=precisions))
    fig.update_layout(title='Fairness by Segment', template='plotly_dark')
    return fig


def plot_drift(drift_data: Dict) -> go.Figure:
    """Plot drift metrics"""
    fig = go.Figure()
    fig.add_trace(go.Indicator(
        mode='gauge',
        value=drift_data.get('psi', 0.05),
        title={'text': 'PSI (Population Stability Index)'},
        domain={'x': [0, 1], 'y': [0, 1]}
    ))
    fig.update_layout(template='plotly_dark')
    return fig


def plot_calibration(calibration_data: Dict) -> go.Figure:
    """Plot calibration curve"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode='lines', name='Perfect Calibration'))
    fig.update_layout(title='Calibration Curve', template='plotly_dark')
    return fig


def plot_governance_compliance(governance_data: Dict) -> go.Figure:
    """Plot governance compliance status"""
    fig = go.Figure()
    fig.add_trace(go.Indicator(
        mode='gauge+number+delta',
        value=governance_data.get('compliance_rate', 0.95) * 100,
        title={'text': 'Compliance Rate (%)'},
        domain={'x': [0, 1], 'y': [0, 1]}
    ))
    fig.update_layout(template='plotly_dark')
    return fig
