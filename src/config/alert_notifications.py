"""
Alert Notification Configuration
Handles routing of alerts to Slack, Email, and PagerDuty
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
import requests
from pathlib import Path


logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertNotificationManager:
    """Manages alert notifications across multiple channels"""
    
    def __init__(self):
        """Initialize notification channels from environment variables"""
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL", "")
        self.slack_channel = os.getenv("SLACK_CHANNEL", "#security-alerts")
        self.email_recipients = os.getenv("ALERT_EMAIL_RECIPIENTS", "").split(",")
        self.pagerduty_key = os.getenv("PAGERDUTY_SERVICE_KEY", "")
        self.enable_slack = bool(self.slack_webhook)
        self.enable_email = bool(self.email_recipients and self.email_recipients[0])
        self.enable_pagerduty = bool(self.pagerduty_key)
        
        # Default channel routing by severity
        self.channel_routing = {
            AlertSeverity.CRITICAL: ["slack", "pagerduty", "email"],
            AlertSeverity.HIGH: ["slack", "email"],
            AlertSeverity.MEDIUM: ["slack"],
            AlertSeverity.LOW: ["slack"],
            AlertSeverity.INFO: ["slack"],
        }
    
    def send_notification(
        self,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.INFO,
        details: Optional[Dict] = None,
        tags: Optional[Dict] = None
    ) -> bool:
        """
        Send alert notification to configured channels
        
        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity level
            details: Additional details dict
            tags: Custom tags for filtering
        
        Returns:
            bool: True if sent successfully
        """
        
        channels = self.channel_routing.get(severity, ["slack"])
        success = True
        
        # Send to each configured channel
        for channel in channels:
            try:
                if channel == "slack" and self.enable_slack:
                    self._send_slack_notification(title, message, severity, details, tags)
                elif channel == "email" and self.enable_email:
                    self._send_email_notification(title, message, severity, details)
                elif channel == "pagerduty" and self.enable_pagerduty:
                    self._send_pagerduty_notification(title, message, severity, details)
            except Exception as e:
                logger.error(f"Failed to send {channel} notification: {str(e)}")
                success = False
        
        return success
    
    def _send_slack_notification(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        details: Optional[Dict],
        tags: Optional[Dict]
    ):
        """Send Slack notification"""
        
        # Color coding by severity
        color_map = {
            AlertSeverity.CRITICAL: "FF0000",  # Red
            AlertSeverity.HIGH: "FF6600",      # Orange
            AlertSeverity.MEDIUM: "FFAA00",    # Yellow
            AlertSeverity.LOW: "0099FF",       # Blue
            AlertSeverity.INFO: "00AA00",      # Green
        }
        
        # Build Slack message
        slack_message = {
            "channel": self.slack_channel,
            "attachments": [
                {
                    "fallback": f"{severity.value.upper()}: {title}",
                    "color": color_map.get(severity, "808080"),
                    "title": f"🚨 {title}",
                    "text": message,
                    "fields": [],
                    "footer": "FinSecAI Alert",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        # Add details as fields if provided
        if details:
            for key, val in details.items():
                slack_message["attachments"][0]["fields"].append({
                    "title": key,
                    "value": str(val),
                    "short": True
                })
        
        # Add tags if provided
        if tags:
            tags_str = " ".join([f"{k}={v}" for k, v in tags.items()])
            slack_message["attachments"][0]["fields"].append({
                "title": "Tags",
                "value": tags_str,
                "short": False
            })
        
        # Send to Slack
        response = requests.post(self.slack_webhook, json=slack_message)
        response.raise_for_status()
        logger.info(f"Slack notification sent: {title}")
    
    def _send_email_notification(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        details: Optional[Dict]
    ):
        """Send Email notification (requires email service)"""
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Get SMTP config
            smtp_server = os.getenv("SMTP_SERVER", "localhost")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_user = os.getenv("SMTP_USER", "")
            smtp_password = os.getenv("SMTP_PASSWORD", "")
            from_addr = os.getenv("ALERT_FROM_EMAIL", "alerts@finsecai.io")
            
            # Build email
            msg = MIMEMultipart()
            msg["Subject"] = f"[{severity.value.upper()}] {title}"
            msg["From"] = from_addr
            msg["To"] = ", ".join(self.email_recipients)
            
            # Build HTML body
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: #FF0000;">{title}</h2>
                    <p><strong>Severity:</strong> {severity.value.upper()}</p>
                    <p><strong>Message:</strong></p>
                    <p>{message}</p>
            """
            
            if details:
                html_body += "<p><strong>Details:</strong></p><ul>"
                for key, val in details.items():
                    html_body += f"<li><strong>{key}:</strong> {val}</li>"
                html_body += "</ul>"
            
            html_body += f"""
                    <hr>
                    <small>FinSecAI Alert - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, "html"))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if smtp_user and smtp_password:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email notification sent to {self.email_recipients}: {title}")
        
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            raise
    
    def _send_pagerduty_notification(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        details: Optional[Dict]
    ):
        """Send PagerDuty incident"""
        
        # Map severity to PagerDuty urgency
        urgency_map = {
            AlertSeverity.CRITICAL: "critical",
            AlertSeverity.HIGH: "high",
            AlertSeverity.MEDIUM: "medium",
            AlertSeverity.LOW: "info",
            AlertSeverity.INFO: "info",
        }
        
        pagerduty_payload = {
            "routing_key": self.pagerduty_key,
            "event_action": "trigger",
            "payload": {
                "summary": f"{title}",
                "severity": urgency_map.get(severity, "info"),
                "source": "FinSecAI",
                "custom_details": details or {},
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        response = requests.post(
            "https://events.pagerduty.com/v2/enqueue",
            json=pagerduty_payload
        )
        response.raise_for_status()
        logger.info(f"PagerDuty incident created: {title}")


# Global notification manager instance
_notification_manager = None


def get_notification_manager() -> AlertNotificationManager:
    """Get or create global notification manager"""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = AlertNotificationManager()
    return _notification_manager


def send_alert(
    title: str,
    message: str,
    severity: AlertSeverity = AlertSeverity.INFO,
    details: Optional[Dict] = None,
    tags: Optional[Dict] = None
) -> bool:
    """
    Convenience function to send alerts
    
    Usage:
        send_alert(
            title="High Risk Incident Detected",
            message="Risk score exceeded threshold",
            severity=AlertSeverity.HIGH,
            details={"user_id": "USER-001", "risk_score": 0.85},
            tags={"org": "Acme Corp", "region": "US-East"}
        )
    """
    manager = get_notification_manager()
    return manager.send_notification(title, message, severity, details, tags)


# Example alert triggers for integration into monitoring
class AlertTriggers:
    """Predefined alert triggers for common events"""
    
    @staticmethod
    def high_risk_incident(risk_score: float, incident_id: str, user_id: str):
        """Alert on high-risk incident detection"""
        send_alert(
            title=f"🚨 High Risk Incident Detected",
            message=f"Incident {incident_id} for user {user_id} exceeded risk threshold",
            severity=AlertSeverity.HIGH,
            details={
                "incident_id": incident_id,
                "user_id": user_id,
                "risk_score": f"{risk_score:.2f}",
                "timestamp": datetime.now().isoformat()
            },
            tags={"alert_type": "risk_threshold", "category": "fraud"}
        )
    
    @staticmethod
    def pipeline_error(error_message: str, pipeline_stage: str):
        """Alert on pipeline processing error"""
        send_alert(
            title="❌ Pipeline Processing Error",
            message=f"Error in {pipeline_stage}: {error_message}",
            severity=AlertSeverity.CRITICAL,
            details={
                "pipeline_stage": pipeline_stage,
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            },
            tags={"alert_type": "system_error", "category": "infrastructure"}
        )
    
    @staticmethod
    def performance_degradation(metric: str, value: float, threshold: float):
        """Alert on performance metric degradation"""
        send_alert(
            title="⚠️ Performance Degradation",
            message=f"{metric} has degraded below acceptable threshold",
            severity=AlertSeverity.MEDIUM,
            details={
                "metric": metric,
                "current_value": f"{value:.2f}",
                "threshold": f"{threshold:.2f}",
                "timestamp": datetime.now().isoformat()
            },
            tags={"alert_type": "performance", "category": "monitoring"}
        )
    
    @staticmethod
    def security_event(event_type: str, user_id: str, details_dict: Dict):
        """Alert on security event"""
        send_alert(
            title=f"🔐 Security Event: {event_type}",
            message=f"Security event detected for user {user_id}",
            severity=AlertSeverity.HIGH,
            details={
                "event_type": event_type,
                "user_id": user_id,
                **details_dict,
                "timestamp": datetime.now().isoformat()
            },
            tags={"alert_type": "security", "category": "security_event"}
        )
