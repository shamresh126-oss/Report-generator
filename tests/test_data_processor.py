"""Unit tests for the DataProcessor module."""

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
# pyrefly: ignore [missing-import]
import pytest

from report_generator.data_processor import DataProcessor, ProcessedData
from report_generator.exceptions import DataProcessingError


@pytest.fixture
def sample_records() -> List[Dict[str, Any]]:
    """Fixture providing standard valid sales records."""
    return [
        {"date": "2026-01-10", "product": "ThinkPad", "category": "Electronics", "quantity": 10, "unit_price": 1000.0, "revenue": 10000.0},
        {"date": "2026-01-15", "product": "Desk Chair", "category": "Furniture", "quantity": 20, "unit_price": 200.0, "revenue": 4000.0},
        {"date": "2026-02-01", "product": "Monitor", "category": "Electronics", "quantity": 5, "unit_price": 500.0, "revenue": 2500.0},
        {"date": "2026-02-10", "product": "Standing Desk", "category": "Furniture", "quantity": 2, "unit_price": 1500.0, "revenue": 3000.0},
    ]


class TestDataProcessor:
    """Test suite for DataProcessor data validation, cleaning, and analytics."""

    def test_missing_csv_file_raises_error(self, tmp_path: Path) -> None:
        """Verify attempting to load a non-existent CSV file raises DataProcessingError."""
        processor = DataProcessor()
        non_existent = tmp_path / "non_existent_data.csv"

        with pytest.raises(DataProcessingError) as exc_info:
            processor.load_from_csv(non_existent)

        assert "ERROR: Input CSV file was not found" in str(exc_info.value)

    def test_empty_csv_file_raises_error(self, tmp_path: Path) -> None:
        """Verify loading an empty CSV file raises DataProcessingError."""
        processor = DataProcessor()
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("", encoding="utf-8")

        with pytest.raises(DataProcessingError) as exc_info:
            processor.load_from_csv(empty_csv)

        assert "ERROR: Input CSV file is empty" in str(exc_info.value)

    def test_missing_required_columns_raises_error(self) -> None:
        """Verify DataFrame missing mandatory columns raises DataProcessingError."""
        processor = DataProcessor()
        invalid_df = pd.DataFrame([
            {"wrong_col_1": 123, "wrong_col_2": "test"}
        ])

        with pytest.raises(DataProcessingError) as exc_info:
            processor.process(invalid_df)

        assert "ERROR: Invalid data format. Missing required columns" in str(exc_info.value)

    def test_duplicate_removal(self) -> None:
        """Verify identical duplicate rows are detected and removed."""
        processor = DataProcessor()
        records_with_duplicates = [
            {"date": "2026-01-01", "product": "Widget A", "category": "Parts", "quantity": 10, "unit_price": 50.0, "revenue": 500.0},
            {"date": "2026-01-01", "product": "Widget A", "category": "Parts", "quantity": 10, "unit_price": 50.0, "revenue": 500.0},  # duplicate
            {"date": "2026-01-02", "product": "Widget B", "category": "Parts", "quantity": 5, "unit_price": 100.0, "revenue": 500.0},
        ]

        result: ProcessedData = processor.process(records_with_duplicates)

        assert result.total_records == 2
        assert result.quality_metrics["duplicates_removed"] == 1
        assert result.total_revenue == 1000.0

    def test_missing_revenue_imputation(self) -> None:
        """Verify missing revenue values are computed as quantity * unit_price."""
        processor = DataProcessor()
        records_with_missing_revenue = [
            {"date": "2026-01-05", "product": "Laptop", "category": "Hardware", "quantity": 3, "unit_price": 1200.0, "revenue": None},
            {"date": "2026-01-06", "product": "Mouse", "category": "Hardware", "quantity": 10, "unit_price": 25.0, "revenue": 250.0},
        ]

        result: ProcessedData = processor.process(records_with_missing_revenue)

        assert result.total_records == 2
        assert result.quality_metrics["missing_values_imputed"] >= 1
        # Laptop revenue imputed to 3 * 1200 = 3600. Total = 3600 + 250 = 3850
        assert result.total_revenue == 3850.0

    def test_invalid_records_dropped(self) -> None:
        """Verify rows where essential numeric values cannot be parsed are dropped."""
        processor = DataProcessor()
        records = [
            {"date": "2026-01-05", "product": "A", "category": "Hardware", "quantity": 5, "unit_price": 100.0, "revenue": 500.0},
            {"date": "2026-01-06", "product": "B", "category": "Hardware", "quantity": "invalid", "unit_price": None, "revenue": None},
        ]

        result = processor.process(records)
        assert result.total_records == 1
        assert result.quality_metrics["invalid_records_dropped"] == 1

    def test_summary_calculations(self, sample_records: List[Dict[str, Any]]) -> None:
        """Verify financial metrics and summary statistics."""
        processor = DataProcessor(currency_symbol="₹")
        result = processor.process(sample_records)

        assert result.total_records == 4
        # 10000 + 4000 + 2500 + 3000 = 19500
        assert result.total_revenue == 19500.0
        assert result.average_revenue == 19500.0 / 4
        assert result.min_revenue == 2500.0
        assert result.max_revenue == 10000.0
        assert result.total_quantity == 37  # 10 + 20 + 5 + 2

    def test_category_breakdown(self, sample_records: List[Dict[str, Any]]) -> None:
        """Verify category breakdown and top category identification."""
        processor = DataProcessor()
        result = processor.process(sample_records)

        # Electronics: 10000 + 2500 = 12500
        # Furniture: 4000 + 3000 = 7000
        assert result.top_category == "Electronics"
        assert result.top_category_revenue == 12500.0

        cat_df = result.category_summary
        assert len(cat_df) == 2
        assert cat_df.iloc[0]["category"] == "Electronics"
        assert cat_df.iloc[0]["revenue"] == 12500.0
        assert round(cat_df["revenue_share_pct"].sum(), 2) == 100.0

    def test_load_from_csv_file(self, tmp_path: Path) -> None:
        """Verify successful processing from a physical CSV file."""
        csv_file = tmp_path / "valid_sales.csv"
        csv_file.write_text(
            "date,product,category,quantity,unit_price,revenue\n"
            "2026-04-01,Test Widget,Tools,10,15.0,150.0\n"
            "2026-04-02,Test Gear,Tools,5,20.0,100.0\n",
            encoding="utf-8",
        )

        processor = DataProcessor()
        result = processor.process(csv_file)

        assert result.total_records == 2
        assert result.total_revenue == 250.0
        assert result.top_category == "Tools"

    def test_empty_records_list_raises_error(self) -> None:
        """Verify empty records list raises DataProcessingError."""
        processor = DataProcessor()
        with pytest.raises(DataProcessingError) as exc_info:
            processor.process([])
        assert "ERROR: Input dataset is empty" in str(exc_info.value)

    def test_missing_category_and_product_imputation(self) -> None:
        """Verify null category and product are imputed with default labels."""
        processor = DataProcessor()
        records = [
            {"date": "2026-06-01", "product": None, "category": None, "quantity": 1, "unit_price": 50.0, "revenue": 50.0}
        ]
        result = processor.process(records)
        assert result.df.iloc[0]["category"] == "General"
        assert result.df.iloc[0]["product"] == "Standard Item"

    def test_unsupported_data_type_raises_error(self) -> None:
        """Verify passing an unsupported type raises DataProcessingError."""
        processor = DataProcessor()
        with pytest.raises(DataProcessingError) as exc_info:
            processor.process(12345)  # type: ignore
        assert "ERROR: Unsupported data input type" in str(exc_info.value)

