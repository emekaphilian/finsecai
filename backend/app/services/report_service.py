"""Incident PDF report generation."""

from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.db.models import Incident

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "tmp" / "finsecai_reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

GOLD = colors.HexColor("#B8860B")
DARK = colors.HexColor("#0F172A")
GRAY = colors.HexColor("#475569")
RED = colors.HexColor("#B91C1C")
LIGHT_GRID = colors.HexColor("#E2E8F0")

_styles = getSampleStyleSheet()
_styles.add(ParagraphStyle("ReportTitle",
            parent=_styles["Title"], textColor=DARK, fontSize=20, spaceAfter=2))
_styles.add(ParagraphStyle(
    "Meta", parent=_styles["Normal"], textColor=GRAY, fontSize=9))
_styles.add(ParagraphStyle("SectionHeading",
            parent=_styles["Heading2"], textColor=DARK, fontSize=12, spaceBefore=14, spaceAfter=6))
_styles.add(ParagraphStyle(
    "Body", parent=_styles["Normal"], fontSize=10, leading=15))
_styles.add(ParagraphStyle(
    "FlagText", parent=_styles["Normal"], fontSize=10, textColor=RED))
_styles.add(ParagraphStyle(
    "Notice", parent=_styles["Normal"], fontSize=10, leading=14,
    textColor=DARK, backColor=colors.HexColor("#FEF3C7"), borderColor=GOLD,
    borderWidth=0.5, borderPadding=8,
))

MISSING = "Not available in supplied incident data"


class ReportGenerationError(ValueError):
    """A full report cannot exist without persisted investigation analysis."""


def _legacy_generate_incident_pdf(incident: Incident) -> str:
    """Retired: reports may not reconstruct conclusions from an incident."""
    raise ReportGenerationError(
        "Legacy score-derived reports are retired; run and persist investigation analysis first."
    )

    # Kept below temporarily for migration reference; deliberately unreachable.
    path = OUTPUT_DIR / f"report_{incident.id}.pdf"
    doc = SimpleDocTemplate(
        str(path), pagesize=letter, topMargin=0.6 * inch, bottomMargin=0.6 * inch, leftMargin=0.7 * inch, rightMargin=0.7 * inch,
    )

    mapping = {}

    story = [
        Paragraph("FinSecAI Incident Report", _styles["ReportTitle"]),
        Paragraph(
            f"Incident {incident.id[:8]} &nbsp;&middot;&nbsp; Generated {incident.created_at.strftime('%Y-%m-%d %H:%M')} UTC",
            _styles["Meta"],
        ),
        HRFlowable(width="100%", thickness=1.2, color=GOLD,
                   spaceBefore=8, spaceAfter=10),
    ]

    summary_data = [
        ["User", incident.user_id, "Risk score", f"{incident.risk_score:.2f}"],
        ["Amount", f"${incident.amount:,.2f}",
            "Anomaly score", f"{incident.anomaly_score:.2f}"],
        ["Type", incident.transaction_type, "Confidence",
            f"{incident.confidence:.2f}" if incident.confidence else "Not analyzed"],
        ["Device", incident.device_id or "—", "Evidence coverage",
            f"{incident.evidence_coverage:.2f}" if incident.evidence_coverage else "—"],
    ]
    summary_table = Table(summary_data, colWidths=[
                          1.1 * inch, 1.7 * inch, 1.4 * inch, 1.4 * inch])
    summary_table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("TEXTCOLOR", (0, 0), (0, -1), GRAY),
                ("TEXTCOLOR", (2, 0), (2, -1), GRAY),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, LIGHT_GRID),
            ]
        )
    )
    story.append(summary_table)

    story.append(Paragraph("Intelligence summary", _styles["SectionHeading"]))
    story.append(HRFlowable(width="100%", thickness=0.6,
                 color=LIGHT_GRID, spaceAfter=6))
    story.append(Paragraph(
        incident.explanation or "No analysis has been run for this incident yet.", _styles["Body"]))
    if incident.limitations:
        story.append(Spacer(1, 4))
        story.append(
            Paragraph(f"<i>Limitations: {incident.limitations}</i>", _styles["Meta"]))

    story.append(Paragraph("Governance flags", _styles["SectionHeading"]))
    story.append(HRFlowable(width="100%", thickness=0.6,
                 color=LIGHT_GRID, spaceAfter=6))
    story.append(Paragraph(incident.governance_flags or "None",
                 _styles["FlagText"] if incident.governance_flags else _styles["Body"]))

    story.append(Paragraph("Framework mapping", _styles["SectionHeading"]))
    story.append(HRFlowable(width="100%", thickness=0.6,
                 color=LIGHT_GRID, spaceAfter=6))
    story.append(Paragraph(mapping["rationale"], _styles["Meta"]))
    story.append(Spacer(1, 6))

    mitre_rows = [["MITRE ATT&CK techniques"]] + \
        [[f"{m['id']}  {m['name']}"] for m in mapping["mitre"]]
    nist_rows = [["NIST controls"]] + \
        [[f"{c['id']}  {c['name']}"] for c in mapping["nist"]]
    max_len = max(len(mitre_rows), len(nist_rows))
    while len(mitre_rows) < max_len:
        mitre_rows.append([""])
    while len(nist_rows) < max_len:
        nist_rows.append([""])
    combined = [[m[0], n[0]] for m, n in zip(mitre_rows, nist_rows)]

    mapping_table = Table(combined, colWidths=[3.1 * inch, 3.1 * inch])
    mapping_table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 0), (-1, 0), DARK),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GRID),
            ]
        )
    )
    story.append(mapping_table)

    # Evidence section: include retrieved evidence and provenance when available.
    analysis = incident.analysis_json or {}
    evidence_list = analysis.get("evidence") or []
    story.append(Spacer(1, 12))
    story.append(Paragraph("Evidence used", _styles["SectionHeading"]))
    story.append(HRFlowable(width="100%", thickness=0.6, color=LIGHT_GRID, spaceAfter=6))
    if evidence_list:
        for ev in evidence_list:
            ev_source = ev.get("source") or ev.get("metadata", {}).get("source") or "unknown"
            ev_summary = (ev.get("summary") or ev.get("text") or "(no summary)")
            ev_conf = ev.get("confidence")
            ev_conf_text = f"Confidence {ev_conf:.2f}" if isinstance(ev_conf, (int, float)) else ""
            ev_meta = ev.get("metadata") or {}
            ev_similarity = ev_meta.get("similarity_score") or ev.get("similarity")
            ev_similarity_text = f"Similarity {ev_similarity:.3f}" if ev_similarity is not None else ""
            story.append(Paragraph(f"Source: {ev_source} — {ev_conf_text} {ev_similarity_text}", _styles["Meta"]))
            story.append(Paragraph(ev_summary, _styles["Body"]))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No evidence was returned for this incident.", _styles["Body"]))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.6, color=LIGHT_GRID))
    story.append(
        Paragraph(
            "FinSecAI SOC Command Center &middot; Confidential &middot; Generated automatically, review before distribution",
            _styles["Meta"],
        )
    )

    doc.build(story)
    return str(path)


def _display(value: Any) -> str:
    return escape(str(value)) if value not in (None, "") else MISSING


def _paragraph(value: Any, style: str = "Body") -> Paragraph:
    return Paragraph(_display(value), _styles[style])


def _section(story: list, title: str) -> None:
    story.extend((
        Paragraph(title, _styles["SectionHeading"]),
        HRFlowable(width="100%", thickness=0.6, color=LIGHT_GRID, spaceAfter=6),
    ))


def _table(rows: list[list[Any]], widths: list[float], header: bool = True) -> Table:
    content = [[cell if isinstance(cell, Paragraph) else _paragraph(cell, "Meta") for cell in row] for row in rows]
    table = Table(content, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GRID),
    ]
    if header:
        style.extend((
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, 0), (-1, 0), DARK),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
        ))
    table.setStyle(TableStyle(style))
    return table


def _framework_rows(entries: list[dict[str, Any]], framework: str) -> list[list[Any]]:
    rows = [["Mapping", "Status", "Basis"]]
    for entry in entries:
        # The intelligence pipeline persists this provenance. A report must
        # never infer a confirmed mapping from a risk score or text itself.
        status = entry.get("status") or "candidate"
        basis = entry.get("basis") or "Persisted provenance unavailable"
        rows.append([
            f"{framework} {entry.get('id') or MISSING} — {entry.get('name') or MISSING}",
            "Evidence-backed" if status == "evidence_backed" else "Candidate",
            basis,
        ])
    return rows


def _first_value(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = payload.get(key)
        if value not in (None, ""):
            return value
    return None


def _fallback_actions(incident: Incident) -> list[str]:
    actions = [
        f"Review the transaction history for {incident.user_id}.",
        "Retrieve supporting evidence records where available.",
        "Confirm whether the observed anomaly represents legitimate activity.",
        "Escalate for enhanced review if the anomalies remain unexplained.",
    ]
    if incident.device_id:
        actions.insert(1, f"Validate the device context involving {incident.device_id}.")
    if incident.governance_flags and "geo" in incident.governance_flags.lower():
        actions.insert(2, "Review the geographic context associated with the transaction.")
    return actions


def _fallback_reasoning(incident: Incident, analysis: dict[str, Any], evidence: list[dict[str, Any]]) -> list[str]:
    reasoning = list(analysis.get("risk_rationale") or [])
    if reasoning:
        return reasoning

    result = [
        f"The transaction received a risk score of {incident.risk_score:.2f}, placing it in the {analysis.get('incident_classification') or 'elevated-risk'} tier.",
        f"The anomaly engine recorded an anomaly score of {incident.anomaly_score:.2f}.",
    ]
    if incident.device_id:
        result.append(
            f"Device context was recorded as {incident.device_id}; an underlying comparison record is not available in the supplied incident data."
        )
    if incident.governance_flags:
        result.append(f"Governance signals recorded for review: {incident.governance_flags}.")
    if not evidence:
        result.append(
            "No underlying evidence records were returned, so this assessment is based primarily on structured transaction and model signals."
        )
    return result


def generate_incident_pdf(incident: Incident) -> str:
    """Render persisted investigation data without recreating conclusions."""
    analysis = incident.analysis_json or {}
    if not analysis:
        raise ReportGenerationError(
            "Full investigation reports require persisted analysis_json. Run investigation analysis first."
        )

    path = OUTPUT_DIR / f"report_{incident.id}.pdf"
    doc = SimpleDocTemplate(
        str(path), pagesize=letter, topMargin=0.6 * inch, bottomMargin=0.6 * inch,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
    )
    assessment = analysis.get("risk_assessment") or {}
    governance = analysis.get("governance") or {}
    evidence = analysis.get("evidence") or []
    recommendations = analysis.get("recommendations") or analysis.get("next_actions") or []
    structured_evidence = analysis.get("structured_evidence") or []
    classification = analysis.get("incident_classification") or MISSING
    coverage = incident.evidence_coverage
    payload = incident.raw_payload or {}

    story = [
        Paragraph("FinSecAI Investigation Report", _styles["ReportTitle"]),
        Paragraph(
            f"Incident {escape(incident.id[:8])} &middot;&nbsp; Generated {incident.created_at.strftime('%Y-%m-%d %H:%M')} UTC",
            _styles["Meta"],
        ),
        HRFlowable(width="100%", thickness=1.2, color=GOLD, spaceBefore=8, spaceAfter=10),
    ]

    _section(story, "1. Executive Summary")
    story.append(_table([
        ["Incident", incident.id, "Investigation status", analysis.get("intelligence_status") or "ANALYSIS_COMPLETED"],
        ["Classification", classification, "Risk score", f"{incident.risk_score:.2f}"],
        ["Confidence", f"{incident.confidence:.2f}" if incident.confidence is not None else None, "Evidence coverage", f"{coverage:.0%}" if coverage is not None else None],
        ["Transaction amount", f"${incident.amount:,.2f}", "Transaction type", incident.transaction_type],
        ["User", incident.user_id, "Device", incident.device_id],
        ["Anomaly score", f"{incident.anomaly_score:.2f}", "Recommended disposition", governance.get("recommended_disposition")],
    ], [1.15 * inch, 2.0 * inch, 1.45 * inch, 1.6 * inch], header=False))
    story.append(Spacer(1, 8))
    story.append(_paragraph(analysis.get("executive_summary") or incident.explanation))

    _section(story, "2. Risk Assessment")
    contributions = assessment.get("score_contributions") or {}
    if contributions:
        story.append(_table([["Persisted contribution", "Value"]] + [
            [key.replace("_", " ").title(), f"{value:.2f}" if isinstance(value, (int, float)) else value]
            for key, value in contributions.items()
        ], [3.8 * inch, 2.4 * inch]))
    else:
        story.append(_paragraph("No persisted risk contributions are available."))

    risk_factors = assessment.get("positive_factors") or []
    if risk_factors:
        story.append(Spacer(1, 6))
        story.append(_paragraph("Risk indicators", "Meta"))
        story.append(_table([["Indicator", "Finding"]] + [
            ["Structured risk signal", factor] for factor in risk_factors
        ], [2.0 * inch, 4.2 * inch]))

    _section(story, "3. Transaction Intelligence")
    transaction_id = _first_value(payload, "transaction_id", "id")
    source_account = _first_value(payload, "source_account", "source_account_id", "from_account")
    destination_account = _first_value(payload, "destination_account", "destination_account_id", "to_account")
    origin_country = _first_value(payload, "origin_country", "source_country", "country")
    destination_country = _first_value(payload, "destination_country", "target_country")
    ip_location = _first_value(payload, "ip", "ip_address", "location", "geo")
    channel = _first_value(payload, "channel", "transaction_channel")
    previous_transaction = _first_value(payload, "previous_transaction", "previous_transaction_id")
    account_age = _first_value(payload, "account_age", "account_age_days")
    story.append(_table([
        ["Attribute", "Value", "Attribute", "Value"],
        ["Transaction ID", transaction_id, "User", incident.user_id],
        ["Timestamp", incident.created_at.isoformat() if incident.created_at else None, "Transaction type", incident.transaction_type],
        ["Amount", f"${incident.amount:,.2f}", "Currency", payload.get("currency")],
        ["Source account", source_account, "Destination account", destination_account],
        ["Channel", channel, "Origin country", origin_country],
        ["Destination country", destination_country, "IP / location", ip_location],
        ["Device", incident.device_id, "Previous transaction", previous_transaction],
        ["Transaction velocity", _first_value(payload, "velocity", "velocity_1h"), "Account age", account_age],
        ["Historical pattern", _first_value(payload, "historical_pattern", "transaction_pattern"), "Data status", "Structured incident fields only"],
    ], [1.2 * inch, 1.9 * inch, 1.35 * inch, 1.75 * inch]))

    _section(story, "4. Anomaly Findings")
    findings = analysis.get("findings") or []
    if findings:
        story.append(_table([["Finding", "Severity", "Observed signal", "Rationale", "Evidence status", "Confidence"]] + [
            [
                item.get("finding"), item.get("severity"), item.get("observed_signal"),
                item.get("rationale"),
                "Supported" if item.get("supporting_evidence") else "Not available",
                f"{item.get('confidence'):.2f}" if isinstance(item.get("confidence"), (int, float)) else None,
            ]
            for item in findings
        ], [1.15 * inch, 0.7 * inch, 1.4 * inch, 1.8 * inch, 0.85 * inch, 0.5 * inch]))
    else:
        story.append(_paragraph("No persisted anomaly findings are available."))

    _section(story, "5. Evidence")
    if structured_evidence:
        story.append(_paragraph("Structured signals", "Meta"))
        story.append(_table([["Source", "Relevance", "Confidence", "Status"]] + [
            [
                item.get("source"), item.get("summary"),
                f"{item.get('confidence'):.2f}" if isinstance(item.get("confidence"), (int, float)) else None,
                (item.get("metadata") or {}).get("evidence_status"),
            ] for item in structured_evidence
        ], [1.45 * inch, 2.85 * inch, 0.9 * inch, 1.0 * inch]))
        story.append(Spacer(1, 6))
    if evidence:
        story.append(_paragraph("Evidence retrieved", "Meta"))
        story.append(_table([["Source", "Summary", "Confidence"]] + [
            [item.get("source"), item.get("summary") or item.get("text"), f"{item.get('confidence'):.2f}" if isinstance(item.get("confidence"), (int, float)) else None]
            for item in evidence
        ], [1.45 * inch, 3.85 * inch, 0.9 * inch]))
    else:
        story.append(_paragraph("Evidence gaps", "Meta"))
        story.append(Paragraph(
            "No supporting evidence documents or evidence chunks were retrieved for this incident. Framework mappings are candidate associations, not evidence-backed findings.",
            _styles["Notice"],
        ))

    _section(story, "6. Investigation Reasoning")
    reasoning = analysis.get("risk_rationale") or []
    if reasoning:
        for number, item in enumerate(reasoning, 1):
            story.append(_paragraph(f"Finding {number} - {item}"))
    else:
        story.append(_paragraph(analysis.get("attack_narrative")))

    _section(story, "7. Framework Mapping")
    framework_groups = (
        ("MITRE ATT&CK", analysis.get("mitre") or []),
        ("NIST", analysis.get("nist") or []),
    )
    evidence_backed_groups = [
        (framework, [
            item for item in entries
            if item.get("status") == "evidence_backed" and item.get("supporting_evidence")
        ])
        for framework, entries in framework_groups
    ]
    if not any(entries for _, entries in evidence_backed_groups):
        story.append(Paragraph(
            "No evidence-backed MITRE ATT&CK or NIST mappings are available for this incident. "
            "Candidate mappings were not promoted because supporting evidence was unavailable.",
            _styles["Notice"],
        ))
        story.append(Spacer(1, 6))
    for framework, entries in evidence_backed_groups:
        story.append(_paragraph(framework))
        story.append(_table(_framework_rows(entries, framework), [2.7 * inch, 1.15 * inch, 2.35 * inch]) if entries else _paragraph("No evidence-backed mappings are available."))
        story.append(Spacer(1, 6))

    _section(story, "8. Governance")
    flags = [flag.strip() for flag in (incident.governance_flags or "").split(",") if flag.strip()]
    story.append(_table([
        ["Governance flags", "\n".join(f"- {flag}" for flag in flags) if flags else "None"],
        ["Evidence sufficiency", governance.get("evidence_sufficiency")],
        ["Human review required", "Yes" if governance.get("human_review_required") else "Not established"],
        ["Automated decision", governance.get("automated_decision") or "NONE"],
        ["Limitations", incident.limitations],
    ], [1.7 * inch, 4.5 * inch], header=False))

    _section(story, "9. Recommended Actions")
    if recommendations:
        for number, action in enumerate(recommendations, 1):
            story.append(_paragraph(f"{number}. {action}"))
    else:
        story.append(Paragraph(
            "No persisted recommendations are available. Investigation analysis should be completed before relying on this report for operational decision-making.",
            _styles["Notice"],
        ))

    _section(story, "10. Disposition")
    story.append(_table([
        ["Risk", classification], ["Evidence", governance.get("evidence_sufficiency")],
        ["Confidence", f"{incident.confidence:.2f}" if incident.confidence is not None else None],
        ["Recommended action", governance.get("recommended_disposition")],
        ["Automated decision", governance.get("automated_decision") or "NONE"],
    ], [2.0 * inch, 4.2 * inch], header=False))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Recommendations are advisory and do not constitute an automated determination of fraud or criminal activity.",
        _styles["Notice"],
    ))
    story.extend((Spacer(1, 20), HRFlowable(width="100%", thickness=0.6, color=LIGHT_GRID), Paragraph("FinSecAI SOC Command Center &middot; Confidential &middot; Generated automatically, review before distribution", _styles["Meta"])))
    doc.build(story)
    return str(path)
