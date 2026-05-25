from fpdf import FPDF
from datetime import date


def generate_pdf(
    client_name: str,
    period: str,
    total_posts: int,
    avg_reach: float,
    avg_engagement: float,
    pending_approvals: int,
    platform_stats: list[dict],
    insights: list[str] | None = None,
) -> bytes:
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(234, 88, 12)
    pdf.cell(0, 12, "MuelaADS", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(0, 6, f"Performance Report - {client_name}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Period: {period} | Generated: {date.today().isoformat()}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(17, 24, 39)
    pdf.cell(0, 8, "Key Metrics", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(55, 65, 81)

    metrics = [
        ("Total Posts", str(total_posts)),
        ("Avg. Reach", f"{avg_reach:.0f}"),
        ("Avg. Engagement", f"{avg_engagement:.1f}%"),
        ("Pending Approvals", str(pending_approvals)),
    ]
    for label, value in metrics:
        pdf.cell(80, 7, label, border="B")
        pdf.cell(0, 7, value, border="B", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    if platform_stats:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(17, 24, 39)
        pdf.cell(0, 8, "By Platform", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(107, 114, 128)
        pdf.cell(50, 7, "Platform", border="B")
        pdf.cell(40, 7, "Posts", border="B")
        pdf.cell(40, 7, "Avg Reach", border="B")
        pdf.cell(0, 7, "Engagement", border="B", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(55, 65, 81)
        for stat in platform_stats:
            pdf.cell(50, 7, stat["platform"].title())
            pdf.cell(40, 7, str(stat["posts"]))
            pdf.cell(40, 7, f"{stat['reach']:.0f}")
            pdf.cell(0, 7, f"{stat['engagement']:.1f}%", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(8)

    if insights:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(17, 24, 39)
        pdf.cell(0, 8, "AI Insights", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(55, 65, 81)
        for i, insight in enumerate(insights, 1):
            pdf.multi_cell(0, 7, f"{i}. {insight}")

    return bytes(pdf.output())
