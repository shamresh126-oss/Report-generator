"""PDF Report Generation module using ReportLab Platypus.

Constructs an executive-grade business report PDF with headers, KPI metric cards,
data-quality summary, embedded high-resolution charts, financial breakdown tables,
and automated strategic insights.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from report_generator.data_processor import ProcessedData
from report_generator.exceptions import PDFGenerationError
from report_generator.logger import get_logger

logger = get_logger("pdf_report")


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for precise running headers, footers, and page numbers."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[Dict] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int) -> None:
        """Draw running header and footer with total page count."""
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        page_w, page_h = letter

        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, page_h - 26, "Apex Enterprise Solutions Inc. — Executive Business Performance Report")
            self.drawRightString(page_w - 36, page_h - 26, datetime.now().strftime("%B %d, %Y"))
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(36, page_h - 30, page_w - 36, page_h - 30)

        # Running Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(36, 36, page_w - 36, 36)

        self.drawString(36, 24, "CONFIDENTIAL & PROPRIETARY — FOR INTERNAL USE ONLY")
        footer_text = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(page_w - 36, 24, footer_text)

        self.restoreState()


class PDFReportGenerator:
    """Generates structured executive PDF reports from processed data and charts."""

    def __init__(
        self,
        output_dir: Union[str, Path] = "reports",
        company_name: str = "Apex Enterprise Solutions Inc.",
        report_title: str = "AUTOMATED BUSINESS PERFORMANCE REPORT",
        currency_symbol: str = "₹",
    ) -> None:
        """Initialize PDFReportGenerator.

        Args:
            output_dir: Output directory for report PDFs.
            company_name: Corporate organization name.
            report_title: Main document title.
            currency_symbol: Currency symbol for tabular and KPI values.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.company_name = company_name
        self.report_title = report_title
        self.currency_symbol = currency_symbol

        self.styles = getSampleStyleSheet()
        self._init_custom_styles()

    def _init_custom_styles(self) -> None:
        """Define executive document typography and paragraph styles."""
        self.styles.add(
            ParagraphStyle(
                name="ReportDocTitle",
                fontName="Helvetica-Bold",
                fontSize=20,
                leading=24,
                textColor=colors.HexColor("#0F172A"),
                spaceAfter=4,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="CompanyHeader",
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=11,
                textColor=colors.HexColor("#2563EB"),
                textTransform="uppercase",
                spaceAfter=4,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="MetaSubtitle",
                fontName="Helvetica",
                fontSize=9,
                leading=12,
                textColor=colors.HexColor("#64748B"),
                spaceAfter=10,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="SectionHeading",
                fontName="Helvetica-Bold",
                fontSize=13,
                leading=16,
                textColor=colors.HexColor("#1E3A8A"),
                spaceBefore=12,
                spaceAfter=6,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="ExecutiveBody",
                fontName="Helvetica",
                fontSize=9.5,
                leading=14,
                textColor=colors.HexColor("#334155"),
                spaceAfter=10,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="InsightBullet",
                fontName="Helvetica",
                fontSize=9,
                leading=13.5,
                textColor=colors.HexColor("#1E293B"),
                leftIndent=12,
                firstLineIndent=-12,
                spaceAfter=5,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="TableHeader",
                fontName="Helvetica-Bold",
                fontSize=8.5,
                leading=10.5,
                textColor=colors.white,
                alignment=1,  # Center
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="TableCell",
                fontName="Helvetica",
                fontSize=8.5,
                leading=11,
                textColor=colors.HexColor("#1E293B"),
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="TableCellRight",
                fontName="Helvetica",
                fontSize=8.5,
                leading=11,
                textColor=colors.HexColor("#1E293B"),
                alignment=2,  # Right
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="TableCellCenter",
                fontName="Helvetica",
                fontSize=8.5,
                leading=11,
                textColor=colors.HexColor("#1E293B"),
                alignment=1,  # Center
            )
        )

    def generate(
        self,
        data: ProcessedData,
        chart_paths: Dict[str, Path],
        output_filename: Optional[str] = None,
        data_source: str = "CSV Data Source",
    ) -> Path:
        """Build and save the complete multi-page PDF performance report.

        Args:
            data: ProcessedData holding analytics and tables.
            chart_paths: Mapping of chart IDs to generated PNG files.
            output_filename: Optional custom filename.
            data_source: Description of data origin (e.g. 'API' or 'CSV').

        Returns:
            Path: Resolved path to the generated PDF.

        Raises:
            PDFGenerationError: If ReportLab fails during generation.
        """
        if output_filename:
            pdf_path = Path(output_filename)
            if not pdf_path.is_absolute():
                pdf_path = self.output_dir / pdf_path.name
        else:
            date_stamp = datetime.now().strftime("%Y-%m-%d")
            pdf_path = self.output_dir / f"business_report_{date_stamp}.pdf"

        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Initiating PDF document build: %s", pdf_path)

        try:
            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=letter,
                leftMargin=36,
                rightMargin=36,
                topMargin=38,
                bottomMargin=42,
            )

            story = []

            # 1. Header & Title Block
            story.append(Paragraph(self.company_name, self.styles["CompanyHeader"]))
            story.append(Paragraph(self.report_title, self.styles["ReportDocTitle"]))
            gen_date = datetime.now().strftime("%d %B %Y at %H:%M:%S")
            subtitle = f"<b>Generated:</b> {gen_date} &nbsp;|&nbsp; <b>Data Source:</b> {data_source} &nbsp;|&nbsp; <b>Status:</b> Validated & Audited"
            story.append(Paragraph(subtitle, self.styles["MetaSubtitle"]))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceAfter=10))

            # 2. Executive Summary
            story.append(Paragraph("Executive Summary", self.styles["SectionHeading"]))
            summary_text = (
                f"This automated performance report compiles and evaluates key enterprise sales metrics across all operational units. "
                f"During this period, a total of <b>{data.total_records:,} verified transactions</b> were recorded, generating an aggregate "
                f"gross revenue of <b>{self.currency_symbol}{data.total_revenue:,.2f}</b> with an average transaction value of "
                f"<b>{self.currency_symbol}{data.average_revenue:,.2f}</b>. The leading performance driver was <b>{data.top_category}</b>, "
                f"contributing <b>{self.currency_symbol}{data.top_category_revenue:,.2f}</b> to overall revenue."
            )
            story.append(Paragraph(summary_text, self.styles["ExecutiveBody"]))

            # 3. Key Metrics KPI Grid
            story.append(Paragraph("Key Performance Metrics", self.styles["SectionHeading"]))
            kpi_table = self._build_kpi_table(data)
            story.append(kpi_table)
            story.append(Spacer(1, 10))

            # 4. Data Quality Audit
            story.append(Paragraph("Data Integrity & Quality Audit", self.styles["SectionHeading"]))
            quality_table = self._build_quality_table(data.quality_metrics)
            story.append(quality_table)
            story.append(Spacer(1, 10))

            # 5. Charts Section - First Chart Pair
            story.append(Paragraph("Visual Analytics & Market Breakdown", self.styles["SectionHeading"]))

            cat_chart = chart_paths.get("category_revenue")
            top_chart = chart_paths.get("top_categories")
            if cat_chart and cat_chart.exists() and top_chart and top_chart.exists():
                chart_row = [
                    [
                        Image(str(cat_chart), width=3.65 * inch, height=2.25 * inch),
                        Image(str(top_chart), width=3.65 * inch, height=2.25 * inch),
                    ]
                ]
                chart_table = Table(chart_row, colWidths=[3.7 * inch, 3.7 * inch])
                chart_table.setStyle(
                    TableStyle([
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ])
                )
                story.append(chart_table)
                story.append(Spacer(1, 8))

            # Page Break for clean multi-page layout
            story.append(PageBreak())

            # Page 2: Revenue Trend Chart
            trend_chart = chart_paths.get("revenue_trend")
            if trend_chart and trend_chart.exists():
                story.append(Paragraph("Revenue Trajectory & Chronological Timeline", self.styles["SectionHeading"]))
                story.append(Image(str(trend_chart), width=7.4 * inch, height=2.8 * inch))
                story.append(Spacer(1, 12))

            # 6. Comprehensive Category Performance Breakdown Table
            story.append(Paragraph("Category Performance & Contribution Breakdown", self.styles["SectionHeading"]))
            summary_table = self._build_category_table(data)
            story.append(summary_table)
            story.append(Spacer(1, 14))

            # 7. Strategic Business Insights & Recommendations
            story.append(Paragraph("Strategic Insights & Automated Recommendations", self.styles["SectionHeading"]))
            insights = self._generate_business_insights(data)
            for bullet in insights:
                story.append(Paragraph(f"• &nbsp; {bullet}", self.styles["InsightBullet"]))

            story.append(Spacer(1, 16))
            story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CBD5E1"), spaceAfter=8))
            signoff = (
                f"<i>Automated report certified by Apex Enterprise Automation Engine v1.0.0. "
                f"Generated for stakeholder review on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.</i>"
            )
            story.append(Paragraph(signoff, self.styles["MetaSubtitle"]))

            # Build the document using the NumberedCanvas
            doc.build(story, canvasmaker=NumberedCanvas)
            logger.info("PDF document successfully generated: %s", pdf_path)
            return pdf_path

        except Exception as exc:
            msg = f"ERROR: PDF report could not be generated: {exc}"
            logger.error(msg, exc_info=True)
            raise PDFGenerationError(msg, original_exception=exc) from exc

    def _build_kpi_table(self, data: ProcessedData) -> Table:
        """Create styled KPI card grid."""
        card_bg = colors.HexColor("#F8FAFC")
        border_col = colors.HexColor("#E2E8F0")

        # 4 Key Metrics
        kpi_data = [
            [
                Paragraph("<b>TOTAL RECORDS</b>", self.styles["TableCellCenter"]),
                Paragraph("<b>TOTAL REVENUE</b>", self.styles["TableCellCenter"]),
                Paragraph("<b>AVERAGE REVENUE</b>", self.styles["TableCellCenter"]),
                Paragraph("<b>TOP CATEGORY</b>", self.styles["TableCellCenter"]),
            ],
            [
                Paragraph(f"<font size=13 color='#1E3A8A'><b>{data.total_records:,}</b></font>", self.styles["TableCellCenter"]),
                Paragraph(f"<font size=13 color='#0D9488'><b>{self.currency_symbol}{data.total_revenue:,.0f}</b></font>", self.styles["TableCellCenter"]),
                Paragraph(f"<font size=13 color='#2563EB'><b>{self.currency_symbol}{data.average_revenue:,.2f}</b></font>", self.styles["TableCellCenter"]),
                Paragraph(f"<font size=12 color='#D97706'><b>{data.top_category}</b></font>", self.styles["TableCellCenter"]),
            ],
        ]

        table = Table(kpi_data, colWidths=[1.85 * inch] * 4)
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), card_bg),
                ("BOX", (0, 0), (-1, -1), 1.0, border_col),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, border_col),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )
        return table

    def _build_quality_table(self, metrics: Dict[str, int]) -> Table:
        """Create a summary table of data quality and cleaning results."""
        header_bg = colors.HexColor("#334155")
        row_bg = colors.HexColor("#F8FAFC")

        headers = [
            Paragraph("<b>Ingested Records</b>", self.styles["TableHeader"]),
            Paragraph("<b>Duplicates Removed</b>", self.styles["TableHeader"]),
            Paragraph("<b>Missing Values Imputed</b>", self.styles["TableHeader"]),
            Paragraph("<b>Dropped Invalid</b>", self.styles["TableHeader"]),
            Paragraph("<b>Clean Records Analyzed</b>", self.styles["TableHeader"]),
        ]
        values = [
            Paragraph(str(metrics.get("initial_records", 0)), self.styles["TableCellCenter"]),
            Paragraph(str(metrics.get("duplicates_removed", 0)), self.styles["TableCellCenter"]),
            Paragraph(str(metrics.get("missing_values_imputed", 0)), self.styles["TableCellCenter"]),
            Paragraph(str(metrics.get("invalid_records_dropped", 0)), self.styles["TableCellCenter"]),
            Paragraph(f"<b>{metrics.get('clean_records', 0)}</b>", self.styles["TableCellCenter"]),
        ]

        table = Table([headers, values], colWidths=[1.48 * inch] * 5)
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), header_bg),
                ("BACKGROUND", (0, 1), (-1, 1), row_bg),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )
        return table

    def _build_category_table(self, data: ProcessedData) -> Table:
        """Create detailed category performance breakdown table."""
        header_bg = colors.HexColor("#1E3A8A")
        alt_bg = colors.HexColor("#F8FAFC")
        white = colors.white

        table_rows = [
            [
                Paragraph("<b>Category</b>", self.styles["TableHeader"]),
                Paragraph("<b>Transactions</b>", self.styles["TableHeader"]),
                Paragraph("<b>Units Sold</b>", self.styles["TableHeader"]),
                Paragraph(f"<b>Total Revenue ({self.currency_symbol})</b>", self.styles["TableHeader"]),
                Paragraph(f"<b>Avg Price ({self.currency_symbol})</b>", self.styles["TableHeader"]),
                Paragraph("<b>Revenue Share</b>", self.styles["TableHeader"]),
            ]
        ]

        for _, row in data.category_summary.iterrows():
            table_rows.append([
                Paragraph(f"<b>{row['category']}</b>", self.styles["TableCell"]),
                Paragraph(f"{int(row['record_count']):,}", self.styles["TableCellCenter"]),
                Paragraph(f"{int(row['quantity']):,}", self.styles["TableCellCenter"]),
                Paragraph(f"{self.currency_symbol}{float(row['revenue']):,.2f}", self.styles["TableCellRight"]),
                Paragraph(f"{self.currency_symbol}{float(row['average_price']):,.2f}", self.styles["TableCellRight"]),
                Paragraph(f"{float(row['revenue_share_pct']):.1f}%", self.styles["TableCellCenter"]),
            ])

        # Summary Total Row
        table_rows.append([
            Paragraph("<b>TOTAL</b>", self.styles["TableCell"]),
            Paragraph(f"<b>{data.total_records:,}</b>", self.styles["TableCellCenter"]),
            Paragraph(f"<b>{data.total_quantity:,}</b>", self.styles["TableCellCenter"]),
            Paragraph(f"<b>{self.currency_symbol}{data.total_revenue:,.2f}</b>", self.styles["TableCellRight"]),
            Paragraph(f"<b>{self.currency_symbol}{data.average_revenue:,.2f}</b>", self.styles["TableCellRight"]),
            Paragraph("<b>100.0%</b>", self.styles["TableCellCenter"]),
        ])

        table = Table(
            table_rows,
            colWidths=[1.8 * inch, 0.9 * inch, 0.9 * inch, 1.6 * inch, 1.2 * inch, 1.0 * inch],
        )

        t_style = [
            ("BACKGROUND", (0, 0), (-1, 0), header_bg),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("LINEBELOW", (0, 0), (-1, 0), 1.5, colors.HexColor("#1D4ED8")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]

        # Alternating row colors
        for i in range(1, len(table_rows) - 1):
            bg = alt_bg if i % 2 == 0 else white
            t_style.append(("BACKGROUND", (0, i), (-1, i), bg))

        # Total row highlight
        t_style.append(("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EEF2F6")))
        t_style.append(("LINEABOVE", (0, -1), (-1, -1), 1.2, colors.HexColor("#1E3A8A")))

        table.setStyle(TableStyle(t_style))
        return table

    def _generate_business_insights(self, data: ProcessedData) -> List[str]:
        """Synthesize algorithmic strategic insights and business takeaways."""
        insights = []

        # Category dominance insight
        top_cat_share = (data.top_category_revenue / data.total_revenue) * 100.0 if data.total_revenue > 0 else 0
        insights.append(
            f"<b>Dominant Vertical:</b> <b>{data.top_category}</b> generated {self.currency_symbol}{data.top_category_revenue:,.2f}, "
            f"representing <b>{top_cat_share:.1f}%</b> of aggregate sales. Maintain supplier partnerships and inventory availability in this segment."
        )

        # Product leader insight
        insights.append(
            f"<b>Star Offering:</b> <b>{data.top_product}</b> generated the highest individual product revenue of "
            f"<b>{self.currency_symbol}{data.top_product_revenue:,.2f}</b>, proving strong enterprise market fit."
        )

        # Volume and average order value
        insights.append(
            f"<b>Transaction Health:</b> Across {data.total_records} closed transactions, the average order value stood at "
            f"<b>{self.currency_symbol}{data.average_revenue:,.2f}</b> with an order spread ranging from {self.currency_symbol}{data.min_revenue:,.0f} "
            f"to {self.currency_symbol}{data.max_revenue:,.0f}."
        )

        # Strategic portfolio diversification
        if len(data.category_summary) > 1:
            second_cat = data.category_summary.iloc[1]
            insights.append(
                f"<b>Expansion Opportunity:</b> The second-largest segment, <b>{second_cat['category']}</b>, captured "
                f"<b>{second_cat['revenue_share_pct']:.1f}%</b> ({self.currency_symbol}{float(second_cat['revenue']):,.2f}). "
                f"Targeted cross-selling between {data.top_category} and {second_cat['category']} accounts is recommended for Q4 growth."
            )

        return insights
