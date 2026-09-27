"""Unit tests for the ChartGenerator and PDFReportGenerator modules."""

from pathlib import Path

# pyrefly: ignore [missing-import]
import pytest

from report_generator.charts import ChartGenerator
from report_generator.data_processor import DataProcessor, ProcessedData
from report_generator.exceptions import PDFGenerationError
from report_generator.pdf_report import PDFReportGenerator


@pytest.fixture
def processed_data() -> ProcessedData:
    """Fixture providing a populated ProcessedData object."""
    records = [
        {"date": "2026-05-01", "product": "Pro Laptop", "category": "Computers", "quantity": 10, "unit_price": 1000.0, "revenue": 10000.0},
        {"date": "2026-05-05", "product": "Office Chair", "category": "Furniture", "quantity": 15, "unit_price": 200.0, "revenue": 3000.0},
        {"date": "2026-05-10", "product": "Wireless Mouse", "category": "Computers", "quantity": 25, "unit_price": 50.0, "revenue": 1250.0},
        {"date": "2026-05-15", "product": "Filing Cabinet", "category": "Furniture", "quantity": 5, "unit_price": 300.0, "revenue": 1500.0},
    ]
    processor = DataProcessor(currency_symbol="₹")
    return processor.process(records)


class TestChartAndPDFReport:
    """Test suite for chart rendering and PDF document generation."""

    def test_chart_generation(self, tmp_path: Path, processed_data: ProcessedData) -> None:
        """Verify ChartGenerator produces all three required PNG chart artifacts."""
        charts_dir = tmp_path / "charts"
        chart_gen = ChartGenerator(output_dir=charts_dir, currency_symbol="₹")

        chart_paths = chart_gen.generate_all(processed_data)

        assert "category_revenue" in chart_paths
        assert "revenue_trend" in chart_paths
        assert "top_categories" in chart_paths

        for name, path in chart_paths.items():
            assert path.exists(), f"Expected chart file for {name} does not exist at {path}"
            assert path.stat().st_size > 0, f"Chart file {name} is empty"

    def test_pdf_generation_success(
        self, tmp_path: Path, processed_data: ProcessedData
    ) -> None:
        """Verify PDFReportGenerator builds a valid non-empty PDF file."""
        reports_dir = tmp_path / "reports"
        charts_dir = tmp_path / "charts"

        chart_gen = ChartGenerator(output_dir=charts_dir, currency_symbol="₹")
        chart_paths = chart_gen.generate_all(processed_data)

        pdf_gen = PDFReportGenerator(
            output_dir=reports_dir,
            company_name="Acme Corp Test",
            report_title="TEST PERFORMANCE REPORT",
            currency_symbol="₹",
        )

        output_pdf = pdf_gen.generate(
            data=processed_data,
            chart_paths=chart_paths,
            output_filename="test_output.pdf",
            data_source="Test Unit Suite",
        )

        assert output_pdf.exists()
        assert output_pdf.name == "test_output.pdf"
        assert output_pdf.stat().st_size > 1000  # ReportLab PDF with images will be substantial

    def test_pdf_generation_default_filename(
        self, tmp_path: Path, processed_data: ProcessedData
    ) -> None:
        """Verify default date-stamped filename is generated when no filename is specified."""
        reports_dir = tmp_path / "reports"
        charts_dir = tmp_path / "charts"

        chart_gen = ChartGenerator(output_dir=charts_dir)
        chart_paths = chart_gen.generate_all(processed_data)

        pdf_gen = PDFReportGenerator(output_dir=reports_dir)
        output_pdf = pdf_gen.generate(
            data=processed_data,
            chart_paths=chart_paths,
        )

        assert output_pdf.exists()
        assert output_pdf.name.startswith("business_report_")
        assert output_pdf.name.endswith(".pdf")

    def test_pdf_generation_error_handling(
        self, tmp_path: Path, processed_data: ProcessedData
    ) -> None:
        """Verify PDFGenerationError is raised when destination directory is unwritable."""
        # Point to an impossible file path (e.g. using a filename that is an existing directory)
        dir_as_file = tmp_path / "unusable_directory"
        dir_as_file.mkdir()

        pdf_gen = PDFReportGenerator(output_dir=tmp_path)
        chart_gen = ChartGenerator(output_dir=tmp_path)
        chart_paths = chart_gen.generate_all(processed_data)

        with pytest.raises(PDFGenerationError):
            # Attempting to save PDF directly onto an existing directory path triggers an OS error in doc.build
            pdf_gen.generate(
                data=processed_data,
                chart_paths=chart_paths,
                output_filename=str(dir_as_file),
            )
