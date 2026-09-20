from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

import os


def generate_report(
    filename,
    username,
    score,
    total,
    percentage,
    integrity_score,
    risk,
    monitor,
    review
):

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph("<b>ExamGuard Report</b>", styles["Title"])
    )

    elements.append(
        Paragraph(f"Candidate : {username}", styles["Normal"])
    )

    elements.append(
        Paragraph(f"Score : {score}/{total}", styles["Normal"])
    )

    elements.append(
        Paragraph(f"Percentage : {percentage}%", styles["Normal"])
    )

    elements.append(
        Paragraph(f"Integrity Score : {integrity_score}%", styles["Normal"])
    )

    elements.append(
        Paragraph(f"Risk Level : {risk}", styles["Normal"])
    )

    elements.append(
        Paragraph("<br/>", styles["Normal"])
    )

    elements.append(
        Paragraph("<b>Monitoring Summary</b>", styles["Heading2"])
    )

    if isinstance(monitor, dict):
        f_missing = monitor.get("face_missing_count", 0)
        m_faces = monitor.get("multiple_face_count", 0)
        t_switches = monitor.get("tab_switches", 0)
        f_losses = monitor.get("focus_losses", 0)
    else:
        f_missing = getattr(monitor, "face_missing_count", 0)
        m_faces = getattr(monitor, "multiple_face_count", 0)
        t_switches = getattr(monitor, "tab_switch_count", 0)
        f_losses = getattr(monitor, "focus_loss_count", 0)

    summary = [
        ["Face Missing", f_missing],
        ["Multiple Faces", m_faces],
        ["Tab Switch", t_switches],
        ["Focus Loss", f_losses]
    ]

    table = Table(summary)

    table.setStyle(TableStyle([

        ("GRID",(0,0),(-1,-1),1,colors.black),

        ("BACKGROUND",(0,0),(-1,-1),colors.beige),

        ("FONTNAME",(0,0),(-1,-1),"Helvetica")

    ]))

    elements.append(table)

    elements.append(
        Paragraph("<br/>", styles["Normal"])
    )

    elements.append(
        Paragraph("<b>Question Review</b>", styles["Heading2"])
    )

    data = [

        ["Question","Student","Correct","Status"]

    ]

    for q in review:

        data.append([

            q["question"],

            q["student"],

            q["correct"],

            "Correct" if q["status"] else "Wrong"

        ])

    review_table = Table(data)

    review_table.setStyle(TableStyle([

        ("GRID",(0,0),(-1,-1),1,colors.black),

        ("BACKGROUND",(0,0),(-1,0),colors.lightblue),

        ("FONTNAME",(0,0),(-1,-1),"Helvetica"),

        ("FONTSIZE",(0,0),(-1,-1),9)

    ]))

    elements.append(review_table)

    doc.build(elements)