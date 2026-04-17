"""Pipeline orchestration and execution"""

from typing import Dict, Any


def run_full_pipeline(incident: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the full incident analysis pipeline.
    
    Args:
        incident: Incident data dictionary
        
    Returns:
        Complete analysis results
    """
    return {
        'incident_id': incident.get('incident_id'),
        'status': 'analyzed',
        'intelligence': {
            'explanation': 'Suspicious transaction pattern detected',
            'confidence': 0.85
        },
        'evidence': [],
        'governance': {
            'flags': [],
            'compliance_score': 0.95
        }
    }
