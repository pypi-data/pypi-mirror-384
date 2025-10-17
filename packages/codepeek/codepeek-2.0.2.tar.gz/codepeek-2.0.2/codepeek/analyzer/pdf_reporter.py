import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch


class PDFReporter:
    def generate_report(self, suggestions: dict, project_name: str):
        project_base = os.path.basename(str(project_name).rstrip("/\\"))
        file_name = os.path.join(os.getcwd(), f"{project_base}_report.pdf")

        doc = SimpleDocTemplate(
            file_name,
            pagesize=A4,
            title=f"CodePeek Report - {project_base}",
            leftMargin=0.6 * inch,
            rightMargin=0.6 * inch,
            topMargin=0.8 * inch,
            bottomMargin=0.8 * inch
        )

        styles = getSampleStyleSheet()
        story = []

        # ===== Styles =====
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Title'],
            textColor=colors.HexColor("#007ACC"),
            fontSize=22,
            leading=26,
            spaceAfter=10
        )

        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            textColor=colors.HexColor("#1A1A1A"),
            fontSize=14,
            spaceAfter=8,
            spaceBefore=14
        )

        normal_wrap = ParagraphStyle(
            'NormalWrap',
            parent=styles['Normal'],
            fontSize=9.5,
            leading=13,
            textColor=colors.black
        )

        # ===== Header =====
        story.append(Paragraph("CodePeek Analysis Report", title_style))
        story.append(Paragraph(f"<b>Project:</b> {project_base}", normal_wrap))
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now():%Y-%m-%d %H:%M:%S}", normal_wrap))
        story.append(Spacer(1, 0.25 * inch))

        # ===== Debug Info =====
        print("🧩 DEBUG: suggestions summary")
        if not suggestions:
            print("⚠️ No AI data received.")
        else:
            for k, v in suggestions.items():
                print(f"  • {k}: {len(v) if isinstance(v, list) else 'n/a'} items")

        # ===== Helper Function =====
        def add_section(title, items, fields):
            story.append(Paragraph(title, section_title_style))
            story.append(Spacer(1, 0.1 * inch))

            if not items:
                story.append(Paragraph("<i>No issues found.</i>", normal_wrap))
                story.append(Spacer(1, 0.25 * inch))
                return

            table_data = [["Field", "Detail"]]
            for item in items:
                for key in fields:
                    if key in item and item[key]:
                        table_data.append([
                            Paragraph(f"<b>{key.capitalize()}</b>", normal_wrap),
                            Paragraph(str(item[key]), normal_wrap)
                        ])
                table_data.append(["", ""])  # separator

            table = Table(table_data, colWidths=[1.5 * inch, 4.7 * inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#007ACC")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9.5),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [colors.whitesmoke, colors.Color(0.95, 0.95, 0.95)]),
            ]))

            story.append(table)
            story.append(Spacer(1, 0.35 * inch))

        # ===== Sections =====
        add_section("🔹 SOLID Principles", suggestions.get("solid_principles", []),
                    ["title", "file", "class", "explanation"])
        add_section("🔹 Design Patterns", suggestions.get("design_patterns", []),
                    ["title", "file", "class", "reason"])
        add_section("🔹 Security Issues", suggestions.get("security_issues", []),
                    ["title", "file", "line", "details"])
        add_section("🔹 Architecture Recommendations", suggestions.get("architecture", []),
                    ["title", "file", "suggestion", "benefit"])
        add_section("🔹 Final Recommendations", suggestions.get("final_recommendations", []),
                    ["title", "description"])

        # ===== Empty Check =====
        if not suggestions or all(len(v) == 0 for v in suggestions.values()):
            story.append(Paragraph("<b>⚠️ No AI suggestions were generated.</b>", normal_wrap))

        doc.build(story)
        print(f"📄 PDF report saved as {file_name}")
