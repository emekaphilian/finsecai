"""PDF Report Generation"""

from typing import Dict, Any, List
from datetime import datetime
import io


class SOCReportGenerator:
    """Generate SOC incident reports in PDF format"""
    
    def __init__(self):
        self.title = "FinSecAI SOC Report"
    
    def generate_incident_report(self, incident: Dict[str, Any], intelligence: Dict = None, evidence: List = None) -> bytes:
        """
        Generate a PDF report for a single incident.
        
        Args:
            incident: Incident data dictionary
            intelligence: Intelligence analysis results
            evidence: Evidence retrieval results
            
        Returns:
            PDF file as bytes
        """
        # Create a simple text-based report for now
        report_text = f"""
FinSecAI SOC Incident Report
Generated: {datetime.now().isoformat()}

Incident ID: {incident.get('incident_id', 'N/A')}
User ID: {incident.get('user_id', 'N/A')}
Risk Score: {incident.get('risk_score', 0.0):.2f}
Amount: ${incident.get('amount', 0.0):.2f}

Intelligence Analysis:
{intelligence.get('explanation', 'N/A') if intelligence else 'N/A'}

Evidence:
{str(evidence) if evidence else 'No evidence retrieved'}
"""
        return report_text.encode('utf-8')
    
    def generate_batch_report(self, incidents: List[Dict], intelligence_results: List[Dict] = None) -> bytes:
        """Generate a batch report for multiple incidents"""
        report_text = f"""
FinSecAI SOC Batch Report
Generated: {datetime.now().isoformat()}
Total Incidents: {len(incidents)}

---- Incident Summary ----
"""
        for incident in incidents:
            report_text += f"\n- {incident.get('incident_id', 'N/A')}: Risk {incident.get('risk_score', 0.0):.2f}"
        
        return report_text.encode('utf-8')
