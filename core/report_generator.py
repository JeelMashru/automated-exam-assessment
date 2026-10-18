"""
Comprehensive Report and Marksheet Generation Engine.
Produces official university-grade PDF marksheets using ReportLab,
alongside CSV, Excel, and structured JSON exports.
"""

import os
import json
import io
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from config.settings import REPORTS_DIR


class ReportGenerator:
    """Generates official academic marksheets and exports."""

    @classmethod
    def generate_student_pdf_marksheet(
        cls,
        assessment_title: str,
        subject: str,
        student_id: str,
        question_text: str,
        max_marks: float,
        final_marks: float,
        ai_marks: float,
        review_status: str,
        criteria_breakdown: List[Dict[str, Any]],
        strengths: List[str],
        gaps: List[str],
        suggestions: List[str],
        bleu_score: Optional[float] = None,
        rouge_l_score: Optional[float] = None,
        human_feedback: Optional[str] = None,
        reviewed_by: Optional[str] = None,
    ) -> str:
        """
        Builds an official university PDF marksheet and saves it to REPORTS_DIR.
        Returns the absolute file path to the PDF.
        """
        filename = f"Marksheet_{student_id.replace(' ', '_')}_{int(final_marks)}m.pdf"
        output_path = REPORTS_DIR / filename

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()
        # Custom Typography
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0f172a"),
            alignment=1,  # Center
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#475569"),
            alignment=1,
        )
        heading2_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#1e3a8a"),
            spaceBefore=10,
            spaceAfter=4,
        )
        cell_style = ParagraphStyle(
            "CellNormal",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1e293b"),
        )
        cell_bold = ParagraphStyle(
            "CellBold",
            parent=cell_style,
            fontName="Helvetica-Bold",
        )

        story = []

        # 1. Header Banner
        story.append(Paragraph("OFFICIAL DESCRIPTIVE EXAMINATION MARKSHEET", title_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"Institution Assessment Engine | Course: {subject} | Title: {assessment_title}", subtitle_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1e3a8a"), spaceAfter=12))

        # 2. Candidate & Assessment Meta Table
        pct = round((final_marks / max_marks) * 100, 1) if max_marks > 0 else 0
        meta_data = [
            [
                Paragraph("<b>Candidate Identifier:</b>", cell_style),
                Paragraph(student_id, cell_bold),
                Paragraph("<b>Review Status:</b>", cell_style),
                Paragraph(f"<font color='#059669'><b>{review_status}</b></font>" if "Approv" in review_status else f"<font color='#d97706'><b>{review_status}</b></font>", cell_style),
            ],
            [
                Paragraph("<b>Total Awarded Marks:</b>", cell_style),
                Paragraph(f"<b>{final_marks:.2f} / {max_marks:.2f} ({pct}%)</b>", cell_bold),
                Paragraph("<b>Original AI Marks:</b>", cell_style),
                Paragraph(f"{ai_marks:.2f} / {max_marks:.2f}", cell_style),
            ],
            [
                Paragraph("<b>BLEU Lexical Overlap:</b>", cell_style),
                Paragraph(f"{bleu_score:.2f}%" if bleu_score is not None else "N/A", cell_style),
                Paragraph("<b>ROUGE-L Sequence F1:</b>", cell_style),
                Paragraph(f"{rouge_l_score:.2f}%" if rouge_l_score is not None else "N/A", cell_style),
            ]
        ]
        meta_table = Table(meta_data, colWidths=[140, 125, 130, 135])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 12))

        # 3. Question Text Box
        story.append(Paragraph("<b>Assessed Question:</b>", heading2_style))
        q_p = Paragraph(f"<i>{question_text}</i>", cell_style)
        q_table = Table([[q_p]], colWidths=[530])
        q_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(q_table)
        story.append(Spacer(1, 12))

        # 4. Rubric Breakdown Table
        story.append(Paragraph("<b>Rubric-Wise Evaluation Breakdown:</b>", heading2_style))
        crit_rows = [
            [
                Paragraph("<b>Criterion</b>", cell_bold),
                Paragraph("<b>Max</b>", cell_bold),
                Paragraph("<b>Awarded</b>", cell_bold),
                Paragraph("<b>Evidence & Justification</b>", cell_bold),
            ]
        ]
        for c in criteria_breakdown:
            c_name = c.get("criterion", "Criterion")
            c_max = f"{float(c.get('maximum_marks', 0)):.1f}"
            c_awarded = f"{float(c.get('awarded_marks', 0)):.1f}"
            just = f"<b>Justification:</b> {c.get('justification', '')}<br/><b>Evidence:</b> <i>{c.get('evidence', 'None')}</i>"
            crit_rows.append([
                Paragraph(c_name, cell_style),
                Paragraph(c_max, cell_style),
                Paragraph(c_awarded, cell_bold),
                Paragraph(just, cell_style),
            ])

        crit_table = Table(crit_rows, colWidths=[120, 40, 50, 320])
        crit_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (1, 0), (2, -1), "CENTER"),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(crit_table)
        story.append(Spacer(1, 12))

        # 5. Strengths & Gaps
        if strengths or gaps or suggestions:
            feed_data = []
            if strengths:
                feed_data.append([
                    Paragraph("<b>Identified Strengths:</b>", cell_bold),
                    Paragraph("<br/>".join([f"• {s}" for s in strengths]), cell_style)
                ])
            if gaps:
                feed_data.append([
                    Paragraph("<b>Conceptual Gaps:</b>", cell_bold),
                    Paragraph("<br/>".join([f"• {g}" for g in gaps]), cell_style)
                ])
            if suggestions:
                feed_data.append([
                    Paragraph("<b>Improvement Suggestions:</b>", cell_bold),
                    Paragraph("<br/>".join([f"• {s}" for s in suggestions]), cell_style)
                ])

            feed_table = Table(feed_data, colWidths=[140, 390])
            feed_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(Paragraph("<b>Qualitative Diagnostics:</b>", heading2_style))
            story.append(feed_table)
            story.append(Spacer(1, 12))

        # 6. Faculty Human Review Sign-Off
        sign_data = [
            [
                Paragraph("<b>Human Reviewer Remarks:</b>", cell_bold),
                Paragraph(human_feedback or "Approved without additional comments.", cell_style),
            ],
            [
                Paragraph("<b>Authorized Evaluator:</b>", cell_bold),
                Paragraph(reviewed_by or "Academic Faculty", cell_style),
            ]
        ]
        sign_table = Table(sign_data, colWidths=[140, 390])
        sign_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(Paragraph("<b>Audit & Verification Sign-Off:</b>", heading2_style))
        story.append(sign_table)
        story.append(Spacer(1, 12))

        # Footer Disclaimer
        disclaimer_text = (
            "Disclaimer: This evaluation was conducted with an LLM-as-a-Judge assessment architecture. "
            "Under university academic integrity guidelines, automated marks remain provisional until ratified "
            "by an authorized human academic examiner."
        )
        story.append(Paragraph(f"<i>{disclaimer_text}</i>", ParagraphStyle("Disc", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.HexColor("#64748b"))))

        doc.build(story)
        return str(output_path)

    @classmethod
    def export_batch_csv(cls, evaluations: List[Dict[str, Any]]) -> str:
        """Converts evaluation records to a standardized CSV format."""
        rows = []
        for ev in evaluations:
            rows.append({
                "Student Identifier": ev.get("student_identifier"),
                "Original Filename": ev.get("filename"),
                "Question": ev.get("question_number", 1),
                "Max Marks": ev.get("maximum_marks"),
                "AI Awarded Marks": ev.get("ai_awarded_marks"),
                "Final Awarded Marks": ev.get("final_awarded_marks"),
                "Percentage": round((ev.get("final_awarded_marks", 0) / max(1, ev.get("maximum_marks", 1))) * 100, 1),
                "BLEU Score (%)": ev.get("bleu_score"),
                "ROUGE-L Score (%)": ev.get("rouge_l_score"),
                "Review Status": ev.get("review_status"),
                "Evaluated Date": str(ev.get("evaluated_at"))[:19],
                "Human Reviewer": ev.get("reviewed_by", "Pending"),
                "Faculty Feedback": ev.get("human_feedback", ""),
            })
        df = pd.DataFrame(rows)
        return df.to_csv(index=False)

    @classmethod
    def export_batch_json(cls, evaluations: List[Dict[str, Any]]) -> str:
        """Serializes evaluations into formatted JSON."""
        # Convert non-serializable datetimes
        clean_evals = []
        for ev in evaluations:
            ev_copy = dict(ev)
            if "evaluated_at" in ev_copy and ev_copy["evaluated_at"]:
                ev_copy["evaluated_at"] = str(ev_copy["evaluated_at"])
            clean_evals.append(ev_copy)
        return json.dumps(clean_evals, indent=2)
