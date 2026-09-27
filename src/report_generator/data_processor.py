"""Data processing and business analytics module using Pandas.

Performs data validation, missing-value imputation, deduplication,
statistical aggregation, category breakdown, and temporal trend analysis.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from report_generator.exceptions import DataProcessingError
from report_generator.logger import get_logger

logger = get_logger("data_processor")


@dataclass
class ProcessedData:
    """Container holding cleaned dataframe and derived business metrics."""

    df: pd.DataFrame
    total_records: int
    total_revenue: float
    average_revenue: float
    min_revenue: float
    max_revenue: float
    total_quantity: int
    top_category: str
    top_category_revenue: float
    top_product: str
    top_product_revenue: float
    category_summary: pd.DataFrame
    date_summary: pd.DataFrame
    quality_metrics: Dict[str, int]


class DataProcessor:
    """Processes, cleans, validates, and analyzes enterprise sales data."""

    REQUIRED_COLUMNS = ["product", "category", "quantity", "unit_price", "revenue"]

    def __init__(self, currency_symbol: str = "₹") -> None:
        """Initialize DataProcessor.

        Args:
            currency_symbol: Currency symbol for formatting metrics.
        """
        self.currency_symbol = currency_symbol

    def load_from_csv(self, file_path: Union[str, Path]) -> pd.DataFrame:
        """Load and read raw sales data from a CSV file.

        Args:
            file_path: Path to the target CSV file.

        Returns:
            pd.DataFrame: Raw uncleaned dataframe.

        Raises:
            DataProcessingError: If file not found, empty, or unparseable.
        """
        path = Path(file_path)
        if not path.is_file():
            msg = f"ERROR: Input CSV file was not found: {path}"
            logger.error(msg)
            raise DataProcessingError(msg)

        logger.info("Loading sales records from CSV: %s", path)
        try:
            df = pd.read_csv(path)
            if df.empty:
                msg = f"ERROR: Input CSV file is empty: {path}"
                logger.error(msg)
                raise DataProcessingError(msg)
            return df
        except pd.errors.EmptyDataError as exc:
            msg = f"ERROR: Input CSV file is empty: {path}"
            logger.error(msg)
            raise DataProcessingError(msg, original_exception=exc) from exc
        except pd.errors.ParserError as exc:
            msg = f"ERROR: Invalid CSV format in {path}: {exc}"
            logger.error(msg)
            raise DataProcessingError(msg, original_exception=exc) from exc
        except Exception as exc:
            msg = f"ERROR: Failed to read CSV file {path}: {exc}"
            logger.error(msg)
            raise DataProcessingError(msg, original_exception=exc) from exc

    def load_from_records(self, records: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert a list of record dictionaries into a DataFrame.

        Args:
            records: List of dictionaries.

        Returns:
            pd.DataFrame: Raw uncleaned dataframe.

        Raises:
            DataProcessingError: If records list is empty or malformed.
        """
        if not records:
            msg = "ERROR: Input dataset is empty (no records provided)."
            logger.error(msg)
            raise DataProcessingError(msg)

        logger.info("Loading %d sales records from in-memory objects", len(records))
        return pd.DataFrame(records)

    def process(self, data: Union[str, Path, List[Dict[str, Any]], pd.DataFrame]) -> ProcessedData:
        """Execute full data cleaning, validation, and analytics pipeline.

        Args:
            data: CSV path, list of dicts, or DataFrame.

        Returns:
            ProcessedData: Processed analytics and clean dataframe.

        Raises:
            DataProcessingError: If required fields are missing or data is invalid.
        """
        if isinstance(data, (str, Path)):
            raw_df = self.load_from_csv(data)
        elif isinstance(data, list):
            raw_df = self.load_from_records(data)
        elif isinstance(data, pd.DataFrame):
            raw_df = data.copy()
        else:
            raise DataProcessingError(f"ERROR: Unsupported data input type: {type(data)}")

        initial_count = len(raw_df)
        logger.info("Beginning data processing for %d raw records", initial_count)

        # 1. Normalize column names (lowercase, stripped)
        raw_df.columns = [col.strip().lower().replace(" ", "_") for col in raw_df.columns]

        # Check required columns
        missing_cols = [c for c in self.REQUIRED_COLUMNS if c not in raw_df.columns]
        if missing_cols:
            msg = f"ERROR: Invalid data format. Missing required columns: {', '.join(missing_cols)}"
            logger.error(msg)
            raise DataProcessingError(msg)

        # Ensure date column exists
        if "date" not in raw_df.columns:
            logger.warning("No 'date' column found; using current date as default")
            raw_df["date"] = pd.Timestamp.now().strftime("%Y-%m-%d")

        # 2. Duplicate Removal
        duplicates_count = int(raw_df.duplicated().sum())
        if duplicates_count > 0:
            logger.warning("Detected %d duplicate records; removing duplicates", duplicates_count)
            raw_df = raw_df.drop_duplicates()

        # 3. Missing Value Handling & Type Coercion
        missing_imputed = 0

        # Fill missing categories and products
        if raw_df["category"].isna().any():
            missing_imputed += int(raw_df["category"].isna().sum())
            raw_df["category"] = raw_df["category"].fillna("General")

        if raw_df["product"].isna().any():
            missing_imputed += int(raw_df["product"].isna().sum())
            raw_df["product"] = raw_df["product"].fillna("Standard Item")

        # Numeric conversions with coercion
        raw_df["quantity"] = pd.to_numeric(raw_df["quantity"], errors="coerce")
        raw_df["unit_price"] = pd.to_numeric(raw_df["unit_price"], errors="coerce")
        raw_df["revenue"] = pd.to_numeric(raw_df["revenue"], errors="coerce")

        # Impute missing revenue when quantity & unit_price exist
        recalc_mask = raw_df["revenue"].isna() & raw_df["quantity"].notna() & raw_df["unit_price"].notna()
        if recalc_mask.any():
            count_recalc = int(recalc_mask.sum())
            missing_imputed += count_recalc
            logger.info("Imputed missing revenue for %d records using quantity * unit_price", count_recalc)
            raw_df.loc[recalc_mask, "revenue"] = raw_df.loc[recalc_mask, "quantity"] * raw_df.loc[recalc_mask, "unit_price"]

        # Drop invalid rows where crucial numerical fields remain NaN
        clean_df = raw_df.dropna(subset=["quantity", "unit_price", "revenue"]).copy()
        dropped_count = len(raw_df) - len(clean_df)
        if dropped_count > 0:
            logger.warning("Dropped %d records due to unresolvable numeric values", dropped_count)

        if clean_df.empty:
            msg = "ERROR: No valid records remaining after cleaning and validation."
            logger.error(msg)
            raise DataProcessingError(msg)

        # Enforce strict positive types
        clean_df["quantity"] = clean_df["quantity"].astype(int)
        clean_df["unit_price"] = clean_df["unit_price"].astype(float)
        clean_df["revenue"] = clean_df["revenue"].astype(float)
        clean_df["date"] = pd.to_datetime(clean_df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        clean_df["date"] = clean_df["date"].fillna(pd.Timestamp.now().strftime("%Y-%m-%d"))

        # Sort chronologically
        clean_df = clean_df.sort_values(by="date").reset_index(drop=True)

        final_count = len(clean_df)
        logger.info("Data cleaning complete. Clean records: %d", final_count)

        # 4. Summary Statistics & Aggregations
        total_revenue = float(clean_df["revenue"].sum())
        average_revenue = float(clean_df["revenue"].mean())
        min_revenue = float(clean_df["revenue"].min())
        max_revenue = float(clean_df["revenue"].max())
        total_quantity = int(clean_df["quantity"].sum())

        # Category-wise analysis
        cat_group = clean_df.groupby("category", as_index=False).agg(
            record_count=("revenue", "count"),
            quantity=("quantity", "sum"),
            revenue=("revenue", "sum"),
            average_price=("unit_price", "mean"),
        )
        cat_group["revenue_share_pct"] = (cat_group["revenue"] / total_revenue) * 100.0
        category_summary = cat_group.sort_values(by="revenue", ascending=False).reset_index(drop=True)

        top_cat_row = category_summary.iloc[0]
        top_category = str(top_cat_row["category"])
        top_category_revenue = float(top_cat_row["revenue"])

        # Product-wise analysis
        prod_group = clean_df.groupby("product", as_index=False).agg(
            revenue=("revenue", "sum"),
            quantity=("quantity", "sum"),
        ).sort_values(by="revenue", ascending=False).reset_index(drop=True)
        top_prod_row = prod_group.iloc[0]
        top_product = str(top_prod_row["product"])
        top_product_revenue = float(top_prod_row["revenue"])

        # Date-wise / trend analysis
        date_group = clean_df.groupby("date", as_index=False).agg(
            revenue=("revenue", "sum"),
            quantity=("quantity", "sum"),
            transactions=("product", "count"),
        ).sort_values(by="date").reset_index(drop=True)

        quality_metrics = {
            "initial_records": initial_count,
            "duplicates_removed": duplicates_count,
            "missing_values_imputed": missing_imputed,
            "invalid_records_dropped": dropped_count,
            "clean_records": final_count,
        }

        logger.info(
            "Analytics computed: Records=%d, Revenue=%.2f, TopCategory=%s (%.2f)",
            final_count,
            total_revenue,
            top_category,
            top_category_revenue,
        )

        return ProcessedData(
            df=clean_df,
            total_records=final_count,
            total_revenue=total_revenue,
            average_revenue=average_revenue,
            min_revenue=min_revenue,
            max_revenue=max_revenue,
            total_quantity=total_quantity,
            top_category=top_category,
            top_category_revenue=top_category_revenue,
            top_product=top_product,
            top_product_revenue=top_product_revenue,
            category_summary=category_summary,
            date_summary=date_group,
            quality_metrics=quality_metrics,
        )
